"""Real legacy process lifecycle and bounded public-download release checks."""

import asyncio
import hashlib
import os
import sys
import time
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import httpx
import test_policy

from asset_library import fetch
from media_tools import command
from motion_board import write_frames


class ReleaseBoundaryTests(unittest.TestCase):
    setUp = test_policy.PolicyTests.setUp
    load = test_policy.PolicyTests.load

    def tool_settings(self, timeout=3):
        settings = self.load()
        settings.data["limits"]["command_timeout_seconds"] = timeout
        return replace(
            settings,
            machine={
                **settings.machine,
                "ffmpeg": Path(sys.executable),
                "ffprobe": Path(sys.executable),
            },
        )

    def test_argument_only_command_preserves_output_and_nonzero_diagnostics(self):
        settings = self.tool_settings()
        script = "import sys; print(sys.argv[1]); print('private diagnostic',file=sys.stderr)"
        argument = "spaces; $(not-a-shell) & literals"
        self.assertEqual(
            command(settings, "ffprobe", ["-c", script, argument], self.root).strip(), argument
        )
        self.assertEqual(
            command(settings, "ffmpeg", ["-c", script, argument], self.root).strip(),
            "private diagnostic",
        )
        with self.assertRaises(RuntimeError):
            command(
                settings,
                "ffprobe",
                ["-c", "import sys; print('failed diagnostic',file=sys.stderr); sys.exit(7)"],
                self.root,
            )
        self.assertIn("failed diagnostic", (self.root / "ffprobe-failure.log").read_text())

    def test_command_timeout_kills_and_reaps_child(self):
        pid_file = self.root / "child.pid"
        script = "import os,sys,time; from pathlib import Path; Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(20)"
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            command(self.tool_settings(1), "ffprobe", ["-c", script, str(pid_file)], self.root)
        self.assertLess(time.monotonic() - started, 4)
        with self.assertRaises(ProcessLookupError):
            os.kill(int(pid_file.read_text()), 0)

    def test_encoder_transfers_all_frames_before_clean_exit(self):
        target = self.root / "received.txt"
        frames = [b"first-frame" * 8000, b"second-frame" * 9000]
        script = "import sys,hashlib; from pathlib import Path; Path(sys.argv[1]).write_text(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())"
        write_frames(
            [sys.executable, "-c", script, str(target)],
            self.root,
            self.root / "encoder.log",
            3,
            frames,
        )
        self.assertEqual(target.read_text(), hashlib.sha256(b"".join(frames)).hexdigest())

    def test_http_stream_bounds_redirects_and_denied_origins(self):
        settings = self.load()
        settings.data["online"]["max_bytes"] = 3
        library = {"allowed_hosts": ["assets.example.test"]}

        class Chunks(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b"ab"
                yield b"cd"

        class SingleChunk(httpx.AsyncByteStream):
            def __init__(self, data):
                self.data = data

            async def __aiter__(self):
                yield self.data

        responses = [
            (httpx.Response(200, stream=SingleChunk(b"abc")), b"abc"),
            (httpx.Response(301, headers={"location": "https://outside.example.test/file"}), None),
            (httpx.Response(200, headers={"content-length": "400"}, content=b"abc"), None),
            (httpx.Response(200, stream=Chunks()), None),
            (httpx.Response(200, stream=SingleChunk(b"")), None),
            (
                httpx.Response(200, headers={"Content-Encoding": "gzip"}, stream=SingleChunk(b"x")),
                None,
            ),
        ]
        for response, expected in responses:
            client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: response))
            with patch("asset_library.httpx.AsyncClient", return_value=client) as factory:
                if expected is None:
                    with self.assertRaises(ValueError):
                        fetch(settings, library, "https://assets.example.test/file")
                else:
                    self.assertEqual(
                        fetch(settings, library, "https://assets.example.test/file"), expected
                    )
                self.assertFalse(factory.call_args.kwargs["follow_redirects"])
                self.assertFalse(factory.call_args.kwargs["trust_env"])
                self.assertTrue(factory.call_args.kwargs["verify"])
        with patch(
            "asset_library.httpx.AsyncClient",
            side_effect=AssertionError("Denied URL must not open a client"),
        ):
            for url in ("http://assets.example.test/file", "https://outside.example.test/file"):
                with self.assertRaises(ValueError):
                    fetch(settings, library, url)

    def test_http_whole_operation_deadline_stops_slow_stream(self):
        settings = self.load()
        settings.data["online"]["timeout_seconds"] = 0.05

        class SlowStream(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b"a"
                await asyncio.sleep(20)
                yield b"b"

        client = httpx.AsyncClient(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=SlowStream()))
        )
        started = time.monotonic()
        with patch("asset_library.httpx.AsyncClient", return_value=client):
            with self.assertRaises(TimeoutError):
                fetch(
                    settings,
                    {"allowed_hosts": ["assets.example.test"]},
                    "https://assets.example.test/file",
                )
        self.assertLess(time.monotonic() - started, 1)

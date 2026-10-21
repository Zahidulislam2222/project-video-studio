"""Critical production contracts, workspace isolation, revisions and real media paths."""

import asyncio
import copy
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from PIL import Image
from pydantic import ValidationError

from studio_v2.__main__ import import_asset
from studio_v2.captions import write_ass
from studio_v2.creative import spoken_beats, train_profile
from studio_v2.graphics import Painter
from studio_v2.models import Project
from studio_v2.package import restore
from studio_v2.preview import preview
from studio_v2.process import render_lock, run, stream_duration
from studio_v2.production import prepare, read_srt, revise
from studio_v2.render import render
from studio_v2.settings import Settings
from studio_v2.store import Conflict, Store


class ContractTests(unittest.TestCase):
    def project(self, **updates):
        return Project.model_validate(
            {"title": "Production test", "shots": [{"id": "one", "title": "First shot"}], **updates}
        )

    def test_closed_contract_and_finite_numbers(self):
        for update in [
            {"command": "execute"},
            {"shots": [{"id": "../escape", "title": "No"}]},
            {"shots": [{"id": "one", "title": "No", "duration": float("nan")}]},
        ]:
            with self.assertRaises(ValidationError):
                self.project(**update)

    def test_layout_templates_and_explicit_overrides(self):
        p = self.project(
            shots=[
                {
                    "id": "one",
                    "title": "Compare",
                    "layout": "stacked",
                    "layers": [{"asset": "first"}, {"asset": "second"}],
                }
            ]
        )
        a, b = p.shots[0].layers
        self.assertLess(a.y, b.y)
        self.assertEqual(a.width, b.width)
        p = self.project(
            shots=[
                {
                    "id": "one",
                    "title": "Custom",
                    "layers": [{"asset": "first", "x": 0.2, "y": 0.3, "width": 0.4, "height": 0.4}],
                }
            ]
        )
        self.assertEqual(p.shots[0].layers[0].x, 0.2)

    def test_proof_needs_owner_source_and_cannot_be_illustration(self):
        for shot in [
            {"id": "one", "title": "No", "proof": True},
            {
                "id": "one",
                "title": "No",
                "proof": True,
                "layout": "diagram",
                "layers": [{"asset": "first"}],
                "source_note": "Owner capture",
            },
        ]:
            with self.assertRaises(ValidationError):
                self.project(shots=[shot])

    def test_mkv_and_webm_stream_timing(self):
        info = {
            "format": {"duration": "100"},
            "streams": [{"codec_type": "video", "tags": {"DURATION": "00:00:01.250000000"}}],
        }
        self.assertEqual(stream_duration(info, "video"), 1.25)

    def test_approved_male_only(self):
        with self.assertRaises(ValidationError):
            self.project(voice="unknown")

    def test_semantic_beats_follow_real_cues_and_keep_authored_timing(self):
        p = self.project()
        settings = Settings.load()
        shot = spoken_beats(
            settings,
            p.shots[0],
            [
                {"start": 0, "text": "First idea"},
                {"start": 1, "text": "Continue"},
                {"start": 5, "text": "Next idea"},
            ],
        )
        self.assertEqual([b.start for b in shot.beats], [0, 5])
        self.assertIs(spoken_beats(settings, shot, []), shot)

    def test_timestamped_revision_preserves_previous_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = self.project(
                shots=[
                    {"id": "one", "title": "Before", "timing": "fixed", "duration": 4},
                    {"id": "two", "title": "Next", "timing": "fixed", "duration": 4},
                ]
            )
            source = root / "project.json"
            source.write_text(project.model_dump_json())
            previous = source.read_bytes()
            changes = root / "changes.json"
            changes.write_text(json.dumps({"at": [{"seconds": 5, "set": {"title": "Corrected"}}]}))
            output = root / "revision.json"
            revise(source, changes, output)
            self.assertEqual(
                Project.model_validate_json(output.read_text()).shots[1].title, "Corrected"
            )
            self.assertEqual(source.read_bytes(), previous)
            with self.assertRaises(ValueError):
                revise(source, changes, output)

    def test_invalid_srt_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "captions.srt"
            source.write_text("1\n00:00:02,000 --> 00:00:01,000\nWrong\n")
            with self.assertRaises(ValueError):
                read_srt(source)

    def test_portrait_captions_use_pixel_resolution_and_bounded_safe_lines(self):
        with tempfile.TemporaryDirectory() as temporary:
            settings = Settings.load()
            p = self.project(ratio="portrait")
            output = Path(temporary) / "Captions.ass"
            write_ass(
                settings,
                p,
                [{"start": 0, "end": 2, "text": "A clear caption with {untrusted} marks"}],
                output,
            )
            text = output.read_text()
            self.assertIn("PlayResX: 1080", text)
            self.assertIn("PlayResY: 1920", text)
            self.assertIn(",49,", text)
            self.assertNotIn("{untrusted}", text)
            with self.assertRaises(ValueError):
                write_ass(
                    settings,
                    p,
                    [{"start": 0, "end": 2, "text": "unreasonably long caption " * 20}],
                    output,
                )


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = replace(Settings.load(), data=Path(self.temp.name))
        self.store = Store(self.settings)
        self.body = Project.model_validate(
            {"title": "Test", "shots": [{"id": "first", "title": "First"}]}
        ).model_dump()

    def tearDown(self):
        self.temp.cleanup()

    def test_tenant_isolation_and_revision_conflicts(self):
        a = self.store.save("alice", self.body)
        self.assertIsNone(self.store.project("bob", a["id"]))
        self.store.save("alice", self.body, a["id"], 1)
        with self.assertRaises(Conflict):
            self.store.save("alice", self.body, a["id"], 1)

    def test_idempotency_recovery_and_cancellation(self):
        project = self.store.save("alice", self.body)
        a = self.store.enqueue("alice", project, "one")
        b = self.store.enqueue("alice", project, "one")
        self.assertEqual(a["id"], b["id"])
        self.assertIsNone(self.store.job("bob", a["id"]))
        self.store.next_job()
        self.store.recover()
        self.assertEqual(self.store.job("alice", a["id"])["state"], "interrupted")
        c = self.store.enqueue("alice", project, "two")
        self.assertFalse(self.store.cancel("bob", c["id"]))
        self.assertTrue(self.store.cancel("alice", c["id"]))
        self.store.update_job(c["id"], "complete", 1, "Must not win")
        self.assertEqual(self.store.job("alice", c["id"])["state"], "cancelled")

    def test_callout_fits_even_at_edge(self):
        p = Project.model_validate(
            {
                "title": "Fit",
                "shots": [
                    {
                        "id": "first",
                        "title": "Fit",
                        "callouts": [
                            {
                                "text": "An important result with enough detail to explain the next step clearly",
                                "x": 0.8,
                                "y": 0.85,
                                "end": 2,
                            }
                        ],
                    }
                ],
            }
        )
        painter = Painter(self.settings, p, p.shots[0])
        image, x, y = painter.callout(p.shots[0].callouts[0], 1920, 1080)
        self.assertLessEqual(x + image.width, 1920)
        self.assertLessEqual(y + image.height, 1080)

    def test_palette_training_and_exclusive_render_lease(self):
        source = Path(self.temp.name) / "reference.png"
        Image.new("RGB", (128, 128), "#1b2540").save(source)
        result = train_profile(
            self.settings, [source], Path(self.temp.name) / "profile", "Readable technical design"
        )
        self.assertGreaterEqual(result["text_contrast"], 4.5)
        with render_lock(self.settings):
            with self.assertRaises(ValueError):
                with render_lock(self.settings):
                    pass

    def test_portable_restore_rejects_inputs_symlink_escape(self):
        root = Path(self.temp.name)
        package = root / "package"
        package.mkdir()
        outside = root / "outside"
        outside.mkdir()
        (package / "Inputs").symlink_to(outside, target_is_directory=True)
        (package / "project.json").write_text(json.dumps(self.body))
        (package / "SourceInputs.json").write_text("[]")
        with self.assertRaises(ValueError):
            restore(self.settings, self.store, "alice", package, root / "restored.json")


class MediaTests(unittest.IsolatedAsyncioTestCase):
    async def test_recorded_draft_composed_preview_and_silent_tail(self):
        import math
        import struct
        import wave

        with tempfile.TemporaryDirectory() as temporary:
            config = copy.deepcopy(Settings.load().config)
            config["render"]["dimensions"]["landscape"] = [640, 360]
            settings = replace(
                Settings.load(),
                config=config,
                data=Path(temporary) / "data",
                model=None,
                voices=None,
            )
            if not settings.ffmpeg or not settings.ffprobe:
                self.skipTest("Configure FFmpeg")
            store = Store(settings)
            root = Path(temporary)
            recording = root / "recording.wav"
            with wave.open(str(recording), "wb") as file:
                file.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                file.writeframes(
                    b"".join(
                        struct.pack("<h", round(math.sin(i / 16000 * 440 * math.tau) * 6000))
                        for i in range(32000)
                    )
                )
            captions = root / "captions.srt"
            captions.write_text("1\n00:00:00,000 --> 00:00:01,000\nOwner supplied speech\n")
            image = root / "view.png"
            Image.new("RGB", (400, 240), "#cf222e").save(image)
            request = root / "request.json"
            request.write_text(
                json.dumps(
                    {
                        "title": "Recorded workflow",
                        "recording": str(recording),
                        "captions_file": str(captions),
                        "footage": [str(image)],
                        "companion": str(image),
                        "media_approved": True,
                    }
                )
            )
            project_file = await prepare(settings, store, "alice", request, root / "production")
            project = Project.model_validate_json(project_file.read_text())
            self.assertEqual(project.shots[0].layout, "side-by-side")
            self.assertEqual(len(project.shots[0].layers), 2)
            self.assertTrue((root / "production" / "Storyboard.txt").is_file())
            await preview(settings, store, "alice", project, root / "preview", stills=True)
            self.assertTrue((root / "preview" / "style-1.png").is_file())
            shot = project.shots[0]
            shot.audio_seconds = 1
            shot.duration = 3
            shot.timing = "fixed"
            saved = store.save("alice", project.model_dump())
            job = store.enqueue("alice", saved, "recorded-tail")
            report = await render(settings, store, job)
            self.assertEqual(report["expected_frames"], 90)
            frame = await run(
                [
                    settings.ffmpeg,
                    "-v",
                    "error",
                    "-ss",
                    "1.5",
                    "-i",
                    str(settings.contained("renders", job["id"], shot.id, "picture.mp4")),
                    "-frames:v",
                    "1",
                    "-f",
                    "rawvideo",
                    "-pix_fmt",
                    "rgb24",
                    "pipe:1",
                ],
                root,
                settings.config["render"]["timeout_seconds"],
            )
            picture = Image.frombytes("RGB", (640, 360), frame)
            note = picture.crop((35, 284, 605, 299))
            self.assertTrue(
                any(min(pixel) > 180 for pixel in note.getdata()),
                "Source credit must stay visible above supplied footage",
            )
            with wave.open(
                str(settings.contained("renders", job["id"], shot.id, "sound.wav")), "rb"
            ) as file:
                file.setpos(round(1.5 * file.getframerate()))
                tail = file.readframes(file.getframerate())
            self.assertTrue(all(value == 0 for value in tail))
            self.assertTrue(settings.contained("renders", job["id"], "Inputs").is_dir())

    async def test_mask_layout_popup_real_export_and_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = copy.deepcopy(Settings.load().config)
            config["render"]["dimensions"]["landscape"] = [320, 180]
            config["render"]["fps"] = 12
            settings = replace(
                Settings.load(), config=config, data=Path(temporary), model=None, voices=None
            )
            if not settings.ffmpeg or not settings.ffprobe:
                self.skipTest("Configure real FFmpeg and ffprobe")
            store = Store(settings)
            path = Path(temporary) / "source.png"
            Image.new("RGB", (160, 90), "red").save(path)
            white = Path(temporary) / "mask.png"
            Image.new("L", (160, 90), 255).save(white)
            source = import_asset(settings, store, "alice", path)
            mask = import_asset(settings, store, "alice", white)
            p = Project.model_validate(
                {
                    "title": "Real export",
                    "shots": [
                        {
                            "id": "first",
                            "title": "Source",
                            "duration": 1,
                            "transition": "cut",
                            "layers": [{"asset": source, "mask": mask, "opacity": 0.2}],
                            "callouts": [
                                {"text": "Source", "x": 0.8, "y": 0.8, "start": 0.1, "end": 0.9}
                            ],
                        }
                    ],
                }
            )
            saved = store.save("alice", p.model_dump())
            job = store.enqueue("alice", saved, "first")
            report = await render(settings, store, job)
            self.assertEqual(report["expected_frames"], 12)
            second = store.enqueue("alice", saved, "second")
            await render(settings, store, second, resume=job["id"])
            board = json.loads(
                settings.contained("renders", second["id"], "Storyboard.json").read_text()
            )
            self.assertTrue(board["scenes"][0]["reused"])
            with self.assertRaises(ValueError):
                await render(
                    settings, store, store.enqueue("bob", saved, "third"), resume=job["id"]
                )

    async def test_cancel_terminates_child(self):
        import sys

        with tempfile.TemporaryDirectory() as temporary:
            task = asyncio.create_task(
                run([sys.executable, "-c", "import time; time.sleep(30)"], Path(temporary), 60)
            )
            await asyncio.sleep(0.1)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(task, 3)

"""Behavioral checks for adaptive timing, motion, sound and licensed asset boundaries."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

import httpx
import test_policy

from asset_library import acquire, fetch, resolve, search
from config import check_timing, film_settings, remote_request
from motion_design import picture_motion, title_motion
from studio import build, new_project


class FlexibleTests(unittest.TestCase):
    setUp = test_policy.PolicyTests.setUp
    load = test_policy.PolicyTests.load
    film = test_policy.PolicyTests.film

    def timeline(self, film, duration):
        fps = self.settings["render"]["fps"]
        times = [4] + [(duration - 8) / (len(film.scenes) - 2)] * (len(film.scenes) - 2) + [4]
        return [{"duration": t, "frames": round(t * fps)} for t in times]

    def formatted(self, name="short"):
        data = copy.deepcopy(self.template)
        data["format"] = name
        data["scenes"][0]["role"] = "intro"
        data["scenes"][-1]["role"] = "outro"
        return data

    def test_duration_boundaries(self):
        for name, low, high in (("short", 60, 120), ("long", 240, 300)):
            film = self.film(self.formatted(name))
            for seconds in (low, high):
                self.assertEqual(
                    check_timing(self.load(), film, self.timeline(film, seconds))["seconds"],
                    seconds,
                )
            for seconds in (low - 1, high + 1):
                with self.assertRaises(ValueError):
                    check_timing(self.load(), film, self.timeline(film, seconds))

    def test_intro_budget_rejects_slow_opening(self):
        film = self.film(self.formatted())
        timing = self.timeline(film, 90)
        timing[0] = {"duration": 10, "frames": 300}
        with self.assertRaisesRegex(ValueError, "intro exceeds"):
            check_timing(self.load(), film, timing)

    def test_formatted_film_requires_bookends(self):
        data = self.formatted()
        data["scenes"][0]["role"] = "body"
        with self.assertRaises(ValueError):
            self.film(data)

    def test_legacy_film_has_no_new_sound_or_motion(self):
        film = self.film()
        self.assertEqual(film.format_name, "custom")
        self.assertEqual(film.motion, "none")
        self.assertFalse(film.sound_enabled)

    def test_format_override_does_not_mutate_defaults(self):
        settings = self.load()
        updated = film_settings(settings, "short")
        self.assertEqual(updated.data["render"]["height"], 1920)
        self.assertEqual(settings.data["render"]["height"], 1080)

    def test_new_named_motion_preset_needs_no_code_change(self):
        self.settings["motion_presets"]["new-style"] = copy.deepcopy(
            self.settings["motion_presets"]["calm"]
        )
        data = self.formatted()
        data["motion"] = "new-style"
        self.assertEqual(self.film(data).scenes[1].motion, "new-style")

    def test_bad_motion_is_rejected(self):
        self.settings["motion_presets"]["calm"]["image_zoom"] = 8
        with self.assertRaises(ValueError):
            self.load()

    def test_scene_motion_override(self):
        data = self.formatted()
        data["motion"] = "dynamic"
        data["scenes"][1]["motion"] = "none"
        film = self.film(data)
        self.assertEqual(film.scenes[1].motion, "none")
        self.assertIn("pow", title_motion(self.load(), film.scenes[0], 100))

    def test_recordings_do_not_zoom(self):
        scene = replace(self.film().scenes[0], media=self.root / "recording.mp4", motion="dynamic")
        self.assertEqual(picture_motion(self.load(), scene, {"frames": 90}), "")
        self.assertIn(
            "zoompan",
            picture_motion(
                self.load(), replace(scene, media=self.root / "image.jpg"), {"frames": 90}
            ),
        )

    def request(self, **overrides):
        return {"library": "commons", "kind": "image", "query": "clouds", **overrides}

    def test_missing_illustration_can_have_request(self):
        data = copy.deepcopy(self.template)
        data["scenes"][0].update(media="missing.jpg", asset_request=self.request())
        self.assertIsNotNone(self.film(data).scenes[0].asset_request)

    def test_stock_cannot_replace_project_proof(self):
        data = copy.deepcopy(self.template)
        data["scenes"][0].update(role="proof", asset_request=self.request())
        with self.assertRaises(ValueError):
            self.film(data)

    def test_online_audio_requires_chosen_non_music_file(self):
        settings = self.load()
        for request in (
            self.request(kind="audio"),
            self.request(kind="audio", title="File:Rain.ogg"),
        ):
            with self.assertRaises(ValueError):
                remote_request(request, settings, "audio")
        self.assertIsNotNone(
            remote_request(
                self.request(kind="audio", title="File:Rain.ogg", non_musical_confirmed=True),
                settings,
                "audio",
            )
        )

    def test_music_effect_rejected(self):
        data = copy.deepcopy(self.template)
        data["scenes"][0]["effect"] = "music"
        with self.assertRaises(ValueError):
            self.film(data)

    def test_ambience_requires_non_music_confirmation(self):
        folder = self.root / "project"
        folder.mkdir()
        (folder / "room.wav").touch()
        data = copy.deepcopy(self.template)
        data["sound"] = {"enabled": True, "ambience": "room.wav"}
        with self.assertRaises(ValueError):
            self.film(data)

    def test_project_sound_tuning_is_effective_and_isolated(self):
        data = copy.deepcopy(self.template)
        data["sound"] = {"enabled": True, "overrides": {"effects_gain_db": -36}}
        film = self.film(data)
        settings = self.load()
        effective = film_settings(settings, film.format_name, film.sound_overrides)
        self.assertEqual(effective.data["sound"]["effects_gain_db"], -36)
        self.assertEqual(settings.data["sound"]["effects_gain_db"], -24)
        data["sound"]["overrides"]["effects_gain_db"] = 0
        with self.assertRaises(ValueError):
            self.film(data)

    def test_disabled_sound_does_not_need_ambience_resource(self):
        data = copy.deepcopy(self.template)
        data["sound"] = {"enabled": False, "ambience": "assets/online/missing.wav"}
        film = self.film(data)
        output = self.root / "output"
        output.mkdir()
        self.assertFalse(resolve(self.load(), film, output).sound_enabled)

    def test_remote_url_security(self):
        settings = self.load()
        library = settings.data["asset_libraries"]["commons"]
        for url in (
            "http://commons.wikimedia.org/file",
            "https://127.0.0.1/file",
            "file:///etc/passwd",
            "https://commons.wikimedia.org.evil.test/file",
            "https://user:secret@commons.wikimedia.org/file",
            "https://commons.wikimedia.org:8443/file",
        ):
            with self.assertRaises(ValueError):
                fetch(settings, library, url)

    def test_search_rejects_unknown_license_and_wrong_media(self):
        response = {
            "query": {
                "pages": {
                    "1": {
                        "title": "File:Cloud.jpg",
                        "imageinfo": [
                            {
                                "url": "unused",
                                "descriptionurl": "unused",
                                "size": 50,
                                "mime": "image/jpeg",
                                "extmetadata": {
                                    "Artist": {"value": "A creator"},
                                    "LicenseShortName": {"value": "All rights reserved"},
                                },
                            }
                        ],
                    }
                }
            }
        }
        with patch("asset_library.fetch", return_value=json.dumps(response).encode()):
            self.assertEqual(search(self.load(), self.request()), [])
            response["query"]["pages"]["1"]["imageinfo"][0]["extmetadata"]["LicenseShortName"][
                "value"
            ] = "CC0"
        with patch("asset_library.fetch", return_value=json.dumps(response).encode()):
            self.assertEqual(len(search(self.load(), self.request())), 1)
            self.assertEqual(search(self.load(), self.request(kind="video")), [])

    def test_search_filters_media_kind_before_limiting_candidates(self):
        for kind in ("image", "video", "audio"):
            with patch("asset_library.fetch", return_value=b"{}") as fetch:
                search(self.load(), self.request(kind=kind))
                query = parse_qs(urlsplit(fetch.call_args.args[2]).query)["gsrsearch"][0]
                self.assertIn(
                    self.settings["asset_libraries"]["commons"]["search_filters"][kind], query
                )

    def test_verified_cache_reusable_offline_and_tampering_rejected(self):
        folder = self.root / "project"
        cache = folder / "assets/online"
        cache.mkdir(parents=True)
        request = self.request()
        identity = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        target = cache / "test.jpg"
        target.write_bytes(b"test asset")
        record = {
            "path": "assets/online/test.jpg",
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "request": request,
            **self.provenance(),
        }
        (cache / (identity + ".json")).write_text(json.dumps(record))
        self.settings["online"]["enabled"] = False
        self.assertEqual(acquire(self.load(), folder, request), record)
        target.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "integrity"):
            acquire(self.load(), folder, request)

    def provenance(self):
        url = self.settings["asset_libraries"]["commons"]["api_url"]
        return {
            "library": "commons",
            "kind": "image",
            "mime": "image/jpeg",
            "suffix": ".jpg",
            "title": "File:Cloud.jpg",
            "license": "CC0",
            "creator": "Test artist",
            "source": url,
            "url": url,
            "license_url": "",
            "modifications": "Test illustration",
        }

    def test_cache_rechecks_current_license_policy(self):
        from asset_library import validate_record

        record = self.provenance()
        self.settings["asset_libraries"]["commons"]["licenses"].remove("CC0")
        with self.assertRaisesRegex(ValueError, "current license"):
            validate_record(self.load(), self.request(), record)

    def test_existing_cache_path_retains_label_and_attribution(self):
        data = copy.deepcopy(self.template)
        data["overlay_titles"] = False
        data["scenes"][0]["media"] = "assets/online/test.jpg"
        folder = self.root / "project"
        cache = folder / "assets/online"
        cache.mkdir(parents=True)
        (cache / "test.jpg").write_bytes(b"test image")
        record = {
            **self.provenance(),
            "path": "assets/online/test.jpg",
            "request": self.request(),
            "sha256": "test-hash",
        }
        (cache / "test.json").write_text(json.dumps(record))
        film = self.film(data)
        output = self.root / "output"
        output.mkdir()
        with patch("asset_library.acquire", return_value=record):
            resolved = resolve(self.load(), film, output)
        self.assertTrue(resolved.scenes[0].illustrative)
        self.assertIn("Illustrative stock", resolved.scenes[0].subtitle)
        self.assertIn("Test artist", (output / "Attribution.txt").read_text())
        changed = replace(film.scenes[0], asset_request=self.request(query="new subject"))
        with self.assertRaisesRegex(ValueError, "request changed"):
            resolve(self.load(), replace(film, scenes=(changed,)), output)

    def test_download_limits_and_redirects_fail_closed(self):
        settings = self.load()
        library = settings.data["asset_libraries"]["commons"]
        for status, size in ((302, "100"), (200, str(settings.data["online"]["max_bytes"] + 1))):
            class UnreadStream(httpx.AsyncByteStream):
                async def __aiter__(self):
                    raise AssertionError("Rejected response body must not be consumed")
                    yield b""

            response = httpx.Response(status, headers={"content-length": size}, stream=UnreadStream())
            client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: response))
            with patch("asset_library.httpx.AsyncClient", return_value=client):
                with self.assertRaises(ValueError):
                    fetch(settings, library, library["api_url"])

    def test_invalid_download_keeps_failed_asset(self):
        folder = self.root / "project"
        folder.mkdir()
        with (
            patch("asset_library.search", return_value=[self.provenance()]),
            patch("asset_library.fetch", return_value=b"bad image"),
            patch("asset_library.probe", return_value={"streams": [{"codec_type": "audio"}]}),
        ):
            with self.assertRaisesRegex(ValueError, "does not match"):
                acquire(self.load(), folder, self.request())
        self.assertEqual(len(list((folder / "assets/online").glob("*.partial.jpg"))), 1)

    def test_explicit_card_fallback_and_default_failure(self):
        data = copy.deepcopy(self.template)
        data["scenes"][0]["asset_request"] = self.request(fallback="card")
        film = self.film(data)
        output = self.root / "output"
        output.mkdir()
        with patch("asset_library.acquire", side_effect=ValueError("offline")):
            resolved = resolve(self.load(), film, output)
        self.assertIsNone(resolved.scenes[0].media)
        self.assertIn("unavailable", resolved.scenes[0].subtitle)
        with patch("asset_library.acquire", side_effect=ValueError("offline")):
            with self.assertRaises(ValueError):
                resolve(
                    self.load(),
                    replace(film, scenes=(replace(film.scenes[0], asset_request=self.request()),)),
                    output,
                )

    def test_short_and_long_templates(self):
        for name in ("short", "long"):
            relative = self.settings["formats"][name]["template"]
            original = Path(__file__).resolve().parents[1] / relative
            (self.root / relative).write_bytes(original.read_bytes())
            folder = new_project(self.load(), "film-" + name, name)
            from config import Film

            film = Film.load(folder, self.load())
            self.assertEqual(film.format_name, name)
            self.assertTrue(film.sound_enabled)

    def test_format_motion_owns_new_project_default(self):
        self.settings["formats"]["short"]["motion"] = "calm"
        relative = self.settings["formats"]["short"]["template"]
        original = Path(__file__).resolve().parents[1] / relative
        (self.root / relative).write_bytes(original.read_bytes())
        folder = new_project(self.load(), "calm-short", "short")
        self.assertEqual(json.loads((folder / "film.json").read_text())["motion"], "calm")

    def test_failed_builds_preserve_success_pointer_and_get_new_folders(self):
        settings = self.load()
        folder = new_project(settings, "failed-film")
        data = self.formatted()
        (folder / "film.json").write_text(json.dumps(data))
        pointer = folder / "latest-export.json"
        pointer.write_text('{"run": "previous-success"}')
        before = pointer.read_bytes()
        timing = [{"frames": 30, "duration": 1} for _ in data["scenes"]]
        for _ in range(2):
            with (
                patch.dict("sys.modules", {"timeline": MagicMock()}),
                patch("studio.bootstrap"),
                patch("narration.synthesize", return_value=(timing, [])),
                patch("studio.render") as render,
            ):
                with self.assertRaisesRegex(ValueError, "Revise the script"):
                    build(settings, "failed-film")
                render.assert_not_called()
        self.assertEqual(pointer.read_bytes(), before)
        self.assertEqual(len(list((folder / "exports").iterdir())), 2)
        self.assertEqual(
            json.loads((self.root / "memory/latest-run.json").read_text())["phase"],
            "failed-narration",
        )


if __name__ == "__main__":
    unittest.main()

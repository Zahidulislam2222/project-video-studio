"""Matting invariants and an actual offline model/media path, when configured."""

import copy
import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from pydantic import ValidationError

from studio_v2.__main__ import import_asset
from studio_v2.matting import MatteRequest, matte, model_path
from studio_v2.models import Project
from studio_v2.package import restore
from studio_v2.process import render_lock, run
from studio_v2.production import ProductionRequest, prepare
from studio_v2.render import asset_path, digest, render
from studio_v2.settings import Settings
from studio_v2.store import Store


class MattingContracts(unittest.TestCase):
    def test_finite_timing_and_explicit_presenter_selection(self):
        for values in ({"start": -1, "seconds": 1}, {"start": 0, "seconds": float("nan")}):
            with self.assertRaises(ValidationError):
                MatteRequest(**values)
        for values in (
            {"title": "No presenter", "matte_presenter": True},
            {
                "title": "Ambiguous",
                "recording": "voice.wav",
                "footage": ["screen.mp4"],
                "matte_presenter": True,
                "media_approved": True,
            },
        ):
            with self.assertRaises(ValidationError):
                ProductionRequest(**values)

    def test_missing_or_tampered_model_is_rejected(self):
        settings = Settings.load()
        with patch.dict(os.environ, {"STUDIO_MATTING_MODEL": ""}):
            with self.assertRaises(ValueError):
                model_path(settings)
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "tampered.onnx"
            model.write_bytes(b"not a neural model")
            with patch.dict(os.environ, {"STUDIO_MATTING_MODEL": str(model)}):
                with self.assertRaisesRegex(ValueError, "integrity"):
                    model_path(settings)

    def test_derived_import_has_separate_bound_and_retains_account_quota(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = copy.deepcopy(Settings.load().config)
            source = root / "generated.png"
            Image.new("RGB", (32, 32), "red").save(source)
            config["storage"]["upload_bytes"] = 1
            config["storage"]["derived_asset_bytes"] = source.stat().st_size
            config["storage"]["account_bytes"] = source.stat().st_size
            settings = replace(Settings.load(), data=root / "data", config=config)
            store = Store(settings)
            with self.assertRaises(ValueError):
                import_asset(settings, store, "local", source)
            imported = import_asset(settings, store, "local", source, derived=True)
            self.assertEqual(store.asset("local", imported)["sha256"], digest(source))
            with self.assertRaises(ValueError):
                import_asset(settings, store, "local", source, derived=True)
            self.assertEqual(len(list(settings.contained("assets").iterdir())), 1)
            config["storage"]["derived_asset_bytes"] = 1
            with self.assertRaises(ValueError):
                import_asset(settings, store, "other", source, derived=True)

    def test_cutout_cannot_be_unaltered_proof_or_lose_its_mask(self):
        origin = {"asset": "original", "start": 0, "seconds": 1, "model_sha256": "a" * 64}
        shot = {
            "id": "one",
            "title": "Illustration",
            "layers": [{"asset": "foreground", "mask": "mask", "matting": origin}],
            "source_note": "Owner footage",
        }
        Project.model_validate({"title": "Valid illustration", "shots": [shot]})
        with self.assertRaises(ValidationError):
            Project.model_validate({"title": "Altered proof", "shots": [{**shot, "proof": True}]})
        shot["layers"][0]["mask"] = None
        with self.assertRaises(ValidationError):
            Project.model_validate({"title": "Missing mask", "shots": [shot]})


class MattingMedia(unittest.IsolatedAsyncioTestCase):
    async def test_gated_budget_and_busy_workspace_leave_no_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            settings = replace(Settings.load(), data=Path(temporary))
            output = Path(temporary) / "not-created"
            with self.assertRaises(ValueError):
                await matte(
                    settings,
                    Path("not-opened"),
                    output,
                    0,
                    settings.config["matting"]["maximum_seconds"] + 1,
                )
            self.assertFalse(output.exists())
            with render_lock(settings):
                with self.assertRaises(ValueError):
                    await matte(settings, Path("not-opened"), output, 0, 1)
            self.assertFalse(output.exists())

    async def test_real_model_guided_layers_and_original_restore(self):
        if not os.environ.get("STUDIO_MATTING_MODEL"):
            self.skipTest("Configure the optional pinned matting model for offline media inference")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = copy.deepcopy(Settings.load().config)
            config["render"]["dimensions"]["landscape"] = [640, 360]
            config["render"]["fps"] = 6
            settings = replace(
                Settings.load(), config=config, data=root / "data", model=None, voices=None
            )
            store = Store(settings)
            source = root / "presenter.mp4"
            # Original generated pattern: this checks inference and composition plumbing,
            # not the semantic quality of human segmentation.
            await run(
                [
                    settings.ffmpeg,
                    "-hide_banner",
                    "-n",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=size=160x90:rate=6",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=220:sample_rate=16000",
                    "-t",
                    "1",
                    "-c:v",
                    "libx264",
                    "-threads",
                    "2",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    str(source),
                ],
                root,
                60,
            )
            source_hash = digest(source)
            captions = root / "input.srt"
            captions.write_text("1\n00:00:00,000 --> 00:00:00,750\nTest recording\n")
            background = root / "background.png"
            Image.new("RGB", (160, 90), "#123456").save(background)
            request = root / "request.json"
            request.write_text(
                json.dumps(
                    {
                        "title": "Cutout workflow",
                        "recording": str(source),
                        "captions_file": str(captions),
                        "footage": [str(background)],
                        "companion": str(source),
                        "matte_presenter": True,
                        "media_approved": True,
                    }
                )
            )
            path = await prepare(settings, store, "local", request, root / "production")
            project = Project.model_validate_json(path.read_text())
            layer = project.shots[0].layers[1]
            self.assertIsNotNone(layer.mask)
            self.assertIsNotNone(layer.matting)
            self.assertEqual(
                digest(asset_path(settings, store.asset("local", layer.matting.asset))), source_hash
            )
            report = json.loads(
                (root / "production/cutouts/shot-01/MatteVerification.json").read_text()
            )
            self.assertEqual(report["frames"], 6)
            self.assertTrue(report["full_decode"])
            self.assertEqual(digest(source), source_hash)
            self.assertFalse((root / "production/cutouts/shot-01/frames").exists())
            saved = store.save("local", project.model_dump())
            job = store.enqueue("local", saved, "matting")
            verification = await render(settings, store, job)
            self.assertEqual(verification["expected_frames"], 6)
            exported = settings.contained("renders", job["id"])
            restored = restore(settings, store, "local", exported, root / "restored.json")
            restored_project = Project.model_validate_json(restored.read_text())
            restored_origin = restored_project.shots[0].layers[1].matting.asset
            self.assertNotEqual(restored_origin, layer.matting.asset)
            self.assertEqual(
                digest(asset_path(settings, store.asset("local", restored_origin))), source_hash
            )
            with self.assertRaises(ValueError):
                await matte(settings, source, root / "production/cutouts/shot-01", 0, 1)
            with self.assertRaises(ValueError):
                await matte(settings, source, root / "out-of-bounds", 1, 1)

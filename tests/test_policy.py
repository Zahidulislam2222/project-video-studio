"""Behavioral regression gates for configuration, isolation and export safety."""

from __future__ import annotations

import ast
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

from config import Film, Settings, contained, number, safe_text, slug
from media_tools import caption_chunks, timestamp, tool_path
from studio import export_folder, new_project, project_folder

ROOT = Path(__file__).resolve().parents[1]


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.settings = json.loads((ROOT / "settings.json").read_text())
        self.template = json.loads((ROOT / "templates/new-project.json").read_text())
        (self.root / "templates").mkdir()
        (self.root / "templates/new-project.json").write_text(json.dumps(self.template))
        machine = {}
        for name in ("ffmpeg", "ffprobe", "font_regular", "font_bold"):
            path = self.root / name
            path.touch()
            machine[name] = str(path)
        (self.root / "machine.local.json").write_text(json.dumps(machine))

    def load(self):
        (self.root / "settings.json").write_text(json.dumps(self.settings))
        return Settings.load(self.root)

    def film(self, data=None):
        folder = self.root / "project"
        folder.mkdir(exist_ok=True)
        (folder / "film.json").write_text(json.dumps(data or self.template))
        return Film.load(folder, self.load())

    def test_stock_male_default(self):
        self.assertEqual(self.film().voice, "am_michael")

    def test_female_project_voice_rejected(self):
        data = copy.deepcopy(self.template)
        data["voice"] = "af_heart"
        with self.assertRaises(ValueError):
            self.film(data)

    def test_female_global_policy_rejected(self):
        self.settings["male_voices"]["af_heart"] = "en-us"
        with self.assertRaises(ValueError):
            self.load()

    def test_unknown_default_voice_rejected(self):
        self.settings["default_voice"] = "am_unknown"
        with self.assertRaises(ValueError):
            self.load()

    def test_unknown_delivery_rejected(self):
        data = copy.deepcopy(self.template)
        data["scenes"][0]["delivery"] = "unknown"
        with self.assertRaises(ValueError):
            self.film(data)

    def test_duplicate_scene_rejected(self):
        data = copy.deepcopy(self.template)
        data["scenes"][1]["id"] = data["scenes"][0]["id"]
        with self.assertRaises(ValueError):
            self.film(data)

    def test_traversal_media_rejected(self):
        data = copy.deepcopy(self.template)
        data["scenes"][0]["media"] = "../../outside.mp4"
        with self.assertRaises(ValueError):
            self.film(data)

    def test_absolute_media_rejected(self):
        data = copy.deepcopy(self.template)
        data["scenes"][0]["media"] = str(self.root / "outside.mp4")
        with self.assertRaises(ValueError):
            self.film(data)

    def test_media_symlink_escape_rejected(self):
        folder = self.root / "project"
        folder.mkdir()
        outside = self.root / "outside.mp4"
        outside.touch()
        (folder / "escape.mp4").symlink_to(outside)
        data = copy.deepcopy(self.template)
        data["scenes"][0]["media"] = "escape.mp4"
        with self.assertRaises(ValueError):
            self.film(data)

    def test_missing_media_rejected(self):
        data = copy.deepcopy(self.template)
        data["scenes"][0]["media"] = "missing.mp4"
        with self.assertRaises(ValueError):
            self.film(data)

    def test_nonfinite_numbers_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                number(value, 0, 10)

    def test_boolean_numeric_rejected(self):
        with self.assertRaises(TypeError):
            number(True, 0, 10)

    def test_shell_names_rejected(self):
        for name in ("../other", "other/name", "a;echo", "a b", "$(id)", "a'", "a--b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                slug(name)

    def test_caption_control_syntax_rejected(self):
        for value in ("hello{tag}", "hello\\Nworld", "hello\x00world"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_text(value)

    def test_caption_text_conserved(self):
        text = "A clear workflow connects the frontend to the backend and provides verified evidence of the changes without exposing private information or invented results."
        chunks = caption_chunks(text, 42)
        self.assertEqual(" ".join(" ".join(chunks).split()), text)
        self.assertTrue(all(len(c.splitlines()) <= 2 for c in chunks))
        self.assertTrue(all(len(line) <= 42 for c in chunks for line in c.splitlines()))

    def test_unreadable_caption_word_rejected(self):
        with self.assertRaises(ValueError):
            caption_chunks("a" * 43, 42)

    def test_timestamp_rounding(self):
        self.assertEqual(timestamp(59.9996), "00:01:00,000")
        self.assertEqual(timestamp(60, True), "0:01:00.00")

    def test_windows_path_conversion(self):
        self.assertEqual(
            tool_path(Path("/mnt/d/Folder with spaces/film.mp4"), True),
            "D:/Folder with spaces/film.mp4",
        )

    def test_windows_unmounted_path_rejected(self):
        with self.assertRaises(ValueError):
            tool_path(self.root / "film.mp4", True)

    def test_path_boundary_rejects_parent(self):
        with self.assertRaises(ValueError):
            contained(self.root, ".")

    def test_existing_project_preserved(self):
        settings = self.load()
        folder = new_project(settings, "my-project")
        before = (folder / "film.json").read_bytes()
        with self.assertRaises(FileExistsError):
            new_project(settings, "my-project")
        self.assertEqual((folder / "film.json").read_bytes(), before)

    def test_exports_symlink_escape_rejected(self):
        folder = self.root / "project"
        folder.mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        (folder / "exports").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            export_folder(folder, "20261012-010203-123456")
        self.assertEqual(list(outside.iterdir()), [])

    def test_projects_symlink_escape_rejected(self):
        external = tempfile.TemporaryDirectory()
        self.addCleanup(external.cleanup)
        outside = Path(external.name)
        (self.root / "projects").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            project_folder(self.load(), "other-project")

    def test_project_symlink_escape_rejected(self):
        projects = self.root / "projects"
        projects.mkdir()
        outside = self.root / "outside"
        outside.mkdir()
        (projects / "other-project").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            project_folder(self.load(), "other-project")

    def test_new_project_uses_configured_male_voice(self):
        self.settings["default_voice"] = "am_fenrir"
        folder = new_project(self.load(), "new-film")
        self.assertEqual(json.loads((folder / "film.json").read_text())["voice"], "am_fenrir")

    def test_provider_config_stays_out_of_business_code(self):
        for path in ROOT.glob("*.py"):
            if path.name == "config.py":
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertFalse(
                        node.value.startswith(
                            (
                                "https://",
                                "http://",
                                "sk-ant-",
                                "sk-proj-",
                                "-----BEGIN PRIVATE KEY",
                            )
                        ),
                        path.name,
                    )
                    self.assertNotIn("kokoro-v1.0", node.value, path.name)


if __name__ == "__main__":
    unittest.main()

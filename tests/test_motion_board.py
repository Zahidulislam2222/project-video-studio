"""Negative boundaries, cadence and genuine motion for editorial boards."""

from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import replace

import test_policy

from motion_board import THEME_KEYS, Painter, load_board, schedule


class MotionBoardTests(unittest.TestCase):
    setUp = test_policy.PolicyTests.setUp
    load = test_policy.PolicyTests.load
    film = test_policy.PolicyTests.film

    def board(self, film):
        board = {
            "headline_size": 42,
            "headline_minimum": 26,
            "images": {},
            "beat_seconds": 1.7,
            "render_scale": 0.5,
            "brand": "example.test",
            "kicker": "TEST",
            "illustration_label": "ILLUSTRATION",
            "theme": dict.fromkeys(THEME_KEYS, "#123456"),
            "scenes": {
                s.ident: {
                    "chapter": "Chapter",
                    "beats": [
                        {
                            "kind": "car",
                            "headline": "Headline",
                            "detail": "Detail",
                            "source": "Illustration",
                            "labels": ["INPUT", "OUTPUT"],
                        }
                    ],
                }
                for s in film.scenes
            },
        }
        board["theme"].update(
            background="#090E1B",
            panel="#111A2D",
            ink="#F3F5FB",
            accent="#A6FFCB",
            secondary="#B3A1FF",
        )
        (film.folder / "motion-board.json").write_text(json.dumps(board))
        return board

    def render_settings(self):
        from studio_v2.settings import Settings as VisualSettings

        font = VisualSettings.load().font
        if not font.is_file():
            self.skipTest("Install/configure a TrueType font for real graphic checks")
        settings = self.load()
        return replace(
            settings, machine={**settings.machine, "font_regular": font, "font_bold": font}
        )

    def test_no_board_leaves_legacy_flow(self):
        self.assertIsNone(load_board(self.film()))

    def test_frame_schedule_and_maximum_cadence(self):
        for frames in (30, 59, 61, 93, 300, 1021, 3000):
            intervals = schedule(frames, 30, 1.7)
            self.assertEqual(intervals[0][0], 0)
            self.assertEqual(intervals[-1][1], frames)
            self.assertTrue(all(30 <= b - a <= 60 for a, b in intervals))
            self.assertTrue(
                all(intervals[i][1] == intervals[i + 1][0] for i in range(len(intervals) - 1))
            )

    def test_board_rejects_missing_scene(self):
        film = self.film()
        board = self.board(film)
        board["scenes"].pop(film.scenes[0].ident)
        (film.folder / "motion-board.json").write_text(json.dumps(board))
        with self.assertRaisesRegex(ValueError, "exactly"):
            load_board(film)

    def test_board_cannot_replace_proof(self):
        film = self.film()
        self.board(film)
        film = replace(film, scenes=(replace(film.scenes[0], role="proof"), *film.scenes[1:]))
        with self.assertRaisesRegex(ValueError, "proof"):
            load_board(film)

    def test_board_rejects_image_escape(self):
        film = self.film()
        board = self.board(film)
        board["scenes"][film.scenes[0].ident]["beats"][0]["image"] = "../../outside.jpg"
        (film.folder / "motion-board.json").write_text(json.dumps(board))
        with self.assertRaises(ValueError):
            load_board(film)

    def test_board_rejects_unknown_composition_and_timing(self):
        for key, value in (("kind", "arbitrary-code"), ("headline", "bad{control}")):
            film = self.film()
            board = self.board(film)
            board["scenes"][film.scenes[0].ident]["beats"][0][key] = value
            (film.folder / "motion-board.json").write_text(json.dumps(board))
            with self.assertRaises(ValueError):
                load_board(film)
        film = self.film()
        board = self.board(film)
        board["beat_seconds"] = 3
        (film.folder / "motion-board.json").write_text(json.dumps(board))
        with self.assertRaises(ValueError):
            load_board(film)

    def test_visual_foreground_changes_over_time(self):
        film = self.film()
        board = self.board(film)
        settings = self.render_settings()
        painter = Painter(settings, board)
        entry = board["scenes"][film.scenes[0].ident]
        a = painter.frame(entry, entry["beats"][0], 0.5, 0, 0.1, film)
        b = painter.frame(entry, entry["beats"][0], 1.1, 0, 0.1, film)
        self.assertNotEqual(
            hashlib.sha256(a.tobytes()).hexdigest(), hashlib.sha256(b.tobytes()).hexdigest()
        )

    def test_rejects_non_list_labels_and_overlong_text(self):
        for value in ("AB", {"A": 1, "B": 2}):
            film = self.film()
            board = self.board(film)
            board["scenes"][film.scenes[0].ident]["beats"][0]["labels"] = value
            (film.folder / "motion-board.json").write_text(json.dumps(board))
            with self.assertRaises(TypeError):
                load_board(film)
        film = self.film()
        board = self.board(film)
        board["scenes"][film.scenes[0].ident]["beats"][0]["headline"] = "x" * 100
        (film.folder / "motion-board.json").write_text(json.dumps(board))
        with self.assertRaises(ValueError):
            load_board(film)

    def test_encoder_watchdog_bounds_blocked_pipe(self):
        import sys
        import time

        from motion_board import write_frames

        start = time.monotonic()
        with self.assertRaises((BrokenPipeError, RuntimeError, TimeoutError)):
            write_frames(
                [sys.executable, "-c", "import time; time.sleep(10)"],
                self.root,
                self.root / "encoder.log",
                0.2,
                [b"x" * 2_000_000],
            )
        self.assertLess(time.monotonic() - start, 3)

    def test_provenance_cannot_override_computed_identity(self):
        film = self.film()
        board = self.board(film)
        board["images"] = {
            "assets/example.jpg": {
                "url": "https://example.test/image.jpg",
                "credit": "Example",
                "usage": "Test illustration",
                "path": "invented",
                "sha256": "invented",
            }
        }
        (film.folder / "motion-board.json").write_text(json.dumps(board))
        with self.assertRaises(ValueError):
            load_board(film)

    def test_complete_palette_is_required(self):
        film = self.film()
        board = self.board(film)
        board["theme"].pop(THEME_KEYS[-1])
        (film.folder / "motion-board.json").write_text(json.dumps(board))
        with self.assertRaises(KeyError):
            load_board(film)

    def test_third_chip_label_is_visible(self):
        film = self.film()
        board = self.board(film)
        settings = self.render_settings()
        painter = Painter(settings, board)
        a = painter.graphic("chip", ["SENSE", "INTERPRET", "ACT"], 0.8, 0)
        b = painter.graphic("chip", ["SENSE", "INTERPRET", "CHECK"], 0.8, 0)
        self.assertNotEqual(
            hashlib.sha256(a.tobytes()).digest(), hashlib.sha256(b.tobytes()).digest()
        )

    def test_oversized_word_fails_at_readable_minimum(self):
        from PIL import Image, ImageDraw

        film = self.film()
        board = self.board(film)
        settings = self.render_settings()
        painter = Painter(settings, board)
        draw = ImageDraw.Draw(Image.new("RGB", (painter.w, painter.h)))
        with self.assertRaises(ValueError):
            painter.headline_layout(draw, "W" * 56, 365 * painter.unit)

"""Validated editorial motion boards, rendered locally as exact-frame scene media."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from config import Film, Settings, contained, number, read_json, safe_text
from media_tools import tool_path

THEME_KEYS = (
    "background",
    "panel",
    "ink",
    "muted",
    "accent",
    "secondary",
    "illustration_shade_1",
    "illustration_shade_2",
    "illustration_shade_3",
    "illustration_shade_4",
    "illustration_shade_5",
    "illustration_shade_6",
    "illustration_shade_7",
    "illustration_shade_8",
    "illustration_shade_9",
    "illustration_shade_10",
    "illustration_shade_11",
    "illustration_shade_12",
    "illustration_shade_13",
    "illustration_shade_14",
    "illustration_shade_15",
    "illustration_shade_16",
)

KINDS = frozenset(
    {
        "car",
        "glasses",
        "flow",
        "chip",
        "workspace",
        "orbit",
        "checks",
        "compare",
        "type",
    }
)


def load_board(film: Film) -> dict[str, Any] | None:
    path = contained(film.folder, "motion-board.json")
    if not path.exists():
        return None
    board = read_json(path)
    if not isinstance(board.get("scenes"), dict) or not isinstance(board.get("theme"), dict):
        raise TypeError("Board scenes and theme must be objects")
    if not isinstance(board.get("images"), dict):
        raise TypeError("Board requires an image provenance object")
    for name, record in board["images"].items():
        contained(film.folder, name)
        if not isinstance(record, dict):
            raise TypeError("Image provenance must be an object")
        parsed = urlsplit(record["url"])
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Image provenance requires a public HTTPS source URL")
        if set(record) != {"url", "credit", "usage"}:
            raise ValueError("Image provenance keys must be url, credit and usage only")
        for key in ("credit", "usage"):
            if len(safe_text(record[key])) > 240:
                raise ValueError("Image provenance text too long")
    number(board["headline_size"], 26, 60)
    number(board["headline_minimum"], 20, board["headline_size"])
    number(board["beat_seconds"], 1, 2)
    number(board["render_scale"], 0.4, 1)
    for key in ("brand", "kicker", "illustration_label"):
        safe_text(board[key])
    for key in THEME_KEYS:
        value = board["theme"][key]
        if not isinstance(value, str) or len(value) != 7 or value[0] != "#":
            raise ValueError("Board colors must be #RRGGBB")
        int(value[1:], 16)
    if set(board["scenes"]) != {s.ident for s in film.scenes}:
        raise ValueError("Board must cover exactly the film's scenes")
    for scene in film.scenes:
        if scene.role == "proof" or scene.media is not None:
            raise ValueError("Motion board cannot replace proof or supplied scene media")
        entry = board["scenes"][scene.ident]
        if not isinstance(entry, dict) or not isinstance(entry.get("beats"), list):
            raise TypeError("Board scene requires an object with a beat list")
        if len(safe_text(entry["chapter"])) > 70:
            raise ValueError("Chapter title too long")
        if not 1 <= len(entry["beats"]) <= 100:
            raise ValueError("Board needs 1–100 beats per scene")
        for beat in entry["beats"]:
            if not isinstance(beat, dict):
                raise TypeError("Each beat must be an object")
            if beat["kind"] not in KINDS:
                raise ValueError("Unknown motion board composition")
            for key in ("headline", "detail", "source"):
                limit = {"headline": 56, "detail": 70, "source": 120}[key]
                if len(safe_text(beat[key])) > limit:
                    raise ValueError("Beat text exceeds readable layout limits")
            if not isinstance(beat.get("labels"), list):
                raise TypeError("Diagram labels must be a list")
            if not 2 <= len(beat["labels"]) <= 4:
                raise ValueError("Each beat needs 2–4 diagram labels")
            if beat["kind"] in ("car", "glasses") and len(beat["labels"]) != 2:
                raise ValueError("Product cutaways require exactly two labels")
            if beat["kind"] in ("workspace", "type") and len(beat["labels"]) > 3:
                raise ValueError("Workspace/type compositions support up to three labels")
            for label in beat["labels"]:
                if len(safe_text(label)) > 30:
                    raise ValueError("Diagram label too long")
            if "image" in beat and not isinstance(beat["image"], str):
                raise TypeError("Image path must be text")
            if beat.get("image"):
                if beat["image"] not in board["images"]:
                    raise ValueError("Every image needs source, credit and usage context")
                image = contained(film.folder, beat["image"])
                if image.suffix.lower() not in (".png", ".jpg", ".jpeg") or not image.is_file():
                    raise ValueError("Board image missing or unsupported")
    return board


def schedule(frames: int, fps: int, target: float) -> list[tuple[int, int]]:
    """Allocate whole frames; every visual interval remains within 1–2 seconds."""
    count = max(1, round(frames / fps / target))
    while frames / count > 2 * fps:
        count += 1
    while count > 1 and frames / count < fps:
        count -= 1
    edges = [round(i * frames / count) for i in range(count + 1)]
    if frames < fps:
        raise ValueError("A motion-board scene must last at least one second")
    return list(zip(edges[:-1], edges[1:], strict=True))


def record_board_sources(film: Film, output: Path, board: dict[str, Any]) -> None:
    """Bind the original data and images, in addition to generated scene media."""
    paths = {"motion-board.json"}
    for scene in board["scenes"].values():
        paths.update(b["image"] for b in scene["beats"] if b.get("image"))
    sources_path = output / "SourceInputs.json"
    sources = json.loads(sources_path.read_text(encoding="utf-8"))
    for name in sorted(paths):
        source = contained(film.folder, name)
        sources.append(
            {
                "scene": "motion-board-source",
                "path": name,
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "purpose": "editorial motion data or credited company image",
            }
        )
    sources_path.write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
    records = []
    lines = ["Editorial product imagery — company copyright retained; no open licence claimed."]
    for name, record in board["images"].items():
        digest = hashlib.sha256(contained(film.folder, name).read_bytes()).hexdigest()
        records.append({**record, "path": name, "sha256": digest})
        lines.extend([record["credit"], record["url"], record["usage"], "SHA-256: " + digest, ""])
    (output / "EditorialAttribution.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "Attribution.txt").open("a", encoding="utf-8") as attribution:
        attribution.write("\n".join(lines) + "\n")


class Painter:
    """Original vector-like diagrams and typography; content comes from the board."""

    def __init__(self, settings: Settings, board: dict[str, Any]):
        from PIL import ImageFont

        r = settings.data["render"]
        self.w = round(r["width"] * board["render_scale"] / 2) * 2
        self.h = round(r["height"] * board["render_scale"] / 2) * 2
        self.portrait = self.h > self.w
        self.board = board
        self.c = board["theme"]
        self.font_paths = (
            settings.machine["font_regular"],
            settings.machine["font_bold"],
        )
        self.fonts: dict[tuple[int, bool], Any] = {}
        self.font_factory = ImageFont.truetype
        self.images: dict[str, Any] = {}
        self.unit = self.w / (540 if self.portrait else 960)

    def font(self, size: float, bold: bool = False) -> Any:
        key = (max(9, round(size * self.unit)), bold)
        if key not in self.fonts:
            self.fonts[key] = self.font_factory(str(self.font_paths[bold]), key[0])
        return self.fonts[key]

    def text(
        self,
        draw: Any,
        xy: tuple[float, float],
        text: str,
        size: float,
        color: str,
        bold: bool = False,
        max_width: float | None = None,
    ) -> None:
        font = self.font(size, bold)
        if max_width:
            while draw.textlength(text, font=font) > max_width and size > 9:
                size -= 1
                font = self.font(size, bold)
        draw.text(xy, text, font=font, fill=color, anchor="lt")

    def graphic(self, kind: str, labels: list[str], t: float, phase: int) -> Any:
        from PIL import Image, ImageDraw

        x: float
        y: float
        art = Image.new("RGB", (900, 430), self.c["panel"])
        d = ImageDraw.Draw(art)
        ac, sec, ink = self.c["accent"], self.c["secondary"], self.c["ink"]
        for x in range(-50, 950, 50):
            offset = int(t * 14) % 50
            d.line((x + offset, 0, x + offset, 430), fill=self.c["illustration_shade_6"])
        for y in range(0, 430, 50):
            d.line((0, y, 900, y), fill=self.c["illustration_shade_6"])

        def label(x: float, y: float, text: str, color: str = ink) -> None:
            font = self.font_factory(str(self.font_paths[1]), 24)
            while d.textlength(text, font=font) > 245:
                font = self.font_factory(str(self.font_paths[1]), font.size - 1)
            d.text((x, y), text, font=font, fill=color, anchor="mm")

        if kind == "car":
            lift = 18 * math.sin(t * 2)
            pts = [
                (170, 270 - lift),
                (225, 190 - lift),
                (350, 160 - lift),
                (560, 170 - lift),
                (665, 222 - lift),
                (750, 250 - lift),
                (725, 292 - lift),
                (185, 292 - lift),
            ]
            d.polygon(pts, fill=self.c["illustration_shade_16"], outline=ink)
            d.polygon(
                [
                    (275, 190 - lift),
                    (365, 174 - lift),
                    (545, 185 - lift),
                    (600, 220 - lift),
                    (263, 220 - lift),
                ],
                fill=self.c["illustration_shade_4"],
                outline=ac,
            )
            for x in (275, 635):
                d.ellipse(
                    (x - 46, 250 - lift, x + 46, 342 - lift),
                    fill=self.c["illustration_shade_1"],
                    outline=ink,
                    width=5,
                )
                d.ellipse((x - 26, 270 - lift, x + 26, 322 - lift), outline=ac, width=4)
            d.line((200, 255 - lift, 242, 248 - lift), fill=sec, width=7)
            for k in range(7):
                x = 180 - ((t * 180 + k * 18) % 125)
                d.line((x, 245 - lift, x + 25, 245 - lift), fill=sec, width=4)
            for x in (360, 450, 540):
                y = 360 - (t * 75 % 45)
                d.line((x, y, x, y - 34), fill=ac, width=3)
                d.polygon([(x, y - 42), (x - 6, y - 30), (x + 6, y - 30)], fill=ac)
            label(235, 75, labels[0], sec)
            label(665, 75, labels[1], ac)
        elif kind == "glasses":
            bob = 8 * math.sin(t * 2)
            for x in (190, 470):
                d.rounded_rectangle(
                    (x, 120 + bob, x + 245, 275 + bob),
                    40,
                    fill=self.c["illustration_shade_3"],
                    outline=ink,
                    width=12,
                )
                for k in range(3):
                    d.arc(
                        (
                            x + 25 + k * 10,
                            145 + bob + k * 10,
                            x + 215 - k * 10,
                            255 + bob - k * 10,
                        ),
                        int(t * 45) + k * 35,
                        int(t * 45) + 160 + k * 35,
                        fill=ac,
                        width=4,
                    )
            d.arc((425, 160 + bob, 475, 210 + bob), 180, 360, fill=ink, width=12)
            d.line((190, 140 + bob, 100, 95 + bob), fill=ink, width=14)
            d.line((715, 140 + bob, 800, 90 + bob), fill=ink, width=14)
            d.line((715, 265 + bob, 780, 300, 780, 345), fill=sec, width=3)
            d.rounded_rectangle(
                (720, 330, 835, 410), 20, fill=self.c["illustration_shade_10"], outline=sec, width=3
            )
            label(450, 55, labels[0], ac)
            label(450, 350, labels[1], sec)
        elif kind in ("flow", "checks", "compare"):
            count = len(labels)
            for k, value in enumerate(labels):
                x = 60 + k * (780 / count)
                width = 730 / count
                y = 130 + 10 * math.sin(t * 2 + k)
                d.rounded_rectangle(
                    (x, y, x + width, y + 155),
                    18,
                    fill=self.c["illustration_shade_7"],
                    outline=ac if k == phase % count else self.c["illustration_shade_13"],
                    width=3,
                )
                label(x + width / 2, y + 77, value, ink)
                if k < count - 1:
                    d.line((x + width + 6, 207, x + width + 42, 207), fill=sec, width=3)
                for q in range(3):
                    px = x + ((t * 75 + q * 55) % width)
                    d.ellipse((px, 315, px + 7, 322), fill=ac)
        elif kind == "workspace":
            for k in range(3):
                x = 85 + k * 245
                y = 90 + (20 if k != 1 else 0) + 8 * math.sin(t * 1.5 + k)
                d.rounded_rectangle(
                    (x, y, x + 230, y + 200),
                    14,
                    fill=self.c["illustration_shade_8"],
                    outline=ac,
                    width=3,
                )
                d.rectangle((x + 15, y + 16, x + 215, y + 30), fill=sec)
                for row in range(5):
                    length = 70 + int(70 * (1 + math.sin(row + k)) / 2)
                    d.rounded_rectangle(
                        (x + 18, y + 55 + row * 22, x + 18 + length, y + 62 + row * 22),
                        3,
                        fill=self.c["illustration_shade_15"],
                    )
                label(x + 115, y + 170, labels[k % len(labels)])
            d.polygon([(200, 345), (690, 345), (775, 408), (120, 408)], outline=sec)
            for x in range(190, 720, 40):
                d.line((x, 350, x - 20, 405), fill=self.c["illustration_shade_14"], width=1)
        elif kind in ("chip", "orbit"):
            center = (450, 215)
            for radius in (110, 160, 200):
                d.ellipse(
                    (450 - radius, 215 - radius, 450 + radius, 215 + radius),
                    outline=self.c["illustration_shade_11"],
                    width=2,
                )
            for k in range(12):
                a = t * 0.5 + k * math.tau / 12
                x, y = 450 + 180 * math.cos(a), 215 + 180 * math.sin(a)
                d.line((*center, x, y), fill=self.c["illustration_shade_12"], width=2)
                d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=ac if k % 2 else sec)
            d.rounded_rectangle(
                (355, 125, 545, 305), 25, fill=self.c["illustration_shade_9"], outline=ac, width=4
            )
            label(450, 215, labels[0], ink)
            label(450, 395, labels[1], sec)
        else:
            font = self.font_factory(str(self.font_paths[1]), 82)
            for k, value in enumerate(labels[:3]):
                while d.textlength(value, font=font) > 780:
                    font = self.font_factory(str(self.font_paths[1]), font.size - 1)
                d.text(
                    (450, 105 + k * 110),
                    value,
                    font=font,
                    fill=ac if k % 2 else ink,
                    anchor="mm",
                )
        if kind in ("car", "glasses", "chip", "orbit"):
            for index, value in enumerate(labels[2:]):
                label(130 + 640 * index, 65, value, sec)
        if kind == "workspace" and len(labels) == 4:
            label(450, 400, labels[3], sec)
        if kind == "type" and len(labels) == 4:
            label(450, 400, labels[3], sec)
        return art

    def headline_layout(self, draw: Any, text: str, width: float) -> tuple[int, list[str]]:
        for size in range(
            int(self.board["headline_size"]), int(self.board["headline_minimum"]) - 1, -1
        ):
            font = self.font(size, True)
            if any(draw.textlength(word, font=font) > width for word in text.split()):
                continue
            lines = []
            line = ""
            for word in text.split():
                candidate = (line + " " + word).strip()
                if draw.textlength(candidate, font=font) > width and line:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
            if len(lines) <= 3:
                return size, lines
        raise ValueError("Headline cannot fit at the configured readable minimum size")

    def frame(
        self,
        entry: dict[str, Any],
        beat: dict[str, Any],
        local: float,
        phase: int,
        progress: float,
        film: Film,
    ) -> Any:
        from PIL import Image, ImageDraw, ImageOps

        w, h, u = self.w, self.h, self.unit
        p = self.portrait
        canvas = Image.new("RGB", (w, h), self.c["background"])
        d = ImageDraw.Draw(canvas)
        margin = 34 * u if p else 48 * u
        reveal = 1 - (1 - min(1, local / 0.32)) ** 3
        for k in range(5):
            x = int((local * 28 + k * w / 4) % (w + 100)) - 50
            d.line(
                (x, 0, x - 120, h), fill=self.c["illustration_shade_2"], width=max(1, round(2 * u))
            )
        # Oversized editorial chapter number and moving calibration marks add depth.
        self.text(
            d, (w * 0.72, h * 0.08), f"{phase + 1:02}", 100, self.c["illustration_shade_5"], True
        )
        self.text(d, (margin, 32 * u), self.board["kicker"], 12, self.c["muted"], True)
        self.text(
            d,
            (margin, 61 * u),
            entry["chapter"].upper(),
            17,
            self.c["accent"],
            True,
            w - 2 * margin,
        )
        flip = phase % 2 == 1
        if p:
            tx, ty, tw = margin, (530 if flip else 105) * u, w - 2 * margin
            ax, ay, aw, ah = margin, (175 if flip else 290) * u, w - 2 * margin, 300 * u
            detail_y = (690 if flip else 645) * u
        else:
            tx, ty, tw = (545 if flip else 48) * u, 125 * u, 365 * u
            ax, ay, aw, ah = (48 if flip else 440) * u, 120 * u, 472 * u, 285 * u
            detail_y = 356 * u
        size, lines = self.headline_layout(d, beat["headline"], tw)
        for k, line in enumerate(lines):
            stagger = 1 - (1 - min(1, max(0, local - k * 0.045) / 0.32)) ** 3
            self.text(
                d,
                (tx + (1 - stagger) * 60 * u, ty + k * 49 * u),
                line,
                size,
                self.c["ink"],
                True,
                tw,
            )
        if beat.get("image"):
            key = beat["image"]
            if key not in self.images:
                with Image.open(contained(film.folder, key)) as raw:
                    self.images[key] = raw.convert("RGB")
            art = Image.new("RGB", (round(aw), round(ah)), self.c["panel"])
            image = ImageOps.contain(self.images[key], (round(aw), round(ah)))
            art.paste(image, ((art.width - image.width) // 2, (art.height - image.height) // 2))
        else:
            art = self.graphic(beat["kind"], beat["labels"], local, phase)
            image = ImageOps.contain(art, (round(aw), round(ah)))
            art = Image.new("RGB", (round(aw), round(ah)), self.c["panel"])
            art.paste(image, ((art.width - image.width) // 2, (art.height - image.height) // 2))
        # A fast entrance settles into restrained tilt and drift; aspect ratios stay intact.
        art = art.rotate(
            (1 - reveal) * (-4 if flip else 4),
            Image.Resampling.BICUBIC,
            expand=False,
            fillcolor=self.c["background"],
        )
        slide = round((1 - reveal) * 110 * u * (-1 if flip else 1))
        canvas.paste(art, (round(ax) + slide, round(ay + math.sin(local * 2) * 3 * u)))
        d = ImageDraw.Draw(canvas)
        d.line(
            (ax, ay + ah + 14 * u, ax + aw * reveal, ay + ah + 14 * u),
            fill=self.c["accent"],
            width=max(2, round(3 * u)),
        )
        self.text(d, (tx, detail_y), beat["detail"], 18, self.c["muted"], False, tw)
        source_y = (727 if p else 446) * u
        self.text(d, (margin, source_y), beat["source"], 11, self.c["muted"], False, w - 2 * margin)
        self.text(
            d,
            (margin, (751 if p else 461) * u),
            self.board["brand"] + "  /  " + self.board["illustration_label"],
            10,
            self.c["muted"],
            False,
            w - 2 * margin,
        )
        for k in range(10):
            height = (6 + 9 * (1 + math.sin(local * 6 + k))) * u
            x = w - margin - k * 6 * u
            d.line(
                (x, source_y - height, x, source_y - 3 * u),
                fill=self.c["secondary"],
                width=max(1, round(2 * u)),
            )
        d.rectangle((0, 0, w * progress, max(2, round(3 * u))), fill=self.c["accent"])
        return canvas


def generate(
    settings: Settings,
    film: Film,
    output: Path,
    timeline: list[dict[str, Any]],
    board: dict[str, Any],
) -> Film:
    """Render original animated illustrations; keep supplied proof flows separate."""
    r = settings.data["render"]
    painter = Painter(settings, board)
    folder = output / "motion"
    folder.mkdir()
    records = []
    scenes = []
    total = sum(x["frames"] for x in timeline)
    offset = 0
    for scene, timing in zip(film.scenes, timeline, strict=True):
        entry = board["scenes"][scene.ident]
        beat_count = len(entry["beats"])
        if beat_count > timing["frames"] // r["fps"]:
            raise ValueError("Too many authored beats for readable 1-second minimum")
        target_seconds = min(board["beat_seconds"], timing["duration"] / beat_count)
        intervals = schedule(timing["frames"], r["fps"], target_seconds)
        target = folder / (scene.ident + ".mp4")
        args = [
            str(settings.machine["ffmpeg"]),
            "-hide_banner",
            "-loglevel",
            "error",
            "-n",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{painter.w}x{painter.h}",
            "-r",
            str(r["fps"]),
            "-i",
            "pipe:0",
            "-an",
            "-frames:v",
            str(timing["frames"]),
            "-vf",
            f"scale={r['width']}:{r['height']}:flags=lanczos",
            "-c:v",
            "libx264",
            "-preset",
            r["preset"],
            "-crf",
            str(r["crf"]),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            tool_path(target, settings.machine["ffmpeg"].suffix == ".exe"),
        ]

        def frames() -> Iterable[bytes]:
            for index, (start, end) in enumerate(intervals):
                beat = entry["beats"][
                    min(len(entry["beats"]) - 1, index * len(entry["beats"]) // len(intervals))
                ]
                records.append(
                    {
                        "scene": scene.ident,
                        "start_frame": offset + start,
                        "end_frame": offset + end,
                        "headline": beat["headline"],
                        "kind": beat["kind"],
                        "source": beat["source"],
                    }
                )
                for frame in range(start, end):
                    image = painter.frame(
                        entry,
                        beat,
                        (frame - start) / r["fps"],
                        index,
                        (offset + frame) / total,
                        film,
                    )
                    yield image.tobytes()

        write_frames(
            args,
            output,
            folder / (scene.ident + "-encoder.log"),
            settings.data["limits"]["command_timeout_seconds"],
            frames(),
        )
        scenes.append(replace(scene, media=target, motion="none"))
        offset += timing["frames"]
        print("Motion: " + scene.ident + f" ({len(intervals)} visual beats)", flush=True)
    report = {
        "fps": r["fps"],
        "beats": records,
        "board_sha256": hashlib.sha256(
            (film.folder / "motion-board.json").read_bytes()
        ).hexdigest(),
        "kind": "Original editorial diagrams; credited company images where labelled",
        "minimum_beat_seconds": min(
            (x["end_frame"] - x["start_frame"]) / r["fps"] for x in records
        ),
        "maximum_beat_seconds": max(
            (x["end_frame"] - x["start_frame"]) / r["fps"] for x in records
        ),
    }
    (output / "MotionBeats.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "motion-board-input.json").write_text(
        json.dumps(board, indent=2) + "\n", encoding="utf-8"
    )
    return replace(film, scenes=tuple(scenes), overlay_titles=False)


def verify_beats(output: Path, expected: int, fps: int) -> dict[str, Any]:
    report = read_json(output / "MotionBeats.json")
    at = 0
    for beat in report["beats"]:
        if beat["start_frame"] != at or not fps <= beat["end_frame"] - at <= 2 * fps:
            raise ValueError("Motion beat gap or cadence outside 1–2 seconds")
        if beat["kind"] not in KINDS:
            raise ValueError("Unknown recorded composition")
        at = beat["end_frame"]
    if at != expected or report["fps"] != fps:
        raise ValueError("Motion beats do not cover the exact exported timeline")
    return {
        "count": len(report["beats"]),
        "coverage": "passed",
        "minimum_seconds": report["minimum_beat_seconds"],
        "maximum_seconds": report["maximum_beat_seconds"],
    }


def write_frames(
    args: list[str], cwd: Path, log_path: Path, timeout: float, frames: Iterable[bytes]
) -> None:
    """A whole-operation deadline bounds encoder backpressure and final waiting."""

    async def execute() -> None:
        with log_path.open("wb") as log:
            encoder = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=log,
                cwd=cwd,
            )

            async def write() -> None:
                if encoder.stdin is None:
                    raise RuntimeError("Encoder input unavailable")
                for frame in frames:
                    encoder.stdin.write(frame)
                    await encoder.stdin.drain()
                encoder.stdin.close()
                if await encoder.wait():
                    raise RuntimeError("Motion encoder failed; inspect preserved scene log")

            try:
                await asyncio.wait_for(write(), timeout)
            finally:
                if encoder.returncode is None:
                    encoder.kill()
                    await encoder.wait()

    asyncio.run(execute())


def validate_layout(settings: Settings, board: dict[str, Any]) -> None:
    from PIL import Image, ImageDraw

    painter = Painter(settings, board)
    draw = ImageDraw.Draw(Image.new("RGB", (painter.w, painter.h)))
    width = (painter.w - 68 * painter.unit) if painter.portrait else 365 * painter.unit
    for scene in board["scenes"].values():
        for beat in scene["beats"]:
            painter.headline_layout(draw, beat["headline"], width)

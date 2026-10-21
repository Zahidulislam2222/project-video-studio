"""Original procedural motion design, with semantic holds and reusable compositions."""

import math

from PIL import Image, ImageDraw, ImageFont


class Painter:
    def __init__(self, settings, project, shot):
        self.settings, self.project, self.shot = settings, project, shot
        width, height = settings.config["render"]["dimensions"][project.ratio]
        self.w, self.h = width // 2, height // 2
        self.theme = (
            project.theme.model_dump()
            if project.theme
            else settings.config["themes"][project.style]
        )
        self.fonts = {}

    def font(self, size):
        size = round(size)
        if size not in self.fonts:
            self.fonts[size] = ImageFont.truetype(str(self.settings.font), size)
        return self.fonts[size]

    def text(self, draw, text, xy, size, color, width=None, height=None):
        maximum = max(5, round(size))
        minimum = max(5, round(maximum * self.settings.config["render"]["title_minimum_scale"]))
        for candidate_size in range(maximum, minimum - 1, -1):
            font = self.font(candidate_size)
            lines = []
            for paragraph in text.splitlines() or [""]:
                line = ""
                for word in paragraph.split():
                    # Long code/identifiers wrap by character rather than overflowing.
                    chunks = []
                    chunk = ""
                    for character in word:
                        if (
                            width
                            and chunk
                            and draw.textlength(chunk + character, font=font) > width
                        ):
                            chunks.append(chunk)
                            chunk = ""
                        chunk += character
                    chunks.append(chunk)
                    for part in chunks:
                        candidate = (line + " " + part).strip()
                        if width and line and draw.textlength(candidate, font=font) > width:
                            lines.append(line)
                            line = part
                        else:
                            line = candidate
                lines.append(line)
            if not height or len(lines) * candidate_size * 1.35 <= height:
                break
        else:
            raise ValueError("Text does not fit at a readable size; shorten this title or label")
        y = xy[1]
        for line in lines:
            draw.text((xy[0], y), line, font=font, fill=color)
            y += candidate_size * 1.35
        return y

    def frame(self, seconds, duration):
        w, h, t = self.w, self.h, self.theme
        beats = [b for b in self.shot.beats if b.start <= seconds]
        beat = beats[-1] if beats else None
        local_time = seconds - beat.start if beat else seconds
        title = beat.title if beat else self.shot.title
        image = Image.new("RGB", (w, h), t["background"])
        d = ImageDraw.Draw(image)
        margin = w * 0.055
        if self.project.style in ("technical", "cinematic"):
            grid = max(20, w // 24)
            for x in range(0, w, grid):
                d.line((x, 0, x, h), fill=t["panel"])
            for y in range(0, h, grid):
                d.line((0, y, w, y), fill=t["panel"])
        elif self.project.style in ("paper", "pixel"):
            for i in range(80):
                x = (i * 137) % w
                y = (i * 233) % h
                d.rectangle((x, y, x + 2, y + 2), fill=t["panel"])
        reveal = 1 - (1 - min(1, local_time / 0.65)) ** 3
        self.text(
            d,
            f"{self.project.title.upper()[:65]}",
            (margin, h * 0.035),
            max(3, w * (0.023 if self.project.ratio == "portrait" else 0.014)),
            t["accent"],
            w - 2 * margin,
        )
        header = self.shot.title if beat else title
        if beat and not self.shot.layers:
            words = header.split()
            header = " ".join(words[:8]) + ("…" if len(words) > 8 else "")
        self.text(
            d,
            header,
            (margin, h * 0.09 + (1 - reveal) * 15),
            max(5, w * 0.034),
            t["foreground"],
            w - 2 * margin,
            h * 0.12,
        )
        d.rounded_rectangle(
            (margin, h * 0.205, margin + (w - 2 * margin) * reveal, h * 0.211),
            radius=2,
            fill=t["accent"],
        )
        labels = beat.labels if beat else self.shot.labels
        if self.shot.layout == "diagram" and labels:
            portrait = self.project.ratio == "portrait"
            count = len(labels)
            centers = []
            for i, label in enumerate(labels):
                x = w * 0.5 if portrait else w * (0.15 + 0.7 * i / max(1, count - 1))
                y = h * (0.32 + 0.45 * i / max(1, count - 1)) if portrait else h * 0.53
                centers.append((x, y))
                if i:
                    a, b = centers[i - 1], centers[i]
                    d.line((*a, *b), fill=t["accent"], width=3)
                    p = (seconds * 0.45) % 1
                    px = a[0] + (b[0] - a[0]) * p
                    py = a[1] + (b[1] - a[1]) * p
                    d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=t["accent"])
            for i, (label, (x, y)) in enumerate(zip(labels, centers, strict=True)):
                visible = local_time > i * 0.22
                if not visible:
                    continue
                boxw = w * (0.66 if portrait else 0.22)
                boxh = h * (0.075 if portrait else 0.17)
                offset = 5 * math.sin(seconds * 0.9 + i)
                d.rounded_rectangle(
                    (x - boxw / 2, y - boxh / 2 + offset, x + boxw / 2, y + boxh / 2 + offset),
                    radius=0 if self.project.style == "pixel" else 12,
                    fill=t["panel"],
                    outline=t["accent"],
                    width=2,
                )
                self.text(
                    d,
                    label,
                    (x - boxw * 0.43, y - boxh * 0.27 + offset),
                    max(4, w * (0.04 if portrait else 0.018)),
                    t["foreground"],
                    boxw * 0.86,
                    boxh * 0.64,
                )
        elif not self.shot.layers:
            headline = labels[0] if labels else title
            self.text(
                d,
                headline,
                (margin, h * 0.34),
                max(8, w * 0.063),
                t["foreground"],
                w - 2 * margin,
                h * 0.30,
            )
            if len(labels) > 1:
                self.text(
                    d,
                    "  /  ".join(labels[1:]),
                    (margin, h * 0.68),
                    max(4, w * 0.022),
                    t["accent"],
                    w - 2 * margin,
                )
        d.rectangle((0, h - 3, w * min(1, seconds / max(duration, 0.001)), h), fill=t["accent"])
        return image

    def source_note(self, width, height):
        style = self.settings.config["source_note"][self.project.ratio]
        x, y = round(width * style["x"]), round(height * style["y"])
        box_width, box_height = round(width * style["width"]), round(height * style["height"])
        image = Image.new("RGBA", (box_width, box_height), self.theme["background"] + "ed")
        draw = ImageDraw.Draw(image)
        padding = max(1, round(width * style["padding"]))
        self.text(
            draw,
            self.shot.source_note,
            (padding, padding),
            max(5, width * style["font_width"]),
            self.theme["foreground"],
            box_width - 2 * padding,
            box_height - 2 * padding,
        )
        return image, x, y

    def callout(self, callout, width, height):
        region_width = round(width * 0.42)
        region_height = round(height * 0.2)
        padding = round(width * 0.012)
        for size in range(round(width * 0.027), max(5, round(width * 0.014)) - 1, -1):
            font = self.font(size)
            measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
            words = callout.text.split()
            lines = []
            line = ""
            too_wide = False
            for word in words:
                candidate = (line + " " + word).strip()
                if measure.textlength(word, font=font) > region_width - 2 * padding:
                    too_wide = True
                    break
                if line and measure.textlength(candidate, font=font) > region_width - 2 * padding:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            if line:
                lines.append(line)
            needed = round(len(lines) * size * 1.4 + 2 * padding)
            if not too_wide and needed <= region_height:
                break
        else:
            raise ValueError("Callout cannot fit at a readable size; shorten it")
        image = Image.new("RGBA", (region_width, needed), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(
            (0, 0, region_width - 1, needed - 1),
            radius=padding,
            fill=self.theme["panel"],
            outline=self.theme["accent"],
            width=2,
        )
        for i, line in enumerate(lines):
            draw.text(
                (padding, padding + i * size * 1.4), line, font=font, fill=self.theme["foreground"]
            )
        x = min(round(width * callout.x), width - region_width - padding)
        y = min(round(height * callout.y), height - needed - round(height * 0.12))
        return image, x, max(padding, y)


def layout_boxes(layout, ratio):
    if layout == "side-by-side":
        return [(0.04, 0.25, 0.45, 0.56), (0.51, 0.25, 0.45, 0.56)]
    if layout == "stacked":
        return [(0.05, 0.23, 0.9, 0.29), (0.05, 0.55, 0.9, 0.29)]
    if layout == "picture-in-picture":
        return [(0.04, 0.23, 0.92, 0.62), (0.68, 0.58, 0.26, 0.25)]
    return [(0.04, 0.23, 0.92, 0.62)]

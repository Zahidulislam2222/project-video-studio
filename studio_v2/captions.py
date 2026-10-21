"""Pixel-calibrated ASS captions with per-format safe areas."""

from PIL import Image, ImageDraw, ImageFont


def write_ass(settings, project, cues, output):
    render = settings.config["render"]
    width, height = render["dimensions"][project.ratio]
    style = settings.config["captions"][project.ratio]
    size = round(width * style["font_width"])
    face = ImageFont.truetype(str(settings.font), max(1, size))
    family = face.getname()[0]
    if not family:
        raise ValueError("Configured caption font has no family name")
    font = family.replace(",", " ").replace("\n", " ")
    margin_x = round(width * style["margin_x"])
    margin_y = round(height * style["margin_y"])

    def timestamp(value):
        ticks = round(value * 100)
        seconds, cs = divmod(ticks, 100)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02}:{seconds:02}.{cs:02}"

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,{style["outline"]},0,2,{margin_x},{margin_x},{margin_y},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for cue in cues:
        text = (
            cue["text"].replace("\\", "＼").replace("{", "｛").replace("}", "｝").replace("\n", " ")
        )
        measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        wrapped = []
        line = ""
        for word in text.split():
            candidate = (line + " " + word).strip()
            if line and measure.textlength(candidate, font=face) > width - 2 * margin_x:
                wrapped.append(line)
                line = ""
            for character in word:
                if line and measure.textlength(line + character, font=face) > width - 2 * margin_x:
                    wrapped.append(line)
                    line = ""
                line += character
            line += " "
        if line.strip():
            wrapped.append(line.strip())
        if len(wrapped) > style["maximum_lines"]:
            raise ValueError("Caption exceeds its safe region; split or shorten this cue")
        text = "\\N".join(item.strip() for item in wrapped)
        lines.append(
            f"Dialogue: 0,{timestamp(cue['start'])},{timestamp(cue['end'])},Default,,0,0,0,,{text}"
        )
    output.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")

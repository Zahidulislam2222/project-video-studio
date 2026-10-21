"""Portable editing package: source project plus picture and audio tracks."""

from urllib.parse import quote

from defusedxml import ElementTree as XML


def media_url(path):
    value = str(path.resolve())
    if value.startswith("/mnt/") and len(value) > 6 and value[6] == "/":
        return "file://localhost/" + quote(value[5].upper() + ":" + value[6:], safe=":/")
    return path.as_uri()


def SubElement(parent, tag, **attributes):
    node = XML.fromstring("<" + tag + "/>")
    for name, value in attributes.items():
        node.set(name, str(value))
    parent.append(node)
    return node


def write_timeline(folder, project, shots, render):
    root = XML.fromstring('<xmeml version="5"/>')
    seq = SubElement(root, "sequence", id="studio-film")

    def text(parent, key, value):
        SubElement(parent, key).text = str(value)

    def rate(parent):
        value = SubElement(parent, "rate")
        text(value, "timebase", render["fps"])
        text(value, "ntsc", "FALSE")

    text(seq, "name", project.title)
    rate(seq)
    media = SubElement(seq, "media")
    video = SubElement(media, "video")
    track = SubElement(video, "track")
    width, height = render["dimensions"][project.ratio]
    fmt = SubElement(SubElement(video, "format"), "samplecharacteristics")
    rate(fmt)
    text(fmt, "width", width)
    text(fmt, "height", height)
    text(fmt, "pixelaspectratio", "square")
    cursor = 0
    for i, shot in enumerate(shots):
        clip = SubElement(track, "clipitem", id=f"shot-{i}")
        for key, value in [
            ("name", shot["title"]),
            ("start", cursor),
            ("end", cursor + shot["frames"]),
            ("in", 0),
            ("out", shot["frames"]),
            ("duration", shot["frames"]),
        ]:
            text(clip, key, value)
        rate(clip)
        f = SubElement(clip, "file", id=f"file-{i}")
        text(f, "name", shot["id"] + "/picture.mp4")
        text(f, "pathurl", media_url(folder / shot["id"] / "picture.mp4"))
        rate(f)
        sample = SubElement(SubElement(SubElement(f, "media"), "video"), "samplecharacteristics")
        rate(sample)
        text(sample, "width", width)
        text(sample, "height", height)
        cursor += shot["frames"]
    text(seq, "duration", cursor)
    audio = SubElement(media, "audio")
    text(audio, "numOutputChannels", 2)
    audio_name = "MasterAudio.wav" if (folder / "MasterAudio.wav").is_file() else "Voiceover.wav"
    for channel in (1, 2):
        clip = SubElement(SubElement(audio, "track"), "clipitem", id=f"audio-{channel}")
        for key, value in [
            ("name", audio_name),
            ("start", 0),
            ("end", cursor),
            ("in", 0),
            ("out", cursor),
            ("duration", cursor),
        ]:
            text(clip, key, value)
        rate(clip)
        f = SubElement(clip, "file", id="voiceover")
        text(f, "name", audio_name)
        text(f, "pathurl", media_url(folder / audio_name))
        rate(f)
        am = SubElement(SubElement(f, "media"), "audio")
        text(am, "channelcount", 2)
        sample = SubElement(am, "samplecharacteristics")
        text(sample, "samplerate", render["audio_rate"])
        text(sample, "depth", 16)
        source = SubElement(clip, "sourcetrack")
        text(source, "mediatype", "audio")
        text(source, "trackindex", channel)
    (folder / "Timeline.xml").write_bytes(
        XML.tostring(root, encoding="utf-8", xml_declaration=True)
    )
    (folder / "Editing-Guide.txt").write_text(
        "Import Timeline.xml and then Captions.srt. Picture clips contain baked graphics; edit all text, layer positions and timing in project.json and rerender. The timeline uses the normalized master audio when available. For finer mixing, replace it with Voiceover.wav and optional Effects.wav; each shot also retains sound.wav. Portable Inputs and SourceInputs.json allow the restore command to register source assets in a new workspace. Local timeline links require relinking after moving this package. Inspect the result in your editor before publishing.\n"
    )

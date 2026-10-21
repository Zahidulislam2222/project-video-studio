"""Layered deterministic production. Original footage remains immutable."""

import asyncio
import hashlib
import importlib.metadata
import json
import math
import platform
import shutil
import sys
from pathlib import Path

from .graphics import Painter
from .models import Project
from .process import native_args, probe, python_environment, run, srt, stream_duration


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            value.update(block)
    return value.hexdigest()


def asset_path(settings, asset):
    return settings.contained("assets", asset["id"] + asset["extension"])


async def graphics(settings, project, shot, folder, seconds):
    painter = Painter(settings, project, shot)
    r = settings.config["render"]
    width, height = r["dimensions"][project.ratio]
    frames = math.ceil(seconds * r["fps"])
    args = [
        settings.ffmpeg,
        "-hide_banner",
        "-n",
        "-threads",
        str(r["threads"]),
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{painter.w}x{painter.h}",
        "-framerate",
        str(r["fps"]),
        "-i",
        "pipe:0",
        "-vf",
        f"scale={width}:{height}:flags=lanczos",
        "-an",
        "-c:v",
        "libx264",
        "-threads",
        str(r["threads"]),
        "-preset",
        r["preset"],
        "-crf",
        str(r["crf"]),
        "-pix_fmt",
        "yuv420p",
        str(folder / "graphics.mp4"),
    ]
    with (folder / "graphics.log").open("wb") as log:
        child = await asyncio.create_subprocess_exec(
            *native_args(args),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=log,
            cwd=folder,
        )

        async def write():
            try:
                if child.stdin is None:
                    raise RuntimeError("Graphics encoder input pipe is unavailable")
                for index in range(frames):
                    child.stdin.write(
                        painter.frame(index / r["fps"], seconds).tobytes()
                    )
                    await child.stdin.drain()
                child.stdin.close()
                await child.wait()
            finally:
                if child.returncode is None:
                    child.terminate()
                    try:
                        await asyncio.wait_for(child.wait(), r["shutdown_seconds"])
                    except TimeoutError:
                        child.kill()
                        await child.wait()

        await asyncio.wait_for(write(), r["timeout_seconds"])
        if child.returncode:
            raise RuntimeError("Graphics encoding failed; inspect graphics.log")


async def render(settings, store, job, resume=None):
    project = Project.model_validate_json(job["body"])
    if not settings.ffmpeg or not settings.ffprobe:
        raise ValueError("FFmpeg and ffprobe must be configured")
    if not settings.font.is_file():
        raise ValueError("Configured font is unavailable")
    root = settings.contained("renders", job["id"])
    root.mkdir(parents=True, exist_ok=False)
    (root / "project.json").write_text(project.model_dump_json(indent=2))
    r = settings.config["render"]
    width, height = r["dimensions"][project.ratio]
    story = []
    captions = []
    sources = {}
    cursor = 0.0
    previous = None
    if resume:
        old = store.job(job["owner"], resume)
        if not old:
            raise ValueError("Resume source is unavailable in this workspace")
        previous = settings.contained("renders", old["id"])
    engine_hash = hashlib.sha256(
        b"".join(
            p.read_bytes() for p in sorted((settings.root / "studio_v2").glob("*.py"))
        )
    ).hexdigest()
    common = {
        "project": project.model_dump(exclude={"shots"}),
        "config": settings.config,
        "engine": engine_hash,
        "ffmpeg": digest(Path(settings.ffmpeg)),
        "font": digest(settings.font),
        "model": digest(settings.model) if settings.model else None,
        "voices": digest(settings.voices) if settings.voices else None,
        "runtime": {
            "python": platform.python_version(),
            **{
                name: importlib.metadata.version(name)
                for name in ["pillow", "pydantic", "defusedxml"]
            },
            "speech": {
                d.metadata["Name"]: d.version
                for d in importlib.metadata.distributions(path=[str(settings.runtime)])
            }
            if settings.runtime
            else {},
        },
    }

    def get_asset(ident):
        asset = store.asset(job["owner"], ident)
        if not asset:
            raise ValueError("A referenced asset is unavailable in this workspace")
        path = asset_path(settings, asset)
        if digest(path) != asset["sha256"]:
            raise ValueError("Asset hash changed")
        sources[ident] = {
            k: asset[k] for k in ["id", "name", "sha256", "kind", "size", "extension"]
        }
        return asset, path

    for i, shot in enumerate(project.shots):
        state = store.job(job["owner"], job["id"])
        if state["state"] == "cancelled":
            raise asyncio.CancelledError
        folder = root / shot.id
        used = {}
        for ident in [
            shot.audio,
            *[layer.asset for layer in shot.layers],
            *[layer.mask for layer in shot.layers],
            *[layer.matting.asset for layer in shot.layers if layer.matting],
        ]:
            if ident:
                asset, _ = get_asset(ident)
                used[ident] = asset["sha256"]
        recipe = hashlib.sha256(
            json.dumps(
                {**common, "shot": shot.model_dump(), "sources": used}, sort_keys=True
            ).encode()
        ).hexdigest()
        cache = previous / shot.id / "ShotVerification.json" if previous else None
        if cache and cache.is_file():
            recorded = json.loads(cache.read_text())
            prior = cache.parent
            if recorded["recipe"] == recipe and all(
                (prior / name).is_file() and digest(prior / name) == sha
                for name, sha in recorded["files"].items()
            ):
                shutil.copytree(prior, folder)
                seconds = recorded["seconds"]
                cues = recorded["cues"]
                if cursor + seconds > r["maximum_seconds"]:
                    raise ValueError("Actual film exceeds duration budget")
                captions += [
                    {**c, "start": c["start"] + cursor, "end": c["end"] + cursor}
                    for c in cues
                ]
                story.append(
                    {
                        "id": shot.id,
                        "title": shot.title,
                        "start": cursor,
                        "duration": seconds,
                        "frames": round(seconds * r["fps"]),
                        "layers": [layer.model_dump() for layer in shot.layers],
                        "reused": True,
                    }
                )
                cursor += seconds
                store.update_job(
                    job["id"],
                    "running",
                    (i + 1) / len(project.shots),
                    f"Reused verified shot: {shot.title}",
                )
                continue
        folder.mkdir()
        seconds = shot.duration
        cues = []
        audio = None
        if shot.narration.strip():
            (folder / "NarrationRequest.json").write_text(
                json.dumps({"project": project.model_dump(), "shot": shot.model_dump()})
            )
            await run(
                [sys.executable, "-m", "studio_v2.speech", str(folder)],
                folder,
                r["timeout_seconds"],
                env=python_environment(settings),
            )
            generated = json.loads((folder / "Narration.json").read_text())
            audio, length, cues = (
                folder / "voice.wav",
                generated["seconds"],
                generated["cues"],
            )
            needed = length + r["scene_tail"]
            if shot.timing == "fixed" and seconds < needed:
                raise ValueError(
                    "Fixed shot duration would cut narration; lengthen it or revise the script"
                )
            seconds = seconds if shot.timing == "fixed" else needed
        elif shot.audio:
            asset, audio = get_asset(shot.audio)
            if asset["kind"] not in ("audio", "video"):
                raise ValueError("Narration attachment must contain audio")
            info = await probe(settings, audio, folder)
            available = stream_duration(info, "audio") - shot.audio_trim
            length = shot.audio_seconds or available
            if available <= 0 or length > available + 0.05:
                raise ValueError("Recorded audio trim exceeds its stream")
            if shot.timing == "fixed" and seconds < length:
                raise ValueError("Fixed shot duration would cut recorded audio")
            seconds = seconds if shot.timing == "fixed" else length
            cues = [c.model_dump() for c in shot.caption_cues]
        else:
            cues = [c.model_dump() for c in shot.caption_cues]
        seconds = math.ceil(seconds * r["fps"]) / r["fps"]
        if cursor + seconds > r["maximum_seconds"]:
            raise ValueError("Actual film exceeds configured duration budget")
        if any(c["end"] > seconds for c in cues):
            raise ValueError("Caption extends beyond its shot")
        if any(beat.start >= seconds for beat in shot.beats):
            raise ValueError("Visual beat starts beyond its spoken shot")
        if any(b["start"] < a["end"] for a, b in zip(cues, cues[1:])):
            raise ValueError("Caption cues overlap")
        from .creative import spoken_beats

        visual_shot = spoken_beats(settings, shot, cues)
        store.update_job(
            job["id"], "running", i / len(project.shots), f"Rendering {shot.title}"
        )
        await compose(settings, project, visual_shot, folder, seconds, get_asset)
        (folder / "VisualBeats.json").write_text(
            json.dumps([b.model_dump() for b in visual_shot.beats], indent=2)
        )
        audioargs = [settings.ffmpeg, "-hide_banner", "-n"]
        if audio:
            if shot.audio and shot.audio_trim:
                audioargs += ["-ss", str(shot.audio_trim)]
            audioargs += [
                "-protocol_whitelist",
                "file,pipe",
                "-i",
                str(audio),
                "-map",
                "0:a:0",
                "-af",
                f"atrim=duration={length},asetpts=PTS-STARTPTS,apad,loudnorm=I={r['loudness']}:TP={r['true_peak']}:LRA={r['loudness_range']}",
            ]
        else:
            audioargs += [
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=r={r['audio_rate']}:cl=stereo",
            ]
        audioargs += [
            "-t",
            str(seconds),
            "-ar",
            str(r["audio_rate"]),
            "-ac",
            "2",
            str(folder / "sound.wav"),
        ]
        await run(audioargs, folder, r["timeout_seconds"])
        (folder / "ShotVerification.json").write_text(
            json.dumps(
                {
                    "recipe": recipe,
                    "seconds": seconds,
                    "cues": cues,
                    "files": {
                        name: digest(folder / name)
                        for name in ["picture.mp4", "sound.wav"]
                    },
                },
                indent=2,
            )
        )
        captions += [
            {**c, "start": c["start"] + cursor, "end": c["end"] + cursor} for c in cues
        ]
        story.append(
            {
                "id": shot.id,
                "title": shot.title,
                "start": cursor,
                "duration": seconds,
                "frames": round(seconds * r["fps"]),
                "layers": [layer.model_dump() for layer in shot.layers],
            }
        )
        cursor += seconds
    for kind, file in [("picture", "pictures.txt"), ("sound", "audio.txt")]:
        (root / file).write_text(
            "".join(
                f"file '{s['id']}/{kind}.{'mp4' if kind == 'picture' else 'wav'}'\n"
                for s in story
            )
        )
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-f",
            "concat",
            "-safe",
            "1",
            "-i",
            "pictures.txt",
            "-an",
            "-c:v",
            "copy",
            "Picture.mp4",
        ],
        root,
        r["timeout_seconds"],
    )
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-f",
            "concat",
            "-safe",
            "1",
            "-i",
            "audio.txt",
            "-c:a",
            "pcm_s16le",
            "Voiceover.wav",
        ],
        root,
        r["timeout_seconds"],
    )
    from .audio import measure, normalize, soundtrack

    mixed = await soundtrack(settings, project, root, story)
    mixed = str(await normalize(settings, root / mixed, root))
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-i",
            "Picture.mp4",
            "-i",
            mixed,
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-ar",
            str(r["audio_rate"]),
            "-movflags",
            "+faststart",
            "Film-Clean.mp4",
        ],
        root,
        r["timeout_seconds"],
    )
    audio_report = await measure(settings, root / "Film-Clean.mp4", root)
    (root / "Captions.srt").write_text(srt(captions))
    from .captions import write_ass

    write_ass(settings, project, captions, root / "Captions.ass")
    shutil.copy2(settings.font, root / "font.ttf")
    (root / "Transcript.txt").write_text(
        "\n\n".join(
            s.narration or s.spoken_text
            for s in project.shots
            if s.narration or s.spoken_text
        )
    )
    (root / "SourceInputs.json").write_text(
        json.dumps(list(sources.values()), indent=2)
    )
    inputs = root / "Inputs"
    inputs.mkdir()
    for ident, record in sources.items():
        source = asset_path(settings, record)
        shutil.copy2(source, inputs / (ident + record["extension"]))
        if digest(inputs / (ident + record["extension"])) != record["sha256"]:
            raise ValueError("Editing-package source copy differs")
    (root / "Storyboard.json").write_text(
        json.dumps(
            {
                "title": project.title,
                "fps": r["fps"],
                "width": width,
                "height": height,
                "audio_rate": r["audio_rate"],
                "scenes": story,
            },
            indent=2,
        )
    )
    if project.captions and captions:
        await run(
            [
                settings.ffmpeg,
                "-hide_banner",
                "-n",
                "-i",
                "Film-Clean.mp4",
                "-vf",
                "ass=Captions.ass:fontsdir=.",
                "-c:v",
                "libx264",
                "-threads",
                str(r["threads"]),
                "-preset",
                r["preset"],
                "-crf",
                str(r["crf"]),
                "-c:a",
                "copy",
                "-movflags",
                "+faststart",
                "Film-Captioned.mp4",
            ],
            root,
            r["timeout_seconds"],
        )
    report = {
        "status": "passed",
        "seconds": cursor,
        "expected_frames": sum(s["frames"] for s in story),
        "sources": len(sources),
        "captions": len(captions),
        "audio": audio_report,
        "outputs": {},
    }
    for filename in [
        "Film-Clean.mp4",
        *(["Film-Captioned.mp4"] if project.captions and captions else []),
    ]:
        path = root / filename
        info = await probe(settings, path, root)
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        if (video["width"], video["height"]) != (width, height):
            raise ValueError("Export dimensions differ")
        if int(video["nb_frames"]) != report["expected_frames"]:
            raise ValueError("Export frame count differs")
        if abs(float(info["format"]["duration"]) - cursor) > 0.15:
            raise ValueError("Export duration differs")
        await run(
            [
                settings.ffmpeg,
                "-v",
                "error",
                "-xerror",
                "-i",
                str(path),
                "-f",
                "null",
                "-",
            ],
            root,
            r["timeout_seconds"],
        )
        report["outputs"][filename] = {
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "full_decode": "passed",
        }
    from .timeline import write_timeline

    write_timeline(root, project, story, r)
    report["limits"] = [
        "Human listening and editorial review required",
        "Recorded-audio captions require authored cues",
        "Native editor import must be checked on the installed version",
    ]
    (root / "Verification.json").write_text(json.dumps(report, indent=2))
    return report


async def compose(settings, project, shot, folder, seconds, get_asset):
    r = settings.config["render"]
    width, height = r["dimensions"][project.ratio]
    await graphics(settings, project, shot, folder, seconds)
    args = [
        settings.ffmpeg,
        "-hide_banner",
        "-n",
        "-threads",
        str(r["threads"]),
        "-filter_complex_threads",
        "1",
        "-i",
        str(folder / "graphics.mp4"),
    ]
    filters = []
    base = "0:v"
    index = 1
    painter = Painter(settings, project, shot)
    drawn = set()

    def callouts(depth, base, index):
        for j, callout in enumerate(shot.callouts):
            if j in drawn or callout.depth > depth:
                continue
            image, x, y = painter.callout(callout, width, height)
            image.save(folder / f"callout-{j}.png")
            args.extend(
                [
                    "-loop",
                    "1",
                    "-protocol_whitelist",
                    "file,pipe",
                    "-i",
                    str(folder / f"callout-{j}.png"),
                ]
            )
            start, end = callout.start, min(callout.end, seconds)
            if start >= seconds:
                raise ValueError("Callout starts after its shot ends")
            filters.append(
                f"[{base}][{index}:v]overlay=x={x}:y='{y}+{r['callout_slide_pixels']}*(1-min(max((t-{start})/{r['callout_slide_seconds']},0),1))':enable='between(t,{start},{end})'[call{j}]"
            )
            base = f"call{j}"
            index += 1
            drawn.add(j)
        return base, index

    base, index = callouts(0, base, index)
    for layer_number, layer in enumerate(shot.layers):
        asset, path = get_asset(layer.asset)
        if asset["kind"] not in ("image", "video"):
            raise ValueError("Picture layers require images or videos")
        if asset["kind"] == "image":
            args += ["-loop", "1"]
        elif layer.trim:
            args += ["-ss", str(layer.trim)]
        args += ["-protocol_whitelist", "file,pipe", "-i", str(path)]
        if asset["kind"] == "video":
            info = await probe(settings, path, folder)
            if stream_duration(info, "video") - layer.trim + 0.05 < seconds:
                raise ValueError(
                    f"Footage is shorter than shot {shot.id}; shorten narration or record more footage"
                )
        w = max(2, round(width * layer.width / 2) * 2)
        h = max(2, round(height * layer.height / 2) * 2)
        mode = "increase" if layer.fit == "cover" else "decrease"
        finish = (
            f"crop={w}:{h}"
            if layer.fit == "cover"
            else f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black@0"
        )
        filters.append(
            f"[{index}:v]setpts=PTS-STARTPTS,fps={r['fps']},scale={w}:{h}:force_original_aspect_ratio={mode},{finish},setsar=1,format=rgba[layer{index}]"
        )
        layerlabel = f"layer{index}"
        if layer.motion != "none":
            if asset["kind"] != "image":
                raise ValueError(
                    "Camera push/pull currently supports still images; author video camera moves in Blender or your editor"
                )
            progress = f"min(on/{max(1, round(seconds * r['fps']) - 1)},1)"
            z = (
                f"1+{r['camera_zoom']}*{progress}"
                if layer.motion == "push-in"
                else f"1+{r['camera_zoom']}*(1-{progress})"
            )
            filters.append(
                f"[{layerlabel}]zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={w}x{h}:fps={r['fps']},format=rgba[zoom{index}]"
            )
            layerlabel = f"zoom{index}"
        if layer.mask:
            mask, maskpath = get_asset(layer.mask)
            if mask["kind"] not in ("image", "video"):
                raise ValueError("Masks must be grayscale image or video assets")
            if mask["kind"] == "image":
                args += ["-loop", "1"]
            else:
                mask_trim = layer.trim if layer.mask_trim is None else layer.mask_trim
                mask_info = await probe(settings, maskpath, folder)
                if stream_duration(mask_info, "video") - mask_trim + 0.05 < seconds:
                    raise ValueError("Mask video is shorter than its shot")
                if mask_trim:
                    args += ["-ss", str(mask_trim)]
            args += ["-protocol_whitelist", "file,pipe", "-i", str(maskpath)]
            mask_finish = (
                f"crop={w}:{h}"
                if layer.fit == "cover"
                else f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black"
            )
            filters.append(
                f"[{index + 1}:v]setpts=PTS-STARTPTS,fps={r['fps']},scale={w}:{h}:force_original_aspect_ratio={mode},{mask_finish},setsar=1,format=gray[mask{index}]"
            )
            filters.append(f"[{layerlabel}][mask{index}]alphamerge[masked{index}]")
            layerlabel = f"masked{index}"
            nextindex = index + 2
        else:
            nextindex = index + 1
        filters.append(
            f"[{layerlabel}]colorchannelmixer=aa={layer.opacity}[alpha{index}]"
        )
        layerlabel = f"alpha{index}"
        motion = ""
        if shot.transition == "slide":
            motion = f"-{w}*pow(1-min(t/{r['transition_seconds']},1),3)"
        filters.append(
            f"[{base}][{layerlabel}]overlay=x='{round(width * layer.x)}{motion}':y={round(height * layer.y)}:shortest=1[base{index}]"
        )
        base = f"base{index}"
        index = nextindex
        base, index = callouts(layer_number + 1, base, index)
    shutil.copy2(settings.font, folder / "font.ttf")
    base, index = callouts(4, base, index)
    if shot.source_note.strip():
        image, x, y = painter.source_note(width, height)
        image.save(folder / "source-note.png")
        args += [
            "-loop",
            "1",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(folder / "source-note.png"),
        ]
        filters.append(f"[{base}][{index}:v]overlay=x={x}:y={y}[sourcecredit]")
        base = "sourcecredit"
    if shot.transition == "fade":
        fade = min(r["transition_seconds"], seconds / 4)
        filters.append(f"[{base}]fade=t=in:st=0:d={fade}[fade]")
        base = "fade"
    if not filters:
        filters = [f"[{base}]null[picture]"]
        base = "picture"
    args += [
        "-filter_complex",
        ";".join(filters),
        "-map",
        f"[{base}]",
        "-frames:v",
        str(round(seconds * r["fps"])),
        "-an",
        "-c:v",
        "libx264",
        "-threads",
        str(r["threads"]),
        "-crf",
        str(r["crf"]),
        "-preset",
        r["preset"],
        "-pix_fmt",
        "yuv420p",
        str(folder / "picture.mp4"),
    ]
    await run(args, folder, r["timeout_seconds"])
    picture_info = await probe(settings, folder / "picture.mp4", folder)
    stream = next(s for s in picture_info["streams"] if s["codec_type"] == "video")
    if int(stream["nb_frames"]) != round(seconds * r["fps"]):
        raise ValueError("Composed shot frame count differs from its timing")

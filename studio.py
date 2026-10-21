"""Reusable local project films: male narration, captions and verified exports."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import Film, Settings, check_timing, contained, film_settings, read_json, slug
from media_tools import ffmpeg, probe, subtitles

ROOT = Path(__file__).resolve().parent


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def bootstrap(settings: Settings) -> None:
    sys.path.insert(0, str(settings.root / settings.data["runtime_packages"]))
    import onnxruntime

    onnxruntime.disable_telemetry_events()


def project_folder(settings: Settings, name: str) -> Path:
    return contained(contained(settings.root, "projects"), slug(name))


def export_folder(folder: Path, run_id: str) -> Path:
    return contained(contained(folder, "exports"), run_id)


def new_project(settings: Settings, name: str, format_name: str = "custom") -> Path:
    if format_name != "custom" and format_name not in settings.data["formats"]:
        raise ValueError("Unknown film format")
    template = (
        settings.data["formats"][format_name]["template"]
        if format_name != "custom"
        else "templates/new-project.json"
    )
    data = read_json(contained(settings.root, template))
    if format_name != "custom":
        data["motion"] = settings.data["formats"][format_name]["motion"]
    folder = project_folder(settings, name)
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "assets").mkdir()
    data["voice"] = settings.data["default_voice"]
    data["delivery"] = settings.data["default_delivery"]
    save(folder / "film.json", data)
    print("Created projects/" + name + "/film.json", flush=True)
    return folder


def plan(settings: Settings, film: Film) -> dict[str, Any]:
    words = sum(len(sentence.split()) for scene in film.scenes for sentence in scene.sentences)
    seconds = words / settings.data["planning"]["words_per_minute"] * 60
    return {
        "format": film.format_name,
        "words": words,
        "estimated_seconds": round(seconds, 1),
        "target": settings.data["formats"].get(film.format_name),
        "motion": film.motion,
        "sound": film.sound_enabled,
        "music": False,
        "online_requests": sum(s.asset_request is not None for s in film.scenes),
        "note": "Estimate only. Build checks actual narration and opening/ending budgets.",
    }


def doctor(settings: Settings) -> dict[str, Any]:
    bootstrap(settings)
    import importlib.metadata

    from kokoro_onnx import Kokoro

    for key in ("model", "voices"):
        path = settings.root / settings.data[key]
        if hashlib.sha256(path.read_bytes()).hexdigest() != settings.data[key + "_sha256"]:
            raise ValueError("Local voice asset integrity check failed: " + key)
    engine = Kokoro(
        str(settings.root / settings.data["model"]),
        str(settings.root / settings.data["voices"]),
    )
    if any(name not in engine.get_voices() for name in settings.data["male_voices"]):
        raise ValueError("An approved male voice is missing")
    ffmpeg(settings, ["-version"], settings.root)
    report = {
        "runtime": "WSL Python",
        "engine": importlib.metadata.version("kokoro-onnx"),
        "voice": settings.data["default_voice"],
        "male_policy": "passed",
        "delivery_presets": list(settings.delivery),
        "model_hashes": "passed",
        "ffmpeg": "passed",
    }
    save(settings.root / "memory" / "doctor.json", report)
    return report


def render(settings: Settings, film: Film, output: Path, timeline: list[dict[str, Any]]) -> None:
    from motion_design import accent_motion, picture_motion, scene_fade, title_motion
    from sound_design import mix_sound

    r = settings.data["render"]
    shutil.copyfile(settings.machine["font_regular"], output / "regular.ttf")
    shutil.copyfile(settings.machine["font_bold"], output / "bold.ttf")
    for scene, timing in zip(film.scenes, timeline, strict=True):
        if scene.media is not None and scene.media.parent == output / "motion":
            shutil.copyfile(scene.media, output / "media" / (scene.ident + ".mp4"))
            print("Rendered motion scene: " + scene.ident, flush=True)
            continue
        args: list[str | Path]
        if scene.media is None:
            args = [
                "-f",
                "lavfi",
                "-i",
                f"color=c={r['background']}:s={r['width']}x{r['height']}:r={r['fps']}",
            ]
        elif scene.media.suffix.lower() in (".png", ".jpg", ".jpeg"):
            args = ["-loop", "1", "-framerate", str(r["fps"]), "-i", scene.media]
        else:
            source = probe(settings, scene.media)
            available = float(source["format"]["duration"]) - scene.trim_start
            if (
                available + settings.data["limits"]["duration_tolerance_seconds"]
                < timing["duration"]
            ):
                raise ValueError("Recording too short for narration: " + scene.ident)
            args = ["-ss", str(scene.trim_start), "-i", scene.media]
        vf = f"setpts=PTS-STARTPTS,fps={r['fps']},scale={r['width']}:{r['height']}:force_original_aspect_ratio=decrease,pad={r['width']}:{r['height']}:(ow-iw)/2:(oh-ih)/2:color={r['background']},setsar=1"
        vf += picture_motion(settings, scene, timing)
        if scene.media is None or film.overlay_titles or scene.illustrative:
            (output / "title.txt").write_text(scene.title, encoding="utf-8")
            (output / "subtitle.txt").write_text(scene.subtitle, encoding="utf-8")
            y = (
                round(r["height"] * r["card_title_y_fraction"])
                if scene.media is None
                else r["title_y"]
            )
            vf += (
                f",drawbox=x=0:y=0:w=iw:h={r['header_height']}:color={r['background']}@{r['header_opacity']}:t=fill"
                if scene.media
                else ""
            )
            vf += (
                f",drawtext=fontfile=bold.ttf:textfile=title.txt:expansion=none:fontsize={r['title_size']}:fontcolor={r['foreground']}"
                + title_motion(settings, scene, y)
            )
            vf += (
                f",drawtext=fontfile=regular.ttf:textfile=subtitle.txt:expansion=none:fontsize={r['subtitle_size']}:fontcolor={r['accent']}"
                + title_motion(settings, scene, y + r["title_gap"], True)
            )
            vf += accent_motion(settings, scene, y + 2 * r["title_gap"])
        vf += scene_fade(settings, scene, timing["duration"])
        ffmpeg(
            settings,
            [
                *args,
                "-vf",
                vf,
                "-frames:v",
                str(timing["frames"]),
                "-an",
                "-c:v",
                "libx264",
                "-preset",
                r["preset"],
                "-crf",
                str(r["crf"]),
                "-pix_fmt",
                "yuv420p",
                "-r",
                str(r["fps"]),
                "-movflags",
                "+faststart",
                output / "media" / (scene.ident + ".mp4"),
            ],
            output,
        )
        print("Rendered: " + scene.ident, flush=True)
    listing = output / "picture-list.txt"
    listing.write_text(
        "".join("file 'media/" + s.ident + ".mp4'\n" for s in film.scenes),
        encoding="utf-8",
    )
    ffmpeg(
        settings,
        ["-f", "concat", "-safe", "1", "-i", listing, "-c", "copy", "picture.mp4"],
        output,
    )
    ffmpeg(
        settings,
        [
            "-i",
            "narration-raw.wav",
            "-af",
            f"loudnorm=I={r['loudness']}:TP={r['true_peak']}:LRA={r['loudness_range']}",
            "-ar",
            str(r["audio_rate"]),
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            "Voiceover.wav",
        ],
        output,
    )
    soundtrack = mix_sound(settings, film, output, timeline)
    ffmpeg(
        settings,
        [
            "-i",
            "picture.mp4",
            "-i",
            soundtrack,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            r["audio_bitrate"],
            "-shortest",
            "-movflags",
            "+faststart",
            "-metadata",
            "title=" + film.title,
            "-metadata",
            "artist=" + film.author,
            "Film-Clean.mp4",
        ],
        output,
    )
    vf = f"drawbox=x=0:y=ih-{settings.data['captions']['safe_band']}:w=iw:h={settings.data['captions']['safe_band']}:color={r['background']}@{settings.data['captions']['band_opacity']}:t=fill,subtitles=filename=Captions.ass"
    ffmpeg(
        settings,
        [
            "-i",
            "Film-Clean.mp4",
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            r["preset"],
            "-crf",
            str(r["crf"]),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            "Film-Captioned.mp4",
        ],
        output,
    )


def verify(settings: Settings, output: Path) -> dict[str, Any]:
    bootstrap(settings)
    from urllib.parse import unquote, urlparse

    from defusedxml import ElementTree as XML

    story = read_json(output / "storyboard.json")
    recorded = read_json(output / "settings-input.json")
    r = recorded["render"]
    expected = sum(x["frames"] for x in story["scenes"])
    exports = {}
    for name in ("Film-Clean.mp4", "Film-Captioned.mp4"):
        data = probe(settings, output / name)
        video = next(x for x in data["streams"] if x["codec_type"] == "video")
        audio = next(x for x in data["streams"] if x["codec_type"] == "audio")
        if (
            video["codec_name"],
            video["width"],
            video["height"],
            video["r_frame_rate"],
            int(video["nb_frames"]),
        ) != ("h264", r["width"], r["height"], f"{r['fps']}/1", expected):
            raise ValueError("Export video format or exact frame count mismatch")
        if (audio["codec_name"], int(audio["sample_rate"]), audio["channels"]) != (
            "aac",
            r["audio_rate"],
            2,
        ):
            raise ValueError("Export audio format mismatch")
        duration = float(data["format"]["duration"])
        if abs(duration - expected / r["fps"]) > recorded["limits"]["duration_tolerance_seconds"]:
            raise ValueError("Export duration mismatch")
        errors = ffmpeg(settings, ["-v", "error", "-i", output / name, "-f", "null", "-"], output)
        if errors.strip():
            raise ValueError("Full export decode reported errors")
        exports[name] = {
            "seconds": duration,
            "frames": expected,
            "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(),
        }
    for scene in story["scenes"]:
        source = probe(settings, output / "media" / (scene["id"] + ".mp4"))
        if int(source["streams"][0]["nb_frames"]) != scene["frames"]:
            raise ValueError("Scene frame count mismatch")
    cues = json.loads((output / "cues.json").read_text(encoding="utf-8"))
    last = 0.0
    for cue in cues:
        if (
            cue["start"] < last
            or cue["end"] - cue["start"] < recorded["captions"]["minimum_seconds"]
        ):
            raise ValueError("Overlapping or brief captions")
        if len(cue["text"].splitlines()) > recorded["captions"]["lines"] or any(
            len(x) > recorded["captions"]["line_characters"] for x in cue["text"].splitlines()
        ):
            raise ValueError("Caption layout outside limits")
        last = cue["end"]
    if last > expected / r["fps"]:
        raise ValueError("Captions exceed the picture")
    xml = XML.parse(output / "Timeline.xml")
    if int(xml.findtext(".//sequence/duration")) != expected or len(
        xml.findall(".//video/track/clipitem")
    ) != len(story["scenes"]):
        raise ValueError("Timeline frame or clip count mismatch")
    for item in xml.findall(".//pathurl"):
        uri = unquote(urlparse(item.text).path).lstrip("/")
        target = (
            Path("/mnt/" + uri[0].lower() + uri[2:])
            if re.match(r"^[A-Za-z]:/", uri)
            else Path("/" + uri)
        )
        if not target.is_file() or not target.resolve().is_relative_to(output.resolve()):
            raise ValueError("Timeline media reference missing or outside export")
    report = {
        "exports": exports,
        "full_decode": "passed",
        "scene_frames": "passed",
        "captions": len(cues),
        "timeline_media": "passed",
        "voice": story["voice"],
        "delivery": "Stock male voice with configured pacing and pauses",
        "limits": [
            "Human listening and installed-editor import have not been verified.",
            "Delivery presets are not emotion prompts.",
        ],
    }
    if (output / "Timing.json").is_file():
        from export_checks import verify_audio, verify_sources

        report["timing"] = read_json(output / "Timing.json")
        actual_seconds = expected / r["fps"]
        if (
            abs(report["timing"]["seconds"] - actual_seconds)
            > recorded["limits"]["duration_tolerance_seconds"]
        ):
            raise ValueError("Timing report does not match rendered frames")
        format_name = read_json(output / "film-input.json").get("format", "custom")
        if format_name != "custom":
            preset = recorded["formats"][format_name]
            if not preset["minimum_seconds"] <= actual_seconds <= preset["maximum_seconds"]:
                raise ValueError("Export outside its format duration range")
            if story["scenes"][0]["role"] != "intro" or story["scenes"][-1]["role"] != "outro":
                raise ValueError("Export missing brief opening or ending")
            for scene in story["scenes"]:
                if (
                    scene["role"] in ("intro", "outro")
                    and scene["duration"] > preset[scene["role"] + "_max_seconds"]
                ):
                    raise ValueError("Export opening or ending exceeds budget")
        report["motion"] = {"presets": sorted({s["motion"] for s in story["scenes"]})}
        report["sound"] = (
            read_json(output / "SoundDesign.json")
            if (output / "SoundDesign.json").is_file()
            else {"enabled": False}
        )
        report["source_assets"] = len(json.loads((output / "AssetSources.json").read_text()))
        report["sources"] = verify_sources(settings, output, recorded)
        report["audio"] = verify_audio(settings, output, recorded, actual_seconds)
    if (output / "MotionBeats.json").is_file():
        from motion_board import verify_beats

        report["visual_beats"] = verify_beats(output, expected, r["fps"])
    save(output / "Verification.json", report)
    return report


def build(settings: Settings, name: str) -> Path:
    folder = project_folder(settings, name)
    film = Film.load(folder, settings)
    from motion_board import generate, load_board, record_board_sources

    board = load_board(film)
    settings = film_settings(settings, film.format_name, film.sound_overrides)
    bootstrap(settings)
    if board is not None:
        from motion_board import validate_layout

        validate_layout(settings, board)
    from narration import synthesize
    from timeline import write_timeline

    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    output = export_folder(folder, run_id)
    output.mkdir(parents=True, exist_ok=False)
    (output / "media").mkdir()
    status = {"project": name, "run": run_id, "phase": "assets", "complete": False}
    checkpoint = settings.root / "memory" / "latest-run.json"
    save(checkpoint, status)
    try:
        from asset_library import resolve

        save(output / "film-input.json", read_json(folder / "film.json"))
        save(output / "settings-input.json", settings.data)
        film = resolve(settings, film, output)
        from export_checks import record_sources

        status["phase"] = "narration"
        save(checkpoint, status)
        timeline, cues = synthesize(settings, film, output)
        save(output / "Timing.json", check_timing(settings, film, timeline))
        subtitles(settings, cues, output)
        story = {
            "title": film.title,
            "author": film.author,
            "voice": film.voice,
            "width": settings.data["render"]["width"],
            "height": settings.data["render"]["height"],
            "fps": settings.data["render"]["fps"],
            "audio_rate": settings.data["render"]["audio_rate"],
            "scenes": timeline,
        }
        save(output / "storyboard.json", story)
        save(output / "cues.json", cues)
        (output / "Transcript.txt").write_text(
            film.title + "\n\n" + "\n\n".join(" ".join(s.sentences) for s in film.scenes) + "\n",
            encoding="utf-8",
        )
        if board is not None:
            status["phase"] = "motion"
            save(checkpoint, status)
            film = generate(settings, film, output, timeline, board)
        record_sources(film, output)
        if board is not None:
            record_board_sources(film, output, board)
        status["phase"] = "render"
        save(checkpoint, status)
        render(settings, film, output, timeline)
        write_timeline(output, story)
        status["phase"] = "verification"
        save(checkpoint, status)
        verify(settings, output)
        status.update(phase="verified", complete=True)
        save(checkpoint, status)
        save(folder / "latest-export.json", {"run": run_id})
        print("Verified export: projects/" + name + "/exports/" + run_id, flush=True)
        return output
    except Exception:
        status["phase"] = "failed-" + str(status["phase"])
        save(checkpoint, status)
        raise


def preview(settings: Settings) -> Path:
    folder = project_folder(settings, "voice-preview")
    if not folder.exists():
        new_project(settings, "voice-preview")
        data = read_json(folder / "film.json")
        content = read_json(settings.root / "templates" / "voice-preview.json")
        data.update(title=content["title"], author=content["author"])
        template = data["scenes"][0]
        data["scenes"] = []
        for name in settings.delivery:
            scene = dict(template)
            scene.update(
                id=name,
                title=content["scene_titles"][name],
                subtitle=content["subtitle"],
                delivery=name,
                sentences=content["sentences"],
            )
            data["scenes"].append(scene)
        save(folder / "film.json", data)
    return build(settings, "voice-preview")


def menu(settings: Settings) -> None:
    while True:
        print(
            "\nProject Video Studio\n1. New project\n2. Build project\n3. Male voice previews\n4. Check tools\n5. Exit"
        )
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                name = input("Project name (lowercase-with-hyphens): ").strip()
                format_name = (
                    input("Format (short / long / custom) [short]: ").strip()
                    or settings.data["default_format"]
                )
                new_project(settings, name, format_name)
            elif choice == "2":
                name = input("Project name: ").strip()
                print(
                    json.dumps(
                        plan(settings, Film.load(project_folder(settings, name), settings)),
                        indent=2,
                    )
                )
                build(settings, name)
            elif choice == "3":
                preview(settings)
            elif choice == "4":
                print(json.dumps(doctor(settings), indent=2))
            elif choice == "5":
                return
        except (ValueError, OSError, RuntimeError) as error:
            print(str(error))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("new", "build", "verify", "timeline", "plan", "search-assets"):
        p = sub.add_parser(name)
        p.add_argument("project")
        if name == "new":
            p.add_argument("--format", dest="format_name")
        if name == "search-assets":
            p.add_argument("kind", choices=("image", "video", "audio"))
            p.add_argument("query")
            p.add_argument("--library")
    for name in ("doctor", "preview", "menu"):
        sub.add_parser(name)
    args = parser.parse_args()
    settings = Settings.load(ROOT)
    if args.action == "new":
        new_project(settings, args.project, args.format_name or settings.data["default_format"])
    elif args.action == "build":
        build(settings, args.project)
    elif args.action == "doctor":
        print(json.dumps(doctor(settings), indent=2))
    elif args.action == "preview":
        preview(settings)
    elif args.action == "menu":
        menu(settings)
    elif args.action == "plan":
        print(
            json.dumps(
                plan(settings, Film.load(project_folder(settings, args.project), settings)),
                indent=2,
            )
        )
    elif args.action == "search-assets":
        from asset_library import search

        folder = project_folder(settings, args.project)
        Film.load(folder, settings)
        request = {
            "kind": args.kind,
            "query": safe_query(args.query, settings),
            "library": args.library or settings.data["default_asset_library"],
        }
        report = search(settings, request)
        save(folder / "asset-candidates.json", report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        folder = project_folder(settings, args.project)
        latest = read_json(folder / "latest-export.json")
        if not re.fullmatch(r"[0-9-]+", latest["run"]):
            raise ValueError("Invalid export identifier")
        output = export_folder(folder, latest["run"])
        if args.action == "verify":
            print(json.dumps(verify(settings, output), indent=2))
        else:
            bootstrap(settings)
            from timeline import write_timeline

            write_timeline(output, read_json(output / "storyboard.json"))
            print("Timeline media locations refreshed")


def safe_query(query: str, settings: Settings) -> str:
    from config import safe_text

    value = safe_text(query)
    if len(value) > settings.data["online"]["query_characters"]:
        raise ValueError("Asset query too long")
    return value


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
        print("Studio stopped: " + str(error), file=sys.stderr)
        sys.exit(1)

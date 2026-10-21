"""Assemble approved inputs into an editable draft; retain timestamped revisions."""

import json
import math
import re

from pydantic import Field, model_validator

from .models import Caption, Contract, Project, Shot
from .process import probe, stream_duration


class ProductionRequest(Contract):
    title: str = Field(min_length=1, max_length=140)
    script: str = Field(default="", max_length=12000)
    script_file: str | None = None
    brief: str = Field(default="", max_length=12000)
    recording: str | None = None
    captions_file: str | None = None
    language: str | None = None
    footage: list[str] = Field(default_factory=list, max_length=160)
    companion: str | None = None
    layout: str = "auto"
    ratio: str = "landscape"
    style: str = "technical"
    profile: str | None = None
    source_note: str = Field(
        default="Owner-supplied media; review before release", max_length=300
    )
    media_approved: bool = False
    use_ai: bool = False
    effects: bool = False
    matte_presenter: bool = False

    @model_validator(mode="after")
    def inputs(self):
        if self.recording and (self.script or self.script_file):
            raise ValueError(
                "Use a spoken script or a recording; correct recorded captions through SRT"
            )
        if (
            self.footage or self.recording or self.companion
        ) and not self.media_approved:
            raise ValueError(
                "Confirm media_approved after checking rights and private content"
            )
        if self.matte_presenter and self.footage and not self.companion:
            raise ValueError(
                "Choose a presenter companion separately from main footage for human matting"
            )
        if self.matte_presenter and not (self.companion or self.recording):
            raise ValueError(
                "Choose a presenter companion or video recording for human matting"
            )
        return self


def read_srt(path):
    cues = []
    for block in re.split(
        r"\n\s*\n", path.read_text(encoding="utf-8-sig").replace("\r", "").strip()
    ):
        lines = block.splitlines()
        time_index = next((i for i, line in enumerate(lines) if " --> " in line), None)
        if time_index is None:
            raise ValueError("Invalid SRT cue")
        values = lines[time_index].split(" --> ")

        def seconds(text):
            hours, minutes, seconds = text.replace(",", ".").split(":")
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

        cues.append(
            {
                "start": seconds(values[0]),
                "end": seconds(values[1]),
                "text": " ".join(lines[time_index + 1 :]),
            }
        )
    if not cues:
        raise ValueError("SRT contains no cues")
    if any(c["start"] < 0 or c["end"] <= c["start"] for c in cues) or any(
        b["start"] < a["end"] for a, b in zip(cues, cues[1:])
    ):
        raise ValueError("SRT cues must be ordered, positive and non-overlapping")
    return cues


async def prepare(settings, store, owner, request_file, output):
    from pathlib import Path

    from .__main__ import import_asset
    from .director import plan
    from .transcription import transcribe

    request = ProductionRequest.model_validate_json(request_file.read_text())
    if output.exists():
        raise ValueError(
            "Choose a new production folder; existing drafts are preserved"
        )
    output.mkdir(parents=True)

    def path(value):
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = request_file.parent / candidate
        return candidate.resolve()

    if request.script_file:
        request.script = path(request.script_file).read_text()
    profile = json.loads(path(request.profile).read_text()) if request.profile else None
    imported = []
    for source in request.footage:
        file = path(source)
        ident = import_asset(settings, store, owner, file)
        asset = store.asset(owner, ident)
        if asset["kind"] not in ("image", "video"):
            raise ValueError("Footage must be image or video media")
        info = await probe(settings, file, output)
        length = stream_duration(info, "video") if asset["kind"] == "video" else None
        imported.append((ident, length))
    companion = (
        import_asset(settings, store, owner, path(request.companion))
        if request.companion
        else None
    )
    companion_seconds = None
    if companion:
        companion_asset = store.asset(owner, companion)
        if companion_asset["kind"] not in ("image", "video"):
            raise ValueError("A companion view must be image or video media")
        if companion_asset["kind"] == "video":
            companion_seconds = stream_duration(
                await probe(settings, path(request.companion), output), "video"
            )
    layout = request.layout
    if layout == "auto":
        layout = (
            ("stacked" if request.ratio == "portrait" else "side-by-side")
            if companion
            else "full"
        )
    if request.recording:
        recording = path(request.recording)
        audio = import_asset(settings, store, owner, recording)
        info = await probe(settings, recording, output)
        available = stream_duration(info, "audio")
        cues = (
            read_srt(path(request.captions_file))
            if request.captions_file
            else (
                await transcribe(
                    settings, recording, output / "transcription", request.language
                )
            )["cues"]
        )
        if (
            cues[-1]["end"]
            > available + settings.config["production"]["timing_tolerance"]
        ):
            raise ValueError("Transcript extends beyond the recording")
        # Preserve the recording continuously; separate shots at spoken cue boundaries.
        groups = []
        start = 0.0
        group = []
        for cue in cues:
            group.append(cue)
            if (
                cue["end"] - start
                >= settings.config["production"]["recorded_shot_seconds"]
            ):
                groups.append((start, cue["end"], group))
                start, group = cue["end"], []
        if group:
            groups.append((start, available, group))
        elif start < available:
            a, _, values = groups[-1]
            groups[-1] = (a, available, values)
        if len(groups) > 1 and groups[-1][1] - groups[-1][0] < 1:
            a, _, first = groups[-2]
            _, end, last = groups.pop()
            groups[-1] = (a, end, first + last)
        shots = []
        video_recording = next(
            (s for s in info["streams"] if s["codec_type"] == "video"), None
        )
        if video_recording and not imported:
            imported = [(audio, stream_duration(info, "video"))]
        for i, (start, end, group) in enumerate(groups):
            seconds = (
                math.ceil((end - start) * settings.config["render"]["fps"])
                / settings.config["render"]["fps"]
            )
            shots.append(
                Shot.model_validate(
                    dict(
                        id=f"shot-{i + 1:02}",
                        title=group[0]["text"][:110],
                        spoken_text=" ".join(c["text"] for c in group),
                        duration=max(1, seconds),
                        timing="fixed",
                        audio=audio,
                        audio_trim=start,
                        audio_seconds=end - start,
                        caption_cues=[
                            {**c, "start": c["start"] - start, "end": c["end"] - start}
                            for c in group
                        ],
                    )
                )
            )
        project = Project.model_validate(
            dict(
                title=request.title,
                ratio=request.ratio,
                style=request.style,
                shots=shots,
            )
        )
    elif request.use_ai and not request.script.strip():
        project = await plan(settings, request.brief, request.ratio, request.style)
        project.title = request.title
    else:
        paragraphs = [p.strip() for p in request.script.split("\n\n") if p.strip()]
        if not paragraphs:
            raise ValueError(
                "Supply a script, recorded narration, or a brief with use_ai enabled"
            )
        project = Project.model_validate(
            {
                "title": request.title,
                "ratio": request.ratio,
                "style": request.style,
                "shots": [
                    {
                        "id": f"shot-{i + 1:02}",
                        "title": p.split(".")[0][:100],
                        "narration": p,
                        "duration": max(
                            1,
                            len(p.split())
                            / settings.config["production"][
                                "planning_words_per_second"
                            ],
                        ),
                    }
                    for i, p in enumerate(paragraphs)
                ],
            }
        )
    # Resolve actual narration before assigning footage offsets; word-count estimates
    # cannot safely determine where the next source clip begins.
    for shot in project.shots:
        if shot.narration.strip():
            import sys

            from .process import python_environment, run

            folder = output / "narration" / shot.id
            folder.mkdir(parents=True)
            (folder / "NarrationRequest.json").write_text(
                json.dumps({"project": project.model_dump(), "shot": shot.model_dump()})
            )
            await run(
                [sys.executable, "-m", "studio_v2.speech", str(folder)],
                folder,
                settings.config["render"]["timeout_seconds"],
                env=python_environment(settings),
            )
            generated = json.loads((folder / "Narration.json").read_text())
            shot.audio = import_asset(settings, store, owner, folder / "voice.wav")
            shot.spoken_text, shot.narration = shot.narration, ""
            shot.audio_seconds = generated["seconds"]
            shot.duration = (
                math.ceil(
                    (generated["seconds"] + settings.config["render"]["scene_tail"])
                    * settings.config["render"]["fps"]
                )
                / settings.config["render"]["fps"]
            )
            shot.timing = "fixed"
            shot.caption_cues = [Caption.model_validate(c) for c in generated["cues"]]
    if not imported and companion:
        imported = [(companion, companion_seconds)]
        companion = None
        if request.layout == "auto":
            layout = "full"
    offsets = {ident: 0.0 for ident, _ in imported}
    companion_cursor = 0.0
    for i, shot in enumerate(project.shots):
        if imported:
            ident, length = imported[i % len(imported)]
            trim = shot.audio_trim if ident == shot.audio else offsets[ident]
            shot_values = shot.model_dump()
            shot_values["layout"] = layout
            shot_values["layers"] = [{"asset": ident, "trim": trim}]
            if companion:
                companion_trim = (
                    (shot.audio_trim if request.recording else companion_cursor)
                    if companion_seconds is not None
                    else 0
                )
                if (
                    companion_seconds is not None
                    and companion_trim + shot.duration
                    > companion_seconds
                    + settings.config["production"]["timing_tolerance"]
                ):
                    raise ValueError(
                        "The companion video does not cover the draft; supply a longer matching recording"
                    )
                shot_values["layers"].append(
                    {"asset": companion, "trim": companion_trim}
                )
                companion_cursor += shot.duration
            shot = Shot.model_validate(shot_values)
            project.shots[i] = shot
            # Recorded speech timing is known; generated speech is validated against media at build.
            if (
                length is not None
                and trim + shot.duration
                > length + settings.config["production"]["timing_tolerance"]
            ):
                raise ValueError(
                    "Footage does not cover the draft. Supply longer footage, more clips, or use stills for this script"
                )
            offsets[ident] = trim + shot.duration
            shot.source_note = request.source_note
        else:
            shot.layout = "diagram" if i % 2 else "full"
            if shot.layout == "diagram":
                shot.labels = [
                    sentence.strip()[:40]
                    for sentence in re.split(
                        r"[.!?]", shot.spoken_text or shot.narration
                    )
                    if sentence.strip()
                ][:3]
        shot.transition = settings.config["production"]["transitions"][
            i % len(settings.config["production"]["transitions"])
        ]
    if request.matte_presenter:
        from .matting import matte
        from .render import asset_path

        for shot in project.shots:
            if shot.proof or not shot.layers:
                raise ValueError(
                    "Automatic cutouts require an illustrative presenter video layer"
                )
            layer = shot.layers[-1] if companion else shot.layers[0]
            original = store.asset(owner, layer.asset)
            if original["kind"] != "video":
                raise ValueError("The selected presenter must be a video recording")
            cutout = output / "cutouts" / shot.id
            result = await matte(
                settings,
                asset_path(settings, original),
                cutout,
                layer.trim,
                shot.duration,
            )
            old_asset, old_trim = layer.asset, layer.trim
            layer.asset = import_asset(
                settings, store, owner, cutout / "Foreground.mkv"
            )
            layer.mask = import_asset(settings, store, owner, cutout / "Mask.mkv", derived=True)
            layer.trim, layer.mask_trim = 0, 0
            layer_values = layer.model_dump()
            layer_values["matting"] = {
                "asset": old_asset,
                "start": old_trim,
                "seconds": shot.duration,
                "model_sha256": result["model_sha256"],
            }
            from .models import Layer

            shot.layers[shot.layers.index(layer)] = Layer.model_validate(layer_values)
            shot.source_note = ("AI human cutout; " + request.source_note)[:300]
    body = project.model_dump()
    if profile:
        body["theme"] = profile["theme"]
    body["effects"] = request.effects
    project = Project.model_validate(body)
    target = output / "project.json"
    target.write_text(project.model_dump_json(indent=2))
    (output / "ProductionRequest.json").write_text(request.model_dump_json(indent=2))
    (output / "Review.txt").write_text(
        "Review the script/transcript for accuracy and source privacy. Run style-test and animation-test, then build. AI does not verify rights or factual claims. Source clips are never silently looped to fill missing footage. Revise into a new folder; retain all earlier drafts.\n"
    )
    cursor = 0.0
    lines = [project.title, "", "Review this storyboard before full production.", ""]
    for shot in project.shots:
        lines.extend(
            [
                f"{cursor:.2f}s | {shot.id} | {shot.layout} | {shot.title}",
                shot.spoken_text or shot.narration,
                shot.source_note,
                "",
            ]
        )
        cursor += shot.duration
    (output / "Storyboard.txt").write_text("\n".join(lines))
    return target


def revise(source, changes_file, output):
    if output.exists():
        raise ValueError("Choose a new revision file; earlier drafts are preserved")
    project = Project.model_validate_json(source.read_text())
    changes = json.loads(changes_file.read_text())
    if set(changes) - {"project", "shots", "at"}:
        raise ValueError("Revisions accept project and shot changes only")
    body = project.model_dump()
    timeline = []
    cursor = 0.0
    for shot in project.shots:
        timeline.append((cursor, cursor + shot.duration, shot.id, shot.timing))
        cursor += shot.duration
    top = changes.get("project", {})
    if "shots" in top:
        raise ValueError("Revise shots by stable ID")
    body.update(top)
    known = {s["id"]: s for s in body["shots"]}
    for ident, updates in changes.get("shots", {}).items():
        if ident not in known or "id" in updates:
            raise ValueError(
                "Revision references an unknown shot or changes its identity"
            )
        known[ident].update(updates)
    for entry in changes.get("at", []):
        if (
            set(entry) != {"seconds", "set"}
            or not isinstance(entry["seconds"], (float, int))
            or not math.isfinite(entry["seconds"])
        ):
            raise ValueError("Timestamp revisions need finite seconds and a set object")
        found = False
        for start, end, ident, timing in timeline:
            if timing != "fixed":
                raise ValueError(
                    "Timestamp revisions need an audio-prepared project with fixed timing"
                )
            if start <= entry["seconds"] < end:
                if "id" in entry["set"]:
                    raise ValueError("A timestamp revision cannot change shot identity")
                known[ident].update(entry["set"])
                found = True
                break
        if not found:
            raise ValueError("Revision timestamp is outside the film")
    validated = Project.model_validate(body)
    with output.open("x") as handle:
        handle.write(validated.model_dump_json(indent=2))
    return output

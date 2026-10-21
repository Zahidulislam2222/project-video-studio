"""Style and animation checkpoints use the production compositor and real sources."""

import json

from .process import probe, run, stream_duration
from .render import asset_path, compose, digest


async def preview(settings, store, owner, project, output, stills=False):
    output.mkdir(parents=True, exist_ok=False)
    for i, original in enumerate(project.shots[:3] if stills else project.shots[:1]):
        folder = output / original.id
        folder.mkdir()

        def get_asset(ident):
            asset = store.asset(owner, ident)
            if not asset:
                raise ValueError("Preview asset is unavailable in this workspace")
            path = asset_path(settings, asset)
            if digest(path) != asset["sha256"]:
                raise ValueError("Preview source hash changed")
            return asset, path

        seconds = min(original.duration, settings.config["render"]["animation_test_seconds"])
        for layer in original.layers:
            for ident, trim in [
                (layer.asset, layer.trim),
                (layer.mask, layer.trim if layer.mask_trim is None else layer.mask_trim),
            ]:
                if ident:
                    asset, path = get_asset(ident)
                    if asset["kind"] == "video":
                        available = (
                            stream_duration(await probe(settings, path, folder), "video") - trim
                        )
                        seconds = min(seconds, available)
        fps = settings.config["render"]["fps"]
        seconds = int(seconds * fps) / fps
        if seconds < 1 / fps:
            raise ValueError("Preview has no usable frames after trimming")
        shot = original.model_copy(
            update={
                "beats": [b for b in original.beats if b.start < seconds],
                "callouts": [
                    c.model_copy(update={"end": min(c.end, seconds)})
                    for c in original.callouts
                    if c.start < seconds
                ],
            }
        )
        from .creative import spoken_beats

        shot = spoken_beats(
            settings, shot, [c.model_dump() for c in original.caption_cues if c.start < seconds]
        )
        await compose(settings, project, shot, folder, seconds, get_asset)
        if stills:
            await run(
                [
                    settings.ffmpeg,
                    "-v",
                    "error",
                    "-n",
                    "-ss",
                    str(seconds / 2),
                    "-i",
                    str(folder / "picture.mp4"),
                    "-frames:v",
                    "1",
                    str(output / f"style-{i + 1}.png"),
                ],
                folder,
                settings.config["render"]["timeout_seconds"],
            )
    (output / "Preview.json").write_text(
        json.dumps(
            {
                "project": digest_source(project),
                "checkpoint": "style" if stills else "animation",
                "scope": "Actual production picture compositor with approved assets, masks, callouts and transitions. Narration-driven automatic beats are resolved during audio production; this is a bounded sample, not the full film.",
            },
            indent=2,
        )
    )
    return output


def digest_source(project):
    import hashlib

    return hashlib.sha256(project.model_dump_json().encode()).hexdigest()

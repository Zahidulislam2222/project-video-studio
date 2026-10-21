"""Local production commands. Existing v1 projects remain independent."""

import argparse
import asyncio
import json
import shutil
import uuid
from pathlib import Path

from .models import Project
from .process import render_lock
from .render import digest, render
from .settings import Settings
from .store import Store


def import_asset(settings, store, owner, source, *, derived=False):
    source = source.resolve()
    extension = source.suffix.lower()
    kinds = {
        ".mp4": "video",
        ".mov": "video",
        ".webm": "video",
        ".mkv": "video",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".wav": "audio",
        ".mp3": "audio",
        ".m4a": "audio",
    }
    if extension not in kinds:
        raise ValueError("Unsupported asset type")
    limit = settings.config["storage"]["derived_asset_bytes" if derived else "upload_bytes"]
    if source.stat().st_size > limit:
        raise ValueError("Asset exceeds its configured input/derived-media limit")
    ident = uuid.uuid4().hex
    folder = settings.contained("assets")
    folder.mkdir(exist_ok=True)
    target = folder / (ident + extension)
    shutil.copy2(source, target)
    try:
        store.add_asset(
            (
                ident,
                owner,
                source.name,
                kinds[extension],
                target.stat().st_size,
                digest(target),
                extension,
            )
        )
    except Exception:
        target.unlink()
        raise
    return ident


async def execute(args):
    settings = Settings.load()
    store = Store(settings)
    owner = "local"
    if args.action == "menu":
        from .menu import menu

        await menu(settings)
        return
    if args.action == "doctor":
        from .doctor import doctor

        print(json.dumps(await doctor(settings), indent=2))
        return
    if args.action == "asset":
        print(import_asset(settings, store, owner, Path(args.file)))
        return
    if args.action == "matte":
        from .matting import matte

        print(
            json.dumps(
                await matte(
                    settings,
                    Path(args.file).resolve(),
                    Path(args.output).resolve(),
                    args.start,
                    args.seconds,
                ),
                indent=2,
            )
        )
        return
    if args.action == "jobs":
        print(json.dumps(store.jobs(owner), indent=2))
        return
    if args.action == "cancel":
        if not store.cancel(owner, args.job):
            raise ValueError("Job is unavailable or no longer active")
        print("Cancellation requested; the render monitor will stop its active child process")
        return
    if args.action == "profile":
        from .creative import train_profile

        print(
            json.dumps(
                train_profile(
                    settings,
                    [Path(p).resolve() for p in args.images],
                    Path(args.output).resolve(),
                    args.notes,
                ),
                indent=2,
            )
        )
        return
    if args.action == "prepare":
        from .production import prepare

        print(
            str(
                await prepare(
                    settings,
                    store,
                    owner,
                    Path(args.request).resolve(),
                    Path(args.output).resolve(),
                )
            )
        )
        return
    if args.action == "revise":
        from .production import revise

        print(
            str(
                revise(
                    Path(args.file).resolve(),
                    Path(args.changes).resolve(),
                    Path(args.output).resolve(),
                )
            )
        )
        return
    if args.action == "help":
        from .director import help_answer

        print("AI production assistant: " + help_answer(settings, args.question))
        return
    if args.action == "restore":
        from .package import restore

        print(
            restore(
                settings,
                store,
                owner,
                Path(args.folder).resolve(),
                Path(args.output).resolve(),
            )
        )
        return
    if args.action == "blender":
        from .integrations import blender

        result = await blender(
            settings,
            Path(args.output).resolve(),
            args.labels,
            args.seconds,
            args.transparent,
        )
        print(str(result))
        return
    if args.action == "new":
        text = Path(args.script).read_text()
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        project = Project.model_validate(
            {
                "title": args.title,
                "ratio": args.ratio,
                "style": args.style,
                "shots": [
                    {
                        "id": f"shot-{i + 1:02}",
                        "title": paragraph.split(".")[0][:100],
                        "narration": paragraph,
                        "duration": 1,
                    }
                    for i, paragraph in enumerate(paragraphs)
                ],
            }
        )
        output = Path(args.output)
        with output.open("x") as handle:
            handle.write(project.model_dump_json(indent=2))
        print(str(output))
        return
    if args.action == "analyze":
        from .reference import analyze

        print(
            json.dumps(
                await analyze(settings, Path(args.file).resolve(), Path(args.output).resolve()),
                indent=2,
            )
        )
        return
    if args.action == "direct":
        from .director import plan

        project = await plan(settings, Path(args.brief).read_text(), args.ratio, args.style)
        Path(args.output).write_text(project.model_dump_json(indent=2))
        print(args.output)
        return
    project = Project.model_validate_json(Path(args.file).read_text())
    if args.action == "plan":
        print(
            json.dumps(
                {
                    "title": project.title,
                    "ratio": project.ratio,
                    "shots": len(project.shots),
                    "planned_seconds": sum(s.duration for s in project.shots),
                    "narration_words": sum(len(s.narration.split()) for s in project.shots),
                    "actual_duration": "Determined by generated or recorded narration; no speech acceleration to force a duration",
                    "storyboard": [
                        {
                            "id": s.id,
                            "title": s.title,
                            "layout": s.layout,
                            "proof": s.proof,
                        }
                        for s in project.shots
                    ],
                },
                indent=2,
            )
        )
        return
    if args.action in ("style-test", "animation-test"):
        from .preview import preview

        print(
            str(
                await preview(
                    settings,
                    store,
                    owner,
                    project,
                    Path(args.output).resolve(),
                    stills=args.action == "style-test",
                )
            )
        )
        return
    if args.action == "build":
        with render_lock(settings):
            await build(settings, store, owner, project, args.resume)


async def build(settings, store, owner, project, resume):
    saved = store.save(owner, project.model_dump())
    job = store.enqueue(owner, saved, uuid.uuid4().hex)
    print("Production job: " + job["id"], flush=True)
    task = asyncio.create_task(render(settings, store, job, resume))

    async def monitor():
        while not task.done():
            await asyncio.sleep(settings.config["server"]["idle_poll_seconds"])
            if store.job(owner, job["id"])["state"] == "cancelled":
                task.cancel()
                return

    watcher = asyncio.create_task(monitor())
    try:
        result = await asyncio.wait_for(task, settings.config["render"]["job_timeout_seconds"])
        store.update_job(job["id"], "complete", 1, "Verified export")
    except asyncio.CancelledError:
        store.cancel(owner, job["id"])
        raise
    except BaseException:
        store.update_job(job["id"], "failed", 0, "Inspect preserved run diagnostics")
        raise
    finally:
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
    latest = settings.contained("latest-export.json")
    temp = latest.with_suffix(".tmp")
    temp.write_text(
        json.dumps(
            {
                "job": job["id"],
                "folder": str(settings.contained("renders", job["id"])),
                "title": project.title,
            },
            indent=2,
        )
    )
    temp.replace(latest)
    print(
        json.dumps(
            {
                "folder": str(settings.contained("renders", job["id"])),
                "verification": result,
            },
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ["doctor", "menu", "jobs"]:
        sub.add_parser(name)
    p = sub.add_parser("cancel")
    p.add_argument("job")
    for name in ["plan", "build", "asset"]:
        p = sub.add_parser(name)
        p.add_argument("file")
        if name == "build":
            p.add_argument("--resume")
    for name in ["style-test", "analyze", "animation-test"]:
        p = sub.add_parser(name)
        p.add_argument("file")
        p.add_argument("output")
    p = sub.add_parser("matte")
    p.add_argument("file")
    p.add_argument("output")
    p.add_argument("--start", type=float, default=0)
    p.add_argument("--seconds", type=float, required=True)
    p = sub.add_parser("direct")
    p.add_argument("brief")
    p.add_argument("output")
    p.add_argument("--ratio", default="landscape")
    p.add_argument("--style", default="technical")
    p = sub.add_parser("profile")
    p.add_argument("output")
    p.add_argument("images", nargs="+")
    p.add_argument("--notes", default="")
    p = sub.add_parser("prepare")
    p.add_argument("request")
    p.add_argument("output")
    p = sub.add_parser("revise")
    p.add_argument("file")
    p.add_argument("changes")
    p.add_argument("output")
    p = sub.add_parser("help")
    p.add_argument("question")
    p = sub.add_parser("restore")
    p.add_argument("folder")
    p.add_argument("output")
    p = sub.add_parser("new")
    p.add_argument("script")
    p.add_argument("output")
    p.add_argument("--title", required=True)
    p.add_argument("--ratio", default="landscape")
    p.add_argument("--style", default="technical")
    p = sub.add_parser("blender")
    p.add_argument("output")
    p.add_argument("--labels", nargs="+", required=True)
    p.add_argument("--seconds", type=float, default=4)
    p.add_argument("--transparent", action="store_true")
    try:
        asyncio.run(execute(parser.parse_args()))
    except (KeyboardInterrupt, asyncio.CancelledError):
        parser.exit(
            130,
            "Render cancelled; partial files and the previous verified export are preserved\n",
        )
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()

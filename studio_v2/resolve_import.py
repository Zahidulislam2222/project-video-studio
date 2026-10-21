"""Run with Resolve's bundled Python; imports into a new Studio-owned project."""

import json
import sys
from pathlib import Path

import DaVinciResolveScript


def main(folder):
    resolve = DaVinciResolveScript.scriptapp("Resolve")
    if resolve is None:
        raise RuntimeError("Open Resolve and enable local scripting if your edition supports it")
    manager = resolve.GetProjectManager()
    previous = manager.GetCurrentProject()
    if previous:
        manager.SaveProject()
    name = "Video Studio - " + folder.name
    project = manager.CreateProject(name)
    if not project:
        raise RuntimeError(
            "A project with this name already exists; preserve it and choose a new export"
        )
    pool = project.GetMediaPool()
    timeline = pool.ImportTimelineFromFile(str(folder / "Timeline.xml"))
    if not timeline:
        raise RuntimeError("Resolve could not import the editing timeline")
    project.SetCurrentTimeline(timeline)
    manager.SaveProject()
    result = {
        "product": resolve.GetProductName(),
        "version": resolve.GetVersionString(),
        "project": name,
        "timeline": timeline.GetName(),
        "video_tracks": timeline.GetTrackCount("video"),
        "audio_tracks": timeline.GetTrackCount("audio"),
    }
    (folder / "ResolveImport.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())

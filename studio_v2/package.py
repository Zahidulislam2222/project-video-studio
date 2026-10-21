"""Restore a portable editing package without trusting its paths or skipping hashes."""

import json

from .models import Project
from .render import digest


def restore(settings, store, owner, folder, output):
    from .__main__ import import_asset

    if output.exists():
        raise ValueError("Choose a new restored project file")
    project = Project.model_validate_json((folder / "project.json").read_text())
    records = json.loads((folder / "SourceInputs.json").read_text())
    inputs = (folder / "Inputs").resolve()
    if not inputs.is_relative_to(folder.resolve()) or not inputs.is_dir():
        raise ValueError("Editing-package inputs must stay inside the selected package")
    derived_ids = {
        ident for shot in project.shots for layer in shot.layers if layer.matting
        for ident in (layer.asset, layer.mask)
    }
    mapping = {}
    for record in records:
        source = (folder / "Inputs" / (record["id"] + record["extension"])).resolve()
        if (
            not source.is_relative_to(inputs)
            or not source.is_file()
            or digest(source) != record["sha256"]
        ):
            raise ValueError("Editing-package source integrity check failed")
        mapping[record["id"]] = import_asset(settings, store, owner, source, derived=record["id"] in derived_ids)
    body = project.model_dump()
    for shot in body["shots"]:
        if shot["audio"]:
            shot["audio"] = mapping[shot["audio"]]
        for layer in shot["layers"]:
            layer["asset"] = mapping[layer["asset"]]
            if layer["matting"]:
                layer["matting"]["asset"] = mapping[layer["matting"]["asset"]]
            if layer["mask"]:
                layer["mask"] = mapping[layer["mask"]]
    with output.open("x") as handle:
        handle.write(Project.model_validate(body).model_dump_json(indent=2))
    return output

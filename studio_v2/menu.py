"""Local guided workflow; no hosted service or publication actions."""

import argparse
import uuid
from pathlib import Path
from typing import Any


def local_path(text):
    text = text.strip().strip('"')
    if len(text) > 2 and text[1] == ":" and text[0].isalpha():
        text = "/mnt/" + text[0].lower() + text[2:].replace("\\", "/")
    return Path(text).expanduser().resolve()


async def menu(settings):
    from .__main__ import execute

    print("\nProject Video Studio — local production workspace")
    print("Your previous films remain separate. No music or paid inference is added.")
    while True:
        print(
            "\n1  Script → new project\n2  AI storyboard from a brief\n3  Reference video breakdown\n4  Three style frames\n5  Animation test\n6  Build video\n7  Make a Blender 3D shot\n8  Import footage/image/audio\n9  Tool check\n10 Create a video from your inputs\n11 Train a reference palette\n12 Production help\n0  Exit"
        )
        choice = input("Choose: ").strip()
        if choice == "0":
            return
        try:
            if choice == "1":
                script = local_path(
                    input("Script text file (blank lines separate shots): ")
                )
                title = input("Film title: ").strip()
                ratio = (
                    input("landscape / portrait / square [landscape]: ").strip()
                    or "landscape"
                )
                style = (
                    input(
                        "technical / editorial / pastel / minimal / pixel / paper / cinematic [technical]: "
                    ).strip()
                    or "technical"
                )
                output = settings.contained("projects", uuid.uuid4().hex + ".json")
                output.parent.mkdir(exist_ok=True)
                await execute(
                    argparse.Namespace(
                        action="new",
                        script=str(script),
                        output=str(output),
                        title=title,
                        ratio=ratio,
                        style=style,
                    )
                )
                print(
                    "Edit this project's narration, labels and layers before production."
                )
            elif choice == "2":
                brief = local_path(input("Brief text file: "))
                output = settings.contained("projects", uuid.uuid4().hex + ".json")
                output.parent.mkdir(exist_ok=True)
                await execute(
                    argparse.Namespace(
                        action="direct",
                        brief=str(brief),
                        output=str(output),
                        ratio=input("Ratio [landscape]: ").strip() or "landscape",
                        style=input("Style [technical]: ").strip() or "technical",
                    )
                )
            elif choice in ("3", "4", "5", "6"):
                source = local_path(
                    input(
                        "Reference video: " if choice == "3" else "Project JSON file: "
                    )
                )
                action = {
                    "3": "analyze",
                    "4": "style-test",
                    "5": "animation-test",
                    "6": "build",
                }[choice]
                output = settings.contained("previews", uuid.uuid4().hex)
                await execute(
                    argparse.Namespace(
                        action=action, file=str(source), output=str(output), resume=None
                    )
                )
            elif choice == "7":
                labels = [
                    label.strip()
                    for label in input("Component labels separated by commas: ").split(
                        ","
                    )
                ]
                output = settings.contained("scenes", uuid.uuid4().hex)
                await execute(
                    argparse.Namespace(
                        action="blender",
                        output=str(output),
                        labels=labels,
                        seconds=float(input("Duration seconds [4]: ") or "4"),
                        transparent=False,
                    )
                )
            elif choice == "8":
                await execute(
                    argparse.Namespace(
                        action="asset",
                        file=str(local_path(input("Approved source file: "))),
                    )
                )
                print("Use this asset ID in a project's layers or audio field.")
            elif choice == "9":
                await execute(argparse.Namespace(action="doctor"))
            elif choice == "10":
                import json

                from .models import Project
                from .preview import preview
                from .production import prepare
                from .store import Store

                title = input("Film title: ").strip()
                kind = (
                    input("Start with script / recording / brief [script]: ").strip()
                    or "script"
                )
                request: dict[str, Any] = {
                    "title": title,
                    "ratio": input(
                        "landscape / portrait / square [landscape]: "
                    ).strip()
                    or "landscape",
                    "style": input("Visual style [technical]: ").strip() or "technical",
                }
                if kind == "recording":
                    request["recording"] = str(local_path(input("Recording file: ")))
                    captions = input(
                        "Corrected SRT file [leave blank for local AI transcription]: "
                    ).strip()
                    if captions:
                        request["captions_file"] = str(local_path(captions))
                    request["language"] = (
                        input("Spoken language code [en]: ").strip() or "en"
                    )
                elif kind == "brief":
                    request["brief"] = local_path(
                        input("Brief text file: ")
                    ).read_text()
                    request["use_ai"] = True
                else:
                    request["script_file"] = str(
                        local_path(input("Script text file: "))
                    )
                footage = input(
                    "Optional footage/image files separated by | : "
                ).strip()
                if footage:
                    request["footage"] = [
                        str(local_path(p)) for p in footage.split("|")
                    ]
                companion = input("Optional second view for split layout: ").strip()
                if companion:
                    request["companion"] = str(local_path(companion))
                if footage or companion or kind == "recording":
                    request["media_approved"] = (
                        input("I checked media rights and private content [yes/no]: ")
                        .strip()
                        .casefold()
                        == "yes"
                    )
                if companion or kind == "recording":
                    request["matte_presenter"] = (
                        input("Automatically cut out the human presenter [yes/no]: ")
                        .strip()
                        .casefold()
                        == "yes"
                    )
                profile = input("Optional approved StyleProfile.json: ").strip()
                if profile:
                    request["profile"] = str(local_path(profile))
                folder = settings.contained("productions", uuid.uuid4().hex)
                folder.parent.mkdir(exist_ok=True)
                request_file = folder.parent / (folder.name + "-request.json")
                request_file.write_text(json.dumps(request, indent=2))
                store = Store(settings)
                project_file = await prepare(
                    settings, store, "local", request_file, folder
                )
                project = Project.model_validate_json(project_file.read_text())
                await preview(
                    settings,
                    store,
                    "local",
                    project,
                    folder / "style-check",
                    stills=True,
                )
                await preview(
                    settings, store, "local", project, folder / "animation-check"
                )
                print("Draft and composed previews: " + str(folder))
                if (
                    input("Build the full video now [yes/no]: ").strip().casefold()
                    == "yes"
                ):
                    await execute(
                        argparse.Namespace(
                            action="build", file=str(project_file), resume=None
                        )
                    )
            elif choice == "11":
                images = [
                    str(local_path(p))
                    for p in input(
                        "Consistent reference images separated by | : "
                    ).split("|")
                ]
                await execute(
                    argparse.Namespace(
                        action="profile",
                        images=images,
                        output=str(settings.contained("profiles", uuid.uuid4().hex)),
                        notes=input(
                            "Describe typography, texture and motion direction: "
                        ),
                    )
                )
            elif choice == "12":
                await execute(
                    argparse.Namespace(
                        action="help", question=input("Production question: ")
                    )
                )
            else:
                print("Choose one of the listed actions.")
        except (ValueError, RuntimeError, OSError) as exc:
            print("Stopped: " + str(exc))
            print(
                "Previous successful films are preserved. Correct the input and retry."
            )

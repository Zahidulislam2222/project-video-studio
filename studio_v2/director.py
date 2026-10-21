"""Optional local AI director with validated output, no media access or action tools."""

import ipaddress
import json
import os
import uuid
from urllib.parse import urlsplit

import httpx

from .models import Project
from .process import run


async def plan(settings, brief, ratio, style):
    cfg = settings.config["ai"]
    if len(brief) > cfg["input_characters"]:
        raise ValueError("Brief exceeds director input limit")
    endpoint = os.environ.get("STUDIO_AI_URL", "")
    model = os.environ.get("STUDIO_AI_MODEL", "")
    parsed = urlsplit(endpoint)
    if (
        not model
        or parsed.path not in ("", "/")
        or parsed.scheme != "http"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Configure a local Ollama URL and installed model; no paid fallback is used"
        )
    try:
        local = ipaddress.ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        local = parsed.hostname == "localhost"
    if not local:
        raise ValueError("AI endpoint must be local loopback")
    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "format": Project.model_json_schema(),
        "options": {"num_predict": cfg["output_tokens"], "temperature": cfg["temperature"]},
        "messages": [
            {"role": "system", "content": cfg["system_prompt"]},
            {"role": "user", "content": brief},
        ],
    }
    curl = os.environ.get("STUDIO_AI_CURL")
    if curl:
        folder = settings.contained("director", uuid.uuid4().hex)
        raw = await run(
            [
                curl,
                "--fail",
                "--silent",
                "--show-error",
                "--max-time",
                str(cfg["timeout_seconds"]),
                "-H",
                "Content-Type: application/json",
                "--data-binary",
                "@-",
                endpoint.rstrip("/") + "/api/chat",
            ],
            folder,
            cfg["timeout_seconds"],
            input_bytes=json.dumps(payload).encode(),
        )
        response_body = json.loads(raw)
    else:
        async with httpx.AsyncClient(timeout=cfg["timeout_seconds"], trust_env=False) as client:
            response = await client.post(endpoint.rstrip("/") + "/api/chat", json=payload)
            response.raise_for_status()
            response_body = response.json()
    body = json.loads(response_body["message"]["content"])
    project = Project.model_validate({**body, "brief": brief, "ratio": ratio, "style": style})
    if len(project.shots) > cfg["maximum_shots"]:
        raise ValueError("Director returned too many shots")
    if any(s.layers or s.audio or s.proof for s in project.shots):
        raise ValueError("Director cannot invent source assets or verified proof")
    return project


def help_answer(settings, question):
    question = question.casefold()
    results = [
        item["answer"]
        for item in settings.config["knowledge"]
        if any(t in question for t in item["terms"])
    ]
    return (
        "\n\n".join(results[:3])
        if results
        else "I can explain footage, layouts, captions, voices and rendering. For a creative storyboard, use the AI director with an operator-configured local model. I cannot verify claims absent from your brief or publish your work."
    )

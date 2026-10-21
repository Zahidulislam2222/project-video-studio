"""Non-musical effects and voice-ducked ambience, with separate editing stems."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import Film, Settings
from media_tools import ffmpeg
from narration import write_wav


def mix_sound(settings: Settings, film: Film, output: Path, timeline: list[dict[str, Any]]) -> str:
    if not film.sound_enabled:
        return "Voiceover.wav"
    import numpy as np

    s, r = settings.data["sound"], settings.data["render"]
    rate = r["audio_rate"]
    duration = sum(t["frames"] for t in timeline) / r["fps"]
    samples = round(duration * rate)
    bed = np.zeros(samples, dtype=np.float64)
    rng = np.random.default_rng(s["noise_seed"])
    events = []
    for scene, timing in zip(film.scenes, timeline, strict=True):
        effect = scene.effect
        if effect == "auto":
            effect = "whoosh" if scene.role in ("intro", "outro") else "click"
        if effect == "none":
            continue
        length = min(samples, round(s[effect + "_seconds"] * rate))
        noise = rng.uniform(-1, 1, length)
        smooth = int(s["noise_smoothing"])
        noise = np.convolve(noise, np.ones(smooth) / smooth, mode="same")[:length]
        envelope = np.sin(np.linspace(0, np.pi, length)) ** (2 if effect == "whoosh" else 8)
        effect_pcm = noise * envelope
        peak = np.max(np.abs(effect_pcm))
        if peak:
            effect_pcm *= 10 ** (s["effects_gain_db"] / 20) / peak
        start = round(timing["start"] * rate)
        stop = min(samples, start + length)
        bed[start:stop] += effect_pcm[: stop - start]
        events.append({"scene": scene.ident, "effect": effect, "start": timing["start"]})
    pcm = (np.clip(bed, -1, 1) * 32767).astype("<i2").tobytes()
    write_wav(output / "effects-raw.wav", pcm, rate)
    args: list[str | Path] = ["-i", "effects-raw.wav"]
    filters = "[0:a]aformat=channel_layouts=stereo[effects]"
    if film.ambience:
        args += ["-stream_loop", "-1", "-i", film.ambience]
        filters += (
            f";[1:a]atrim=duration={duration},asetpts=PTS-STARTPTS,"
            f"aformat=channel_layouts=stereo,volume={s['ambience_gain_db']}dB[ambience]"
            ";[effects][ambience]amix=inputs=2:normalize=0:duration=first[bed]"
        )
    else:
        filters += ";[effects]anull[bed]"
    fade = min(s["fade_seconds"], duration / 2)
    filters += f";[bed]afade=t=in:d={fade},afade=t=out:st={duration - fade}:d={fade}[out]"
    ffmpeg(
        settings,
        [
            *args,
            "-filter_complex",
            filters,
            "-map",
            "[out]",
            "-ar",
            str(rate),
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            "SoundEffects.wav",
        ],
        output,
    )
    filters = (
        "[0:a]asplit=2[voice][key];"
        f"[1:a][key]sidechaincompress=threshold={s['duck_threshold']}:"
        f"ratio={s['duck_ratio']}:attack={s['duck_attack_ms']}:"
        f"release={s['duck_release_ms']}[ducked];"
        "[voice][ducked]amix=inputs=2:normalize=0:duration=first,"
        f"loudnorm=I={r['loudness']}:TP={r['true_peak']}:LRA={r['loudness_range']}[out]"
    )
    ffmpeg(
        settings,
        [
            "-i",
            "Voiceover.wav",
            "-i",
            "SoundEffects.wav",
            "-filter_complex",
            filters,
            "-map",
            "[out]",
            "-ar",
            str(rate),
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            "Soundtrack.wav",
        ],
        output,
    )
    (output / "SoundDesign.json").write_text(
        json.dumps(
            {
                "music": False,
                "effects": events,
                "ambience": bool(film.ambience),
                "ducking": True,
                "seconds": duration,
                "settings": s,
                "limits": "Listen to the mix and confirm external ambience contains no music before publication.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return "Soundtrack.wav"

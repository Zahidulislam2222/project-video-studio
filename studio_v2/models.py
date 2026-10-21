"""Versioned, closed editing contracts. No executable expressions from clients."""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")]
Color = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Theme(Contract):
    background: Color
    foreground: Color
    accent: Color
    panel: Color


class Beat(Contract):
    start: float = Field(ge=0)
    title: str = Field(min_length=1, max_length=110)
    labels: list[Annotated[str, Field(max_length=60)]] = Field(
        default_factory=list, max_length=4
    )


class MattingOrigin(Contract):
    asset: Identifier
    start: float = Field(ge=0)
    seconds: float = Field(gt=0)
    model_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Layer(Contract):
    asset: Identifier
    x: float = Field(default=0.04, ge=0, le=1)
    y: float = Field(default=0.23, ge=0, le=1)
    width: float = Field(default=0.92, gt=0, le=1)
    height: float = Field(default=0.62, gt=0, le=1)
    trim: float = Field(default=0, ge=0)
    fit: Literal["contain", "cover"] = "contain"
    matting: MattingOrigin | None = None
    mask: Identifier | None = None
    mask_trim: float | None = Field(default=None, ge=0)
    opacity: float = Field(default=1, gt=0, le=1)
    motion: Literal["none", "push-in", "pull-out"] = "none"

    @model_validator(mode="after")
    def inside_frame(self):
        if self.x + self.width > 1.001 or self.y + self.height > 1.001:
            raise ValueError("Layer must fit inside the frame")
        if self.matting and not self.mask:
            raise ValueError(
                "Derived human footage requires its synchronized alpha mask"
            )
        if self.mask and self.motion != "none":
            raise ValueError(
                "Use pre-authored camera moves for masked layers to preserve exact subject alignment"
            )
        return self


class Callout(Contract):
    text: str = Field(min_length=1, max_length=100)
    x: float = Field(ge=0.04, le=0.8)
    y: float = Field(ge=0.05, le=0.85)
    start: float = Field(default=0, ge=0)
    end: float = Field(gt=0)
    depth: int = Field(default=4, ge=0, le=4)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("Callout end must follow start")
        return self


class Shot(Contract):
    id: Identifier
    title: str = Field(min_length=1, max_length=110)
    narration: str = Field(default="", max_length=6000)
    spoken_text: str = Field(default="", max_length=6000)
    duration: float = Field(default=8, ge=1, le=600)
    timing: Literal["narration", "fixed"] = "narration"
    layout: Literal[
        "full", "side-by-side", "stacked", "picture-in-picture", "diagram"
    ] = "full"
    layers: list[Layer] = Field(default_factory=list, max_length=4)
    labels: list[Annotated[str, Field(max_length=60)]] = Field(
        default_factory=list, max_length=4
    )
    callouts: list[Callout] = Field(default_factory=list, max_length=12)
    transition: Literal["cut", "fade", "slide"] = "fade"
    proof: bool = False
    audio: Identifier | None = None
    audio_trim: float = Field(default=0, ge=0)
    audio_seconds: float | None = Field(default=None, gt=0, le=600)
    source_note: str = Field(default="", max_length=300)
    caption_cues: list["Caption"] = Field(default_factory=list, max_length=300)
    beats: list[Beat] = Field(default_factory=list, max_length=60)
    automatic_beats: bool = True

    @model_validator(mode="after")
    def proof_requires_source(self):
        if any(b.start <= a.start for a, b in zip(self.beats, self.beats[1:])):
            raise ValueError("Visual beat times must increase")
        from .graphics import layout_boxes

        boxes = layout_boxes(self.layout, "")
        for i, layer in enumerate(self.layers):
            if not ({"x", "y", "width", "height"} & layer.model_fields_set):
                if i >= len(boxes):
                    raise ValueError(
                        "This layout requires explicit rectangles for extra layers"
                    )
                layer.x, layer.y, layer.width, layer.height = boxes[i]
        if self.proof and (not self.layers or not self.source_note.strip()):
            raise ValueError("Proof needs genuine footage and a source note")
        if self.proof and any(layer.matting for layer in self.layers):
            raise ValueError(
                "Human cutouts are derived illustrations, not unaltered proof"
            )
        if self.proof and self.layout == "diagram":
            raise ValueError("An illustration cannot stand in for proof")
        if self.audio and self.narration.strip():
            raise ValueError("Use recorded audio or generated narration per shot")
        return self


class Caption(Contract):
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    text: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("Caption end must follow start")
        return self


class Project(Contract):
    version: Literal[2] = 2
    title: str = Field(min_length=1, max_length=140)
    brief: str = Field(default="", max_length=12000)
    ratio: Literal["landscape", "portrait", "square"] = "landscape"
    style: Literal[
        "technical", "editorial", "pastel", "minimal", "pixel", "paper", "cinematic"
    ] = "technical"
    voice: Literal["am_michael", "am_fenrir", "am_puck", "bm_george"] = "am_michael"
    delivery: Literal["confident", "warm", "energetic", "thoughtful"] = "confident"
    captions: bool = True
    effects: bool = False
    theme: Theme | None = None
    shots: list[Shot] = Field(min_length=1, max_length=160)

    @model_validator(mode="after")
    def unique_shots(self):
        if len({s.id for s in self.shots}) != len(self.shots):
            raise ValueError("Shot identifiers must be unique")
        if sum(s.duration for s in self.shots) > 7200:
            raise ValueError("Project exceeds the two-hour editing envelope")
        for shot in self.shots:
            for text in [
                shot.title,
                shot.narration,
                *shot.labels,
                *(c.text for c in shot.callouts),
            ]:
                if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
                    raise ValueError("Control characters are not allowed")
        return self

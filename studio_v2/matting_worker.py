"""Isolated CPU inference worker. No downloads or media tools run in this process."""

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

from .matting import model_path
from .settings import Settings


def infer(folder):
    settings = Settings.load()
    cfg = settings.config["matting"]
    model = model_path(settings)
    request = json.loads((folder / "MatteRequest.json").read_text())
    if Path(request["model"]).resolve() != model:
        raise ValueError("Matting worker model differs from configured model")
    count = request["frames"]
    if not isinstance(count, int) or not 1 <= count <= math.ceil(
        cfg["maximum_seconds"] * settings.config["render"]["fps"]
    ):
        raise ValueError("Matting worker frame budget exceeded")
    options = ort.SessionOptions()
    options.intra_op_num_threads = cfg["threads"]
    options.inter_op_num_threads = 1
    ort.disable_telemetry_events()
    session = ort.InferenceSession(
        str(model), sess_options=options, providers=["CPUExecutionProvider"]
    )
    recurrent = [np.zeros((1, 1, 1, 1), dtype=np.float32) for _ in range(4)]
    frames = folder / "frames"
    started = time.monotonic()
    samples, previous, deltas = [], None, []
    shape = None
    for index in range(1, count + 1):
        with Image.open(frames / f"src-{index:06}.png") as original:
            if max(original.size) > cfg["maximum_edge"]:
                raise ValueError("Decoded presenter frame exceeds inference dimensions")
            rgb = np.asarray(original.convert("RGB"), dtype=np.float32) / 255
        if shape is not None and rgb.shape != shape:
            raise ValueError("Presenter resolution changed within the shot")
        shape = rgb.shape
        ratio = np.asarray([min(1, cfg["internal_edge"] / max(shape[:2]))], dtype=np.float32)
        foreground, alpha, *recurrent = session.run(
            None,
            {
                "src": rgb.transpose(2, 0, 1)[None],
                **{f"r{i + 1}i": value for i, value in enumerate(recurrent)},
                "downsample_ratio": ratio,
            },
        )
        if alpha.shape != (1, 1, *rgb.shape[:2]) or foreground.shape != (1, 3, *rgb.shape[:2]):
            raise ValueError("Matting model output dimensions differ from input frame")
        if not np.isfinite(alpha).all() or not np.isfinite(foreground).all():
            raise ValueError("Matting model produced non-finite output")
        mask = np.rint(np.clip(alpha[0, 0], 0, 1) * 255).astype(np.uint8)
        picture = np.rint(np.clip(foreground[0].transpose(1, 2, 0), 0, 1) * 255).astype(np.uint8)
        Image.fromarray(picture).save(frames / f"foreground-{index:06}.png")
        Image.fromarray(mask).save(frames / f"mask-{index:06}.png")
        if index in (1, (count + 1) // 2, count):
            samples.append({"frame": index, "foreground_fraction": float((mask > 127).mean())})
            Image.fromarray(mask).save(folder / f"MaskPreview-{index:06}.png")
        if previous is not None:
            deltas.append(float(np.abs(mask.astype(float) - previous.astype(float)).mean()) / 255)
        previous = mask
    if shape is None:
        raise ValueError("No presenter frames were processed")
    result = {
        "dimensions": [shape[1], shape[0]],
        "model_sha256": cfg["model_sha256"],
        "model_source": cfg["model_source"],
        "model_license": cfg["model_license"],
        "provider": "CPUExecutionProvider",
        "recurrent_states": "Four outputs recycled sequentially; reset at each independent shot",
        "inference_seconds": round(time.monotonic() - started, 3),
        "alpha_samples": samples,
        "mean_interframe_alpha_difference": sum(deltas) / len(deltas) if deltas else 0,
        "quality": "Measured alpha coverage and temporal differences; not a semantic quality score",
    }
    (folder / "MatteInference.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    infer(Path(sys.argv[1]).resolve())

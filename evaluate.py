"""Replay labeled videos through external liveness checkpoints and report aggregate metrics."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path

import cv2
import numpy as np
from ai_edge_litert.interpreter import Interpreter

CLASSES = {"fake": "Video fake", "real": "Video real"}
EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


class LivenessModel:
    def __init__(self, path: Path):
        self.runtime = Interpreter(model_path=str(path), num_threads=2)
        self.runtime.allocate_tensors()
        (self.input,) = self.runtime.get_input_details()
        (self.output,) = self.runtime.get_output_details()
        if (
            tuple(self.input["shape"]) != (1, 32, 32, 3)
            or tuple(self.output["shape"]) != (1, 2)
            or self.input["dtype"] != np.float32
            or self.output["dtype"] != np.float32
        ):
            raise ValueError("Expected float32 [1,32,32,3] input and [1,2] output.")

    def real_probability(self, batch: np.ndarray) -> float:
        self.runtime.set_tensor(self.input["index"], batch)
        self.runtime.invoke()
        scores = self.runtime.get_tensor(self.output["index"])[0]
        if not np.isfinite(scores).all() or np.any(scores < 0) or not np.isclose(scores.sum(), 1, atol=0.01):
            raise ValueError("Model output must be probabilities in [fake, real] order.")
        return float(scores[1])


def find_single_face(detector, image: np.ndarray) -> tuple[str, np.ndarray | None]:
    height, width = image.shape[:2]
    scale = min(1.0, 640 / max(height, width))
    small_width = max(1, round(width * scale))
    small_height = max(1, round(height * scale))
    resized = cv2.resize(image, (small_width, small_height), interpolation=cv2.INTER_AREA)
    detector.setInputSize((small_width, small_height))
    _, faces = detector.detect(resized)
    if faces is None or len(faces) == 0:
        return "no_face", None
    if len(faces) != 1:
        return "multiple_faces", None
    x, y, box_width, box_height = faces[0, :4]
    left = max(0, math.floor(x * width / small_width))
    top = max(0, math.floor(y * height / small_height))
    right = min(width, math.ceil((x + box_width) * width / small_width))
    bottom = min(height, math.ceil((y + box_height) * height / small_height))
    if right <= left or bottom <= top:
        return "invalid_crop", None
    crop = cv2.resize(image[top:bottom, left:right], (32, 32), interpolation=cv2.INTER_LINEAR)
    return "scored", crop[None].astype(np.float32) / 255.0


def metrics(rows: Counter) -> dict:
    # Rows are actual classes, columns are predicted classes.
    matrix = [[rows[actual, prediction] for prediction in CLASSES] for actual in CLASSES]
    fake, real = map(sum, matrix)
    apcer = matrix[0][1] / fake if fake else None
    bpcer = matrix[1][0] / real if real else None
    return {
        "confusion_matrix_fake_real": matrix,
        "scored": fake + real,
        "pooled_apcer": apcer,
        "bpcer": bpcer,
        "pooled_acer": (apcer + bpcer) / 2 if apcer is not None and bpcer is not None else None,
    }


def replay_video(path, detector, models, sample_fps, max_seconds):
    statuses = Counter()
    probabilities = {name: [] for name in models}
    capture = cv2.VideoCapture(str(path))
    try:
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not capture.isOpened() or not math.isfinite(fps) or fps <= 0:
            return "unreadable", statuses, probabilities
        stride = max(1, round(fps / sample_fps))
        for index in range(math.ceil(fps * max_seconds)):
            if not capture.grab():
                break
            if index % stride:
                continue
            ok, frame = capture.retrieve()
            if not ok:
                statuses["decode_failure"] += 1
                continue
            status, batch = find_single_face(detector, frame)
            statuses[status] += 1
            if batch is not None:
                for name, model in models.items():
                    probabilities[name].append(model.real_probability(batch))
    finally:
        capture.release()
    if not statuses or sum(statuses.values()) == statuses["decode_failure"]:
        return "unreadable", statuses, probabilities
    return ("scored" if statuses["scored"] else "no_eligible_face"), statuses, probabilities


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, type=Path, help='Folder with "Video real" and "Video fake".')
    parser.add_argument("--detector", required=True, type=Path, help="YuNet ONNX path.")
    parser.add_argument("--model", required=True, action="append", metavar="NAME=PATH",
                        help="External TFLite file, repeat to compare checkpoints.")
    parser.add_argument("--output", type=Path, default=Path("reports/replay.json"))
    parser.add_argument("--sample-fps", type=float, default=2)
    parser.add_argument("--max-seconds", type=float, default=12)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    if not all(math.isfinite(x) and x > 0 for x in (args.sample_fps, args.max_seconds)):
        parser.error("Sampling rate and clip duration must be positive and finite.")
    if not 0 <= args.threshold <= 1:
        parser.error("Threshold must be between zero and one.")
    if args.output.suffix.lower() != ".json":
        parser.error("Output must be a .json file.")

    models = {}
    for spec in args.model:
        name, sep, path = spec.partition("=")
        if not sep or not name or not path or name in models:
            parser.error("Use unique NAME=PATH model arguments.")
        models[name] = LivenessModel(Path(path))

    files = {}
    for label, directory in CLASSES.items():
        folder = args.data / directory
        files[label] = sorted(path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() in EXTENSIONS)
        if not files[label]:
            parser.error(f"No videos found under {directory!r}.")

    cv2.setNumThreads(2)
    detector = cv2.FaceDetectorYN.create(str(args.detector), "", (320, 320), 0.62, 0.3, 5000)
    frame_statuses = {label: Counter() for label in CLASSES}
    clip_statuses = {label: Counter() for label in CLASSES}
    frame_results = {name: Counter() for name in models}
    clip_results = {name: Counter() for name in models}
    for label, paths in files.items():
        for number, path in enumerate(paths, 1):
            status, frames, probabilities = replay_video(
                path, detector, models, args.sample_fps, args.max_seconds,
            )
            clip_statuses[label][status] += 1
            frame_statuses[label].update(frames)
            for name, scores in probabilities.items():
                if scores:
                    frame_results[name].update(
                        (label, "real" if score > args.threshold else "fake") for score in scores
                    )
                    prediction = "real" if sum(scores) / len(scores) > args.threshold else "fake"
                    clip_results[name][label, prediction] += 1
            print(f"{label}: {number}/{len(paths)} clips processed", flush=True)

    report = {
        "protocol": {
            "scope": "descriptive replay; independence from training not established",
            "sample_fps_target": args.sample_fps,
            "max_seconds_per_clip": args.max_seconds,
            "real_probability_threshold_exclusive": args.threshold,
            "detector_score_threshold": 0.62,
            "clip_decision": "mean P(real) over eligible frames",
        },
        "video_counts": {label: len(paths) for label, paths in files.items()},
        "frame_statuses": frame_statuses,
        "clip_statuses": clip_statuses,
        "models": {
            name: {"frames": metrics(frame_results[name]), "clips": metrics(clip_results[name])}
            for name in models
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

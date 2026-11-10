"""Fixed, descriptive replay of the two supplied folders; never a held-out test.

Run with the project-local ML packages on PYTHONPATH. No source videos or
production weights are changed. Scores use the existing YuNet crop, BGR/255,
32x32 input, argmax, and FastBinaryDecision with an independent history per clip.
Ambiguous multi-face frames are excluded, with coverage reported separately.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline import FaceDetector, FastBinaryDecision, preprocess, quality
from inference_runtime import LiteModel

OUT = ROOT / 'deliverables/data-audit-20261021'
SOURCES = {'fake': 'Fake-20261021T081403Z-1-001/Fake',
           'real': 'Real-20261021T081402Z-1-001/Real'}
HOLDER_CLIPS = {'fake/REC-0001-A.mp4', 'fake/REC-0002-A.mp4', 'fake/REC-0003-A.mp4'}


def detect_target(detector, frame, vid):
    # Visually verified on the supplied clips; matches the existing extractor's
    # holder mask. The detector sees the left 65%, crops retain original pixels.
    if vid in HOLDER_CLIPS:
        masked = frame.copy()
        masked[:, int(frame.shape[1] * .65):] = 0
        return [f for f in detector.detect(masked)
                if f['box'][0] < frame.shape[1] * .62 and f['box'][2] <= frame.shape[1] * .65]
    return detector.detect(frame)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def rates(rows):
    scored = [r for r in rows if r['status'] == 'scored']
    cm = [[sum(r['label'] == a and r['prediction'] == b for r in scored)
           for b in ('fake', 'real')] for a in ('fake', 'real')]
    nf, nr = sum(cm[0]), sum(cm[1])
    ap = cm[0][1] / nf if nf else None
    bp = cm[1][0] / nr if nr else None
    return {'attempts': len(rows), 'scored': len(scored),
            'coverage': len(scored) / len(rows) if rows else 0,
            'status_counts': dict(Counter(r['status'] for r in rows)),
            'confusion_matrix_fake_real': cm,
            'accuracy': (cm[0][0] + cm[1][1]) / len(scored) if scored else None,
            'pooled_APCER': ap, 'BPCER': bp,
            'pooled_ACER': (ap + bp) / 2 if ap is not None and bp is not None else None}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'samples').mkdir(exist_ok=True)
    cv2.setNumThreads(2)
    detector = FaceDetector()
    models = {name: LiteModel(ROOT / path) for name, path in {
        'cam4k': 'web_models/liveness_cam4k.tflite',
        'original': 'web_models/liveness.tflite'}.items()}
    videos, records = [], []
    start = time.monotonic()
    for label, folder in SOURCES.items():
        for path in sorted((ROOT / folder).glob('*.mp4')):
            vid = f'{label}/{path.name}'
            cap = cv2.VideoCapture(str(path))
            cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
            fps = float(cap.get(cv2.CAP_PROP_FPS))
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width, height = int(cap.get(3)), int(cap.get(4))
            v = {'video_id': vid, 'relative_path': path.relative_to(ROOT).as_posix(),
                 'label': label, 'bytes': path.stat().st_size, 'sha256': sha(path),
                 'fps': fps, 'metadata_frames': total,
                 'duration_seconds': total / fps if fps else None,
                 'width': width, 'height': height, 'opened': cap.isOpened()}
            histories = {name: FastBinaryDecision() for name in models}
            selected_step = max(1, round(fps / 2)) if fps > 0 else 30
            decoded, selected = 0, 0
            preview = None
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                index = decoded
                decoded += 1
                if index == min(total // 2, int(fps * 6)):
                    preview = frame.copy()
                if index >= min(total, int(fps * 12)) or index % selected_step:
                    continue
                selected += 1
                faces = detect_target(detector, frame, vid)
                base = {'video_id': vid, 'label': label, 'frame_index': index,
                        'time_seconds': index / fps, 'face_count': len(faces)}
                if len(faces) != 1:
                    for name in models:
                        records.append(dict(base, model=name,
                                            status='no_face' if not faces else 'multiple_faces'))
                        histories[name].tracks.clear()
                    continue
                face = faces[0]
                x, y, r, b = face['box']
                crop = frame[y:b, x:r]
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                q = quality(frame, face)
                base.update(box=list(face['box']), quality=q,
                            gray_mean=float(gray.mean()),
                            saturated_fraction=float((gray > 245).mean()),
                            dark_fraction=float((gray < 20).mean()),
                            laplacian_var=float(cv2.Laplacian(cv2.resize(gray, (128, 128)), cv2.CV_32F).var()))
                for name, model in models.items():
                    probs = model(preprocess(crop)[None])[0]
                    track = histories[name].associate([face['box']])[0]
                    decision, smoothed = histories[name].update(track, probs, index / fps)
                    records.append(dict(base, model=name, status='scored',
                                        prediction=('fake', 'real')[int(decision)],
                                        raw_prediction=('fake', 'real')[int(probs.argmax())],
                                        p_real=float(probs[1]),
                                        smoothed_p_real=float(smoothed[1])))
            cap.release()
            v.update(decoded_frames=decoded, selected_frames=selected,
                     full_decode_matches_metadata=(decoded == total))
            if preview is not None:
                for face in detector.detect(preview):
                    x, y, r, b = face['box']
                    cv2.rectangle(preview, (x, y), (r, b), (0, 200, 255), 2)
                img = Image.fromarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB))
                img.thumbnail((320, 180))
                img.save(OUT / 'samples' / f'{label}_{path.stem}.png')
            videos.append(v)
            print(f'{len(videos):02d}/91 {vid}: {decoded}/{total} frames, {selected} sampled', flush=True)
    for label in SOURCES:
        paths = sorted((OUT / 'samples').glob(f'{label}_*.png'))
        for offset in range(0, len(paths), 24):
            subset = paths[offset:offset + 24]
            sheet = Image.new('RGB', (1280, ((len(subset) + 3) // 4) * 210), '#152034')
            draw = ImageDraw.Draw(sheet)
            font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17)
            for i, p in enumerate(subset):
                x, y = (i % 4) * 320, (i // 4) * 210
                sheet.paste(Image.open(p), (x, y))
                draw.text((x + 5, y + 184), p.stem, fill='white', font=font)
            sheet.save(OUT / f'contact_{label}_{offset // 24 + 1}.jpg', quality=92)
    summaries = {}
    for name in models:
        sub = [r for r in records if r['model'] == name]
        summaries[name] = rates(sub)
        summaries[name]['quality_pass_only'] = rates([r for r in sub if r['status'] == 'scored' and r.get('quality') is None])
        per_video = []
        for v in videos:
            rr = [r for r in sub if r['video_id'] == v['video_id'] and r['status'] == 'scored']
            if rr:
                # Descriptive fixed mean probability; no threshold fitting or checkpoint selection.
                p = float(np.mean([r['p_real'] for r in rr]))
                per_video.append({'video_id': v['video_id'], 'label': v['label'],
                                  'status': 'scored', 'p_real': p,
                                  'prediction': 'real' if p > .5 else 'fake', 'samples': len(rr)})
            else:
                per_video.append({'video_id': v['video_id'], 'label': v['label'], 'status': 'unscored'})
        summaries[name]['video_mean_score'] = rates(per_video)
        summaries[name]['video_results'] = per_video
    duplicates = [ids for h in {v['sha256'] for v in videos}
                  if len(ids := [v['video_id'] for v in videos if v['sha256'] == h]) > 1]
    report = {'date': '2026-10-21', 'scope': 'descriptive replay; possible training overlap; not held-out test',
              'sampling': 'first 12 seconds, 2 FPS, all clips, no threshold fitting',
              'target_policy': 'Visually verified left 65% detector ROI for fake REC-0001/2/3 to exclude the real phone holder; all other frames require exactly one detected face.',
              'decision': 'YuNet confidence 0.62, single-face only, 32x32 BGR /255, FastBinaryDecision defaults',
              'labels': ['fake', 'real'], 'model_hashes': {
                  name: sha(ROOT / ('web_models/liveness_cam4k.tflite' if name == 'cam4k' else 'web_models/liveness.tflite'))
                  for name in models},
              'source_counts': dict(Counter(v['label'] for v in videos)),
              'total_duration_seconds': sum(v['duration_seconds'] or 0 for v in videos),
              'duplicate_groups': duplicates, 'videos': videos, 'metrics': summaries,
              'elapsed_seconds': time.monotonic() - start,
              'training_overlap': 'User confirmed these are the 91 videos used for cam4k training on 2026-10-20; descriptive replay only.',
              'limitations': ['No verified subject, session, camera or attack-medium IDs supplied.',
                              'Folder label is assumed to describe the sole detected face; visually review attack targets.',
                              'Multi-face and no-face samples are excluded and coverage is reported.',
                              'APCER is pooled across unknown attack media, not worst-PAI APCER.',
                              'Video means and frame samples are correlated; no claim of unseen-person generalization.']}
    (OUT / 'audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    (OUT / 'predictions.json').write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')
    fields = sorted({k for v in videos for k in v})
    with (OUT / 'video_manifest.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(videos)
    print(json.dumps({name: {k: v for k, v in m.items() if k != 'video_results'}
                      for name, m in summaries.items()}, indent=2), flush=True)


if __name__ == '__main__':
    main()

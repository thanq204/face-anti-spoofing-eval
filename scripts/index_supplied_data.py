"""Index supplied files without moving them or inventing person-disjoint splits."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/data-audit-20261021'
DATA = ROOT / 'data/supplied-20261021'
audit = json.loads((OUT / 'audit.json').read_text(encoding='utf-8'))
DATA.mkdir(parents=True, exist_ok=True)
entries = []
for v in audit['videos']:
    entry = {key: v[key] for key in ('video_id','relative_path','label','sha256','bytes','width','height','fps','duration_seconds')}
    entry.update(subject_id='', source_id='', session_id='', camera_id='',
                 attack_type='', attack_device_id='', illumination='', environment='',
                 split='', target_roi=('left_65_percent' if v['video_id'] in {
                     'fake/REC-0001-A.mp4','fake/REC-0002-A.mp4','fake/REC-0003-A.mp4'} else 'review_single_face'))
    entries.append(entry)
manifest = {
    'status': 'indexed_and_evaluated_not_split',
    'source_policy': 'relative_path is relative to repository root; original files preserved',
    'training_overlap': audit['training_overlap'],
    'split_policy': 'No new train/validation/test split until subject/source IDs are verified. Keep all clips of one identity and source together.',
    'evaluation_report': 'deliverables/data-audit-20261021/audit.json',
    'videos': entries,
}
(DATA / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
with (OUT / 'metadata_can_bo_sung.csv').open('w', encoding='utf-8-sig', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(entries[0]))
    writer.writeheader()
    writer.writerows(entries)
(DATA / 'README.md').write_text('''# Dữ liệu đã nhập ngày 21/10/2026

manifest.json ánh xạ 47 fake và 44 real đến file nguồn trong dự án, giữ nguyên video và hash kiểm tra. Hai model đã chạy trên các nguồn này; báo cáo ở deliverables/data-audit-20261021/.

Chưa tự tạo split mới: người dùng xác nhận đây là bộ train cam4k cũ, còn thiếu mã người và nguồn. Bổ sung metadata_can_bo_sung.csv trước khi chia train/validation/test theo danh tính và nguồn. Không chia ngẫu nhiên từng frame.
''', encoding='utf-8')
print(f'Indexed {len(entries)} video files in {DATA / "manifest.json"}')

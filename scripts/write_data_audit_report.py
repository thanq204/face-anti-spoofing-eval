"""Build the Vietnamese research report and editable HTML source for Canva."""
from pathlib import Path
import json
from collections import Counter
from html import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/data-audit-20261021'
a = json.loads((OUT / 'audit.json').read_text(encoding='utf-8'))
pred = json.loads((OUT / 'predictions.json').read_text(encoding='utf-8'))
m, b = a['metrics']['cam4k'], a['metrics']['original']
pct = lambda x: f'{100*x:.2f}%'
cm = m['confusion_matrix_fake_real']
scores = [r for r in pred if r['model'] == 'cam4k' and r['status'] == 'scored']
qc = Counter(r['quality'] for r in scores if r['quality'])
sources = [
 ('[1] Boulkenafet et al., FG 2017 — OULU-NPU', 'https://sites.google.com/site/oulunpudatabase/welcome'),
 ('[2] Liu, Jourabloo & Liu, CVPR 2018 — Learning Deep Models for Face Anti-Spoofing: Binary or Auxiliary Supervision (SiW)', 'https://arxiv.org/html/1803.11097'),
 ('[3] Zhang et al., ECCV 2020 — CelebA-Spoof: Large-Scale Face Anti-Spoofing Dataset with Rich Annotations', 'https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123570069.pdf'),
 ('[4] Sun et al., CVPR 2023 — Rethinking Domain Generalization for Face Anti-Spoofing: Separability and Alignment', 'https://openaccess.thecvf.com/content/CVPR2023/html/Sun_Rethinking_Domain_Generalization_for_Face_Anti-Spoofing_Separability_and_Alignment_CVPR_2023_paper.html'),
]
research_rows = [
 ('Góc mặt & chuyển động', 'SiW [2]: thay đổi góc đầu, biểu cảm, khoảng cách và hướng chiếu sáng.', 'Thu chính diện, trái/phải, cúi/ngẩng, gần/xa; có nói, chớp mắt và chuyển động tự nhiên.'),
 ('Ánh sáng & môi trường', 'CelebA-Spoof [3]: 4 mức sáng × 2 môi trường; gán nhãn điều kiện quay.', 'Thu real và fake dưới sáng thường, mạnh, ngược, thiếu; ghi thêm lóa/phản xạ.'),
 ('Camera & kiểu tấn công', 'OULU-NPU [1]: nhiều camera, máy in, màn hình; test thiết bị mới.', 'Ghép điều kiện real–fake; thêm ảnh in, replay màn hình khác; đổi độ sáng/góc cầm.'),
 ('Chia tập & nhãn', 'OULU-NPU [1]: train/dev/test tách người; kiểm tra chéo phiên, camera, vật giả mạo.', 'Ghi subject_id, source_id, session, camera, attack; chia nhóm trước khi trích frame, chống trùng.'),
 ('Chất lượng ảnh', 'SA-FAS [4]: độ phân giải, mờ và cảm biến tạo chênh lệch giữa các miền.', 'Giữ video gốc; đo kích thước mặt, mờ, cháy sáng; sửa clip lỗi, giữ ca khó có nhãn.'),
]
failures = [v for v in m['video_results'] if v.get('prediction') and v['prediction'] != v['label']]
unscored = [v['video_id'] for v in m['video_results'] if v['status'] != 'scored']
report = f'''# Báo cáo dữ liệu Face Anti-Spoofing — Thắng — 21/10/2026

## Kết luận và phạm vi

Đã lập manifest cho 91 video và chạy hai model hiện có trên cùng mẫu video gốc. Người dùng xác nhận đây là bộ đã dùng để huấn luyện cam4k ngày 20/10/2026. Vì vậy các số dưới đây là **kiểm tra mô tả trên bộ phát triển đã thấy**, không phải test độc lập và không dùng để chứng minh tổng quát hóa. Không huấn luyện lại hay thay trọng số đang chạy trong đợt kiểm tra này.

## 1. Kiểm kê dữ liệu thực tế

- 47 fake, 44 real; tổng thời lượng {a['total_duration_seconds']/60:.2f} phút.
- **91/91 video 640×360**; không thể gọi các file hiện có là video 4K. Khả năng của camera và độ phân giải file là hai thông tin khác nhau.
- 91/91 giải mã đủ số frame khai báo; không có cặp file trùng SHA-256. Kiểm tra hash không phát hiện được mọi clip gần trùng hoặc cùng người.
- Không có manifest danh tính, phiên, thiết bị và loại tấn công ở nguồn. Không suy đoán số người từ số clip hoặc tự nhận diện danh tính từ mặt.
- Quan sát ảnh kiểm kê của tất cả clip: có nghiêng/cúi/ngẩng, kính, biểu cảm và bối cảnh khác nhau. Fake chủ yếu là phát lại trên điện thoại. Không có bằng chứng đã phủ máy in, nhiều loại màn hình, mọi ánh sáng hoặc mọi nhóm người.
- Fake REC-0001/2/3 có người thật cầm điện thoại ở bên phải. Dùng vùng phát hiện phía trái 65% đã kiểm tra bằng ảnh; không sửa pixel crop dùng phân loại. Khung có nhiều mặt còn lại được loại và báo riêng. Đây là quy tắc gán mục tiêu cho phép đo, không phải cải tiến khả năng model.

## 2. Đọc bài báo và chuyển thành tiêu chí thu thập

Các nghiên cứu chỉ ra các trục biến thiên và cách đánh giá, **không đặt một số clip, độ lux, góc mặt hay độ chói tối thiểu dùng chung cho mọi ứng dụng**. Thông số thu bên dưới là đề xuất thực nghiệm cho nhóm.

| Trục | Bằng chứng từ bài báo | Áp dụng |
|---|---|---|
'''
for topic, evidence, requirement in research_rows:
    report += f'| {topic} | {evidence} | {requirement} |\n'
report += f'''
SiW dùng nhiều người, phiên, chất liệu print/replay và góc mặt rộng; thu các biến thiên riêng có kiểm soát giúp kiểm tra lỗi. Không cần buộc người sử dụng quay toàn bộ góc ±90°: ưu tiên miền góc thực tế của ứng dụng, rồi có tập stress riêng. OULU-NPU cho thấy cần tách người và kiểm tra điều kiện chưa thấy. CelebA-Spoof bổ sung căn cứ cho nhãn ánh sáng, môi trường và loại giả mạo. SA-FAS nhấn mạnh độ phân giải/mờ/cảm biến khi chuyển miền.

## 3. Phép đo có thể tái hiện

Chạy `scripts/audit_current_data.py`. Thư viện được cài riêng ở `.runtime/site-packages`; cần đặt PYTHONPATH tới đó. Dùng YuNet confidence 0.62, crop BGR 32×32 chia 255, bản TFLite mà pipeline dự án đang ưu tiên. Thứ tự nhãn đã kiểm tra: fake, real. Hai model dùng cùng mặt và cùng mẫu.

Lấy cố định 2 frame/giây trong tối đa 12 giây đầu của từng video, bắt đầu tại frame 0. Tổng {m['attempts']} lần lấy mẫu. Chỉ chấm khi có đúng một mặt mục tiêu; {m['status_counts'].get('multiple_faces',0)} khung nhiều mặt và {m['status_counts'].get('no_face',0)} khung không phát hiện mặt không được tính là dự đoán đúng. Có {m['scored']} khung chấm được, coverage {pct(m['coverage'])}. Không áp dụng quality gate để bỏ ca khó trong kết quả chính vì chế độ binary mặc định vẫn phân loại các ca này.

FastBinaryDecision dùng cấu hình mặc định. Ở 2 FPS, khoảng lấy mẫu dài hơn cửa sổ 0,45 giây nên phép đo gần với phân loại từng mẫu, không đánh giá đầy đủ độ ổn định ở FPS camera thực. Không đo HTTP, camera trực tiếp hoặc tốc độ FPS triển khai. Điểm theo video dùng trung bình xác suất gốc, ngưỡng 0,5 cố định.

| Model TFLite | Accuracy mẫu chấm được | Fake → real (APCER gộp) | Real → fake (BPCER) | ACER gộp |
|---|---:|---:|---:|---:|
| cam4k hiện tại | {pct(m['accuracy'])} | {pct(m['pooled_APCER'])} | {pct(m['BPCER'])} | {pct(m['pooled_ACER'])} |
| model gốc | {pct(b['accuracy'])} | {pct(b['pooled_APCER'])} | {pct(b['BPCER'])} | {pct(b['pooled_ACER'])} |

Ma trận nhầm lẫn cam4k, hàng là nhãn thật, cột là nhãn dự đoán:

| | Dự đoán fake | Dự đoán real |
|---|---:|---:|
| Fake | {cm[0][0]} | {cm[0][1]} |
| Real | {cm[1][0]} | {cm[1][1]} |

APCER ở đây là số mẫu fake bị nhận real chia số mẫu fake đã chấm; BPCER là số mẫu real bị nhận fake chia số mẫu real đã chấm. ACER gộp là trung bình hai tỷ lệ đó. Chưa có nhãn loại vật giả mạo nên không thể báo APCER tệ nhất theo từng PAI như đánh giá OULU. Đơn vị ở bảng là **khung mẫu**, không phải lượt tấn công độc lập.

Theo trung bình xác suất video: cam4k {pct(m['video_mean_score']['accuracy'])} trên {m['video_mean_score']['scored']}/91 clip chấm được. Model gốc: {pct(b['video_mean_score']['accuracy'])}. Clip không có mẫu chấm được: {', '.join(unscored) or 'không có'}. Khung cùng video tương quan; số frame không tương đương số quan sát độc lập.

Cam4k cải thiện accuracy {(m['accuracy']-b['accuracy'])*100:.2f} điểm phần trăm so với bản gốc trong phép đo này. Cần đọc đồng thời hai loại lỗi; không dùng riêng accuracy để quyết định chấp nhận model. Những lỗi video cần kiểm tra lại: {', '.join(v['video_id'] for v in failures)}. Đây là nơi ưu tiên xem lại từng khung và thu thêm trường hợp tương tự, không mặc nhiên kết luận nguyên nhân do ánh sáng hay góc.

Cờ chất lượng trên các mẫu chấm được: {dict(qc)}. Đây là ngưỡng heuristic của code, không phải chuẩn quốc tế và không chứng minh bộ dữ liệu đã phủ đủ độ sáng, lóa, góc mặt. Không có cảm biến lux hoặc nhãn góc, nên không bịa tỷ lệ phủ.

## 4. Điểm mạnh, điểm yếu và rủi ro

**Điểm mạnh:** hai lớp gần cân bằng ở cấp video; clip đọc được toàn bộ; có chuyển động/góc mặt, kính và bối cảnh đa dạng trong ảnh kiểm kê; dữ liệu replay sát một nguy cơ triển khai; có hai model làm mốc so sánh.

**Điểm yếu:** nguồn hiện có chỉ 640×360 rồi crop 32×32, làm hạn chế chi tiết nhỏ; chưa đo mức ảnh hưởng bằng ablation. Fake thiên về màn hình điện thoại, chưa chứng minh có print và nhiều thiết bị. Người, phiên và nguồn video chưa có mã chuẩn. Có người cầm máy và người nền làm gán nhãn ở cấp thư mục không đủ. Cùng bộ đã dùng huấn luyện nên kết quả có thể lạc quan; cần giữ tập test mới.

**Giả thuyết cần kiểm tra:** màu màn hình, viền điện thoại, bối cảnh hoặc thời điểm quay có thể trở thành dấu hiệu dễ học thay cho dấu vết giả mạo. SiW [2] cảnh báo về dấu hiệu tùy ý như viền màn hình. Chưa có thí nghiệm che viền/đổi điều kiện nên chưa kết luận model thực sự dựa vào chúng. Thu real–fake dưới điều kiện tương ứng và có replay che viền, in chất lượng cao để kiểm tra.

Tài liệu dự án cũ nêu test crop 98,09%, 14/14 video và 99,84% camera ngoài. Lần này khác tập ảnh, detector/crop và phương thức lấy mẫu; không lấy chênh lệch để kết luận model suy giảm. Không có manifest split và xác suất gốc của thí nghiệm đó trong checkout để xác minh lại tính độc lập hay phạm vi “camera ngoài”. Train/val loss gần nhau tự nó không chứng minh không overfit.

## 5. Công việc tuần sau (26/10–01/11/2026)

Đây là mục tiêu đề xuất của nhóm, không phải ngưỡng bắt buộc trong các bài báo.

1. **Thứ 2:** hoàn thiện CSV cho 91 clip: video_id, label, subject_id (người trên mặt/vật tấn công), source_id của video gốc, session_id, camera_id, attack_type, attack_device_id, ánh sáng, môi trường, khoảng cách, góc, chất lượng và vùng mục tiêu. Rà lại fake 1–3, người nền, các file có hậu tố (2). Không tự xem hậu tố (2) là video trùng.
2. **Thứ 3–5:** mục tiêu 15 người mới × 2 camera × 4 ánh sáng × (real + print + replay) = **360 clip**, mỗi clip 10–15 giây, khoảng 60–90 phút video. Quay 5 người/ngày là mục tiêu tổ chức; điều chỉnh theo nguồn lực. Cân bằng các ô thay vì chỉ tăng frame. Có cả sáng thường/mạnh/ngược/thiếu; trong/ngoài nhà trong ma trận phân bổ. Trong clip có đoạn chính diện, trái/phải, cúi/ngẩng và gần/xa theo miền vận hành. Gợi ý yaw 0°, ±15°, ±30°, thêm ±45° vào stress; đây là thiết kế nhóm, không phải chuẩn paper.
3. **Vật giả mạo:** luân phiên ít nhất 2 thiết bị màn hình, 2 nguồn ảnh/thiết lập in (nhám/bóng khi có), độ sáng màn hình thấp/vừa/cao, có/không viền, cầm tĩnh/rung nhẹ, giấy phẳng/uốn. Luân phiên các biến này trong 360 clip, không khẳng định đã chạy toàn bộ tích Descartes. Nhắc lại một phần ở phiên khác để kiểm tra biến thiên theo buổi. Lưu bản gốc độ phân giải cao và metadata; không upscale 360p thành “4K”.
4. **Thứ 6:** chia theo người trước khi trích frame, dự kiến 9 train / 3 validation / 3 test cho 15 người mới; mọi real và fake cùng danh tính/source phải cùng tập. Đây còn là test nhỏ, cần tiếp tục tăng người. Đóng băng tập test mới; chọn checkpoint/ngưỡng bằng validation. Giữ thêm cấu hình kiểm tra camera hoặc màn hình chưa gặp theo OULU, tách khỏi benchmark cùng miền.
5. **Cuối tuần:** phối hợp thành viên model train candidate trên phần train đủ điều kiện; so baseline và candidate trên cùng test mới, báo APCER từng vật giả mạo, BPCER, ACER, coverage và kết quả theo người/video/điều kiện. Báo số người và mẫu số, không chỉ số ảnh. Chỉ đề nghị thay model sau khi đọc trade-off hai loại lỗi. Augmentation vừa phải bổ trợ việc thu thật; không thay được camera/màn hình/ánh sáng mới và không xóa hết ca lóa khó.

## 6. Nguồn nghiên cứu

'''
report += '\n'.join(f'- [{title}]({url})' for title, url in sources)
report += '\n\nBằng chứng cục bộ: audit.json, predictions.json, video_manifest.csv, contact_fake_1/2.jpg và contact_real_1/2.jpg. Hash model và từng video được lưu trong audit.json.\n'
(OUT / 'Bao_cao_du_lieu_Thang.md').write_text(report, encoding='utf-8')

notes5 = ('Nghiên cứu phục vụ phần dữ liệu của Thắng. Các paper không đặt ngưỡng góc, lux hoặc số clip dùng chung. '
          'Mục tiêu định lượng là đề xuất của nhóm. ' + '\n'.join(t + ': ' + u for t,u in sources))
notes6 = (f'Nguồn: scripts/audit_current_data.py và deliverables/data-audit-20261021/audit.json; ngày 21/10/2026. '
          f'Người dùng xác nhận 91 clip đã dùng train cam4k. Lấy 2 FPS trong tối đa 12 giây đầu, {m["scored"]}/{m["attempts"]} mẫu chấm được; '
          f'loại {m["status_counts"].get("multiple_faces",0)} nhiều mặt và {m["status_counts"].get("no_face",0)} không mặt. '
          'Ba clip fake đầu dùng ROI phát hiện trái 65% đã rà bằng ảnh, loại người cầm điện thoại. '
          'TFLite, YuNet 0.62, BGR32/255, ngưỡng cố định; không đo FPS camera hay test người mới. '
          'APCER/ACER gộp trên frame, chưa tách PAI. ' + '\n'.join(t + ': ' + u for t,u in sources))
tr = ''.join(f'<tr><td class="topic">{escape(t)}</td><td>{escape(e)}</td><td>{escape(r)}</td></tr>' for t,e,r in research_rows)
html = f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Thắng — Dữ liệu Face Anti-Spoofing</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;font-family:Arial,sans-serif;background:#0b101e;color:#f4f6fb}}.page{{width:1920px;height:1080px;position:relative;padding:68px 100px;background:#0b101e;overflow:hidden;margin-bottom:20px}}.eyebrow{{font-size:25px;font-weight:bold;color:#36c7f5;margin:0 0 22px}}h1{{font-size:54px;line-height:1.12;margin:0 0 22px}}.sub{{font-size:28px;line-height:1.3;color:#a8b5c9;margin:0}}table{{border-collapse:collapse;width:100%;font-size:29px;line-height:1.27}}th{{text-align:left;font-size:25px;color:#36c7f5;background:#101a2e;padding:18px 24px;border-bottom:2px solid #345070}}td{{vertical-align:top;padding:15px 22px;border-bottom:1px solid #29344a}}.topic{{width:265px;color:#e6edf8;font-weight:bold}}.evidence{{margin-top:38px}}.evidence td:nth-child(2){{width:640px;color:#b7c4d8}}.evidence td:nth-child(3){{color:#f0f5fb}}.note{{font-size:25px;line-height:1.35;color:#a8b5c9}}.callout{{border-left:5px solid #f5b700;padding:16px 24px;background:#111b2b;color:#f6da85;font-size:28px;line-height:1.35}}.footer{{position:absolute;bottom:36px;left:100px;right:100px;font-size:20px;line-height:1.35;color:#8295b3}}.statrow{{display:flex;gap:30px;margin:34px 0 24px}}.stat{{width:33.333%;padding:20px 26px;background:#101a2e;border:1px solid #304564}}.stat strong{{display:block;font-size:50px;color:#66dcb4;margin-bottom:10px}}.stat span{{font-size:26px;color:#c4cfdf}}.metric{{font-size:28px}}.metric td,.metric th{{padding:14px 23px}}.metric td{{color:#dbe6f5}}.metric tr:nth-child(2) td{{color:#70e1bc;font-weight:bold}}.lower{{display:flex;gap:36px;margin-top:28px}}.col{{width:33.333%;border-top:3px solid #31465f;padding-top:18px}}h2{{font-size:29px;margin:0 0 12px;color:#36c7f5}}.col p{{font-size:27px;line-height:1.4;margin:0 0 12px;color:#d8e1ee}}.col.bad h2{{color:#ffc045}}.col.plan h2{{color:#67ddb2}}a{{color:inherit}}b{{color:#f2f7ff}}
</style></head><body>
<section class="page" data-document-role="page" data-label="Thắng — Yêu cầu dữ liệu" data-speaker-notes="{escape(notes5, quote=True)}">
<p class="eyebrow">THẮNG • PHỤ TRÁCH DỮ LIỆU • 21/10/2026</p>
<h1>Yêu cầu dữ liệu từ các nghiên cứu Face Anti-Spoofing</h1>
<p class="sub">Phủ điều kiện sử dụng thực tế, gán nhãn rõ và kiểm tra khả năng xử lý điều kiện chưa gặp</p>
<table class="evidence" style="font-size:28px;line-height:1.24"><tr><th>Yếu tố cần phủ</th><th>Bằng chứng nghiên cứu</th><th>Áp dụng cho bộ dữ liệu nhóm</th></tr>{tr}</table>
<div class="callout" style="margin-top:26px">Đề xuất của nhóm: thu theo ma trận <b>người × thiết bị × ánh sáng × real/print/replay</b>.<br>Chưa có ngưỡng góc, lux hay số video tối thiểu dùng chung trong các bài báo trên.</div>
<div class="footer">[1] OULU-NPU — FG 2017 · [2] SiW — CVPR 2018 · [3] CelebA-Spoof — ECCV 2020 · [4] SA-FAS — CVPR 2023<br>Link bài báo và diễn giải chi tiết trong ghi chú thuyết trình.</div></section>
<section class="page" data-document-role="page" data-label="Thắng — Đánh giá và kế hoạch" data-speaker-notes="{escape(notes6, quote=True)}">
<p class="eyebrow">THẮNG • KIỂM TRA DỮ LIỆU & MODEL • 21/10/2026</p>
<h1>Dữ liệu hiện tại và kế hoạch bổ sung tuần sau</h1>
<p class="sub">Bộ đã dùng train cam4k • Kết quả dưới đây là kiểm tra lại, chưa phải test độc lập trên người mới</p>
<div class="statrow"><div class="stat"><strong>91 video</strong><span>47 fake / 44 real · {a['total_duration_seconds']/60:.1f} phút</span></div><div class="stat"><strong>640 × 360</strong><span>91/91 file hiện có · chưa phải 4K</span></div><div class="stat"><strong>{pct(m['coverage'])}</strong><span>Coverage: {m['scored']:,}/{m['attempts']:,} mẫu chấm được</span></div></div>
<table class="metric"><tr><th>Model / cùng mẫu video gốc</th><th>Accuracy</th><th>Fake → real¹</th><th>Real → fake²</th><th>ACER gộp</th></tr>
<tr><td>cam4k hiện tại</td><td>{pct(m['accuracy'])}</td><td>{pct(m['pooled_APCER'])}</td><td>{pct(m['BPCER'])}</td><td>{pct(m['pooled_ACER'])}</td></tr>
<tr><td>Model gốc</td><td>{pct(b['accuracy'])}</td><td>{pct(b['pooled_APCER'])}</td><td>{pct(b['BPCER'])}</td><td>{pct(b['pooled_ACER'])}</td></tr></table>
<div class="lower"><div class="col"><h2>Điểm mạnh</h2><p>Hai lớp gần cân bằng; 91/91 clip đọc đủ frame, không trùng hash.</p><p>Có góc mặt, chuyển động, kính và bối cảnh khác nhau; replay sát bài toán thực tế.</p></div>
<div class="col bad"><h2>Khoảng trống dữ liệu</h2><p>Fake thiên về điện thoại; chưa chứng minh đủ print, camera và ánh sáng.</p><p>Thiếu mã người/phiên/thiết bị; 3 clip đầu lẫn người cầm máy. Cần gán mặt mục tiêu.</p></div>
<div class="col plan"><h2>Tuần 26/10–01/11: đề xuất</h2><p><b>15 người mới × 2 camera × 4 ánh sáng × 3 loại = 360 clip.</b></p><p>Chuẩn hóa nhãn; chia theo người trước trích frame. Giữ test mới; so lỗi từng điều kiện.</p></div></div>
<div class="footer">2 FPS trong tối đa 12 giây đầu; YuNet + TFLite, crop BGR 32×32. Loại {m['status_counts'].get('multiple_faces',0)} mẫu nhiều mặt / {m['status_counts'].get('no_face',0)} không mặt; không tính chúng là đúng.<br>¹ APCER gộp; ² BPCER, tính trên mẫu chấm được. ROI trái 65% cho fake 1–3. Không so trực tiếp với test crop 98,09% trước đây. Nguồn: audit.json; [1–4] slide 5.</div>
</section></body></html>'''
(OUT / 'slides_5_6_Thang.html').write_text(html, encoding='utf-8')
print(json.dumps({'report': str(OUT / 'Bao_cao_du_lieu_Thang.md'), 'html': str(OUT / 'slides_5_6_Thang.html'),
                  'metrics': {k: m[k] for k in ('accuracy','coverage','pooled_APCER','BPCER','pooled_ACER')}}, ensure_ascii=False))

# Face Anti-Spoofing | Video Replay Evaluation

Công cụ đánh giá hai checkpoint chống giả mạo khuôn mặt trên cùng một bộ clip có nhãn. Pipeline dùng YuNet để phát hiện mặt, chạy mô hình TFLite trên CPU và xuất báo cáo tổng hợp ở cấp frame và cấp video.

## Nguồn gốc và phạm vi

Bài toán, dữ liệu, mô hình và ứng dụng gốc thuộc **đồ án nhóm**. Trưởng nhóm **thanhAI408** viết mã ứng dụng và pipeline gốc. Repo riêng này chứa phần đánh giá được bổ sung cho đồ án: CLI chạy hai checkpoint trên cùng dữ liệu, quy tắc xử lý clip, thống kê tỷ lệ lỗi và kiểm tra độ bao phủ. Checkpoint và detector được nạp từ đường dẫn bên ngoài. [Repo gốc của nhóm](https://github.com/thanhAI408/face_anti_spoofing)

## Kết quả chạy lại trên dữ liệu nhóm

Ngày 10/11/2026, chạy trên **91 clip** đã đối chiếu SHA-256 với manifest của nhóm, gồm **47 fake và 44 real**. Có **87 clip được chấm** (46 fake, 41 real) và **1.712/2.098 frame lấy mẫu** đủ điều kiện. Bốn clip không có frame chỉ chứa đúng một khuôn mặt được detector phát hiện.

| Checkpoint | Fake bị nhận là real | Real bị nhận là fake | ACER gộp theo clip |
| --- | ---: | ---: | ---: |
| Original | 1/46 (2,17%) | 7/41 (17,07%) | 9,62% |
| Cam4K | 1/46 (2,17%) | 4/41 (9,76%) | 5,97% |

Trong lần chạy này, Cam4K từ chối nhầm ít clip thật hơn. Ở cấp frame, tỷ lệ fake bị nhận là real tăng từ 2,81% lên 3,37%, còn tỷ lệ real bị nhận là fake giảm từ 19,71% xuống 11,44%. Báo cáo có ma trận nhầm lẫn và số lượng frame không đủ điều kiện theo nhãn. [JSON kết quả](docs/replay.json)

## Cách chạy lại

Cần Python 3.11 và quyền truy cập cục bộ vào thư mục đồ án nhóm. Từ thư mục repo này, tạo và kích hoạt môi trường ảo rồi cài dependencies.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

$GroupProject = 'C:\path\to\face_anti_spoofing'
python evaluate.py --data "$GroupProject\data\supplied-20261021" --detector "$GroupProject\face_detector\face_detection_yunet_2023mar.onnx" --model "original=$GroupProject\web_models\liveness.tflite" --model "cam4k=$GroupProject\web_models\liveness_cam4k.tflite" --output reports/replay.json
```

Thư mục truyền vào `--data` có hai thư mục con `Video fake` và `Video real`. Cờ `--model NAME=PATH` lặp lại được. Các cờ `--sample-fps`, `--max-seconds` và `--threshold` lần lượt mặc định là 2, 12 và 0,5.

## Cách tính

1. Lấy mẫu khoảng hai frame mỗi giây trong 12 giây đầu của mỗi clip. Chỉ chấm frame mà YuNet phát hiện đúng một mặt tại ngưỡng 0,62.
2. Cắt mặt, đổi kích thước thành 32 × 32, giữ thứ tự kênh BGR và chuẩn hóa về [0, 1]. Hai checkpoint trả về hai xác suất theo thứ tự `[fake, real]`.
3. Quyết định `real` khi xác suất lớn hơn 0,5. Ở cấp clip, dùng trung bình xác suất trên các frame đủ điều kiện. Không áp dụng temporal smoothing hoặc fusion của ứng dụng nhóm.
4. Tính APCER gộp bằng tỷ lệ fake bị nhận là real. Tính BPCER bằng tỷ lệ real bị nhận là fake. ACER gộp là trung bình của hai tỷ lệ trên. Các trường hợp bỏ qua được đếm riêng và nằm ngoài mẫu số tỷ lệ lỗi. [Tham khảo NIST FATE PAD](https://pages.nist.gov/frvt/html/frvt_pad.html)

## Giới hạn

91 clip này từng được dùng để train Cam4K. Manifest chưa có mã người, phiên quay, nguồn hay loại tấn công. Kết quả mô tả hành vi trên dữ liệu đã có, chưa xác nhận hiệu quả trên người hoặc thiết bị mới. Tỷ lệ lỗi cấp frame cũng có tương quan giữa các frame cùng clip. Khi có dữ liệu độc lập, hãy chia theo người và phiên, cố định ngưỡng từ validation rồi báo riêng tỷ lệ lỗi và độ bao phủ theo từng loại tấn công.

Dữ liệu mặt, video, checkpoint, detector và báo cáo thô được giữ cục bộ. Repo lưu số đếm tổng hợp, không lưu tên video, danh tính hay crop khuôn mặt.

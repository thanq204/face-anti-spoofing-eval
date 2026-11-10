# Face Anti-Spoofing · Đánh giá mô hình liveness

**Nguyễn Chiến Thắng** · Python · OpenCV YuNet · TensorFlow Lite

Trong đồ án chống giả mạo khuôn mặt, tôi tập trung vào một câu hỏi: khi đổi checkpoint, hệ thống chặn được bao nhiêu video giả và từ chối nhầm bao nhiêu video thật? Tôi xây dựng công cụ chạy hai checkpoint trên cùng bộ video và xuất báo cáo ở cả cấp clip lẫn cấp frame.

## Kết quả

Tôi chạy Original và Cam4K trên **91 video của đồ án**. Hai checkpoint dùng cùng cách lấy mẫu, cùng bộ phát hiện mặt và cùng ngưỡng 0,5. Có **87/91 clip** và **1.712/2.098 frame lấy mẫu** đủ điều kiện chấm.

| Checkpoint | Clip giả bị nhận là thật (APCER gộp) | Clip thật bị nhận là giả (BPCER) | ACER gộp |
| --- | ---: | ---: | ---: |
| Original | 1/46 (2,17%) | 7/41 (17,07%) | 9,62% |
| Cam4K | 1/46 (2,17%) | 4/41 (9,76%) | 5,97% |

**Cam4K từ chối nhầm ít hơn 3 clip thật.** Cả hai checkpoint đều nhận nhầm 1 clip giả. Ở cấp frame, Cam4K nhận nhầm nhiều frame giả hơn (3,37% so với 2,81%) nhưng từ chối nhầm ít frame thật hơn (11,44% so với 19,71%). Vì vậy tôi báo riêng hai loại lỗi, thay vì chỉ nhìn vào một chỉ số tổng hợp. [Báo cáo JSON và ma trận nhầm lẫn](docs/replay.json)

## Phần tôi thực hiện

- **Tạo CLI đánh giá.** Chạy nhiều checkpoint TFLite trên CPU trong một lượt đọc video để mỗi model nhận đúng cùng frame và vùng mặt. [evaluate.py](evaluate.py)
- **Đặt quy tắc chấm rõ ràng.** Chỉ chấm frame có đúng một khuôn mặt. Báo riêng số frame không có mặt hoặc có nhiều mặt để người đọc biết tỷ lệ lỗi được tính trên bao nhiêu dữ liệu.
- **Tổng hợp lỗi ở cấp video.** Lấy trung bình điểm liveness của các frame đủ điều kiện để ra một quyết định cho mỗi clip. Lưu số đếm và ma trận nhầm lẫn dưới dạng JSON.

## Pipeline

```text
Video có nhãn → Lấy mẫu frame → YuNet tìm mặt → Crop 32 × 32 → TFLite
             → Điểm liveness từng frame → Quyết định từng clip → Báo cáo JSON
```

Công cụ lấy mẫu khoảng 2 frame/giây trong 12 giây đầu. YuNet dùng ngưỡng phát hiện 0,62. Vùng mặt giữ thứ tự kênh BGR và được chuẩn hóa về [0, 1]. Clip được xếp loại thật khi điểm trung bình lớn hơn 0,5. ACER gộp là trung bình của tỷ lệ nhận nhầm clip giả và tỷ lệ từ chối nhầm clip thật.

## Chạy lại

Dùng Python 3.11. Trỏ lệnh vào thư mục chứa detector, checkpoint và hai thư mục video có nhãn `Video fake` và `Video real`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

$GroupProject = 'C:\path\to\face_anti_spoofing'
python evaluate.py --data "$GroupProject\data\supplied-20261021" --detector "$GroupProject\face_detector\face_detection_yunet_2023mar.onnx" --model "original=$GroupProject\web_models\liveness.tflite" --model "cam4k=$GroupProject\web_models\liveness_cam4k.tflite" --output reports/replay.json
```

Dùng `python evaluate.py --help` để xem các tùy chọn. Video và checkpoint được đọc trực tiếp từ máy. Báo cáo trong repo chỉ chứa số liệu tổng hợp.

## Phạm vi đánh giá

Đây là một lần chạy lại trên dữ liệu từng dùng để train Cam4K. Kết quả cho biết hai checkpoint hành xử thế nào trên bộ clip hiện có. Bước tiếp theo là đánh giá trên video mới, chia theo người và phiên quay, rồi báo riêng lỗi theo loại giả mạo.

*Case study cá nhân phát triển từ đồ án nhóm Face Anti-Spoofing.* [Dự án nhóm](https://github.com/thanhAI408/face_anti_spoofing)

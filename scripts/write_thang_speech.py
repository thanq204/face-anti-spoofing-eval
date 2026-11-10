"""Vietnamese speaking script for Thắng's two slides, with one capture camera."""
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/thuyet-trinh-20261022'
OUT.mkdir(parents=True, exist_ok=True)

slide5 = [
    'Ở slide 5, em trình bày các yêu cầu đối với dữ liệu dựa trên bốn nghiên cứu về chống giả mạo khuôn mặt. Thiết bị ghi hình của nhóm là camera USB SC-M200. Toàn bộ video real và fake đều được quay bằng chính thiết bị này. Nội dung slide tập trung vào người, ánh sáng, góc mặt, kiểu giả mạo và cách tổ chức dữ liệu.',
    'Đầu tiên là góc mặt và chuyển động. Nghiên cứu SiW xem xét sự thay đổi góc đầu, biểu cảm và khoảng cách tới camera. Áp dụng vào nhóm, mỗi người nên được quay ở tư thế chính diện, quay trái, quay phải, cúi và ngẩng nhẹ. Trong video có thể thêm nói hoặc thay đổi biểu cảm để gần với cách người dùng xuất hiện trước camera thực tế.',
    'Tiếp theo là ánh sáng và môi trường. CelebA-Spoof phân biệt các điều kiện sáng bình thường, sáng mạnh, ngược sáng và thiếu sáng. Với SC-M200, nhóm có thể thu các điều kiện này bằng cách đổi vị trí quay, hướng chiếu sáng hoặc thời điểm quay. Cần ghi nhận thêm lóa trên kính, phản xạ trên màn hình và vùng khuôn mặt bị cháy sáng.',
    'Điểm cần chú ý là real và fake nên được thu trong điều kiện tương ứng. Ví dụ, cùng một góc đặt camera và cùng điều kiện sáng thì quay cả người thật lẫn ảnh hoặc video giả mạo. Nếu người thật luôn đủ sáng còn fake luôn tối, model có thể học sự khác biệt về độ sáng thay vì dấu hiệu giả mạo.',
    'Về kiểu tấn công, OULU-NPU có dữ liệu ảnh in và video phát lại. Phần nhóm áp dụng là bổ sung các kiểu giả mạo này, vẫn dùng SC-M200 để ghi hình. Với replay, có thể thay đổi độ sáng màn hình, góc cầm và việc có lộ viền điện thoại hay không. Với ảnh in, có thể thử giấy phẳng và uốn nhẹ. Điện thoại hoặc tờ giấy là vật dùng để giả mạo; thiết bị ghi lại các trường hợp real và fake vẫn là SC-M200.',
    'Về nhãn và chia tập, mỗi video cần có mã người, phiên quay, nguồn và kiểu giả mạo. Cần chia theo người trước khi trích khung hình. Các video real và fake của cùng một người hoặc cùng nguồn nên được giữ trong cùng tập. Như vậy sẽ hạn chế việc các khung hình gần giống nhau xuất hiện ở cả train và test, khiến kết quả đánh giá lạc quan.',
    'Cuối cùng là chất lượng ảnh. SA-FAS xem xét sự khác biệt về độ phân giải và độ mờ giữa các miền dữ liệu. Với nhóm, việc cần làm là giữ video gốc, kiểm tra khuôn mặt có đủ lớn, đủ nét và có bị chói hay không. Clip lỗi hoặc sai nhãn cần được sửa; những trường hợp khó nhưng đúng nhãn vẫn nên được giữ để đánh giá.',
]

slide6 = [
    'Sang slide 6, em đối chiếu các yêu cầu trên với dữ liệu và model hiện tại. Bộ dữ liệu có 91 video, gồm 47 fake và 44 real, tổng thời lượng khoảng 39 phút. Hai lớp khá cân bằng về số video. Tất cả video được ghi hình bằng cùng một camera USB SC-M200.',
    'Qua kiểm tra, cả 91 video đều đọc được đủ số khung hình khai báo và không có file trùng hoàn toàn theo mã kiểm tra. Ảnh kiểm kê cho thấy có thay đổi góc mặt, chuyển động, kính và bối cảnh. Các file hiện có đều ở độ phân giải 640 nhân 360. Đây là độ phân giải của file dữ liệu đã kiểm tra, không phải kết luận về độ phân giải tối đa của SC-M200.',
    'Về cách đánh giá, hai model được chạy trên cùng các mẫu lấy từ video gốc. Mỗi giây lấy hai khung hình trong tối đa 12 giây đầu của từng video. Tổng cộng có 2.098 mẫu, trong đó 1.784 mẫu chấm được, tương ứng coverage là 85,03%. Những mẫu không phát hiện được mặt hoặc có nhiều mặt chưa xác định được một mục tiêu được báo riêng, không tính là dự đoán đúng.',
    'Trên các mẫu chấm được, model cam4k hiện tại đạt accuracy 94,28%, so với 90,92% của model gốc. Tuy nhiên, cần đọc thêm hai loại lỗi. Fake bị nhận thành real nghĩa là giả mạo lọt qua hệ thống; tỷ lệ này của cam4k là 1,69%. Real bị nhận thành fake nghĩa là người thật bị từ chối nhầm; tỷ lệ này là 10,30%.',
    'So với model gốc, cam4k giảm tỷ lệ từ chối nhầm người thật từ 18,08% xuống 10,30%, nhưng tỷ lệ fake lọt qua tăng từ 1,16% lên 1,69%. ACER gộp, là trung bình hai loại lỗi này, giảm từ 9,62% xuống 5,99%. Vì vậy, model cải thiện kết quả tổng thể trong phép đo này, nhưng vẫn cần cải thiện cả hai loại lỗi.',
    'Một giới hạn quan trọng là đây là bộ dữ liệu đã dùng trong đợt huấn luyện cam4k. Kết quả lần này giúp tìm lỗi còn tồn tại trên dữ liệu hiện có, chưa chứng minh khả năng xử lý người hoàn toàn mới. Cũng không nên so trực tiếp với mức 98,09% trước đây vì cách lấy mẫu và đánh giá khác nhau.',
    'Về điểm còn thiếu, fake đang thiên về phát lại trên điện thoại; cần kiểm tra độ phủ đối với ảnh in, ánh sáng và góc mặt khó. Dữ liệu cũng cần có mã người và phiên quay rõ ràng. Ba clip fake đầu còn có người thật cầm điện thoại cạnh màn hình, nên phải gán đúng mặt mục tiêu. Không thể coi mọi khuôn mặt trong thư mục fake đều là mặt giả.',
    'Định hướng tuần sau là rà lại dữ liệu hiện có để xác định những tình huống chưa được kiểm tra đầy đủ. Với người thật, cần xem các trường hợp thiếu sáng, ngược sáng, lóa trên kính; quay trái hoặc phải, cúi hoặc ngẩng và đứng gần hoặc xa thiết bị. Với replay, cần kiểm tra độ sáng màn hình và góc cầm điện thoại. Với ảnh in, các trường hợp cần xem xét là giấy phẳng hoặc uốn nhẹ. Thiết bị ghi hình cho các tình huống này vẫn là SC-M200.',
    'Khi rà soát, em sẽ ghi lại model sai ở tình huống nào, kiểm tra nhãn và tách kết quả theo từng điều kiện. Đây là các trường hợp cần kiểm tra độ phủ; nhóm chưa chốt kế hoạch thu thêm dữ liệu hoặc số lượng video. Việc có cần quay bổ sung sẽ được xem xét sau bước rà soát. Em xin hết phần trình bày của mình.',
]

doc = Document()
for border in list(doc.styles.element.iter(qn('w:pBdr'))):
    border.getparent().remove(border)
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(1.8)
sec.left_margin = sec.right_margin = Cm(2)
for name in ('Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2'):
    style = doc.styles[name]
    style.font.name = 'Arial'
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:hAnsi'), 'Arial')
    style.element.rPr.rFonts.set(qn('w:ascii'), 'Arial')
normal = doc.styles['Normal']
normal.font.size = Pt(12)
normal.paragraph_format.line_spacing = 1.08
normal.paragraph_format.space_after = Pt(7)
normal.paragraph_format.widow_control = True
doc.styles['Title'].font.size = Pt(20)
doc.styles['Title'].paragraph_format.space_after = Pt(7)
doc.styles['Heading 1'].font.size = Pt(15)
doc.styles['Heading 1'].paragraph_format.space_before = Pt(7)
doc.styles['Heading 1'].paragraph_format.space_after = Pt(8)
doc.styles['Heading 1'].paragraph_format.keep_with_next = True
doc.add_paragraph('Lời thuyết trình slide 5 và 6', 'Title')
p = doc.add_paragraph('Thắng phụ trách dữ liệu')
p.paragraph_format.space_after = Pt(4)
p.runs[0].bold = True
p = doc.add_paragraph('Thời lượng tham khảo 6 đến 8 phút. Thiết bị ghi hình duy nhất là camera USB SC-M200.')
p.runs[0].italic = True
p.runs[0].font.size = Pt(11)
doc.add_heading('Slide 5 Yêu cầu dữ liệu thu bằng thiết bị của nhóm', 1)
for text in slide5:
    doc.add_paragraph(text)
doc.add_page_break()
doc.add_heading('Slide 6 Đánh giá dữ liệu và tình huống cần kiểm tra', 1)
for text in slide6:
    doc.add_paragraph(text)

doc.core_properties.title = 'Lời thuyết trình slide 5 và 6'
doc.core_properties.author = 'Thắng'
doc.core_properties.subject = 'Dữ liệu Face Anti Spoofing thu bằng camera USB SC-M200'
path = OUT / 'Loi_thuyet_trinh_Thang_slide_5_6_SC_M200.docx'
doc.save(path)
print(path)
print('Spoken whitespace words:', sum(len(p.split()) for p in slide5 + slide6))
print('Paragraphs slide 5:', len(slide5), 'slide 6:', len(slide6))

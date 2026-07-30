# Prompt hướng dẫn xây dựng Prototype: Website AI Tư Vấn Tuyển Sinh "AI Thực Chiến"

## Bối cảnh & Mục tiêu

Xây dựng một **prototype HTML/CSS/JS chạy được ngay trên trình duyệt** (không cần backend) cho một website tư vấn tuyển sinh sử dụng AI chatbot, tên chương trình "AI Thực Chiến" của VinUni. Đây là bản demo để duyệt UI/UX, dữ liệu có thể là giả lập (mock), không cần kết nối API AI thật.

## Yêu cầu kỹ thuật

- Tạo **1 file `index.html`** duy nhất (inline CSS + JS), dùng **Tailwind CSS qua CDN** để dựng nhanh.
- Dùng JavaScript thuần (vanilla JS) để chuyển đổi giữa các trang/section mà **không reload trang** (single-page app, ẩn/hiện các `<div>` theo trang, hoặc dùng router đơn giản dựa trên hash `#`).
- Responsive cơ bản (ưu tiên desktop layout ~1280px, nhưng không vỡ layout ở màn hình nhỏ hơn).
- Icon: dùng [Lucide icons](https://lucide.dev) qua CDN hoặc emoji tương đương nếu cần.
- Không cần thư viện chat/backend thật — chatbot trả lời bằng **dữ liệu mock cứng trong JS** (xem phần "Logic chatbot mô phỏng" bên dưới).

## Design system

- **Màu chủ đạo:** tím-indigo (khoảng `#6D5FFD` / `#7C6EF2`) làm màu nhấn chính (nút, badge, icon active, chip).
- **Logo:** chữ "VinUni" màu đỏ đậm + icon check nhỏ, dòng dưới "AI THỰC CHIẾN" chữ đen đậm, có thể thêm tagline nhỏ màu xám "AI Admissions Assistant".
- **Nền:** trắng cho card/nội dung chính, xám rất nhạt (`#F7F8FA`) cho nền trang.
- **Card:** bo góc lớn (rounded-xl/2xl), border mỏng xám nhạt hoặc shadow nhẹ.
- **Card "tổng quan chương trình"** (trang Chương trình đào tạo): nền gradient tối (navy → xanh đậm), chữ trắng.
- **Font:** sans-serif hiện đại (Inter hoặc tương tự qua Google Fonts).
- **Nút chính (primary button):** nền tím, chữ trắng, bo tròn.
- **Chip/pill gợi ý câu hỏi:** nền xám nhạt, bo tròn full, hover đổi sang tím nhạt.

## Cấu trúc trang (6 trang, điều hướng qua sidebar/menu)

### 1. Trang Landing (Trang chủ)
- Header: logo trái, menu ngang (Trang chủ, Chương trình, Quyền lợi, Câu hỏi thường gặp, Liên hệ), nút "Đăng ký ngay" (tím) bên phải.
- Hero section: tiêu đề lớn "AI Tư vấn tuyển sinh" + "AI THỰC CHIẾN" (chữ tím nổi bật), đoạn mô tả ngắn, ô input lớn "Bạn muốn hỏi gì về chương trình AI Thực Chiến?" + nút gửi (icon paper-plane, tròn tím) — khi bấm gửi hoặc Enter sẽ **chuyển sang trang Chat** và tự động điền câu hỏi đó vào khung chat.
- 4 chip câu hỏi gợi ý bên dưới ô input (VD: "AI có thể đăng ký chương trình?", "Bài test đầu vào gồm những gì?", "Chương trình học kéo dài bao lâu?", "Quyền lợi của học viên là gì?") — bấm vào chip cũng chuyển sang trang Chat kèm câu hỏi đó.
- Minh hoạ: hình robot mascot (có thể dùng SVG đơn giản hoặc placeholder) bên phải, nền gradient tím nhạt với silhouette toà nhà.
- Dải thống kê 4 ô: "12 — Tuần đào tạo", "Miễn 100% — Học phí", "8 triệu VNĐ — Phụ cấp/tháng", "Cơ hội tuyển dụng — tại Vingroup" (mỗi ô có icon riêng).

### 2. Trang Chat (Trò chuyện) — trang trọng tâm
**Bố cục 3 cột:**

**Cột trái (sidebar điều hướng, cố định trên mọi trang):**
- Logo trên cùng.
- Menu: Trò chuyện, FAQ, Điều kiện tuyển sinh, Chương trình đào tạo, Quyền lợi, Lịch tuyển sinh, Hồ sơ & đăng ký, Cơ hội việc làm, Bài viết & Hỏi đáp, Liên hệ. Mục đang active có nền tím nhạt + chữ tím.
- Card quảng cáo nhỏ ở cuối sidebar: hình robot + text "AI TƯ VẤN TUYỂN SINH — Chương trình AI Thực Chiến Khoá Cơ bản".

**Cột giữa (khung chat):**
- Header khung chat: tên bot "AI Tư vấn tuyển sinh AI Thực Chiến" + chấm xanh "AI đang online", icon lịch sử hội thoại + menu 3 chấm bên phải.
- Vùng tin nhắn (scroll được):
  - Bong bóng chat của user: căn phải, nền tím nhạt, kèm giờ gửi.
  - Bong bóng chat của bot: căn trái, có avatar tròn (icon robot), nội dung format với heading nhỏ in đậm, emoji 🎯 cho mục "Điều kiện chính", danh sách bullet với icon ✅, và câu hỏi mở ở cuối để gợi ý tiếp tục hội thoại.
  - Dưới mỗi trả lời của bot: 2 icon feedback (thumbs up/down) + nút dropdown "Xem nguồn (n)".
  - Dưới đó: các chip câu hỏi liên quan (follow-up), bấm vào sẽ tự gửi câu hỏi đó.
- Ô nhập liệu cố định dưới cùng: input "Nhập câu hỏi của bạn..." + nút gửi tròn tím. Dòng disclaimer nhỏ bên dưới: "AI có thể trả lời sai. Vui lòng kiểm tra lại thông tin quan trọng."

**Cột phải (thông tin bổ trợ):**
- Card "Nguồn tham khảo": danh sách 4 nguồn (icon + tiêu đề + domain nhỏ màu xám), VD "Điều kiện tuyển sinh AI Thực Chiến K1 — vinuni.edu.vn".
- Card "Chủ đề phổ biến": danh sách các chủ đề có mũi tên chevron (Điều kiện & Đăng ký, Bài test đầu vào, Chương trình & Học tập, Học phí & Chăm sóc, Cơ hội nghề nghiệp) + nút "Xem tất cả chủ đề". Bấm vào 1 chủ đề sẽ gửi câu hỏi mẫu tương ứng vào chat.

### 3. Trang Chương trình đào tạo
- Breadcrumb: Trang chủ > Chương trình đào tạo.
- Card tổng quan (nền gradient tối): "Tổng quan chương trình AI Thực Chiến — Khoá cơ bản" + mô tả ngắn + badge "AI".
- Section "Lộ trình học tập": 2 card giai đoạn nối bằng mũi tên:
  - "3 TUẦN — NỀN TẢNG": Python cơ bản, Toán cho AI, Thống kê & Xác suất, Machine Learning cơ bản.
  - "9 TUẦN — THỰC CHIẾN": Làm việc theo nhóm, Dự án với doanh nghiệp, Mentor 1:1, Demo & Đánh giá.
- 3 mini-card bên dưới với icon: "Học cùng chuyên gia từ VinUni & doanh nghiệp", "Dự án thực tế giải quyết bài toán doanh nghiệp", "Công nghệ hiện đại: AI, Data, Cloud...".

### 4. Trang Điều kiện tuyển sinh
- Breadcrumb.
- Tiêu đề "Điều kiện chung" + minh hoạ nhân vật sinh viên bên phải.
- Danh sách điều kiện (icon + text): Tốt nghiệp đại học hoặc sắp tốt nghiệp, Mọi ngành học đều có thể đăng ký, Có tư duy logic đam mê công nghệ, Có kinh nghiệm lập trình/phân tích dữ liệu (không bắt buộc), Vượt qua bài kiểm tra đầu vào và vòng phỏng vấn.
- Section "Yêu cầu về kỹ năng (khuyến nghị)": các tag/pill (Python cơ bản, Tư duy giải quyết vấn đề, Tiếng Anh đọc hiểu, Làm việc nhóm).

### 5. Trang Lịch tuyển sinh
- Breadcrumb.
- Timeline dạng danh sách (icon lịch + ngày + mô tả): Mở đơn đăng ký 01/06/2024, Hạn đăng ký 30/07/2024, Kiểm tra đầu vào 10/08/2024, Phỏng vấn 17/08/2024, Thông báo kết quả 24/08/2024, Khai giảng 02/09/2024.
- Nút "Đăng ký ngay" (tím, full-width hoặc lớn) + link "Tài liệu hướng dẫn đăng ký".

### 6. Trang Quyền lợi học viên
- Breadcrumb.
- Tiêu đề "Học viên AI Thực Chiến nhận được".
- Grid 6 card quyền lợi (icon + tiêu đề ngắn): Miễn 100% học phí toàn khoá, Phụ cấp 8 triệu VNĐ/tháng, Học cùng chuyên gia & mentor 1:1, Dự án thực tế với doanh nghiệp lớn, Cơ hội tuyển dụng tại Vingroup, Cộng đồng học viên chất lượng cao.
- Banner CTA cuối trang: "Bạn đã sẵn sàng trở thành nhân tài AI?" + nút "Đăng ký ngay" + link "Tìm hiểu thêm về chương trình →".

## Logic chatbot mô phỏng (mock)

- Tạo 1 object/array trong JS chứa **3–5 cặp câu hỏi–trả lời mẫu** (dựa theo nội dung điều kiện tuyển sinh, chương trình học, quyền lợi...), mỗi câu trả lời có format Markdown-like (heading, bullet ✅) và danh sách câu hỏi gợi ý tiếp theo.
- Khi user gửi bất kỳ câu hỏi nào (gõ tay hoặc bấm chip):
  1. Hiện bong bóng chat user ngay lập tức.
  2. Hiện trạng thái "đang gõ..." (typing indicator) trong ~800ms–1.2s.
  3. Nếu câu hỏi khớp (fuzzy match theo từ khoá) với 1 mẫu trong data → hiện câu trả lời mẫu tương ứng.
  4. Nếu không khớp → trả về 1 câu trả lời mặc định lịch sự kèm gợi ý các chủ đề phổ biến.
- Không cần gọi API thật, toàn bộ là giả lập phía client.

## Ưu tiên khi triển khai

1. Làm đúng trang **Chat** trước tiên vì đây là trọng tâm sản phẩm (độ ưu tiên cao nhất).
2. Sau đó làm trang **Landing**.
3. Cuối cùng 4 trang nội dung tĩnh còn lại (Chương trình, Điều kiện, Lịch tuyển sinh, Quyền lợi) — có thể đơn giản hoá nếu thiếu thời gian, miễn giữ đúng bố cục sidebar + breadcrumb.
4. Đảm bảo **điều hướng giữa các trang mượt, sidebar luôn hiển thị đúng trạng thái active**.

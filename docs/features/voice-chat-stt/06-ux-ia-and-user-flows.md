# Thiết Kế Trải Nghiệm Người Dùng (UX) & Luồng Tương Tác
## Phân Hệ: Voice Input & STT | Tính Năng: `FEAT-006`

## 1. Kiến Trúc Thông Tin & Vị Trí Giao Diện (Information Architecture)
- **Nút Thu Âm (Voice Recording Button)**: Tọa lạc ngay bên cạnh ô nhập văn bản tại thanh [`MessageComposer`](file:///c:/Users/sv/Project/ChatJPT/ai-frontend/src/components/chat/MessageComposer.tsx).
- **Bộ Chọn Ngôn Ngữ Nói (Language Pill)**: Hiển thị ngay trên thanh trạng thái thu âm, cho phép người dùng chuyển nhanh giữa:
  - 🇻🇳 Tiếng Việt (`vi`)
  - 🇬🇧 Tiếng Anh (`en`)
  - 🇯🇵 Tiếng Nhật (`ja`)
  - 🌐 Tự động (`auto`)
- **Thanh Trạng Thái Thu Âm (Active Recording Bar - `UX-015`)**:
  - Khi bắt đầu nói, khung nhập liệu chuyển thành thanh ghi âm cao cấp chuẩn Anime Minimalist.
  - Sóng âm thời gian thực dao động nhịp nhàng theo biên độ giọng nói.
  - Đồng hồ đếm thời lượng `00:00 / 02:00` với cảnh báo đổi màu cam khi đạt mốc `01:45`.
  - Cụm nút bấm tiện ích: `Nút Hủy (Thùng rác đỏ)`, `Nút Tạm dừng/Tiếp tục`, `Nút Hoàn tất & Gửi`.

---

## 2. Giao Diện Tin Nhắn Giọng Nói Trong Khung Chat (`UX-016`)

```
┌────────────────────────────────────────────────────────┐
│  Học viên (User)                             10:30 AM  │
├────────────────────────────────────────────────────────┤
│  ▶  ───●────────────────────────────  0:04 / 0:04  🔊  │
│                                                        │
│  "すみません、この電車は新宿に行きますか"                │
│  (Ngôn ngữ phát hiện: Tiếng Nhật • Độ tin cậy: 98.5%) │
└────────────────────────────────────────────────────────┘
```

- **Phần tử 1: Trình phát âm thanh nhỏ gọn (Compact Audio Player)**:
  - Nút Play/Pause phản hồi ngay tức thì.
  - Thanh sóng âm/tiến trình (Scrub Bar) cho phép nhấp hoặc kéo để tua đoạn âm thanh.
  - Hiển thị thời lượng đếm ngược chính xác.
- **Phần tử 2: Khối văn bản chuyển đổi (Transcript Subtitle)**:
  - Hiển thị nội dung văn bản ngay dưới thanh phát âm thanh (`BR-050`).
  - Hỗ trợ nút sao chép (Copy) đoạn text nhanh vào clipboard.

---

## 3. Luồng Người Dùng Chi Tiết (User Interaction Flows)

### Luồng A: Thu âm gửi tin nhắn thành công
1. Người dùng bấm biểu tượng Micro 🎤.
2. Sóng âm nhảy đều theo tiếng nói, đếm giờ `00:03... 00:07`.
3. Người dùng bấm nút Send ➤.
4. Trạng thái hiển thị nhẹ *"Đang nhận diện giọng nói..."* (khoảng 0.8 giây).
5. Tin nhắn người dùng xuất hiện với Audio Player + Dòng chữ tiếng Nhật vừa nói.
6. Sensei AI-Chan bắt đầu stream lời giải đáp và phân tích ngữ pháp liên dòng.

### Luồng B: Nghe lại phát âm để sửa sai
1. Sau khi nhận được lời chữa của Sensei (chỉ ra lỗi phát âm trợ từ hoặc ngữ điệu), học viên bấm nút Play trên tin nhắn của mình để tự đối chiếu với giọng mẫu của Sensei.
2. Học viên thu âm lại một lần nữa để cải thiện phản xạ giao tiếp.


# UX Information Architecture & User Flows: Voice Management

## 1. Information Architecture (IA)
- **Sidebar Menu Navigation**:
  - `Luyện Kaiwa (Chat)` (`/chat`)
  - `Chỉ Dẫn Sensei (Prompts)` (`/prompts`)
  - `Quản Lý Giọng Nói (Voices)` (`/voices`) *(Mục Mới Thêm)*
  - `Quy Tắc Ngữ Pháp` (`/rules`)
  - `Tổng Quan Học Tập` (`/dashboard`)
  - `Cài Đặt Hệ Thống` (`/settings`)

---

## 2. Screen Layouts

### 2.1. Trang Quản Lý Giọng Nói (`/voices`)
- **Header Card**:
  - Tiêu đề: **Quản Lý Giọng Nói VoiceVox (Character Voice Management)**
  - Huy hiệu trạng thái Engine:
    - Xanh lá: `🟢 VoiceVox Engine Đang Hoạt Động (v0.14.4 - 15ms)`
    - Xám/Vàng: `🟡 VoiceVox Ngoại Tuyến (Chế độ Fallback / Web Speech khả dụng)`
  - Nút tải lại trạng thái / Nút thêm giọng tùy chỉnh.
- **Thanh Công Cụ Lọc & Tìm Kiếm**:
  - Ô tìm kiếm theo tên nhân vật (Fuzzy Search).
  - Chip lọc giới tính: Tất cả | Nữ | Nam | Khác.
  - Chip lọc phong cách: Tất cả | Normal | Sweet | Whisper | Joy | Angry.
- **Lưới Thẻ Nhân Vật (Voice Character Cards Grid)**:
  - Mỗi thẻ hiển thị Avatar nhân vật, huy hiệu giới tính, tên Kanji + Romaji.
  - Huy hiệu Speaker ID VoiceVox.
  - Nút **"Phát Âm Thử (Play Sample)"** với hoạt ảnh sóng âm khi đang phát.
  - Nút **"Tùy Chỉnh Âm Học (Tune)"** mở modal điều chỉnh thông số.

### 2.2. Modal Tùy Chỉnh Âm Học (Voice Tuning Modal)
- Thanh trượt điều chỉnh với hiển thị giá trị số thực thời:
  - **Tốc độ (Speed)**: `0.5x` đến `2.0x`.
  - **Cao độ (Pitch)**: `-0.15` đến `+0.15`.
  - **Luyến láy (Intonation)**: `0.0x` đến `2.0x`.
  - **Âm lượng (Volume)**: `0.0x` đến `2.0x`.
- Ô nhập câu thoại mẫu thử nghiệm.
- Nút "Nghe Thử Ngay" kiểm tra kết quả ngay trong modal trước khi lưu.

### 2.3. Tích Hợp Vào Cấu Hình Sensei (`/prompts`)
- Trong modal tạo/chỉnh sửa Sensei:
  - Trường **"Giọng Nói Nhân Vật (Voice)"**: Dropdown trực quan với hình đại diện, tên nhân vật và nút nghe thử nhanh bên cạnh.

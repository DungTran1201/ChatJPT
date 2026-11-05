# Các Trường Hợp Sử Dụng (Use Cases) & Tiêu Chí Nghiệm Thu
## Phân Hệ: Voice Input & STT | Tính Năng: `FEAT-006`

## 1. Danh Mục Use Case

### 1.1. `UC-021`: Thu âm giọng nói bằng Tiếng Việt, Tiếng Anh hoặc Tiếng Nhật và gửi tới AI
- **Tác nhân**: Học viên (`ACT-02`)
- **Luồng sự kiện chính (Main Flow)**:
  1. Học viên mở một cuộc trò chuyện trong ChatJPT.
  2. Học viên nhấp vào biểu tượng Micro tại thanh nhập liệu [`MessageComposer`](file:///c:/Users/sv/Project/ChatJPT/ai-frontend/src/components/chat/MessageComposer.tsx) (`FR-079`).
  3. Hệ thống kiểm tra quyền micro. Nếu chưa có, hệ thống hiển thị hộp thoại xin cấp quyền.
  4. Trình duyệt hiển thị thanh thu âm với sóng âm động (`UX-015`) và đồng hồ đếm thời gian.
  5. Học viên nói câu tiếng Nhật (ví dụ: *"すみません、この電車は新宿に行きますか"*), tiếng Việt hoặc tiếng Anh.
  6. Học viên nhấn nút "Dừng & Gửi" (hoặc tự động ngắt sau 120s - `BR-048`).
  7. Client gửi tệp âm thanh nén lên `POST /api/v1/chat/stt` (`OP-066`).
  8. Hệ thống Backend chuyển đổi âm thanh thành văn bản qua Whisper/Gemini STT Engine (`FR-080`).
  9. Tin nhắn của người dùng xuất hiện trên màn hình chat gồm cả thanh nghe lại âm thanh và đoạn chữ vừa nói (`FR-081`, `BR-050`).
  10. Trợ lý ảo AI-Chan tiếp nhận câu hỏi và stream câu trả lời kèm sửa lỗi phát âm/ngữ pháp (`FR-082`).

- **Luồng rẽ nhánh & Ngoại lệ (Alternative & Exception Flows)**:
  - *Luồng 3a (Bị từ chối quyền micro)*: Người dùng nhấn "Block" -> Hệ thống hiển thị thông báo hướng dẫn người dùng bật lại micro trong thanh địa chỉ của trình duyệt (`TC-064`).
  - *Luồng 6a (Người dùng hủy bỏ)*: Người dùng nhấn nút biểu tượng Thùng rác -> Toàn bộ dữ liệu thu âm bị hủy bỏ, thanh nhập liệu trở về trạng thái IDLE.
  - *Luồng 8a (Mất kết nối mạng / Lỗi máy chủ STT)*: Nếu backend không phản hồi, client sử dụng văn bản nháp từ Web Speech API hoặc thông báo người dùng cho phép thử lại (Retry) mà không làm mất file thu âm (`BR-049`, `TC-067`).

### 1.2. `UC-022`: Nghe lại bản ghi âm và đối chiếu phụ đề trong lịch sử hội thoại
- **Tác nhân**: Học viên (`ACT-02`)
- **Luồng sự kiện chính**:
  1. Học viên cuộn xem lại các tin nhắn cũ trong cuộc trò chuyện.
  2. Tại bất kỳ tin nhắn giọng nói nào trước đó, học viên nhấn nút Play trên trình phát âm thanh (`UX-016`).
  3. Hệ thống phát lại đúng giọng nói mà học viên đã ghi âm trước đó.
  4. Học viên đối chiếu câu phát âm thực tế của mình với văn bản chuyển đổi và phân tích của Sensei.

---

## 2. Tiêu Chí Nghiệm Thu (Acceptance Criteria)

- **`AC-060` (Tiếng Việt)**: Thu âm đoạn tiếng Việt độ dài 5-30 giây -> STT nhận diện đúng dấu thanh và ngữ cảnh tiếng Việt đạt độ chính xác >= 95%.
- **`AC-061` (Tiếng Nhật)**: Thu âm câu giao tiếp tiếng Nhật -> STT nhận diện đúng chữ Hán (Kanji), Kana và các trợ từ tiếng Nhật (は, が, を, に, で).
- **`AC-062` (Tiếng Anh)**: Thu âm câu tiếng Anh giao tiếp -> STT nhận diện đúng chính tả và ngắt câu hợp lý.
- **`AC-063` (Giao diện kép)**: Sau khi gửi, tin nhắn người dùng hiển thị đồng thời cả trình phát âm thanh và văn bản STT.
- **`AC-064` (Bảo mật tệp âm thanh)**: Tệp tải lên vượt quá 10MB bị từ chối với mã lỗi HTTP 413 (`SEC-021`).


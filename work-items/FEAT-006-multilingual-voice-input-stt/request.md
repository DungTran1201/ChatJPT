# Yêu Cầu Thay Đổi: Đầu Vào Giọng Nói Đa Ngữ (Vi/En/Ja) & Tích Hợp STT Cho ChatJPT

## 1. Thông Tin Yêu Cầu
- **Mã công việc**: `FEAT-006-multilingual-voice-input-stt`
- **Hệ thống**: Nền tảng ChatJPT (FastAPI Backend + Next.js Frontend)
- **Nhánh chức năng**: Quản lý Hội thoại & Chat Streaming (`CAP-CHAT-AI`, `CAP-CONV`)
- **Tác nhân chính**: Học viên tiếng Nhật (`ACT-001`), Trợ lý ảo AI-Chan / Virtual Sensei (`ACT-002`)

## 2. Mô Tả Nhu Cầu Người Dùng (User Story)
> **Là một** học viên đang luyện tập giao tiếp và học tiếng Nhật trên ChatJPT,  
> **Tôi muốn** có thể trực tiếp nói bằng tiếng Việt, tiếng Anh hoặc tiếng Nhật qua microphone thay vì chỉ gõ văn bản, và hệ thống tự động chuyển đổi giọng nói của tôi thành văn bản (Speech-to-Text),  
> **Để** tôi có thể tương tác phản xạ tự nhiên như trong các tình huống thực tế, đồng thời xem lại được cả bản ghi âm giọng nói lẫn văn bản vừa chuyển đổi ngay trên giao diện chat nhằm tự đánh giá phát âm và kiểm tra độ chính xác của câu nói.

## 3. Tiêu Chí Nghiệm Thu (Acceptance Criteria)
1. **Hỗ trợ 3 ngôn ngữ cốt lõi**: Nhận dạng và chuyển đổi giọng nói chính xác đối với Tiếng Việt (`vi`), Tiếng Anh (`en`) và Tiếng Nhật (`ja`).
2. **Hiển thị kép (Dual Display)**: Tin nhắn người dùng sau khi nói phải hiển thị đồng thời:
   - Trình phát âm thanh (Audio Player) cho phép nghe lại chính giọng nói vừa thu.
   - Nội dung văn bản chuyển đổi (Transcribed Text) để người dùng kiểm chứng.
3. **Đưa trực tiếp vào luồng AI**: Văn bản sau STT (hoặc âm thanh kèm ngữ cảnh) được chuyển trực tiếp vào mô hình LLM để sinh câu trả lời sư phạm kèm phân tích ngữ pháp.
4. **Phản hồi thời gian thực**: Trải nghiệm thu âm trực quan, có sóng âm (Waveform), đồng hồ bấm giờ, nút tạm dừng/hủy/gửi.


# Phạm Vi, Giả Định & Quyết Định Kiến Trúc: Voice Input & STT
## Mã Tính Năng: `FEAT-006` | Phân Hệ: Quản Lý Chat & Hội Thoại (`CAP-CHAT-AI`)

## 1. Phạm Vi Tính Năng (Feature Scope)
- **Trong phạm vi (In-Scope)**:
  - Cho phép người học sử dụng Microphone để thu âm giọng nói trực tiếp trên trình duyệt Web (Next.js 16).
  - Hỗ trợ chính xác 3 ngôn ngữ giao tiếp: Tiếng Việt (`vi`), Tiếng Anh (`en`), Tiếng Nhật (`ja`) (`FR-079`, `BR-047`).
  - Chuyển đổi giọng nói thành văn bản thông qua mô hình Speech-to-Text (STT) (`FR-080`).
  - Hiển thị song song bản ghi âm (Audio Player có thể nghe lại) và đoạn văn bản chuyển đổi trên bong bóng chat của người dùng (`FR-081`, `BR-050`).
  - Đưa trực tiếp văn bản đã chuyển đổi (hoặc âm thanh kèm ngữ cảnh) vào luồng suy luận của AI Sensei để nhận câu trả lời sư phạm liên dòng qua Server-Sent Events (`FR-082`).
- **Ngoài phạm vi (Out-of-Scope)**:
  - Dịch tự động từ tiếng Việt sang tiếng Nhật ở tầng client trước khi đưa vào LLM (việc dịch/hiểu thuộc trách nhiệm của mô hình LLM sư phạm).
  - Nhận diện giọng nói của nhiều người cùng lúc trong một phòng họp (Dự án tập trung vào 1 kèm 1 giữa Học viên và Sensei).

## 2. Phân Loại Sự Thật (Fact Classification)
- **FACT (Sự thật đã kiểm chứng)**:
  - Hệ thống ChatJPT hiện đã có sẵn module lưu trữ tệp đính kèm (`attachments`) và module tổng hợp giọng nói VOICEVOX (`voices`) nhưng chưa có chiều thu âm đầu vào và STT.
  - Trình duyệt hiện đại hỗ trợ Web Audio API và MediaRecorder API nén định dạng Opus trong container WebM với bitrate tối ưu.
- **ASSUMPTION (Giả định kỹ thuật)**:
  - Người dùng sử dụng thiết bị có microphone hoạt động bình thường và đồng ý cấp quyền truy cập khi được hỏi.
  - Tốc độ mạng của người học đủ để tải tệp âm thanh nén 24-32kbps (khoảng 300KB - 800KB cho 30 giây nói).
- **DECISION (Quyết định kiến trúc đã thông qua)**:
  - `ADR-008`: Lựa chọn kiến trúc lai (Hybrid STT): Sử dụng OpenAI Whisper / Groq Whisper / Faster-Whisper làm engine backend chính xác cao, đồng thời hỗ trợ Web Speech API client-side làm phương án dự phòng độ trễ thấp (`BR-049`).
  - Ràng buộc an ninh `SEC-021`: Giới hạn dung lượng tệp âm thanh tối đa 10MB và thời lượng tối đa 120 giây (`BR-048`).
- **OPEN QUESTION (Câu hỏi mở)**:
  - Có nên tích hợp thêm tính năng chấm điểm phát âm (Pronunciation Scoring) theo thang điểm JLPT trong tương lai hay không? (Đề xuất ghi nhận vào backlog phiên bản v3.1).


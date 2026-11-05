# Danh Mục Tính Năng & Ma Trận Truy Vết: Voice Input & STT
## Mã Tính Năng: `FEAT-006`

## 1. Danh Mục Yêu Cầu Chức Năng (Functional Requirements)
- **`FR-079`**: Multilingual Voice Input Audio Capture (vi, en, ja) — Cho phép thu âm giọng nói trực tiếp từ trình duyệt web hỗ trợ 3 ngôn ngữ tiếng Việt, tiếng Anh, tiếng Nhật.
- **`FR-080`**: Speech-to-Text (STT) Multilingual Transcription Pipeline — Pipeline chuyển đổi âm thanh giọng nói thành văn bản chuẩn xác với cơ chế tự động nhận diện hoặc chỉ định ngôn ngữ.
- **`FR-081`**: Synchronized Audio Playback & Real-time Transcript Message Bubble in Chat — Hiển thị đồng thời trình phát âm thanh thu nhỏ và đoạn văn bản chuyển đổi trên bong bóng tin nhắn của người dùng trong lịch sử chat.
- **`FR-082`**: Direct Multimodal and Transcribed Audio Prompt Dispatching to LLM Core — Điều phối văn bản và âm thanh đầu vào tới mô hình LLM để kích hoạt luồng trả lời sư phạm kèm chấm chữa ngữ pháp.

## 2. Quy Tắc Nghiệp Vụ (Business Rules)
- **`BR-047`**: Multilingual Spoken Language Scope — Giới hạn phạm vi nhận dạng giọng nói chuẩn hóa trong 3 ngôn ngữ: Tiếng Việt, Tiếng Anh, Tiếng Nhật.
- **`BR-048`**: Audio Message Quota & Duration Constraints — Thời lượng tối đa 120 giây và dung lượng tối đa 10MB cho mỗi lượt thu âm giọng nói.
- **`BR-049`**: STT Provider Failover & Local Web Speech API Fallback — Tự động chuyển đổi hoặc sử dụng bản nháp cục bộ khi dịch vụ STT máy chủ gặp sự cố mạng.
- **`BR-050`**: User Audio Verification & Playback Invariant — Luôn hiển thị thanh phát âm thanh để người dùng có thể nghe lại chính phát âm của mình bất kỳ lúc nào.

## 3. Yêu Cầu Phi Chức Năng & Bảo Mật (NFR & SEC)
- **`NFR-021`**: Độ trễ xử lý STT máy chủ phải nhỏ hơn 1.5 giây đối với đoạn thu âm dưới 15 giây.
- **`NFR-022`**: Tối ưu nén âm thanh WebM/Opus đạt dung lượng dưới 400KB cho 30 giây thu âm.
- **`NFR-023`**: Quyền riêng tư âm thanh: Âm thanh thu âm được bảo vệ, cách ly theo phiên tài khoản người dùng.
- **`SEC-021`**: Xác thực Magic Bytes định dạng âm thanh (chặn tệp thực thi giả mạo đuôi audio).
- **`SEC-022`**: Phân quyền truy cập tệp ghi âm, chống lỗ hổng tham chiếu trực tiếp đối tượng không an toàn (IDOR).
- **`UX-015`**: Giao diện thu âm trực quan kèm thanh sóng âm động (Waveform Visualizer) trong MessageComposer.
- **`UX-016`**: Giao diện phát lại âm thanh dạng thanh nhỏ gọn (Audio Player Bar) tích hợp trong bong bóng tin nhắn.

## 4. Ma Trận Truy Vết Chéo (Traceability Matrix)

| Yêu Cầu | Quy Tắc | Bảo Mật / NFR | API Endpoint | Biểu Đồ Liên Quan | Ca Kiểm Thử |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-079` | `BR-047`, `BR-048` | `NFR-021`, `UX-015` | `OP-066` | `SEQ-018`, `STATE-VOICE-INPUT` | `TC-060`, `TC-064`, `TC-065` |
| `FR-080` | `BR-047`, `BR-049` | `NFR-021`, `SEC-021` | `OP-066` | `SEQ-018`, `SWIM-VOICE-CHAT` | `TC-061`, `TC-062`, `TC-067` |
| `FR-081` | `BR-050` | `NFR-022`, `UX-016` | `OP-067` | `SEQ-018`, `COMP-007` | `TC-063` |
| `FR-082` | `BR-048` | `NFR-023`, `SEC-022` | `OP-009`, `OP-067` | `SEQ-018`, `PROC-VOICE-CHAT` | `TC-060`, `TC-061`, `TC-068` |


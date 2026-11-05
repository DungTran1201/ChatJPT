# Câu Hỏi Mở & Báo Cáo Sẵn Sàng Triển Khai (Readiness Report)
## Phân Hệ: Voice Input & STT | Tính Năng: `FEAT-006`

## 1. Danh Mục Câu Hỏi Mở & Hướng Xử Lý

| STT | Vấn Đề Thảo Luận | Tác Động | Quyết Định / Hướng Xử Lý |
| :--- | :--- | :--- | :--- |
| 1 | Có nên cho phép người học sửa thủ công văn bản (Transcript) trước khi gửi vào LLM không? | Trải nghiệm người dùng | **DECISION**: Cho phép. Sau khi STT hoàn tất, nếu người học thấy nhận diện chưa đúng một từ, họ có thể nhấp vào ô văn bản để sửa nhanh trước khi bấm gửi. |
| 2 | Khi chạy offline (không có internet), tính năng giọng nói xử lý thế nào? | Độ sẵn sàng hệ thống | **DECISION**: Tận dụng Web Speech API có sẵn trên trình duyệt (Chrome/Edge hỗ trợ một phần offline), hoặc thông báo người dùng chuyển sang chế độ gõ phím khi offline. |
| 3 | Tỷ lệ nén và bitrate khuyến nghị cho âm thanh? | Băng thông và tải máy chủ | **DECISION**: Cấu hình MediaRecorder ở mức 24kbps - 32kbps Mono 16kHz, đủ chuẩn để mô hình Whisper đạt độ chính xác cao nhất mà tệp chỉ nặng khoảng 100KB - 300KB. |

---

## 2. Báo Cáo Sẵn Sàng Triển Khai (Implementation Readiness)

- **Đặc tả yêu cầu**: Đã hoàn thành 100% (`FR-079..FR-082`, `BR-047..BR-050`, `NFR-021..NFR-023`).
- **Mô hình chuẩn hóa (Models)**: Đã tích hợp đầy đủ vào `requirements.yaml`, `api.yaml`, `domain.yaml`, `voice-input-state.yaml`, `interactions.yaml`, `security-threat-model.yaml`, `testing.yaml`, `ux.yaml`.
- **Thiết kế biểu đồ (Diagrams)**: Đầy đủ 5 loại biểu đồ tiêu chuẩn: Sequence (`SEQ-018`), BPMN (`PROC-VOICE-CHAT`), State (`STATE-VOICE-INPUT`), Component (`COMP-007`), Swimlane (`SWIM-VOICE-CHAT`).
- **Kiến trúc an ninh**: Đã xác lập các biện pháp chặn mã độc (`SEC-021`), chống cạn kiệt tài nguyên (`BR-048`) và bảo vệ chống IDOR (`SEC-022`).
- **Kế hoạch kiểm thử**: Đã lập 9 ca kiểm thử chuẩn hóa từ `TC-060` đến `TC-068`.

=> **Kết luận**: Tính năng đạt tiêu chuẩn **READY FOR IMPLEMENTATION (Sẵn sàng triển khai mã nguồn)**.


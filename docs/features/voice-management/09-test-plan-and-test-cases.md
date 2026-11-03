# Test Plan & Test Cases: Voice Management

## 1. Test Matrix
| Mã Test Case | Mục Tiêu Kiểm Thử | Yêu Cầu Liên Quan | Loại Kiểm Thử |
| :--- | :--- | :--- | :--- |
| `TC-VOICE-001` | Lấy danh mục giọng đọc và lọc theo giới tính/phong cách | `FR-069` | Backend API / Unit |
| `TC-VOICE-002` | Kiểm tra ràng buộc dải tham số âm học (`BR-040`) | `FR-070`, `BR-040` | Validation / Unit |
| `TC-VOICE-003` | Kiểm tra endpoint trạng thái VoiceVox engine | `FR-071` | API Integration |
| `TC-VOICE-004` | Gán giọng đọc cho Sensei và bảo toàn toàn vẹn dữ liệu | `FR-072`, `BR-041` | Integration |
| `TC-VOICE-005` | Khả năng suy giảm chất lượng linh hoạt khi engine ngoại tuyến | `FR-071`, `BR-042` | Resilience |
| `TC-VOICE-006` | Kiểm tra cơ chế vệ sinh dữ liệu và chống injection (`SEC-015`) | `SEC-015` | Security |
| `TC-VOICE-007` | Phát âm thanh hội thoại trong Chat bằng giọng Sensei | `FR-073` | E2E Frontend |

---

## 2. Chi Tiết Các Kịch Bản Kiểm Thử

### `TC-VOICE-001`: Lấy danh mục giọng đọc VoiceVox
- **Input**: Gửi `GET /api/v1/voices?gender=female`.
- **Expected Result**: Trả về danh sách chứa các giọng nữ (Kasukabe Tsumugi, Shikoku Metan, Kyushu Sora, v.v.), mã HTTP 200, trường `total >= 1`.

### `TC-VOICE-002`: Kiểm tra ràng buộc dải tham số âm học
- **Input**: Gửi `PUT /api/v1/voices/{id}` với `speed_scale = 5.0` (vượt ngưỡng 2.0).
- **Expected Result**: Backend trả về mã lỗi 422 Unprocessable Entity kèm thông báo trường `speed_scale` vượt quá giá trị cho phép.

### `TC-VOICE-004`: Gán giọng đọc cho Sensei
- **Input**: Gửi `PUT /api/v1/system-prompts/{id}` với `voice_id = "voice_kasukabe_tsumugi"`.
- **Expected Result**: Cập nhật thành công, khi `GET` thông tin Sensei trả về trường `voice_id` và thông tin chi tiết của giọng tương ứng.

### `TC-VOICE-005`: Fallback khi VoiceVox engine ngoại tuyến
- **Input**: Gửi `POST /api/v1/voices/{id}/synthesize` khi engine không hoạt động.
- **Expected Result**: Hệ thống không trả về lỗi 500; trả về âm thanh mẫu dự phòng WAV chuẩn với HTTP 200.

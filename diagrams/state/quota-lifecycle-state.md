# Sơ Đồ Máy Trạng Thái: Vòng Đời Hạn Ngạch Quota (Quota Lifecycle State Machine)
## Dự Án: Website Hỗ Trợ Học Tiếng Nhật & AI Virtual Sensei (ChatJPT)

---

| Thông Tin Sơ Đồ | Chi Tiết |
| :--- | :--- |
| **Mã Sơ Đồ** | `DIAG-STATE-005` |
| **Mã Trạng Thái** | `STATE-005` |
| **Nguồn Sự Thật Thượng Nguồn** | [docs/09-behavior/state-machines.md](../../docs/09-behavior/state-machines.md), [docs/07-domain/entities.md](../../docs/07-domain/entities.md) (`UserQuota`), [docs/02-requirements/business-rules.md](../../docs/02-requirements/business-rules.md) (`BR-020`) |
| **Mục Đích** | Mô tả các trạng thái định mức và các biến cố chuyển đổi hạn ngạch tiêu thụ token hàng ngày của người dùng, từ ngưỡng an toàn, ngưỡng cảnh báo 80% tới trạng thái chặn 100% (HTTP 429) |

---

## 1. STATE-005: Biểu Đồ Trạng Thái Hạn Ngạch Quota Người Dùng

```mermaid
stateDiagram-v2
    [*] --> NORMAL_TIER: Khởi tạo hạn ngạch nguyên tử (daily_tokens_used = 0)

    state NORMAL_TIER {
        [*] --> COMFORTABLE
        COMFORTABLE: An Toàn (Used < 80% limit)
        WARNING_80: Cảnh Báo (80% <= Used < 100%)

        COMFORTABLE --> WARNING_80: Tiêu thụ token chạm mốc 80% limit (BR-020: Amber Alert)
        WARNING_80 --> COMFORTABLE: 00:00 UTC Tự động reset hạn ngạch ngày mới
    }

    NORMAL_TIER --> EXHAUSTED: Tiêu thụ đạt 100% limit (BR-020: Throttling kích hoạt)

    state EXHAUSTED {
        [*] --> LOCKED_429
        LOCKED_429: Chặn gọi API LLM (HTTP 429 Too Many Requests)
        RETRY_WAIT: Chờ chu kỳ làm mới 00:00 UTC (Header Retry-After)

        LOCKED_429 --> RETRY_WAIT: Trả về HTTP 429 kèm Retry-After
        RETRY_WAIT --> LOCKED_429: Người dùng tiếp tục gửi yêu cầu trước thời điểm reset
    }

    EXHAUSTED --> NORMAL_TIER: 00:00 UTC Tự động reset daily_tokens_used = 0
    EXHAUSTED --> NORMAL_TIER: Quản trị viên nâng hạn ngạch (Admin Top-up)

    note right of WARNING_80
        Banner cảnh báo màu cam xuất hiện trên Dashboard (/dashboard)
        Yêu cầu API vẫn được thực thi bình thường
    end note

    note right of EXHAUSTED
        Mọi yêu cầu gọi Chat/Completion tiếp theo bị chặn với HTTP 429
        Header Retry-After kèm số giây tới 00:00 UTC
    end note
```

---

## 2. Bảng Thuyết Minh Chuyển Đổi Trạng Thái Hạn Ngạch (State Transition Table)

| Trạng Thái Ban Đầu | Biến Cố Kích Hoạt (Event) | Điều Kiện Thẩm Định (Guard) | Trạng Thái Đích | Hành Động Kèm Theo (Action) |
| :--- | :--- | :--- | :--- | :--- |
| `[*]` | Lần đầu gọi API / Đăng ký | Chưa có bản ghi `user_quotas` | `COMFORTABLE` | `INSERT OR IGNORE` bản ghi `user_quotas` (`daily_token_limit = 100,000`, `daily_tokens_used = 0`). |
| `COMFORTABLE` | Hoàn thành yêu cầu Chat AI | `daily_tokens_used >= 80% * daily_token_limit` | `WARNING_80` | Đánh dấu `warning_80 = true`, phát sự kiện SSE lên Dashboard. |
| `WARNING_80` | Hoàn thành yêu cầu Chat AI | `daily_tokens_used + estimated > daily_token_limit` | `EXHAUSTED` | Chặn mọi yêu cầu LLM tiếp theo với `HTTP 429` (`DAILY_QUOTA_EXCEEDED`). |
| `LOCKED_429` | Yêu cầu bị từ chối | `now() < reset_at` | `RETRY_WAIT` | Trả về `HTTP 429` kèm header `Retry-After`. |
| `WARNING_80` / `EXHAUSTED` | Chạm mốc 00:00 UTC hàng ngày | `now() >= reset_at` | `COMFORTABLE` | `TelemetryRepository` tự động đặt lại `daily_tokens_used = 0` trong giao dịch nguyên tử. |

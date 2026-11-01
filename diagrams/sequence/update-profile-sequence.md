# Sơ Đồ Tuần Tự: Cập Nhật Hồ Sơ & Tùy Chọn Cá Nhân (Profile Update Sequence)
## Dự Án: Website Hỗ Trợ Học Tiếng Nhật & AI Virtual Sensei (ChatJPT)

---

| Thông Tin Sơ Đồ | Chi Tiết |
| :--- | :--- |
| **Mã Sơ Đồ** | `DIAG-SEQ-006` |
| **Mã Kịch Bản** | `SEQ-006` |
| **Nguồn Sự Thật Thượng Nguồn** | [docs/09-behavior/sequence-diagrams.md](file:///c:/Users/PC/Project/ChatJPT/docs/09-behavior/sequence-diagrams.md), [docs/02-requirements/functional-requirements.md](file:///c:/Users/PC/Project/ChatJPT/docs/02-requirements/functional-requirements.md) (`FR-016`, `FR-017`, `FR-020`) |
| **Mục Đích** | Mô tả trình tự cập nhật các thông tin cá nhân thường (Họ tên, username slug, bio, avatar và cài đặt theme/language) |

---

## 1. Biểu Đồ Tuần Tự SEQ-006: Cập Nhật Hồ Sơ & Cài Đặt

```mermaid
sequenceDiagram
    autonumber
    actor User as ACT-02: User
    participant UI as Next.js Client
    participant Auth as Auth Middleware
    participant API as User Router
    participant DB as SQLite DB

    User->>UI: Thay đổi Họ tên, Username, Bio, Số điện thoại, Độ tuổi, Nghề nghiệp, Sở thích, Cấp độ tiếng Nhật, Mục tiêu
    User->>UI: Nhấn [Lưu thay đổi]
    UI->>UI: Regex validate Username slug (3-30 ký tự [a-z0-9_-])
    UI->>Auth: PATCH /api/v1/users/me/profile (Payload JSON)
    
    Auth->>Auth: Xác thực Token -> Lấy user_id
    Auth->>API: Chuyển tiếp request

    opt Có thay đổi Username
        API->>DB: SELECT id FROM users WHERE username = :new_username COLLATE NOCASE AND id != :user_id
        DB-->>API: Kết quả kiểm tra
        alt Username ĐÃ TỒN TẠI
            API-->>UI: HTTP 409 Conflict ("Username đã có người sử dụng")
            UI-->>User: Cảnh báo đỏ tại ô Username
        end
    end

    API->>DB: UPDATE users SET full_name = :name, username = :user, bio = :bio, phone_number = :phone, age = :age, occupation = :occ, interests = :int, japanese_level = :lvl, learning_goal = :goal, updated_at = CURRENT_TIMESTAMP WHERE id = :user_id
    DB-->>API: Cập nhật thành công
    API-->>UI: HTTP 200 OK (UserProfile mới)
    UI->>UI: Cập nhật thông tin Header / Sidebar
    UI-->>User: Thông báo Toast: "Cập nhật hồ sơ thành công"

    %% Nhánh Tùy Chỉnh Giao Diện & Cá Nhân Hóa (FR-020, UC-015, OP-028)
    Note over User, DB: Tùy Chỉnh Giao Diện (Theme, Wallpaper, Dimming, Opacity, Blur, RGB Accent, Font Size, Language vi/en/ja)
    User->>UI: Chọn Theme (Dark/Light frosted glass), Kéo dải màu RGB (#ff007f), Tải nền, Chỉnh Dim (35%), Opacity (85%), Blur (14px), Đổi ngôn ngữ (ja)
    UI->>UI: Phản hồi thời gian thực qua CSS Variables (--accent, --bg-base, --bg-surface, --app-backdrop-blur) & React AppContext i18n
    UI->>Auth: PATCH /api/v1/users/me/preferences (Payload JSON)
    Auth->>API: Xác thực phiên người dùng & giải mã token
    API->>API: Validate ràng buộc miền (20<=opacity<=100, 0<=blur<=40, 0<=dim<=100, accent hex/preset, lang in vi/en/ja)
    API->>DB: UPDATE users SET custom_bg_url = :bg, bg_opacity = :op, bg_blur = :blur, bg_dim = :dim, accent_color = :acc, ui_font_size = :fs, language_preference = :lang WHERE id = :user_id
    DB-->>API: Cập nhật cấu hình thành công
    API-->>UI: HTTP 200 OK (Preferences JSON)
    UI->>UI: Đồng bộ lại AppContext & Toast thông báo thành công đa ngôn ngữ
```

---

## 2. Thuyết Minh Tương Tác Trực Quan

- **Cải thiện trải nghiệm (Zero-latency UI)**: Khi người dùng đổi theme, giao diện Next.js lập tức kích hoạt hoán đổi theme thông qua CSS class mà không đợi server phản hồi, mang lại cảm giác mượt mà tức thì. Request lên API chạy ngầm để lưu cấu hình bền vững cho các phiên sau.

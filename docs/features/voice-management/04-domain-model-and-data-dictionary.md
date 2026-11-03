# Domain Model & Data Dictionary: Voice Management

## 1. Domain Entities & Relationships
- **Entity Voice**: Đại diện cho một hồ sơ giọng đọc của nhân vật VoiceVox, bao gồm định danh speaker, tên hiển thị, phong cách và các tham số điều chế âm học.
- **Entity SystemPrompt (Sensei Persona)**: Mở rộng trường `voice_id` (FK -> `Voice.id`) để liên kết một Sensei với một nhân vật giọng đọc cụ thể.

```
+-----------------------------------+               +----------------------------------+
|           SystemPrompt            |               |              Voice               |
+-----------------------------------+               +----------------------------------+
| id: string (PK)                   |               | id: string (PK)                  |
| name: string                      |               | name: string                     |
| japanese_level: enum              |  N         1  | character_name: string           |
| voice_id: string (FK)  ----------+--------------->| speaker_id: integer              |
| catchphrase: string               |               | style_name: string               |
| avatar_url: string                |               | gender: enum(female,male,other)  |
| ...                               |               | speed_scale: float               |
+-----------------+-----------------+               | pitch_scale: float               |
                  |                                 | intonation_scale: float          |
                  | 1                               | volume_scale: float              |
                  |                                 | sample_text: string              |
                  | N                               | status: enum(ACTIVE,INACTIVE)    |
+-----------------v-----------------+               +-----------------+----------------+
|              Message              |                                 | 1
+-----------------------------------+                                 |
| id: UUID (PK)                     |                                 |
| conversation_id: UUID (FK)        |                                 |
| role: USER | ASSISTANT            |                                 |
| content: text                     |                                 |
| sensei_id: string (FK)            |                                 |
| voice_id: string (FK)  <----------+---------------------------------+ N
+-----------------------------------+
```

---

## 2. Data Dictionary: Bảng `voices`

| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Giá Trị Mặc Định | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(50)` | `PRIMARY KEY` | Không | Mã định danh duy nhất (e.g. `voice_kasukabe_tsumugi`) |
| `name` | `VARCHAR(100)` | `NOT NULL` | Không | Tên hiển thị (e.g. `Kasukabe Tsumugi (Normal)`) |
| `character_name` | `VARCHAR(100)` | `NOT NULL` | Không | Tên nhân vật gốc (e.g. `春日部つむぎ`) |
| `speaker_id` | `INTEGER` | `NOT NULL, INDEX` | Không | Mã Speaker ID của VoiceVox Engine |
| `style_name` | `VARCHAR(50)` | `NULLABLE` | `'Normal'` | Phong cách phát âm (Normal, Sweet, Whisper, v.v.) |
| `gender` | `VARCHAR(20)` | `CHECK(female, male, other)` | `'female'` | Giới tính nhân vật |
| `description` | `TEXT` | `NULLABLE` | `NULL` | Mô tả tính cách và đặc tính giọng đọc |
| `speed_scale` | `REAL` | `0.5 <= val <= 2.0` | `1.0` | Hệ số tốc độ phát âm (`BR-040`) |
| `pitch_scale` | `REAL` | `-0.15 <= val <= 0.15`| `0.0` | Hệ số cao độ phát âm (`BR-040`) |
| `intonation_scale` | `REAL` | `0.0 <= val <= 2.0` | `1.0` | Hệ số luyến láy / nhấn nhá (`BR-040`) |
| `volume_scale` | `REAL` | `0.0 <= val <= 2.0` | `1.0` | Hệ số âm lượng phát âm (`BR-040`) |
| `sample_text` | `VARCHAR(255)`| `NULLABLE` | `こんにちは！...` | Câu thoại mẫu nghe thử |
| `avatar_url` | `VARCHAR(500)`| `NULLABLE` | `NULL` | Đường dẫn ảnh chân dung nhân vật |
| `status` | `VARCHAR(20)` | `CHECK(ACTIVE, INACTIVE)` | `'ACTIVE'` | Trạng thái kích hoạt của giọng |
| `is_system_preset`| `BOOLEAN` | `DEFAULT 0` | `0` | Cờ bảo vệ giọng mẫu hệ thống |
| `user_id` | `VARCHAR(36)` | `NULLABLE` | `'system'` | Người sở hữu bản ghi |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Hiện tại | Thời điểm tạo |
| `updated_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Hiện tại | Thời điểm cập nhật |


---

## 3. Data Dictionary: Bảng messages (Mở rộng cho Voice TTS)

| Tên Cột | Kiểu Dữ Liệu | Ràng Buộc | Giá Trị Mặc Định | Ý Nghĩa Nghiệp Vụ |
| :--- | :--- | :--- | :--- | :--- |
| sensei_id | VARCHAR(36) | NULLABLE, INDEX | NULL | ID của Sensei tham gia hội thoại (FK -> system_prompts.id) |
| oice_id | VARCHAR(50) | NULLABLE, INDEX | NULL | ID giọng nói VoiceVox được gán cho lượt trả lời này (FK -> oices.id) |

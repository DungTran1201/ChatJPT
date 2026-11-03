# Domain Model & Data Dictionary: Exam Management

## 1. Sơ Đồ Thực Thể Domain (Entity Relationships)

```
+-----------------------------------+               +-----------------------------------+
|               Exam                | 1           N |           ExamQuestion            |
+-----------------------------------+---------------+-----------------------------------+
| id: UUID (PK)                     |               | id: UUID (PK)                     |
| title: string                     |               | exam_id: UUID (FK -> Exam.id)     |
| description: text                 |               | section: enum(GOI,BUNPOU,DOKKAI)  |
| level: enum(N5..N1,KAIWA,GENERAL) |               | question_number: integer          |
| category: string                  |               | question_text: text               |
| year: integer                     |               | furigana_text: text               |
| duration_minutes: integer         |               | option_1..4: text                 |
| total_questions: integer          |               | correct_option: integer (1..4)    |
| passing_score: integer            |               | explanation: text                 |
| max_score: integer                |               +-----------------------------------+
| drive_folder_url: string (HTTPS)  |
| status: enum(ACTIVE,DRAFT)        |               +-----------------------------------+
| is_system_preset: boolean         |               |         ReferenceMaterial         |
+-----------------------------------+               +-----------------------------------+
                                                    | id: UUID (PK)                     |
                                                    | title: string                     |
                                                    | category: enum(JLPT_N5..N1,KAIWA) |
                                                    | level: string                     |
                                                    | source_type: enum(GOOGLE_DRIVE..) |
                                                    | external_url: string (HTTPS)      |
                                                    | author: string                    |
                                                    | tags: string                      |
                                                    | is_pinned: boolean                |
                                                    | is_system_preset: boolean         |
                                                    +-----------------------------------+
```

---

## 2. Từ Điển Dữ Liệu (Data Dictionary)

### Bảng `exams`
| Cột | Kiểu | Ràng Buộc | Ý Nghĩa |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | `PRIMARY KEY` | Định danh duy nhất đề thi |
| `title` | `VARCHAR(255)` | `NOT NULL` | Tên đề thi |
| `description` | `TEXT` | `NULLABLE` | Mô tả đề thi |
| `level` | `VARCHAR(20)` | `CHECK(N5..N1, KAIWA, GENERAL)` | Cấp độ tiếng Nhật |
| `category` | `VARCHAR(50)` | `DEFAULT 'JLPT_FULL'` | Thể loại bài thi |
| `year` | `INTEGER` | `NULLABLE` | Năm khảo thí |
| `duration_minutes` | `INTEGER` | `DEFAULT 60` | Thời lượng làm bài |
| `total_questions` | `INTEGER` | `DEFAULT 0` | Số câu hỏi |
| `passing_score` | `INTEGER` | `DEFAULT 90` | Điểm đỗ |
| `max_score` | `INTEGER` | `DEFAULT 180` | Điểm tối đa |
| `drive_folder_url`| `VARCHAR(1000)`| `NULLABLE` | Đường dẫn Google Drive |
| `status` | `VARCHAR(20)` | `CHECK(ACTIVE, DRAFT, ARCHIVED)` | Trạng thái đề thi |
| `is_system_preset`| `BOOLEAN` | `DEFAULT 1` | Đề thi mẫu hệ thống |
| `user_id` | `VARCHAR(36)` | `DEFAULT 'system'` | Người sở hữu |

### Bảng `exam_questions`
| Cột | Kiểu | Ràng Buộc | Ý Nghĩa |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | `PRIMARY KEY` | Định danh câu hỏi |
| `exam_id` | `VARCHAR(36)` | `FK -> exams.id ON DELETE CASCADE`| Khóa ngoại tới đề thi |
| `section` | `VARCHAR(50)` | `NOT NULL` | Phân môn (`GOI`, `BUNPOU`, v.v.) |
| `question_number` | `INTEGER` | `NOT NULL` | Số thứ tự câu hỏi |
| `question_text` | `TEXT` | `NOT NULL` | Nội dung câu hỏi tiếng Nhật |
| `furigana_text` | `TEXT` | `NULLABLE` | Câu hỏi có Furigana |
| `option_1`..`4` | `TEXT` | `NOT NULL` | 4 phương án lựa chọn |
| `correct_option` | `INTEGER` | `CHECK(1 <= val <= 4)` | Phương án đúng |
| `explanation` | `TEXT` | `NULLABLE` | Lời giải thích tiếng Việt |

### Bảng `reference_materials`
| Cột | Kiểu | Ràng Buộc | Ý Nghĩa |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | `PRIMARY KEY` | Định danh tài liệu |
| `title` | `VARCHAR(255)` | `NOT NULL` | Tên tài liệu |
| `description` | `TEXT` | `NULLABLE` | Mô tả tài liệu |
| `category` | `VARCHAR(50)` | `CHECK(JLPT_N5..N1, KAIWA, GRAMMAR_GUIDE, VOCABULARY_DICT)` | Chuyên mục tài liệu |
| `level` | `VARCHAR(20)` | `DEFAULT 'ALL'` | Cấp độ (`N5`..`N1`, `ALL`) |
| `source_type` | `VARCHAR(50)` | `DEFAULT 'GOOGLE_DRIVE'` | Loại nguồn tài liệu |
| `external_url` | `VARCHAR(1000)`| `NOT NULL` | Đường dẫn liên kết |
| `author` | `VARCHAR(100)` | `NULLABLE` | Tác giả / Nguồn tài liệu |
| `file_type` | `VARCHAR(20)` | `DEFAULT 'folder'` | Định dạng tệp |
| `tags` | `VARCHAR(255)` | `NULLABLE` | Thẻ tìm kiếm |
| `is_pinned` | `BOOLEAN` | `DEFAULT 0` | Đánh dấu ghim |
| `is_system_preset`| `BOOLEAN` | `DEFAULT 1` | Tài liệu mẫu hệ thống |

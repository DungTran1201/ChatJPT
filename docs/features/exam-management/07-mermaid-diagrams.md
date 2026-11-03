# Mermaid Diagrams: Exam Management Architecture & Flows

## 1. Sequence Diagram: Luồng Khám Phá & Thi Thử Trực Tuyến (`SEQ-016`)

```mermaid
sequenceDiagram
    autonumber
    actor Learner as Người Học (Learner)
    participant UI as Exam Page (/exams)
    participant API as Exam Router (/api/v1/exams)
    participant DB as SQLite app.db (exams, questions)

    Learner->>UI: Truy cập /exams (Chọn cấp độ N5)
    UI->>API: GET /api/v1/exams?level=N5
    API->>DB: SELECT * FROM exams WHERE level = 'N5'
    DB-->>API: Trả về danh sách bộ đề N5
    API-->>UI: 200 OK (Danh sách đề thi)
    UI->>Learner: Hiển thị Exam Cards kèm Drive Link

    Learner->>UI: Nhấn "Làm Bài Thi Thử" trên đề thi
    UI->>API: GET /api/v1/exams/{id}
    API->>DB: SELECT * FROM exam_questions WHERE exam_id = {id}
    DB-->>API: Danh sách câu hỏi trắc nghiệm
    API-->>UI: 200 OK (Chi tiết đề & câu hỏi)
    UI->>Learner: Mở Modal thi thử trực tuyến (Bắt đầu đếm ngược)

    Learner->>UI: Chọn đáp án và nhấn "Nộp Bài"
    UI->>API: POST /api/v1/exams/{id}/submit {answers}
    API->>DB: Đối chiếu đáp án đúng từ DB
    API->>API: Tính tổng điểm và đánh giá Đạt/Không đạt
    API-->>UI: 200 OK (Kết quả, tỷ lệ đúng & lời giải thích chi tiết)
    UI->>Learner: Hiển thị bảng tổng kết điểm số kèm phân tích sư phạm
```

---

## 2. Component Diagram: Cấu Trúc Thành Phần Hệ Thống (`COMP-006`)

```mermaid
graph TD
    subgraph Frontend["Frontend Layer (ai-frontend)"]
        EP["Exams Page (/exams)"]
        ET["Exam Bank Tab"]
        MT["Reference Materials Tab"]
        EM["Exam Runner Modal"]
        ES["examService.ts"]
        SB["Sidebar Navigation Item"]
    end

    subgraph Backend["Backend Layer (ai-backend)"]
        ER["exams_router (/api/v1/exams)"]
        SC["Exam Scoring Engine"]
        SG["Sanitization & Guard"]
    end

    subgraph Storage["Database & External Resources"]
        DB[("SQLite app.db (exams, exam_questions, reference_materials)")]
        GD["Google Drive Folders (N5..N1, Kaiwa)"]
        TK["Tae Kim Japanese Grammar Guide"]
    end

    SB --> EP
    EP --> ET
    EP --> MT
    ET --> EM
    ET --> ES
    MT --> ES
    EM --> ES
    ES --> ER
    ER --> SG
    SG --> SC
    SC --> DB
    MT -.->|1-Click Open| GD
    MT -.->|Reference Link| TK
```

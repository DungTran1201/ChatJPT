# Sơ Đồ Tuần Tự: Mô Hình Nhúng Trực Tiếp Nội Bộ & Tự Động Học Bộ Nhớ Đệm Ngữ Nghĩa (Embedded Model & Cache Auto-Learning Sequence Diagram)
## Dự Án: Website Hỗ Trợ Học Tiếng Nhật & Trợ Lý Ảo (ChatJPT)

---

| Thông Tin Sơ Đồ | Chi Tiết |
| :--- | :--- |
| **Mã Sơ Đồ** | `DIAG-SEQ-004` |
| **Mã Kịch Bản** | `SEQ-005` |
| **Nguồn Sự Thật Thượng Nguồn** | [docs/02-requirements/functional-requirements.md](file:///c:/Users/PC/Project/ChatJPT/docs/02-requirements/functional-requirements.md#FR-061), [models/api/api.yaml](file:///c:/Users/PC/Project/ChatJPT/models/api/api.yaml) |
| **Mục Đích** | Mô tả quy trình kiểm tra cổng phần cứng trước khi tải mô hình trực tiếp, thực thi suy luận in-process nội bộ dự án (không phụ thuộc server ngoài), và cơ chế tự động ghi nhớ hội thoại vào Semantic Cache có khử trùng lặp |

---

## 1. SEQ-005: Kiểm Tra Cổng Phần Cứng, Tải Mô Hình Nhúng & Tự Động Học Khử Trùng Lặp

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng (Learner)
    participant UI as Next.js Client
    participant API as FastAPI Backend (embedded_model.py)
    participant HW as HardwareInspectionService
    participant Downloader as EmbeddedModelService
    participant Runner as InProcessModelRunner (llm/agent.py)
    participant Cache as SemanticCacheService (FTS5 + SQLite)

    %% Giai đoạn 1: Kiểm tra phần cứng
    User->>UI: Mở tab Cài đặt Mô hình (AI Models)
    UI->>API: GET /api/v1/models/embedded/hardware-check
    API->>HW: get_hardware_specs() & evaluate_eligibility()
    HW-->>API: {eligible: true/false, cpu_cores, ram_total, ram_avail, disk_free}
    API-->>UI: HTTP 200 OK (Chẩn đoán chi tiết phần cứng)
    
    alt Phần cứng KHÔNG đủ điều kiện (RAM < 4GB hoặc Disk < 1.5GB)
        Note over UI: UI khóa nút Tải về, hiển thị cảnh báo thông số chưa đạt
    else Phần cứng ĐỦ điều kiện (Pass Gate)
        Note over UI: UI mở khóa nút "Tải Mô Hình Nhúng Trực Tiếp"
        User->>UI: Nhấn "Tải về mô hình trực tiếp trong dự án"
        UI->>API: POST /api/v1/models/embedded/download
        API->>Downloader: start_background_download()
        API-->>UI: HTTP 202 Accepted {status: "DOWNLOADING"}
        
        loop Định kỳ theo dõi tiến độ tải về
            UI->>API: GET /api/v1/models/embedded/status
            API-->>UI: {status: "DOWNLOADING", progress: 45%, bytes: 180MB}
        end
        Downloader->>Downloader: Hoàn tất tải vào ai-backend/models/embedded/
        Downloader-->>API: Trạng thái READY (Kích thước ~380MB)
    end

    %% Giai đoạn 2: Suy luận in-process nội bộ & Tự động học vào Semantic Cache
    User->>UI: Gửi câu hỏi tiếng Nhật (model: qwen2.5-0.5b-embedded)
    UI->>API: POST /api/v1/conversations/{id}/messages/stream
    API->>Runner: astream_agent(prompt, history, model_override='qwen2.5-0.5b-embedded')
    Note over Runner: Thực thi suy luận trực tiếp trong cùng tiến trình (In-Process) KHÔNG qua server ngoài
    loop Truyền luồng câu trả lời
        Runner-->>API: Token chunks
        API-->>UI: SSE event: chunk
    end
    Runner-->>API: Hoàn tất {status: "done", final_text}

    %% Giai đoạn 3: Tự động học với khử trùng lặp
    API->>Cache: learn_interaction(prompt, final_text, category="learned_chat")
    Cache->>Cache: normalize_text(prompt) -> norm_prompt
    Cache->>Cache: SELECT id FROM semantic_cache WHERE prompt_normalized = norm_prompt
    alt Đã tồn tại câu hỏi trong Cache (Đã học trước đó)
        Note over Cache: KHÔNG tạo bản ghi trùng lặp (Deduplication Gate)
        Cache->>Cache: UPDATE semantic_cache SET hit_count = hit_count + 1, updated_at = NOW
    else Chưa có trong Cache (Câu hỏi mới)
        Cache->>Cache: INSERT INTO semantic_cache (prompt_raw, prompt_normalized, response_text...)
        Cache->>Cache: Đồng bộ vào bảng ảo FTS5 (semantic_cache_fts)
    end
    API-->>UI: SSE event: done\ndata: {"status": "done", "learned": true}
```


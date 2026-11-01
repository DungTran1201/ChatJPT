# Sơ Đồ Tuần Tự: Tự Động Chuyển Đổi Dự Phòng LLM & Bộ Nhớ Đệm Ngữ Nghĩa Ngoại Tuyến (Failover & Offline Semantic Cache Sequence Diagram)
## Dự Án: Website Hỗ Trợ Học Tiếng Nhật & Trợ Lý Ảo (ChatJPT)

---

| Thông Tin Sơ Đồ | Chi Tiết |
| :--- | :--- |
| **Mã Sơ Đồ** | `DIAG-SEQ-003` |
| **Mã Kịch Bản** | `SEQ-004` |
| **Nguồn Sự Thật Thượng Nguồn** | [docs/02-requirements/functional-requirements.md](file:///c:/Users/PC/Project/ChatJPT/docs/02-requirements/functional-requirements.md#FR-058), [models/api/api.yaml](file:///c:/Users/PC/Project/ChatJPT/models/api/api.yaml) |
| **Mục Đích** | Mô tả hành vi chuyển đổi dự phòng đa tầng khi gặp lỗi HTTP 429 Quota Exceeded (Gemini -> Groq -> OpenAI -> Claude -> Ollama CPU -> Offline Semantic Cache) và phát thông báo `event: failover` tới người dùng với toàn bộ ngữ cảnh hội thoại |

---

## 1. SEQ-004: Trình Tự Bắt Ngoại Lệ & Kích Hoạt Dự Phòng (Failover)

```mermaid
sequenceDiagram
    autonumber
    participant UI as Next.js Client
    participant Backend as FastAPI Backend (chat.py)
    participant Orchestrator as ChatAgentOrchestrator (llm/agent.py)
    participant CircuitBreaker as ModelQuotaTracker
    participant CloudPrimary as Cloud LLM (Gemini / Groq)
    participant CloudFallback as Fallback LLM (Groq / OpenAI / Claude)
    participant SemanticCache as SemanticCacheService (SQLite app.db)

    UI->>Backend: POST /conversations/{id}/messages/stream (model: selectedModelId)
    Backend->>Orchestrator: astream_agent(prompt, history=context_msgs[20], model_override)
    Orchestrator->>CloudPrimary: Gọi astream(messages) với 20 tin nhắn lịch sử
    
    alt Trường hợp Model cạn kiệt hạn ngạch truy cập (HTTP 429 RESOURCE_EXHAUSTED)
        CloudPrimary-->>Orchestrator: HTTP 429 Rate Limit / Quota Exceeded
        Orchestrator->>CircuitBreaker: record_quota_exhausted(model, delay=1800s)
        Orchestrator-->>Backend: yield {"status": "failover", "from_model": primary, "to_model": fallback}
        Backend-->>UI: event: failover\ndata: {"status": "failover", "to_model": fallback, "reason": "..."}\n\n
        Note over UI: UI hiển thị thông báo chuyển tiếp và tự động cập nhật Model Selector
        
        Orchestrator->>CloudFallback: Gọi astream(messages) với CÙNG bộ 20 tin nhắn lịch sử
        CloudFallback-->>Orchestrator: Stream token chunks
        loop Truyền luồng tiếp tục từ Fallback Model
            Orchestrator-->>Backend: yield {"token": "...", "status": "streaming"}
            Backend-->>UI: event: chunk\ndata: {"token": "..."}\n\n
        end
        Orchestrator-->>Backend: yield {"status": "done", "model": fallback, "failover": true}
        Backend-->>UI: event: done\ndata: {"status": "done", "model": fallback}\n\n
        Backend->>Backend: Lưu message với model_used = fallback
    else Trường hợp cực đoan: Không có API Key hoặc mất kết nối đám mây / CPU không chạy Ollama
        Orchestrator->>CircuitBreaker: Toàn bộ Cloud & Local Provider không khả dụng
        Orchestrator-->>Backend: yield {"status": "failover", "to_model": "offline-semantic-cache"}
        Backend-->>UI: event: failover\ndata: {"to_model": "offline-semantic-cache"}\n\n
        Orchestrator->>SemanticCache: lookup(prompt, threshold=0.48)
        alt Cache Hit (tương đồng >= 0.48)
            SemanticCache-->>Orchestrator: Trả về câu trả lời đã lưu và tăng hit_count
        else Cache Miss
            SemanticCache->>SemanticCache: synthesize_offline_response(prompt) & store()
            SemanticCache-->>Orchestrator: Trả về câu trả lời sư phạm tiếng Nhật
        end
        loop Stream từng từ ngoại tuyến
            Orchestrator-->>Backend: yield {"token": "...", "status": "streaming"}
            Backend-->>UI: event: chunk\ndata: {"token": "..."}\n\n
        end
        Orchestrator-->>Backend: yield {"status": "done", "model": "offline-semantic-cache"}
        Backend-->>UI: event: done\ndata: {"status": "done", "model": "offline-semantic-cache"}\n\n
    end
```

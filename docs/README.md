# Hệ Thống Hồ Sơ Kỹ Thuật Toàn Diện (Master Documentation Index)
## Dự Án: ChatJPT — Hệ Sinh Thái Hỗ Trợ Học Tiếng Nhật Thông Minh (ChatJPT)

---

Chào mừng bạn đến với hệ thống tài liệu kỹ thuật hoàn chỉnh của dự án **ChatJPT — Nền Tảng Hỗ Trợ Học Tiếng Nhật Tích Hợp AI Chatbot & Gia Sư Ảo 3D**.
Toàn bộ tài liệu được tổ chức theo quy chuẩn vòng đời kỹ thuật nghiêm ngặt (Engineering Lifecycle Pipeline) từ **Phase 00** đến **Phase 14**, đảm bảo tính truy vết 2 chiều khép kín, tuân thủ nguyên tắc Nguồn chân lý (Source of Truth), và phân tách tuyệt đối giữa Mô hình chuẩn (`models/`) và Bản chiếu tài liệu (`docs/`).

---

## 1. Bản Đồ 15 Giai Đoạn Hồ Sơ Kỹ Thuật (Pipeline Directory Map)

```
docs/
├── 00-discovery/            # Khảo sát dự án, đăng ký minh chứng hiện trạng, phân loại FACT/ASSUMPTION
├── 01-planning/             # Kế hoạch phát triển, WBS, phân rã Work Packages, quản lý phụ thuộc
├── 02-requirements/         # Đặc tả FRS (FR-001..014), NFR (NFR-001..019), BR (BR-001..006), AC (AC-001..005)
├── 03-business-process/     # Quy trình nghiệp vụ BPMN (PROC-001..010), sơ đồ Swimlane phân vai trò
├── 04-use-cases/            # Mô hình Use Case (UC-001..009), 9 tài liệu đặc tả Use Case chi tiết
├── 05-system-analysis/      # Phân tích biên giới hệ thống, năng lực cốt lõi, so sánh SSE vs WebSocket
├── 06-architecture/         # SAD C4 Model, Quyết định kiến trúc (ADR-001..004), Khái niệm triển khai
├── 07-domain/               # Mô hình miền DDD, Bounded Contexts, Thực thể, Aggregates, Bất biến (INV-01..04)
├── 08-api/                  # Hợp đồng REST & SSE (API-001..008), OpenAPI 3.1.0 schema, Hợp đồng LLM Gateway
├── 09-behavior/             # Sơ đồ tuần tự (SEQ-001..004), Máy trạng thái (STATE-001..003)
├── 10-security/             # Đặc tả an ninh 3 lớp, Mô hình đe dọa STRIDE (THR-001..006), Kiểm soát (CTRL-001..006)
├── 11-ux/                   # Information Architecture, Sơ đồ luồng người dùng, Đặc tả tương tác UI (UX-001..005)
├── 12-testing/              # Chiến lược kiểm thử Testing Pyramid, Kế hoạch kiểm thử, 15 Test Cases (TC-001..015)
├── 13-operations/           # Hướng dẫn triển khai Docker Compose (DEP-001), Runbook, Giám sát (DEP-002), Tự phục hồi
└── 14-governance/           # Quy chế quản trị tài liệu, Mục lục ADR, Ngôn ngữ phổ quát, Definition of Done
```

---

## 2. Bảng Mục Lục Các Giai Đoạn & Trạng Thái Baseline

| Giai Đoạn | Tên Giai Đoạn Kỹ Thuật | Canonical Model | Tài Liệu Chi Tiết | Trạng Thái Quản Trị |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 00** | [Khảo Sát & Khám Phá Dự Án](./00-discovery/README.md) | `N/A` | [README.md](./00-discovery/README.md) | **`APPROVED`** |
| **Phase 01** | [Kế Hoạch Dự Án & Phân Rã Công Việc](./01-planning/README.md) | `N/A` | [README.md](./01-planning/README.md) | **`APPROVED`** |
| **Phase 02** | [Đặc Tả Yêu Cầu Kỹ Thuật (SRS)](./02-requirements/README.md) | `models/requirements/` | [SRS.md](./02-requirements/SRS.md) | **`APPROVED`** |
| **Phase 03** | [Quy Trình Nghiệp Vụ (BPMN)](./03-business-process/README.md) | `models/process/` | [README.md](./03-business-process/README.md) | **`APPROVED`** |
| **Phase 04** | [Mô Hình Trường Hợp Sử Dụng (Use Cases)](./04-use-cases/README.md) | `models/context/` | [README.md](./04-use-cases/README.md) | **`APPROVED`** |
| **Phase 05** | [Phân Tích Hệ Thống & Biên Giới](./05-system-analysis/README.md) | `models/context/` | [README.md](./05-system-analysis/README.md) | **`APPROVED`** |
| **Phase 06** | [Kiến Trúc Hệ Thống (SAD & ADR)](./06-architecture/README.md) | `models/architecture/` | [sad.md](./06-architecture/sad.md) / [ADR-017](./06-architecture/ADR/ADR-017-backend-solid-kiss-refactoring.md) | **`APPROVED`** |
| **Phase 07** | [Mô Hình Miền & Thiết Kế Thực Thể (DDD)](./07-domain/README.md) | `models/domain/` | [domain-model.md](./07-domain/domain-model.md) | **`APPROVED`** |
| **Phase 08** | [Hợp Đồng Giao Tiếp API & Tích Hợp](./08-api/README.md) | `models/api/api.yaml` | [api-specifications.md](./08-api/api-specifications.md) | **`APPROVED`** |
| **Phase 09** | [Mô Hình Hành Vi Động (Sequence & State)](./09-behavior/README.md) | `models/interaction/` | [sequence-diagrams.md](./09-behavior/sequence-diagrams.md) | **`APPROVED`** |
| **Phase 10** | [Đặc Tả An Ninh & Mô Hình Đe Dọa STRIDE](./10-security/README.md) | `models/security/` | [security-specification.md](./10-security/security-specification.md) | **`APPROVED`** |
| **Phase 11** | [Trải Nghiệm Người Dùng & Giao Diện (UX)](./11-ux/README.md) | `models/ux/ux.yaml` | [information-architecture.md](./11-ux/information-architecture.md) | **`APPROVED`** |
| **Phase 12** | [Kiểm Thử & Đảm Bảo Chất Lượng (QA)](./12-testing/README.md) | `models/testing/testing.yaml` | [test-cases.md](./12-testing/test-cases.md) | **`APPROVED`** |
| **Phase 13** | [Vận Hành & Triển Khai (Operations)](./13-operations/README.md) | `models/deployment/deployment.yaml` | [deployment-guide.md](./13-operations/deployment-guide.md) | **`APPROVED`** |
| **Phase 14** | [Quản Trị Vòng Đời Hồ Sơ Kỹ Thuật](./14-governance/README.md) | `N/A` | [documentation-governance.md](./14-governance/documentation-governance.md) | **`APPROVED`** |

---

## 3. Khóa Baseline Tài Liệu (Documentation Baseline)

Hồ sơ baseline chính thức được tổng hợp và khóa tại tệp:
👉 [docs/documentation-baseline.md](./documentation-baseline.md)

---

## 4. Trạng Thái Thực Thi Mã Nguồn (Implementation Status)

- **Trạng thái Coding**: **`IMPLEMENTED (SOLID/KISS REFACTORED — ADR-017)`**.
- Backend (`ai-backend/`) đã được tái cấu trúc đầy đủ theo kiến trúc 4 tầng (`src/api/v1/`, `src/schemas/v1/`, `src/models/v1/`, `src/services/`, `src/repositories/`, `src/core/`, `llm/`), bổ sung bộ Unit Test (`ai-backend/tests/unit/`) và Integration Pipeline Test (`ai-backend/tests/integration/test_pipelines.py`).

---

## 5. Các Nhánh Hồ Sơ Đặc Tả Tính Năng Mới (Feature Branches Specification)

| Nhánh Tính Năng | Thư Mục Hồ Sơ Chi Tiết | Mô Tả Trọng Tâm | Trạng Thái Quản Trị |
| :--- | :--- | :--- | :---: |
| **Quản Lý Project (Project Management MVP)** | [docs/features/project-management/](./features/project-management/README.md) | Nhánh đặc tả lịch sử (không còn active trong nhánh ChatJPT hiện hành). | **`RETIRED`** |
| **Development Orchestrator (External Projects)** | [docs/development-orchestrator/](./development-orchestrator/README.md) | Đặc tả tham khảo điều phối tác vụ ngoài. | **`ARCHIVED`** |
| **Hệ Thống Upload File Dùng Chung (Chat & Prompts)** | [docs/features/chat-file-upload/](./features/chat-file-upload/README.md) | Hạ tầng tải lên tệp tin dùng chung, lưu trữ nguyên tử, chống path traversal, xác thực magic bytes, RFC 5987 UTF-8 download. | **`IMPLEMENTED`** |
| **Quản Lý Quy Tắc (Rules Management MVP)** | [docs/features/rules-management/](./features/rules-management/README.md) | Thư viện Rules tập trung, OCC nguyên tử, Anti-IDOR clone, tự động tiêm quy tắc `always_on` vào luồng Chat Sensei. | **`IMPLEMENTED`** |
| **Quản Lý API Keys & Tích Hợp (User Settings)** | [docs/features/api-keys-management/](./features/api-keys-management/README.md) | Quản lý API Key cá nhân (BYOK), mã hóa AES-256-GCM tại nghỉ, SSRF guard Ollama, cập nhật nguyên tử `.env` cho Admin. | **`IMPLEMENTED`** |
| **Nhập Tệp Văn Bản (Rules & Prompts)** | [docs/features/text-file-import/](./features/text-file-import/README.md) | Nhập tệp văn bản cục bộ (`.md`, `.txt`, `.json`, `.yaml`), khử UTF-8 BOM, phân tích YAML frontmatter qua `TextImportService`. | **`IMPLEMENTED`** |



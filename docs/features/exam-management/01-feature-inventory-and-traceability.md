# Feature Inventory & Traceability Matrix: Exam Management

## 1. Feature Inventory
| Feature ID | Feature Name | Capability | Layer | Status |
| :--- | :--- | :--- | :--- | :--- |
| `FR-074` | Exam Bank Catalog & Multi-Level Filtering (N5..N1 & Kaiwa) | `CAP-EXAM-MGMT` | Fullstack | BASELINED |
| `FR-075` | Exam Creation, Modification, and Google Drive Folder Linking | `CAP-EXAM-MGMT` | Fullstack | BASELINED |
| `FR-076` | Online Interactive Exam Taking, Auto-Scoring & Sensei Explanation | `CAP-EXAM-MGMT` | Fullstack | BASELINED |
| `FR-077` | Reference Materials Repository (JLPT N5..N1, Kaiwa, Tae Kim, Dictionary) | `CAP-EXAM-MGMT` | Fullstack | BASELINED |
| `FR-078` | Reference Material Pinning & Quick Navigation Access | `CAP-EXAM-MGMT` | Frontend + DB | BASELINED |

---

## 2. Business Rules & Security Controls
| Rule / Security ID | Rule Name | Enforcing Component | Verification Gate |
| :--- | :--- | :--- | :--- |
| `BR-043` | Exam Level Sanity (N5, N4, N3, N2, N1, KAIWA, GENERAL) | `exams.py` (Pydantic / Check Constraint) | `TC-EXAM-002` |
| `BR-044` | System Preset Exam Immutability (Chặn xóa/sửa trái phép bộ đề chuẩn) | `exams.py` (Authorization Guard) | `TC-EXAM-003` |
| `BR-045` | Exam Duration and Score Bounds Sanity | `exams.py` (Pydantic Validator) | `TC-EXAM-002` |
| `BR-046` | Reference Material URL Protocol Validation (Chỉ chấp nhận HTTPS an toàn) | `exams.py` (URL Sanitizer) | `TC-EXAM-005` |
| `SEC-016` | Exam Submission & Resource Injection Sanitization | API Gateway & Exam Service | `TC-EXAM-006` |

---

## 3. End-to-End Traceability Mapping
| Req ID | Use Case | Architecture Component | API Operations | Database Entities | UI Views | Test Cases |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-074` | `UC-045` | `COMP-001`, `COMP-002` | `OP-055`, `OP-056` | `Exam` | `/exams` (Exam Bank Tab) | `TC-EXAM-001` |
| `FR-075` | `UC-045` | `COMP-002` | `OP-057`, `OP-058`, `OP-059` | `Exam` | Exam Modal | `TC-EXAM-002`, `TC-EXAM-003` |
| `FR-076` | `UC-046` | `COMP-001`, `COMP-002` | `OP-060` | `Exam`, `ExamQuestion` | Exam Runner Modal | `TC-EXAM-004` |
| `FR-077` | `UC-047` | `COMP-001`, `COMP-002` | `OP-061`, `OP-062` | `ReferenceMaterial` | `/exams` (Materials Tab) | `TC-EXAM-005` |
| `FR-078` | `UC-047` | `COMP-001` | `OP-061` | `ReferenceMaterial` | Pinned Card Widget | `TC-EXAM-005` |


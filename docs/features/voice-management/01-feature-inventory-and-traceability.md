# Feature Inventory & Traceability Matrix: Voice Management

## 1. Feature Inventory
| Feature ID | Feature Name | Capability | Layer | Status |
| :--- | :--- | :--- | :--- | :--- |
| `FR-069` | VoiceVox Character Voice Catalog & Filtering | `CAP-VOICE-MGMT` | Frontend + Backend | BASELINED |
| `FR-070` | Voice Customization & Acoustic Parameter Tuning | `CAP-VOICE-MGMT` | Frontend + Backend + DB | BASELINED |
| `FR-071` | Voice Audio Preview & TTS Synthesis Pipeline | `CAP-VOICE-MGMT` | Backend Service + Engine | BASELINED |
| `FR-072` | Sensei Persona Voice Binding & Selection | `CAP-VOICE-MGMT` | Fullstack | BASELINED |
| `FR-073` | Interactive Japanese Kaiwa Voice Playback via Assigned Sensei Voice | `CAP-VOICE-MGMT` | Frontend UX + Audio Player | BASELINED |

---

## 2. Business Rules & Security Controls
| Rule / Security ID | Rule Name | Enforcing Component | Verification Gate |
| :--- | :--- | :--- | :--- |
| `BR-040` | Voice Parameter Bounds Sanity (Speed: 0.5-2.0, Pitch: -0.15-0.15, Intonation: 0.0-2.0, Volume: 0.0-2.0) | `ai-backend/src/api/v1/voices.py` (Pydantic Validator) | `TC-VOICE-002` |
| `BR-041` | Sensei Voice Assignment Invariant | `ai-backend/src/api/v1/system_prompts.py` (FK Constraint) | `TC-VOICE-004` |
| `BR-042` | Graceful Voice Engine Degradation & Acoustic Fallback | `ai-backend/src/services/voicevox_service.py` | `TC-VOICE-005` |
| `SEC-015` | Audio Ingress & Voice Parameter Injection Sanitization | API Gateway & Audio Route Guard | `TC-VOICE-006` |

---

## 3. End-to-End Traceability Mapping
| Req ID | Use Case | Architecture Component | API Operations | Database Entities | UI Views | Test Cases |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `FR-069` | `UC-042` | `COMP-001`, `COMP-002` | `OP-047`, `OP-048` | `Voice` | `/voices` (Grid View) | `TC-VOICE-001` |
| `FR-070` | `UC-042` | `COMP-002`, `COMP-005` | `OP-050`, `OP-051`, `OP-052` | `Voice` | Voice Tuning Modal | `TC-VOICE-002` |
| `FR-071` | `UC-043` | `COMP-005` | `OP-049`, `OP-053`, `OP-054` | LRU Cache | Audio Preview Widget | `TC-VOICE-003`, `TC-VOICE-005` |
| `FR-072` | `UC-044` | `COMP-001`, `COMP-002` | `/system-prompts` (PUT/GET) | `SystemPrompt`, `Voice` | Sensei Edit Modal | `TC-VOICE-004` |
| `FR-073` | `UC-044` | `COMP-001`, `COMP-005` | `OP-054`, Web Speech | `SystemPrompt` | Chat Speaker Button | `TC-VOICE-007` |

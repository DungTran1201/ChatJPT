# VoiceVox Core Embedded Engine (v0.17.1)

Thư mục này lưu trữ các thành phần nhúng cục bộ của **VoiceVox Core Engine** (Official VoiceVox - https://github.com/VOICEVOX/voicevox_core):

## 1. Cấu trúc thư mục:
- `dict/open_jtalk_dic_utf_8-1.11/`: Từ điển phân tích âm vị học tiếng Nhật OpenJTalk UTF-8.
- `onnxruntime/lib/voicevox_onnxruntime.dll`: Thư viện suy luận mạng nơ-ron DirectML/CPU ONNX Runtime của VoiceVox.
- `models/vvms/*.vvm`: Các mô hình nơ-ron giọng đọc nhân vật (`0.vvm` đến `15.vvm`) cho 30 nhân vật và phong cách (Kasukabe Tsumugi, Shikoku Metan, Zundamon, Kuronotake, Ryusei, Himari, Goki, Sora, Ritsu, v.v.).

## 2. Tự động tích hợp:
Dịch vụ `VoicevoxService` (`ai-backend/src/services/voicevox_service.py`) tự động kiểm tra sự hiện diện của thư mục này. Khi các thành phần đã sẵn sàng, hệ thống khởi tạo `Synthesizer` nhúng trực tiếp trong tiến trình Python (`voicevox_core.blocking`) để tổng hợp âm thanh giọng thật cực nhanh mà không phụ thuộc vào daemon ngoại vi cổng 50021.


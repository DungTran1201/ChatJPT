# Biểu Đồ Trạng Thái: Vòng Đời Thu Âm Giọng Nói & Xử Lý STT
## Mô Hình: `STATE-VOICE-INPUT` | Tham Chiếu: `FR-079`, `FR-080`, `FR-081`, `FR-082`

Biểu đồ mô tả các trạng thái chuyển tiếp trong suốt vòng đời của một phiên thu âm giọng nói từ khi sẵn sàng (IDLE), ghi âm, tạm dừng, xử lý chuyển đổi chữ viết (STT) cho đến khi phát lại trên khung chat.

```mermaid
stateDiagram-v2
    [*] --> IDLE : Khởi tạo giao diện Chat

    IDLE --> REQUESTING_PERMISSION : Người dùng nhấn nút Thu âm (Click Mic)
    REQUESTING_PERMISSION --> RECORDING : Trình duyệt cấp quyền mic thành công
    REQUESTING_PERMISSION --> PERMISSION_DENIED : Người dùng từ chối cấp quyền

    PERMISSION_DENIED --> IDLE : Người dùng cấp lại quyền trong cài đặt trình duyệt

    state RECORDING {
        [*] --> AUDIO_SAMPLING
        AUDIO_SAMPLING --> WAVEFORM_PULSING : Thu từng frame PCM/Opus
        WAVEFORM_PULSING --> TIME_TICKING : Cập nhật đồng hồ đếm giây (0..120s)
    }

    RECORDING --> PAUSED : Người dùng nhấn Tạm dừng (Pause)
    PAUSED --> RECORDING : Người dùng nhấn Tiếp tục (Resume)

    RECORDING --> CANCELLED : Người dùng nhấn Hủy/Xóa bỏ (Trash icon)
    CANCELLED --> IDLE : Hủy bộ đệm âm thanh & reset thanh công cụ

    RECORDING --> TRANSCRIBING_SERVER : Người dùng bấm Dừng/Gửi hoặc chạm mốc 120 giây (BR-048)

    state TRANSCRIBING_SERVER {
        [*] --> UPLOAD_BLOB
        UPLOAD_BLOB --> MAGIC_BYTES_CHECK : Kiểm tra định dạng audio hợp lệ (SEC-021)
        MAGIC_BYTES_CHECK --> SPEECH_RECOGNITION : Gửi tới Whisper/Gemini STT Engine
        SPEECH_RECOGNITION --> [*]
    }

    TRANSCRIBING_SERVER --> READY_TO_SEND : Nhận văn bản chuyển đổi thành công (STT Success)
    TRANSCRIBING_SERVER --> READY_TO_SEND : Lỗi máy chủ STT -> Kích hoạt Fallback Web Speech (BR-049)

    READY_TO_SEND --> DISPATCHING_STREAM : Người dùng xác nhận gửi tin nhắn
    READY_TO_SEND --> RECORDING : Người dùng chọn Thu âm lại (Re-record)

    state DISPATCHING_STREAM {
        [*] --> PERSIST_USER_AUDIO_MESSAGE : Lưu tin nhắn User kèm audio_attachment_id
        PERSIST_USER_AUDIO_MESSAGE --> STREAM_SENSEI_REPLY : Nhận SSE chunks từ mô hình AI
        STREAM_SENSEI_REPLY --> [*]
    }

    DISPATCHING_STREAM --> IN_CHAT_PLAYBACK : Hoàn tất lượt trò chuyện (Done event)

    state IN_CHAT_PLAYBACK {
        [*] --> AUDIO_STOPPED
        AUDIO_STOPPED --> AUDIO_PLAYING : Người dùng bấm nút Play trên bong bóng tin nhắn
        AUDIO_PLAYING --> AUDIO_PAUSED : Người dùng bấm nút Pause
        AUDIO_PAUSED --> AUDIO_PLAYING : Người dùng bấm Resume
        AUDIO_PLAYING --> AUDIO_STOPPED : Kết thúc bản ghi âm (Playback Ended)
    }

    IN_CHAT_PLAYBACK --> IDLE : Sẵn sàng cho lượt thu âm tiếp theo
```

## Nguồn Tham Chiếu
- Trạng thái bắt buộc: `IDLE`, `RECORDING`, `PAUSED`, `TRANSCRIBING_SERVER`, `READY_TO_SEND`, `DISPATCHING_STREAM`, `IN_CHAT_PLAYBACK`.
- Quy tắc điều kiện: `BR-047`, `BR-048`, `BR-049`, `BR-050`.


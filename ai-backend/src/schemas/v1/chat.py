"""Chat streaming & Speech-to-Text (STT) API schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field


class MessageStreamRequest(BaseModel):
    content: str = Field(default="", max_length=4000, description="Nội dung prompt câu hỏi (tối đa 4000 ký tự)")
    model: Optional[str] = "gemini-3.8-flash"
    sensei_id: Optional[str] = Field(default=None, description="ID của Sensei đồng hành (N5..N1)")
    language: Optional[str] = Field(default=None, description="Ngôn ngữ giao diện người dùng (vi, en, ja)")
    attachments: Optional[List[str]] = Field(default=None, description="Danh sách attachment_id đính kèm cho lượt chat này")
    audio_attachment_id: Optional[str] = Field(default=None, description="ID tệp ghi âm giọng nói đính kèm (nếu gửi voice message)")
    audio_duration_ms: Optional[int] = Field(default=0, description="Thời lượng tệp ghi âm (ms)")
    stt_language: Optional[str] = Field(default=None, description="Mã ngôn ngữ ghi âm đã nhận diện (vi, en, ja, auto)")
    stt_transcript: Optional[str] = Field(default=None, description="Bản dịch văn bản từ giọng nói qua STT")


class STTResult(BaseModel):
    transcript: str = Field(description="Đoạn văn bản chuyển đổi từ giọng nói")
    detected_language: str = Field(default="ja", description="Ngôn ngữ phát hiện (vi, en, ja)")
    confidence: float = Field(default=0.95, description="Độ tin cậy của kết quả nhận diện (0.0..1.0)")
    engine_used: str = Field(default="whisper", description="Tên công nghệ STT đã xử lý")
    latency_ms: float = Field(default=0.0, description="Độ trễ xử lý (ms)")

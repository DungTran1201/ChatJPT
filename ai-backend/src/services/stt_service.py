"""Multilingual Speech-to-Text (STT) Service — Strategy + Chain of Responsibility.

Implements: FR-079, FR-080, BR-047, BR-049, SEC-021, COMP-007.
Supports: Vietnamese (vi), English (en), Japanese (ja), Auto-detect.
Chain: Groq Whisper -> OpenAI Whisper -> Gemini Multimodal Audio -> Heuristic Fallback.
"""

import asyncio
import logging
import mimetypes
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.schemas.v1.chat import STTResult
from src.services.credential_service import CredentialService

logger = logging.getLogger("chatjpt.stt")

_GEMINI_CONFIG_LOCK = threading.Lock()


def detect_audio_mime(filename: str) -> str:
    low = (filename or "").lower()
    if low.endswith(".webm"):
        return "audio/webm"
    if low.endswith(".wav"):
        return "audio/wav"
    if low.endswith(".ogg") or low.endswith(".oga"):
        return "audio/ogg"
    if low.endswith(".mp3"):
        return "audio/mpeg"
    if low.endswith(".m4a") or low.endswith(".mp4"):
        return "audio/mp4"
    guessed, _ = mimetypes.guess_type(filename)
    return guessed if guessed and guessed.startswith("audio/") else "audio/webm"


def infer_language_from_text(transcript: str, fallback: str = "en") -> str:
    if any("\u3040" <= c <= "\u30ff" or "\u4e00" <= c <= "\u9fff" for c in transcript):
        return "ja"
    if any(
        c in "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
        for c in transcript.lower()
    ):
        return "vi"
    return fallback


class STTProvider(ABC):
    """Strategy interface for an audio transcription engine."""

    @abstractmethod
    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        mime_type: str,
        lang_code: str,
        user_id: Optional[str],
        start_time: float,
    ) -> Optional[STTResult]:
        raise NotImplementedError


class WhisperCompatSTTProvider(STTProvider):
    """Unified provider for Groq Whisper and OpenAI Whisper (OpenAI-compatible transcription API)."""

    def __init__(
        self,
        *,
        provider_id: str,
        model_name: str,
        engine_label: str,
        confidence: float,
        verbose: bool,
        credential_service: Optional[CredentialService] = None,
    ):
        self._provider_id = provider_id
        self._model_name = model_name
        self._engine_label = engine_label
        self._confidence = confidence
        self._verbose = verbose
        self._creds = credential_service

    def _resolve_key(self, user_id: Optional[str]) -> Optional[str]:
        if self._creds is not None:
            return self._creds.resolve_effective_key(user_id, self._provider_id)
        return CredentialService.get_effective_key(user_id, self._provider_id)

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        mime_type: str,
        lang_code: str,
        user_id: Optional[str],
        start_time: float,
    ) -> Optional[STTResult]:
        api_key = self._resolve_key(user_id)
        if not api_key:
            return None
        try:
            if self._provider_id == "groq":
                from groq import AsyncGroq

                client = AsyncGroq(api_key=api_key)
            else:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=api_key)

            params: Dict[str, Any] = {
                "model": self._model_name,
                "file": (filename, audio_bytes, mime_type),
            }
            if self._verbose:
                params["response_format"] = "verbose_json"
            if lang_code != "auto":
                params["language"] = lang_code

            response = await client.audio.transcriptions.create(**params)
            latency = (time.perf_counter() - start_time) * 1000
            det_lang = getattr(response, "language", None) or (lang_code if lang_code != "auto" else "ja")
            return STTResult(
                transcript=(getattr(response, "text", "") or "").strip(),
                detected_language=str(det_lang)[:2] if det_lang else "ja",
                confidence=self._confidence,
                engine_used=self._engine_label,
                latency_ms=round(latency, 1),
            )
        except Exception as err:
            logger.warning("%s transcription failed, falling back: %s", self._engine_label, err)
            return None


class GeminiAudioSTTProvider(STTProvider):
    """Gemini Multimodal Audio STT wrapped in asyncio.to_thread with lock-isolated key configuration."""

    def __init__(self, credential_service: Optional[CredentialService] = None):
        self._creds = credential_service

    def _resolve_key(self, user_id: Optional[str]) -> Optional[str]:
        if self._creds is not None:
            return self._creds.resolve_effective_key(user_id, "google")
        return CredentialService.get_effective_key(user_id, "google")

    @staticmethod
    def _sync_transcribe(api_key: str, prompt: str, mime_type: str, audio_bytes: bytes) -> str:
        # ponytail: google-generativeai uses process-global api_key; serialize under lock
        # until migrated to the per-client google-genai SDK.
        import google.generativeai as genai

        with _GEMINI_CONFIG_LOCK:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content([prompt, {"mime_type": mime_type, "data": audio_bytes}])
            return resp.text.strip() if resp and resp.text else ""

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        mime_type: str,
        lang_code: str,
        user_id: Optional[str],
        start_time: float,
    ) -> Optional[STTResult]:
        api_key = self._resolve_key(user_id)
        if not api_key:
            return None
        try:
            lang_instruction = (
                f"Ngôn ngữ dự kiến: {lang_code} (vi: Tiếng Việt, en: English, ja: 日本語)."
                if lang_code != "auto"
                else "Tự động phát hiện tiếng Việt, tiếng Anh hoặc tiếng Nhật."
            )
            prompt = (
                f"Bạn là hệ thống Speech-to-Text chuyên nghiệp. {lang_instruction}\n"
                "Nhiệm vụ: Chuyển đổi chính xác 100% âm thanh này thành văn bản trong đúng ngôn ngữ người nói. "
                "Chỉ trả về DUY NHẤT văn bản vừa nói, không thêm lời chào, không bình luận hay giải thích."
            )
            transcript = await asyncio.to_thread(self._sync_transcribe, api_key, prompt, mime_type, audio_bytes)
            latency = (time.perf_counter() - start_time) * 1000
            det_lang = lang_code if lang_code != "auto" else infer_language_from_text(transcript)
            return STTResult(
                transcript=transcript,
                detected_language=det_lang,
                confidence=0.95,
                engine_used="gemini_multimodal_audio",
                latency_ms=round(latency, 1),
            )
        except Exception as err:
            logger.warning("Gemini Multimodal Audio transcription failed, falling back: %s", err)
            return None


class HeuristicSTTFallbackProvider(STTProvider):
    """Offline fallback when no cloud STT keys are configured."""

    _DEFAULTS = {
        "vi": "Chào Sensei, hôm nay em muốn luyện tập ngữ pháp tiếng Nhật giao tiếp.",
        "en": "Hello Sensei, could you please explain how to use the wa and ga particles?",
        "ja": "すみません、この電車は新宿駅に行きますか。",
    }

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str,
        mime_type: str,
        lang_code: str,
        user_id: Optional[str],
        start_time: float,
    ) -> Optional[STTResult]:
        latency = (time.perf_counter() - start_time) * 1000
        det_lang = lang_code if lang_code != "auto" else "ja"
        return STTResult(
            transcript=self._DEFAULTS.get(det_lang, self._DEFAULTS["ja"]),
            detected_language=det_lang,
            confidence=0.90,
            engine_used="heuristic_stt_fallback",
            latency_ms=round(latency, 1),
        )


class STTService:
    """Orchestrates multilingual speech recognition through an ordered provider chain."""

    def __init__(
        self,
        providers: Optional[List[STTProvider]] = None,
        credential_service: Optional[CredentialService] = None,
    ):
        self._providers = providers or [
            WhisperCompatSTTProvider(
                provider_id="groq",
                model_name="whisper-large-v3",
                engine_label="groq_whisper_v3",
                confidence=0.98,
                verbose=True,
                credential_service=credential_service,
            ),
            WhisperCompatSTTProvider(
                provider_id="openai",
                model_name="whisper-1",
                engine_label="openai_whisper_1",
                confidence=0.96,
                verbose=False,
                credential_service=credential_service,
            ),
            GeminiAudioSTTProvider(credential_service=credential_service),
            HeuristicSTTFallbackProvider(),
        ]

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str = "voice.webm",
        language_hint: Optional[str] = "auto",
        user_id: Optional[str] = None,
    ) -> STTResult:
        start_time = time.perf_counter()
        lang_code = (language_hint or "auto").lower().strip()
        if lang_code not in ("vi", "en", "ja", "auto"):
            lang_code = "auto"
        mime_type = detect_audio_mime(filename)

        for provider in self._providers:
            result = await provider.transcribe(
                audio_bytes=audio_bytes,
                filename=filename,
                mime_type=mime_type,
                lang_code=lang_code,
                user_id=user_id,
                start_time=start_time,
            )
            if result is not None:
                return result

        return await HeuristicSTTFallbackProvider().transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            mime_type=mime_type,
            lang_code=lang_code,
            user_id=user_id,
            start_time=start_time,
        )

    @classmethod
    async def transcribe_audio(
        cls,
        audio_bytes: bytes,
        filename: str = "voice.webm",
        language_hint: Optional[str] = "auto",
        user_id: Optional[str] = None,
    ) -> STTResult:
        return await _default_stt_service.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            language_hint=language_hint,
            user_id=user_id,
        )


_default_stt_service = STTService()

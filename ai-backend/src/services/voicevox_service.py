"""VoiceVox Neural TTS Service — Chain of Responsibility TTS + Thread-Safe LRU + VoiceRepository.

Implements ADR-015, COMP-005, FR-069..FR-073, BR-040, BR-042:
  1. EmbeddedCoreTTSProvider (in-process ONNX Runtime + OpenJTalk + VVM models)
  2. DaemonHttpTTSProvider (external VoiceVox REST daemon :50021)
  3. AcousticFallbackTTSProvider (deterministic 24kHz PCM WAV chime — NEVER cached in LRU!)
"""

import hashlib
import io
import json
import logging
import math
import os
import pathlib
import struct
import threading
import time
import urllib.parse
import urllib.request
import uuid
import wave
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from src.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from src.core.security import is_admin_user
from src.models.v1.voice import DEFAULT_VOICE_SPEAKER_ID
from src.repositories.prompt_repo import PromptRepository
from src.repositories.voice_repo import VoiceRepository

logger = logging.getLogger("voicevox_service")

_BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
_CORE_DIR = _BASE_DIR / "voicevox_core"
_DLL_PATH = _CORE_DIR / "onnxruntime" / "lib" / "voicevox_onnxruntime.dll"
_DICT_PATH = _CORE_DIR / "dict" / "open_jtalk_dic_utf_8-1.11"
_MODELS_DIR = _CORE_DIR / "models" / "vvms"


def clamp_acoustic_params(
    *,
    speed_scale: float = 1.0,
    pitch_scale: float = 0.0,
    intonation_scale: float = 1.0,
    volume_scale: float = 1.0,
) -> Tuple[float, float, float, float]:
    """Enforces BR-040 acoustic tuning bounds."""
    return (
        max(0.5, min(2.0, float(speed_scale))),
        max(-0.15, min(0.15, float(pitch_scale))),
        max(0.0, min(2.0, float(intonation_scale))),
        max(0.0, min(2.0, float(volume_scale))),
    )


class TTSProvider(ABC):
    """Strategy interface for a VoiceVox synthesis provider."""

    is_fallback: bool = False

    @abstractmethod
    def synthesize(
        self,
        *,
        text: str,
        speaker_id: int,
        speed_scale: float,
        pitch_scale: float,
        intonation_scale: float,
        volume_scale: float,
    ) -> Optional[bytes]:
        raise NotImplementedError


class EmbeddedCoreTTSProvider(TTSProvider):
    """In-process VoiceVox Core ONNX Runtime + OpenJTalk synthesizer."""

    def __init__(self):
        self._synthesizer = None
        self._init_attempted = False
        self._supported_style_ids: set = set()
        self._lock = threading.Lock()

    @property
    def init_failed(self) -> bool:
        return self._init_attempted and self._synthesizer is None

    @property
    def supported_style_ids(self) -> set:
        return self._supported_style_ids

    def _ensure_synthesizer(self) -> Optional[Any]:
        if self._synthesizer is not None:
            return self._synthesizer
        with self._lock:
            if self._synthesizer is not None:
                return self._synthesizer
            if self._init_attempted:
                return None
            self._init_attempted = True
            try:
                if not (_DLL_PATH.exists() and _DICT_PATH.exists() and _MODELS_DIR.exists()):
                    logger.warning(
                        "VoiceVox Core files missing: DLL=%s, Dict=%s, Models=%s",
                        _DLL_PATH.exists(),
                        _DICT_PATH.exists(),
                        _MODELS_DIR.exists(),
                    )
                    return None

                from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

                ort = Onnxruntime.load_once(filename=str(_DLL_PATH))
                open_jtalk = OpenJtalk(str(_DICT_PATH))
                synth = Synthesizer(ort, open_jtalk)

                vvm_files = sorted(
                    _MODELS_DIR.glob("*.vvm"),
                    key=lambda p: int(p.stem) if p.stem.isdigit() else 999,
                )
                loaded_count = 0
                for vvm in vvm_files:
                    try:
                        with VoiceModelFile.open(str(vvm)) as model:
                            synth.load_voice_model(model)
                            loaded_count += 1
                    except Exception as me:
                        logger.warning("Could not load voice model %s: %s", vvm.name, me)

                try:
                    for speaker in synth.metas():
                        for style in speaker.styles:
                            self._supported_style_ids.add(style.id)
                except Exception as meta_err:
                    logger.warning("Error querying synthesizer metas: %s", meta_err)

                self._synthesizer = synth
                logger.info(
                    "VoiceVox Core ready: %d VVM models, %d styles.",
                    loaded_count,
                    len(self._supported_style_ids),
                )
                return self._synthesizer
            except Exception as err:
                logger.error("Failed to initialize VoiceVox Core engine: %s", err)
                return None

    def synthesize(
        self,
        *,
        text: str,
        speaker_id: int,
        speed_scale: float,
        pitch_scale: float,
        intonation_scale: float,
        volume_scale: float,
    ) -> Optional[bytes]:
        synth = self._ensure_synthesizer()
        if synth is None:
            return None

        effective_id = speaker_id
        if self._supported_style_ids and speaker_id not in self._supported_style_ids:
            if 8 in self._supported_style_ids:
                effective_id = 8
            elif 2 in self._supported_style_ids:
                effective_id = 2
            else:
                effective_id = next(iter(self._supported_style_ids))

        query = synth.create_audio_query(text, style_id=effective_id)
        query.speed_scale = speed_scale
        query.pitch_scale = pitch_scale
        query.intonation_scale = intonation_scale
        query.volume_scale = volume_scale
        return bytes(synth.synthesis(query, style_id=effective_id))


class DaemonHttpTTSProvider(TTSProvider):
    """External VoiceVox REST API daemon (:50021)."""

    def __init__(self, engine_url: str):
        self.engine_url = engine_url.rstrip("/")

    def synthesize(
        self,
        *,
        text: str,
        speaker_id: int,
        speed_scale: float,
        pitch_scale: float,
        intonation_scale: float,
        volume_scale: float,
    ) -> Optional[bytes]:
        try:
            query_url = f"{self.engine_url}/audio_query?text={urllib.parse.quote(text)}&speaker={speaker_id}"
            with urllib.request.urlopen(urllib.request.Request(query_url, method="POST"), timeout=3.0) as resp:
                if resp.getcode() != 200:
                    return None
                query_json = json.loads(resp.read().decode("utf-8"))

            query_json["speedScale"] = speed_scale
            query_json["pitchScale"] = pitch_scale
            query_json["intonationScale"] = intonation_scale
            query_json["volumeScale"] = volume_scale

            synth_url = f"{self.engine_url}/synthesis?speaker={speaker_id}"
            synth_req = urllib.request.Request(
                synth_url,
                data=json.dumps(query_json).encode("utf-8"),
                headers={"Content-Type": "application/json", "Accept": "audio/wav"},
                method="POST",
            )
            with urllib.request.urlopen(synth_req, timeout=8.0) as synth_resp:
                if synth_resp.getcode() == 200:
                    return synth_resp.read()
        except Exception as err:
            logger.debug("VoiceVox daemon synthesis failed: %s", err)
        return None


class AcousticFallbackTTSProvider(TTSProvider):
    """Resilient 24kHz 16-bit mono PCM WAV melodic chime fallback (BR-042). Never cached."""

    is_fallback: bool = True

    def synthesize(
        self,
        *,
        text: str,
        speaker_id: int,
        speed_scale: float,
        pitch_scale: float,
        intonation_scale: float,
        volume_scale: float,
    ) -> Optional[bytes]:
        sample_rate = 24000
        base_duration = min(3.0, max(0.8, len(text) * 0.08 / max(0.5, speed_scale)))
        num_samples = int(sample_rate * base_duration)
        base_freq = 440.0 * (1.0 + pitch_scale * 1.5)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            frames = []
            for i in range(num_samples):
                t = float(i) / sample_rate
                env = math.sin(math.pi * (i / num_samples))
                mod = math.sin(2 * math.pi * 3.5 * t) * 0.15
                f1 = base_freq * (1.0 + mod)
                f2 = base_freq * 1.25 * (1.0 + mod)
                val = math.sin(2 * math.pi * f1 * t) * 0.65 + math.sin(2 * math.pi * f2 * t) * 0.35
                sample = max(-32768, min(32767, int(val * env * 14000)))
                frames.append(struct.pack("<h", sample))
            wav_file.writeframes(b"".join(frames))
        return buf.getvalue()


class VoicevoxService:
    """Facade combining VoiceVox TTS synthesis chain, thread-safe LRU cache, and voice catalog CRUD."""

    def __init__(
        self,
        *,
        engine_url: Optional[str] = None,
        max_cache_size: int = 200,
        voice_repo: Optional[VoiceRepository] = None,
        prompt_repo: Optional[PromptRepository] = None,
        providers: Optional[List[TTSProvider]] = None,
    ):
        self.engine_url = (engine_url or os.environ.get("VOICEVOX_ENGINE_URL", "http://127.0.0.1:50021")).rstrip("/")
        self.max_cache_size = max_cache_size
        self._audio_cache: OrderedDict[str, bytes] = OrderedDict()
        self._cache_lock = threading.Lock()
        self._voices = voice_repo or VoiceRepository()
        self._prompts = prompt_repo or PromptRepository()

        self._embedded_provider = EmbeddedCoreTTSProvider()
        self._daemon_provider = DaemonHttpTTSProvider(self.engine_url)
        self._fallback_provider = AcousticFallbackTTSProvider()
        self._providers: List[TTSProvider] = providers or [
            self._embedded_provider,
            self._daemon_provider,
            self._fallback_provider,
        ]

    def get_engine_status(self) -> Dict[str, Any]:
        with self._cache_lock:
            cached_count = len(self._audio_cache)

        embedded_present = _DLL_PATH.exists() and _DICT_PATH.exists() and _MODELS_DIR.exists()
        if embedded_present and not self._embedded_provider.init_failed:
            vvm_count = len(list(_MODELS_DIR.glob("*.vvm")))
            speakers_count = (
                len(self._embedded_provider.supported_style_ids)
                if self._embedded_provider.supported_style_ids
                else 30
            )
            return {
                "engine_available": True,
                "engine_mode": "embedded_core",
                "engine_url": "embedded://voicevox_core",
                "version": "0.17.1 (voicevox_core)",
                "latency_ms": 0.5,
                "cached_audio_count": cached_count,
                "loaded_models_count": vvm_count,
                "supported_speakers_count": speakers_count,
                "error": None,
            }

        start_time = time.time()
        try:
            req = urllib.request.Request(f"{self.engine_url}/version", method="GET")
            with urllib.request.urlopen(req, timeout=1.2) as response:
                status_code = response.getcode()
                raw_version = response.read().decode("utf-8").strip('"\n\r ')
                return {
                    "engine_available": status_code == 200,
                    "engine_mode": "daemon",
                    "engine_url": self.engine_url,
                    "version": raw_version,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                    "cached_audio_count": cached_count,
                    "loaded_models_count": 0,
                    "supported_speakers_count": 0,
                    "error": None,
                }
        except Exception as err:
            logger.debug("VoiceVox daemon check failed: %s", err)
            return {
                "engine_available": False,
                "engine_mode": "offline",
                "engine_url": self.engine_url,
                "version": None,
                "latency_ms": None,
                "cached_audio_count": cached_count,
                "loaded_models_count": 0,
                "supported_speakers_count": 0,
                "error": str(err),
            }

    def synthesize(
        self,
        text: str,
        speaker_id: int,
        speed_scale: float = 1.0,
        pitch_scale: float = 0.0,
        intonation_scale: float = 1.0,
        volume_scale: float = 1.0,
    ) -> bytes:
        cleaned_text = (text or "").strip() or "こんにちは。"
        speed_scale, pitch_scale, intonation_scale, volume_scale = clamp_acoustic_params(
            speed_scale=speed_scale,
            pitch_scale=pitch_scale,
            intonation_scale=intonation_scale,
            volume_scale=volume_scale,
        )

        cache_key = hashlib.sha256(
            f"{cleaned_text}_{speaker_id}_{speed_scale:.2f}_{pitch_scale:.2f}_{intonation_scale:.2f}_{volume_scale:.2f}".encode(
                "utf-8"
            )
        ).hexdigest()

        with self._cache_lock:
            if cache_key in self._audio_cache:
                self._audio_cache.move_to_end(cache_key)
                return self._audio_cache[cache_key]

        for provider in self._providers:
            try:
                wav_bytes = provider.synthesize(
                    text=cleaned_text,
                    speaker_id=speaker_id,
                    speed_scale=speed_scale,
                    pitch_scale=pitch_scale,
                    intonation_scale=intonation_scale,
                    volume_scale=volume_scale,
                )
            except Exception as err:
                logger.warning("TTS provider %s failed: %s", provider.__class__.__name__, err)
                wav_bytes = None

            if wav_bytes:
                if not provider.is_fallback:
                    with self._cache_lock:
                        self._audio_cache[cache_key] = wav_bytes
                        if len(self._audio_cache) > self.max_cache_size:
                            self._audio_cache.popitem(last=False)
                return wav_bytes

        return self._fallback_provider.synthesize(
            text=cleaned_text,
            speaker_id=speaker_id,
            speed_scale=speed_scale,
            pitch_scale=pitch_scale,
            intonation_scale=intonation_scale,
            volume_scale=volume_scale,
        ) or b""

    def synthesize_for_profile(
        self,
        voice_or_sensei_id: str,
        *,
        text: str,
        speed_scale: Optional[float] = None,
        pitch_scale: Optional[float] = None,
        intonation_scale: Optional[float] = None,
        volume_scale: Optional[float] = None,
    ) -> bytes:
        voice = self._voices.get_by_id(voice_or_sensei_id)
        if not voice:
            sensei_voice_id = self._prompts.get_voice_id(voice_or_sensei_id)
            if sensei_voice_id:
                voice = self._voices.get_by_id(sensei_voice_id)

        if not voice:
            return self.synthesize(
                text=text,
                speaker_id=DEFAULT_VOICE_SPEAKER_ID,
                speed_scale=speed_scale if speed_scale is not None else 1.0,
                pitch_scale=pitch_scale if pitch_scale is not None else 0.0,
                intonation_scale=intonation_scale if intonation_scale is not None else 1.0,
                volume_scale=volume_scale if volume_scale is not None else 1.0,
            )

        return self.synthesize(
            text=text,
            speaker_id=voice["speaker_id"],
            speed_scale=speed_scale if speed_scale is not None else voice.get("speed_scale", 1.0),
            pitch_scale=pitch_scale if pitch_scale is not None else voice.get("pitch_scale", 0.0),
            intonation_scale=intonation_scale if intonation_scale is not None else voice.get("intonation_scale", 1.0),
            volume_scale=volume_scale if volume_scale is not None else voice.get("volume_scale", 1.0),
        )

    # ------------------------------------------------------------------
    # Voice Catalog CRUD
    # ------------------------------------------------------------------
    def list_voices(
        self,
        gender: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._voices.list_filtered(gender=gender, status_filter=status, search=search)

    def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        return self._voices.get_by_id(voice_id)

    def get_voice_or_404(self, voice_id: str) -> Dict[str, Any]:
        voice = self._voices.get_by_id(voice_id)
        if not voice:
            raise NotFoundError(f"Không tìm thấy giọng đọc với mã '{voice_id}'.")
        return voice

    def create_voice(self, data: Dict[str, Any], user_id: str = "system") -> Dict[str, Any]:
        speed, pitch, intonation, volume = clamp_acoustic_params(
            speed_scale=data.get("speed_scale", 1.0),
            pitch_scale=data.get("pitch_scale", 0.0),
            intonation_scale=data.get("intonation_scale", 1.0),
            volume_scale=data.get("volume_scale", 1.0),
        )
        record = {
            "id": data.get("id") or f"voice_custom_{uuid.uuid4().hex[:8]}",
            "name": data.get("name", "Custom Voice"),
            "character_name": data.get("character_name", "Custom Character"),
            "speaker_id": int(data.get("speaker_id", DEFAULT_VOICE_SPEAKER_ID)),
            "style_name": data.get("style_name", "Normal"),
            "gender": data.get("gender", "female"),
            "description": data.get("description", ""),
            "speed_scale": speed,
            "pitch_scale": pitch,
            "intonation_scale": intonation,
            "volume_scale": volume,
            "sample_text": data.get("sample_text", "こんにちは！"),
            "avatar_url": data.get("avatar_url", "/avatars/voices/default.png"),
            "status": data.get("status", "ACTIVE"),
            "user_id": user_id,
        }
        return self._voices.create(record)

    def update_voice(
        self,
        voice_id: str,
        updates: Dict[str, Any],
        current_user: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        existing = self._voices.get_by_id(voice_id)
        if not existing:
            return None

        if current_user is not None:
            owner_id = existing.get("user_id")
            if existing.get("is_system_preset") and not is_admin_user(current_user):
                raise ForbiddenError("Không có quyền chỉnh sửa giọng mẫu mặc định của hệ thống.")
            if (
                owner_id
                and owner_id not in ("system", "guest_user")
                and owner_id != current_user.get("id")
                and not is_admin_user(current_user)
            ):
                raise ForbiddenError("Bạn không có quyền chỉnh sửa hồ sơ giọng đọc của người dùng khác.")

        sanitized: Dict[str, Any] = {}
        for key, val in updates.items():
            if val is None:
                continue
            if key == "speed_scale":
                val = max(0.5, min(2.0, float(val)))
            elif key in ("intonation_scale", "volume_scale"):
                val = max(0.0, min(2.0, float(val)))
            elif key == "pitch_scale":
                val = max(-0.15, min(0.15, float(val)))
            sanitized[key] = val

        return self._voices.update(voice_id, sanitized)

    def delete_voice(
        self,
        voice_id: str,
        current_user: Optional[Dict[str, Any]] = None,
    ) -> bool:
        existing = self._voices.get_by_id(voice_id)
        if not existing:
            if current_user is not None:
                raise NotFoundError(f"Không tìm thấy giọng đọc với mã '{voice_id}'.")
            return False
        if existing.get("is_system_preset"):
            if current_user is not None:
                raise BadRequestError("Không thể xóa giọng mẫu mặc định của hệ thống.")
            return False
        if current_user is not None:
            owner_id = existing.get("user_id")
            if (
                owner_id
                and owner_id not in ("system", "guest_user")
                and owner_id != current_user.get("id")
                and not is_admin_user(current_user)
            ):
                raise ForbiddenError("Bạn không có quyền xóa hồ sơ giọng đọc của người dùng khác.")

        self._voices.delete(voice_id)
        return True


voicevox_service = VoicevoxService()

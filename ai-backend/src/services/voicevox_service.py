import io
import math
import struct
import wave
import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import logging
from collections import OrderedDict
from typing import Optional, Dict, Any, List

from src.db import query_one, query_all, execute_commit

logger = logging.getLogger("voicevox_service")

class VoicevoxService:
    """
    VoiceVox Neural Text-to-Speech Service (ADR-015, COMP-005, FR-069..FR-073).
    Supports VoiceVox REST API daemon integration (:50021), LRU audio cache,
    acoustic parameter modulation, and standard-library fallback WAV synthesis for offline resilience.
    """

    def __init__(self, engine_url: Optional[str] = None, max_cache_size: int = 200):
        self.engine_url = (engine_url or os.environ.get("VOICEVOX_ENGINE_URL", "http://127.0.0.1:50021")).rstrip("/")
        self.max_cache_size = max_cache_size
        self._audio_cache: OrderedDict[str, bytes] = OrderedDict()

    # --------------------------------------------------------------------------
    # 1. Engine Connectivity & Health Check (FR-071, OP-049)
    # --------------------------------------------------------------------------
    def get_engine_status(self) -> Dict[str, Any]:
        """Checks VoiceVox daemon health, version, and latency."""
        start_time = time.time()
        url = f"{self.engine_url}/version"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.2) as response:
                status_code = response.getcode()
                raw_version = response.read().decode("utf-8").strip('"\n\r ')
                latency_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "engine_available": status_code == 200,
                    "engine_url": self.engine_url,
                    "version": raw_version,
                    "latency_ms": latency_ms,
                    "cached_audio_count": len(self._audio_cache)
                }
        except Exception as e:
            logger.debug(f"VoiceVox engine check failed: {e}")
            return {
                "engine_available": False,
                "engine_url": self.engine_url,
                "version": None,
                "latency_ms": None,
                "cached_audio_count": len(self._audio_cache),
                "error": str(e)
            }

    # --------------------------------------------------------------------------
    # 2. Audio Synthesis & Cache (FR-071, FR-073, BR-040, BR-042, OP-053, OP-054)
    # --------------------------------------------------------------------------
    def synthesize(
        self,
        text: str,
        speaker_id: int,
        speed_scale: float = 1.0,
        pitch_scale: float = 0.0,
        intonation_scale: float = 1.0,
        volume_scale: float = 1.0
    ) -> bytes:
        """
        Synthesizes Japanese text into PCM WAV audio.
        Checks in-memory LRU cache first; calls VoiceVox engine if available;
        falls back to acoustic multi-tone synthesis if engine is offline (BR-042).
        """
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            cleaned_text = "こんにちは。"

        # Sanitize parameters against bounds (BR-040)
        speed_scale = max(0.5, min(2.0, float(speed_scale)))
        pitch_scale = max(-0.15, min(0.15, float(pitch_scale)))
        intonation_scale = max(0.0, min(2.0, float(intonation_scale)))
        volume_scale = max(0.0, min(2.0, float(volume_scale)))

        cache_key = hashlib.sha256(
            f"{cleaned_text}_{speaker_id}_{speed_scale:.2f}_{pitch_scale:.2f}_{intonation_scale:.2f}_{volume_scale:.2f}".encode("utf-8")
        ).hexdigest()

        # Check LRU cache
        if cache_key in self._audio_cache:
            self._audio_cache.move_to_end(cache_key)
            return self._audio_cache[cache_key]

        # Attempt synthesis with local VoiceVox daemon
        wav_bytes = self._call_voicevox_engine(
            cleaned_text,
            speaker_id,
            speed_scale,
            pitch_scale,
            intonation_scale,
            volume_scale
        )

        # Fallback if engine is offline / failed
        if not wav_bytes:
            wav_bytes = self._generate_fallback_wav(cleaned_text, speed_scale, pitch_scale)

        # Store in LRU cache
        self._audio_cache[cache_key] = wav_bytes
        if len(self._audio_cache) > self.max_cache_size:
            self._audio_cache.popitem(last=False)

        return wav_bytes

    def _call_voicevox_engine(
        self,
        text: str,
        speaker_id: int,
        speed_scale: float,
        pitch_scale: float,
        intonation_scale: float,
        volume_scale: float
    ) -> Optional[bytes]:
        """Calls VoiceVox 2-step synthesis: /audio_query followed by /synthesis."""
        try:
            # Step 1: POST /audio_query?text=...&speaker=...
            query_url = f"{self.engine_url}/audio_query?text={urllib.parse.quote(text)}&speaker={speaker_id}"
            query_req = urllib.request.Request(query_url, method="POST")
            with urllib.request.urlopen(query_req, timeout=3.0) as query_resp:
                if query_resp.getcode() != 200:
                    return None
                query_json = json.loads(query_resp.read().decode("utf-8"))

            # Step 2: Override acoustic parameters in query JSON
            query_json["speedScale"] = speed_scale
            query_json["pitchScale"] = pitch_scale
            query_json["intonationScale"] = intonation_scale
            query_json["volumeScale"] = volume_scale

            # Step 3: POST /synthesis?speaker=...
            synth_url = f"{self.engine_url}/synthesis?speaker={speaker_id}"
            post_data = json.dumps(query_json).encode("utf-8")
            synth_req = urllib.request.Request(
                synth_url,
                data=post_data,
                headers={"Content-Type": "application/json", "Accept": "audio/wav"},
                method="POST"
            )
            with urllib.request.urlopen(synth_req, timeout=8.0) as synth_resp:
                if synth_resp.getcode() == 200:
                    return synth_resp.read()
        except Exception as e:
            logger.warning(f"VoiceVox engine synthesis call failed: {e}. Activating BR-042 fallback.")
        return None

    def _generate_fallback_wav(self, text: str, speed_scale: float = 1.0, pitch_scale: float = 0.0) -> bytes:
        """
        Generates standard 24kHz 16-bit mono PCM WAV fallback audio using Python standard library (BR-042).
        Produces a melodic multi-tone chime sequence corresponding to text length.
        """
        sample_rate = 24000
        # Calculate duration based on text length and speed
        base_duration = min(3.0, max(0.8, len(text) * 0.08 / max(0.5, speed_scale)))
        num_samples = int(sample_rate * base_duration)
        
        # Base pitch adjusted by pitch_scale (-0.15 to +0.15 -> 400Hz to 600Hz)
        base_freq = 440.0 * (1.0 + pitch_scale * 1.5)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            frames = []
            for i in range(num_samples):
                t = float(i) / sample_rate
                # Multi-harmonic chord with smooth envelope
                env = math.sin(math.pi * (i / num_samples))
                # Slight modulation to mimic speech pitch dynamics
                mod = math.sin(2 * math.pi * 3.5 * t) * 0.15
                f1 = base_freq * (1.0 + mod)
                f2 = base_freq * 1.25 * (1.0 + mod)
                val = math.sin(2 * math.pi * f1 * t) * 0.65 + math.sin(2 * math.pi * f2 * t) * 0.35
                sample = int(val * env * 14000)
                clamped = max(-32768, min(32767, sample))
                frames.append(struct.pack("<h", clamped))

            wav_file.writeframes(b"".join(frames))

        return buf.getvalue()

    # --------------------------------------------------------------------------
    # 3. Voice Catalog Database CRUD (FR-069, FR-070, OP-047, OP-048, OP-050..052)
    # --------------------------------------------------------------------------
    def list_voices(
        self,
        gender: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves list of character voices with optional filtering."""
        sql = "SELECT * FROM voices WHERE 1=1"
        params: List[Any] = []

        if gender:
            sql += " AND gender = ?"
            params.append(gender.lower())

        if status:
            sql += " AND status = ?"
            params.append(status.upper())

        if search:
            sql += " AND (name LIKE ? OR character_name LIKE ? OR description LIKE ?)"
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern])

        sql += " ORDER BY is_system_preset DESC, character_name ASC, speaker_id ASC"
        return query_all(sql, tuple(params))

    def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single voice profile by its unique ID."""
        return query_one("SELECT * FROM voices WHERE id = ?", (voice_id,))

    def create_voice(self, data: Dict[str, Any], user_id: str = "system") -> Dict[str, Any]:
        """Creates a new custom voice profile."""
        import uuid
        voice_id = data.get("id") or f"voice_custom_{uuid.uuid4().hex[:8]}"
        
        # Enforce boundary constraints (BR-040)
        speed = max(0.5, min(2.0, float(data.get("speed_scale", 1.0))))
        pitch = max(-0.15, min(0.15, float(data.get("pitch_scale", 0.0))))
        intonation = max(0.0, min(2.0, float(data.get("intonation_scale", 1.0))))
        volume = max(0.0, min(2.0, float(data.get("volume_scale", 1.0))))

        sql = """
        INSERT INTO voices (
            id, name, character_name, speaker_id, style_name, gender, description,
            speed_scale, pitch_scale, intonation_scale, volume_scale,
            sample_text, avatar_url, status, is_system_preset, user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            voice_id,
            data.get("name", "Custom Voice"),
            data.get("character_name", "Custom Character"),
            int(data.get("speaker_id", 8)),
            data.get("style_name", "Normal"),
            data.get("gender", "female"),
            data.get("description", ""),
            speed,
            pitch,
            intonation,
            volume,
            data.get("sample_text", "こんにちは！"),
            data.get("avatar_url", "/avatars/voices/default.png"),
            data.get("status", "ACTIVE"),
            0,
            user_id
        )
        execute_commit(sql, params)
        return self.get_voice(voice_id) or {}

    def update_voice(self, voice_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates acoustic parameters and properties of a voice profile."""
        existing = self.get_voice(voice_id)
        if not existing:
            return None

        allowed_fields = [
            "name", "character_name", "speaker_id", "style_name", "gender", "description",
            "speed_scale", "pitch_scale", "intonation_scale", "volume_scale",
            "sample_text", "avatar_url", "status"
        ]

        set_clauses = []
        params = []
        for key in allowed_fields:
            if key in updates and updates[key] is not None:
                val = updates[key]
                if key in ["speed_scale", "intonation_scale", "volume_scale"]:
                    val = max(0.0, min(2.0, float(val)))
                    if key == "speed_scale":
                        val = max(0.5, val)
                elif key == "pitch_scale":
                    val = max(-0.15, min(0.15, float(val)))
                set_clauses.append(f"{key} = ?")
                params.append(val)

        if not set_clauses:
            return existing

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        sql = f"UPDATE voices SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(voice_id)

        execute_commit(sql, tuple(params))
        return self.get_voice(voice_id)

    def delete_voice(self, voice_id: str) -> bool:
        """Deletes a custom voice profile. System presets cannot be deleted."""
        existing = self.get_voice(voice_id)
        if not existing or existing.get("is_system_preset"):
            return False

        execute_commit("DELETE FROM voices WHERE id = ?", (voice_id,))
        return True


voicevox_service = VoicevoxService()

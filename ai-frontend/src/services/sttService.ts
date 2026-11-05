import { STTTranscriptResponse } from '@/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';

export interface TranscribeAudioResult {
  attachment_id: string;
  filename: string;
  audio_url: string;
  duration_ms: number;
  transcript: string;
  detected_language: string;
  confidence: number;
  engine_used?: string;
  latency_ms?: number;
}

export class STTService {
  /**
   * Transcribes spoken audio into text via POST /api/v1/chat/stt.
   * Supports multilingual recognition (vi, en, ja, auto).
   *
   * @param blob The recorded audio Blob (e.g. audio/webm or audio/wav).
   * @param language Language code hint: 'vi' | 'en' | 'ja' | 'auto'.
   * @param durationMs Approximate duration of recorded audio in milliseconds.
   * @param filename Optional filename.
   */
  static async transcribeAudio(
    blob: Blob,
    language: string = 'auto',
    durationMs: number = 0,
    filename: string = 'voice-input.webm'
  ): Promise<TranscribeAudioResult> {
    const formData = new FormData();
    formData.append('file', blob, filename);
    formData.append('language', language);
    formData.append('duration_ms', String(Math.round(durationMs)));

    const headers: Record<string, string> = {};
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('ai_chan_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    const response = await fetch(`${BASE_URL}/chat/stt`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      let errorMessage = `STT failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData?.detail?.message) {
          errorMessage = errorData.detail.message;
        } else if (typeof errorData?.detail === 'string') {
          errorMessage = errorData.detail;
        }
      } catch {
        // Use default error message
      }
      throw new Error(errorMessage);
    }

    const json: STTTranscriptResponse = await response.json();
    return json.data;
  }
}


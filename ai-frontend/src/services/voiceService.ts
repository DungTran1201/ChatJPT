import {
  VoiceItem,
  VoiceEngineStatus,
  VoiceListResponse,
  VoiceSynthesizeRequest,
} from '@/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';

function getAuthHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('ai_chan_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
}

let activeAudio: HTMLAudioElement | null = null;

export class VoiceService {
  /**
   * Check VoiceVox local engine connectivity status.
   */
  static async getEngineStatus(): Promise<VoiceEngineStatus> {
    try {
      const res = await fetch(`${BASE_URL}/voices/status`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (!res.ok) {
        return {
          engine_available: false,
          engine_url: 'http://127.0.0.1:50021',
          cached_audio_count: 0,
          error: `HTTP ${res.status}`,
        };
      }
      return res.json();
    } catch (err: any) {
      return {
        engine_available: false,
        engine_url: 'http://127.0.0.1:50021',
        cached_audio_count: 0,
        error: err?.message || 'Connection failed',
      };
    }
  }

  /**
   * List character voices with optional filtering.
   */
  static async getVoices(params?: {
    gender?: string;
    status?: string;
    q?: string;
  }): Promise<VoiceListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.gender && params.gender !== 'all') {
      searchParams.append('gender', params.gender);
    }
    if (params?.status && params.status !== 'all') {
      searchParams.append('status', params.status);
    }
    if (params?.q && params.q.trim()) {
      searchParams.append('q', params.q.trim());
    }

    const queryStr = searchParams.toString() ? `?${searchParams.toString()}` : '';
    const res = await fetch(`${BASE_URL}/voices${queryStr}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to load voice roster.');
    }

    return res.json();
  }

  /**
   * Get single voice profile by ID.
   */
  static async getVoice(id: string): Promise<VoiceItem> {
    const res = await fetch(`${BASE_URL}/voices/${encodeURIComponent(id)}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Voice profile not found.');
    }

    return res.json();
  }

  /**
   * Create custom voice profile.
   */
  static async createVoice(data: Partial<VoiceItem>): Promise<VoiceItem> {
    const res = await fetch(`${BASE_URL}/voices`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to create custom voice.');
    }

    return res.json();
  }

  /**
   * Update acoustic tuning parameters.
   */
  static async updateVoice(id: string, updates: Partial<VoiceItem>): Promise<VoiceItem> {
    const res = await fetch(`${BASE_URL}/voices/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updates),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to update voice parameters.');
    }

    return res.json();
  }

  /**
   * Delete custom voice profile.
   */
  static async deleteVoice(id: string): Promise<{ message: string }> {
    const res = await fetch(`${BASE_URL}/voices/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Failed to delete voice.');
    }

    return res.json();
  }

  /**
   * Synthesize audio from text using speaker ID or direct options.
   */
  static async synthesizeAudio(req: VoiceSynthesizeRequest): Promise<Blob> {
    const res = await fetch(`${BASE_URL}/voices/synthesize`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(req),
    });

    if (!res.ok) {
      throw new Error('Audio speech synthesis failed.');
    }

    return res.blob();
  }

  /**
   * Synthesize audio using stored voice ID parameters.
   */
  static async synthesizeByVoiceId(
    voiceId: string,
    text: string,
    options?: Partial<VoiceSynthesizeRequest>
  ): Promise<Blob> {
    const res = await fetch(`${BASE_URL}/voices/${encodeURIComponent(voiceId)}/synthesize`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        text,
        ...options,
      }),
    });

    if (!res.ok) {
      throw new Error('Character voice synthesis failed.');
    }

    return res.blob();
  }

  /**
   * Helper to stop any currently playing voice audio and play a new WAV blob.
   */
  static playAudioBlob(blob: Blob): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        if (activeAudio) {
          activeAudio.pause();
          activeAudio.currentTime = 0;
          activeAudio = null;
        }

        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        activeAudio = audio;

        audio.onended = () => {
          URL.revokeObjectURL(url);
          activeAudio = null;
          resolve();
        };

        audio.onerror = (e) => {
          URL.revokeObjectURL(url);
          activeAudio = null;
          reject(e);
        };

        audio.play().catch(reject);
      } catch (err) {
        reject(err);
      }
    });
  }

  /**
   * Stop any currently playing audio.
   */
  static stopAudio(): void {
    if (activeAudio) {
      activeAudio.pause();
      activeAudio.currentTime = 0;
      activeAudio = null;
    }
  }

  /**
   * High-level helper for chat playback:
   * 1. Try VoiceVox synthesis via backend with assigned voiceId
   * 2. If network fails or Web Speech API preferred fallback, speak via window.speechSynthesis
   */
  static async playJapaneseSpeech(text: string, voiceId?: string): Promise<void> {
    // 1. Try VoiceVox backend synthesis
    try {
      const targetVoice = voiceId || 'voice_kasukabe_tsumugi';
      const blob = await this.synthesizeByVoiceId(targetVoice, text);
      await this.playAudioBlob(blob);
      return;
    } catch (voicevoxErr) {
      console.warn('VoiceVox synthesis error, falling back to Web Speech API:', voicevoxErr);
    }

    // 2. Fallback to Web Speech API
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ja-JP';
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  }
}


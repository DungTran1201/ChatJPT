'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';

export type VoiceLanguage = 'auto' | 'vi' | 'en' | 'ja';

interface VoiceRecorderProps {
  onRecorded: (blob: Blob, durationMs: number, language: VoiceLanguage, sendImmediately: boolean) => void;
  onCancel: () => void;
  isTranscribing?: boolean;
}

const MAX_DURATION_SECS = 120; // 2 minutes (FR-079)

export default function VoiceRecorder({
  onRecorded,
  onCancel,
  isTranscribing = false,
}: VoiceRecorderProps) {
  const [selectedLanguage, setSelectedLanguage] = useState<VoiceLanguage>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('chatjpt_voice_lang') as VoiceLanguage) || 'auto';
    }
    return 'auto';
  });
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [audioLevel, setAudioLevel] = useState<number[]>([10, 15, 25, 18, 12, 28, 20, 14]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const startTimeRef = useRef<number>(0);
  const sendImmediatelyRef = useRef<boolean>(false);

  // Format seconds to mm:ss
  const formatTimer = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Safe stream cleanup (SEC-022)
  const cleanupStream = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  }, []);

  const handleLanguageChange = (lang: VoiceLanguage) => {
    setSelectedLanguage(lang);
    if (typeof window !== 'undefined') {
      localStorage.setItem('chatjpt_voice_lang', lang);
    }
  };

  // Stop recording and emit audio
  const stopRecording = useCallback((sendImmediately: boolean) => {
    sendImmediatelyRef.current = sendImmediately;
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  // Cancel and discard recording without sending (SEC-022)
  const handleCancel = useCallback(() => {
    audioChunksRef.current = [];
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
    }
    cleanupStream();
    onCancel();
  }, [cleanupStream, onCancel]);

  // Start audio capture
  useEffect(() => {
    let isCancelled = false;

    async function startCapture() {
      try {
        setErrorMsg(null);
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('Trình duyệt của bạn không hỗ trợ ghi âm trực tiếp.');
        }

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });

        if (isCancelled) {
          stream.getTracks().forEach(t => t.stop());
          return;
        }

        streamRef.current = stream;

        // Visualizer setup via Web Audio API
        try {
          const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
          if (AudioContextClass) {
            const ctx = new AudioContextClass();
            audioContextRef.current = ctx;
            const source = ctx.createMediaStreamSource(stream);
            const analyser = ctx.createAnalyser();
            analyser.fftSize = 64;
            source.connect(analyser);

            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            const updateVisualizer = () => {
              if (!audioContextRef.current) return;
              analyser.getByteFrequencyData(dataArray);
              // Pick 8 representative frequency bars
              const step = Math.floor(bufferLength / 8) || 1;
              const levels: number[] = [];
              for (let i = 0; i < 8; i++) {
                const val = dataArray[i * step] || 0;
                levels.push(Math.max(6, Math.round((val / 255) * 28)));
              }
              setAudioLevel(levels);
              animFrameRef.current = requestAnimationFrame(updateVisualizer);
            };
            updateVisualizer();
          }
        } catch {
          // Visualizer fallback
        }

        // Setup MediaRecorder
        let mimeType = 'audio/webm;codecs=opus';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          if (MediaRecorder.isTypeSupported('audio/webm')) {
            mimeType = 'audio/webm';
          } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
            mimeType = 'audio/mp4';
          } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
            mimeType = 'audio/ogg';
          } else {
            mimeType = '';
          }
        }

        const options = mimeType ? { mimeType } : undefined;
        const recorder = new MediaRecorder(stream, options);
        mediaRecorderRef.current = recorder;
        audioChunksRef.current = [];

        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            audioChunksRef.current.push(e.data);
          }
        };

        recorder.onstop = () => {
          const finalBlob = new Blob(audioChunksRef.current, {
            type: mimeType || 'audio/webm',
          });
          const durationMs = Math.max(1000, Date.now() - startTimeRef.current);
          cleanupStream();
          if (finalBlob.size > 0) {
            onRecorded(finalBlob, durationMs, selectedLanguage, sendImmediatelyRef.current);
          } else {
            onCancel();
          }
        };

        recorder.start(250); // Slice chunks every 250ms
        startTimeRef.current = Date.now();

        // Timer interval
        timerRef.current = setInterval(() => {
          setElapsedSeconds((prev) => {
            const next = prev + 1;
            if (next >= MAX_DURATION_SECS) {
              stopRecording(false);
            }
            return next;
          });
        }, 1000);
      } catch (err: any) {
        console.error('Microphone error:', err);
        setErrorMsg(
          err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError'
            ? 'Quyền truy cập Micro bị từ chối. Vui lòng cho phép micro trong cài đặt trình duyệt.'
            : err.message || 'Không thể bắt đầu ghi âm.'
        );
      }
    }

    startCapture();

    return () => {
      isCancelled = true;
      cleanupStream();
    };
  }, [cleanupStream, onCancel, onRecorded, selectedLanguage, stopRecording]);

  if (errorMsg) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 14px',
          borderRadius: 'var(--radius-lg, 12px)',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: 'var(--danger, #ef4444)',
          fontSize: '0.82rem',
          gap: '12px',
        }}
      >
        <span>{errorMsg}</span>
        <button
          type="button"
          onClick={handleCancel}
          style={{
            background: 'var(--danger, #ef4444)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-sm, 4px)',
            padding: '3px 8px',
            fontSize: '0.75rem',
            cursor: 'pointer',
          }}
        >
          Đóng
        </button>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '6px 12px',
        borderRadius: 'var(--radius-lg, 12px)',
        background: 'var(--bg-elevated, #1a1a24)',
        border: '1px solid var(--accent, #10b981)',
        boxShadow: '0 0 16px rgba(16, 185, 129, 0.15)',
        gap: '10px',
        width: '100%',
        minHeight: '44px',
      }}
    >
      {/* Left: Recording Pulse + Timer */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
        <span
          style={{
            display: 'inline-block',
            width: '9px',
            height: '9px',
            borderRadius: '50%',
            backgroundColor: '#ef4444',
            boxShadow: '0 0 8px #ef4444',
            animation: 'pulse 1.2s infinite ease-in-out',
          }}
        />
        <span
          style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            color: '#ef4444',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
          }}
        >
          REC
        </span>
        <span
          style={{
            fontFamily: 'var(--font-mono, monospace)',
            fontSize: '0.82rem',
            fontWeight: 600,
            color: 'var(--text-primary)',
          }}
        >
          {formatTimer(elapsedSeconds)}
        </span>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-disabled)' }}>
          / {formatTimer(MAX_DURATION_SECS)}
        </span>
      </div>

      {/* Center: Live Audio Waveform Bars */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '3px',
          height: '28px',
          overflow: 'hidden',
          padding: '0 8px',
        }}
      >
        {audioLevel.map((height, i) => (
          <div
            key={i}
            style={{
              width: '4px',
              height: `${height}px`,
              backgroundColor: 'var(--accent, #10b981)',
              borderRadius: '2px',
              transition: 'height 0.08s ease',
              opacity: 0.85,
            }}
          />
        ))}
      </div>

      {/* Right Controls: Language Selector Pill + Cancel + Done/Send */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
        {/* Language selector toggle */}
        <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg-surface)', borderRadius: 'var(--radius-full)', padding: '2px', border: '1px solid var(--border-subtle)' }}>
          {(['auto', 'vi', 'en', 'ja'] as VoiceLanguage[]).map((lang) => {
            const isSelected = selectedLanguage === lang;
            const labels: Record<VoiceLanguage, string> = {
              auto: '🌐 Auto',
              vi: '🇻🇳 VI',
              en: '🇬🇧 EN',
              ja: '🇯🇵 JA',
            };
            return (
              <button
                key={lang}
                type="button"
                onClick={() => handleLanguageChange(lang)}
                style={{
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-full)',
                  border: 'none',
                  background: isSelected ? 'var(--accent, #10b981)' : 'transparent',
                  color: isSelected ? '#fff' : 'var(--text-secondary)',
                  fontSize: '0.68rem',
                  fontWeight: isSelected ? 600 : 500,
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                }}
              >
                {labels[lang]}
              </button>
            );
          })}
        </div>

        {/* Cancel / Trash */}
        <button
          type="button"
          onClick={handleCancel}
          disabled={isTranscribing}
          title="Hủy ghi âm (Discard)"
          aria-label="Discard recording"
          style={{
            width: '30px',
            height: '30px',
            borderRadius: '50%',
            background: 'transparent',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'color 0.15s ease, border-color 0.15s ease',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.color = 'var(--danger, #ef4444)';
            e.currentTarget.style.borderColor = 'rgba(239,68,68,0.4)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.color = 'var(--text-muted)';
            e.currentTarget.style.borderColor = 'var(--border-subtle)';
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
          </svg>
        </button>

        {/* Done / Stop & Review into composer */}
        <button
          type="button"
          onClick={() => stopRecording(false)}
          disabled={isTranscribing}
          title="Dừng & Xem trước văn bản (Stop & Transcribe)"
          aria-label="Stop and preview transcription"
          style={{
            padding: '4px 10px',
            borderRadius: 'var(--radius-md, 6px)',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
            color: 'var(--text-primary)',
            fontSize: '0.74rem',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <span style={{ display: 'inline-block', width: '8px', height: '8px', backgroundColor: 'var(--accent, #10b981)', borderRadius: '1px' }} />
          <span>Xong</span>
        </button>

        {/* Send Directly */}
        <button
          type="button"
          onClick={() => stopRecording(true)}
          disabled={isTranscribing}
          title="Chuyển thành văn bản và Gửi ngay (Send Voice Message)"
          aria-label="Transcribe and send directly"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'var(--accent, #10b981)',
            border: 'none',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            boxShadow: '0 2px 8px rgba(16, 185, 129, 0.4)',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>
  );
}


'use client';

import React, { useState, useRef, useEffect } from 'react';

interface AudioPlayerBarProps {
  audioUrl: string;
  durationMs?: number;
  sttLanguage?: string;
  className?: string;
}

function formatTime(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

export default function AudioPlayerBar({
  audioUrl,
  durationMs,
  sttLanguage,
  className = '',
}: AudioPlayerBarProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const initialDuration = durationMs ? durationMs / 1000 : 0;
  const [duration, setDuration] = useState(initialDuration);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      if (audio.duration && !isNaN(audio.duration) && isFinite(audio.duration)) {
        setDuration(audio.duration);
      }
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
    };

    const handleError = () => {
      setIsError(true);
      setIsPlaying(false);
    };

    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
    };
  }, [audioUrl]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play().then(() => {
        setIsPlaying(true);
      }).catch((err) => {
        console.warn('Audio playback error:', err);
        setIsError(true);
      });
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    const target = parseFloat(e.target.value);
    setCurrentTime(target);
    if (audio) {
      audio.currentTime = target;
    }
  };

  const cyclePlaybackRate = () => {
    const audio = audioRef.current;
    const rates = [1, 1.25, 1.5, 2];
    const nextRate = rates[(rates.indexOf(playbackRate) + 1) % rates.length];
    setPlaybackRate(nextRate);
    if (audio) {
      audio.playbackRate = nextRate;
    }
  };

  const progressPercent = duration > 0 ? Math.min((currentTime / duration) * 100, 100) : 0;

  // Language flag / tag mapping
  const langLabel = (() => {
    switch (sttLanguage?.toLowerCase()) {
      case 'vi': return '🇻🇳 Tiếng Việt';
      case 'en': return '🇬🇧 English';
      case 'ja': return '🇯🇵 日本語';
      default: return '🌐 Voice';
    }
  })();

  if (isError) {
    return (
      <div
        className={className}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 12px',
          borderRadius: 'var(--radius-md, 8px)',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.25)',
          color: 'var(--danger, #ef4444)',
          fontSize: '0.78rem',
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>Audio unavailable</span>
      </div>
    );
  }

  return (
    <div
      className={className}
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        gap: '6px',
        padding: '8px 12px',
        borderRadius: 'var(--radius-lg, 12px)',
        background: 'rgba(255, 255, 255, 0.04)',
        border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.1))',
        backdropFilter: 'blur(8px)',
        minWidth: '280px',
        maxWidth: '380px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
        userSelect: 'none',
      }}
    >
      <audio ref={audioRef} src={audioUrl} preload="metadata" />

      {/* Top row: Play/Pause button + Waveform/Scrubber + Time */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Play/Pause Button */}
        <button
          type="button"
          onClick={togglePlay}
          aria-label={isPlaying ? 'Pause voice message' : 'Play voice message'}
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
            flexShrink: 0,
            transition: 'transform 0.15s ease, background 0.15s ease',
            boxShadow: '0 2px 6px rgba(16, 185, 129, 0.3)',
          }}
          onMouseDown={e => { e.currentTarget.style.transform = 'scale(0.92)'; }}
          onMouseUp={e => { e.currentTarget.style.transform = 'scale(1)'; }}
        >
          {isPlaying ? (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="4" width="4" height="16" rx="1" />
              <rect x="14" y="4" width="4" height="16" rx="1" />
            </svg>
          ) : (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style={{ marginLeft: '2px' }}>
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
          )}
        </button>

        {/* Central visualizer / scrubber */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '3px', position: 'relative' }}>
          {/* Animated Waveform bars */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '2px',
              height: '14px',
              overflow: 'hidden',
            }}
          >
            {[4, 8, 12, 10, 6, 14, 11, 7, 9, 13, 8, 5, 12, 14, 7, 10, 6, 8, 12, 9].map((height, i) => {
              const barPercent = (i / 20) * 100;
              const isPassed = barPercent <= progressPercent;
              return (
                <div
                  key={i}
                  style={{
                    flex: 1,
                    height: isPlaying ? `${Math.max(3, (height * (Math.sin((currentTime * 6) + i) * 0.4 + 0.8)))}px` : `${height}px`,
                    backgroundColor: isPassed ? 'var(--accent, #10b981)' : 'var(--text-disabled, rgba(255,255,255,0.25))',
                    borderRadius: '1px',
                    transition: 'height 0.1s ease, background-color 0.15s ease',
                  }}
                />
              );
            })}
          </div>

          {/* Hidden range input overlaid for scrubbing */}
          <input
            type="range"
            min={0}
            max={duration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
            aria-label="Seek audio playback"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              opacity: 0,
              cursor: 'pointer',
              margin: 0,
            }}
          />
        </div>

        {/* Playback speed multiplier button */}
        <button
          type="button"
          onClick={cyclePlaybackRate}
          title="Playback speed"
          style={{
            fontSize: '0.68rem',
            fontWeight: 700,
            padding: '2px 5px',
            borderRadius: 'var(--radius-sm, 4px)',
            background: 'var(--bg-elevated, rgba(255,255,255,0.08))',
            border: '1px solid var(--border-subtle, rgba(255,255,255,0.1))',
            color: 'var(--text-secondary, #9ca3af)',
            cursor: 'pointer',
            flexShrink: 0,
            lineHeight: 1.2,
          }}
        >
          {playbackRate}x
        </button>
      </div>

      {/* Bottom meta row: Language badge + Time elapsed / duration */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '0.7rem',
          color: 'var(--text-muted, #9ca3af)',
          paddingLeft: '42px',
        }}
      >
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '0.66rem',
            color: 'var(--accent, #10b981)',
            fontWeight: 500,
          }}
        >
          {langLabel}
        </span>
        <span style={{ fontFamily: 'var(--font-mono, monospace)', fontSize: '0.68rem' }}>
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>
    </div>
  );
}


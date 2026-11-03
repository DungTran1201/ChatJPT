'use client';

import React, { useState } from 'react';
import { useApp } from '@/context/AppContext';
import {
  parsePedagogicalBlocks,
  speakJapaneseSpeech,
  JapaneseSentenceBlock,
  isPredominantlyJapanese,
} from '@/utils/japaneseParser';

interface JapaneseInterlinearViewProps {
  content: string;
  showTranslation?: boolean;
  showFurigana?: boolean;
  highlightGrammar?: boolean;
  showRomaji?: boolean;
  showAudio?: boolean;
  isStreaming?: boolean;
  voiceId?: string;
}

export default function JapaneseInterlinearView({
  content,
  showTranslation = true,
  showFurigana = true,
  highlightGrammar = true,
  showRomaji = true,
  showAudio = true,
  isStreaming = false,
  voiceId,
}: JapaneseInterlinearViewProps) {
  const { t } = useApp();
  const [playingIdx, setPlayingIdx] = useState<number | null>(null);

  const blocks: JapaneseSentenceBlock[] = parsePedagogicalBlocks(content);

  const handleSpeak = (text: string, idx: number) => {
    setPlayingIdx(idx);
    speakJapaneseSpeech(text, voiceId);
    setTimeout(() => setPlayingIdx(null), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', width: '100%' }}>
      {blocks.map((block, bIdx) => {
        const isJp = isPredominantlyJapanese(block.rawText);

        if (!isJp) {
          return (
            <div
              key={bIdx}
              style={{
                fontSize: '0.92rem',
                color: 'var(--text-primary)',
                lineHeight: 1.6,
              }}
            >
              {block.rawText}
            </div>
          );
        }

        return (
          <div
            key={bIdx}
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              padding: '6px 0',
              borderBottom: bIdx < blocks.length - 1 ? '1px dashed var(--border-subtle)' : 'none',
              paddingBottom: bIdx < blocks.length - 1 ? '14px' : '6px',
            }}
          >
            {/* Top row: Word tokens + Speaker button */}
            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '12px' }}>
              {/* Words row */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'flex-end',
                  columnGap: '10px',
                  rowGap: '12px',
                }}
              >
                {block.tokens.map((token, tIdx) => {
                  const isHighlighted = highlightGrammar && token.grammarHighlight === 'green';

                  return (
                    <div
                      key={tIdx}
                      style={{
                        display: 'inline-flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        minWidth: '18px',
                      }}
                    >
                      {/* 1. Furigana (Hiragana reading above Kanji) */}
                      {showFurigana && (
                        <span
                          style={{
                            fontSize: '0.74rem',
                            color: 'var(--accent, #10b981)',
                            lineHeight: 1.1,
                            minHeight: '16px',
                            fontWeight: 500,
                            letterSpacing: '0.02em',
                            userSelect: 'none',
                          }}
                        >
                          {token.furigana || ''}
                        </span>
                      )}

                      {/* 2. Main Japanese Word / Kanji */}
                      <span
                        style={{
                          fontSize: '1.22rem',
                          fontWeight: isHighlighted ? 600 : 500,
                          color: isHighlighted ? 'var(--accent, #16a34a)' : 'var(--text-primary)',
                          lineHeight: 1.35,
                          padding: isHighlighted ? '2px 8px' : '2px 2px',
                          borderRadius: isHighlighted ? '6px' : '0',
                          border: isHighlighted ? '1.5px solid var(--accent, #22c55e)' : 'none',
                          backgroundColor: isHighlighted ? 'rgba(34, 197, 94, 0.12)' : 'transparent',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        {token.text}
                      </span>

                      {/* 3. Romaji (Pronunciation underneath with clear legible typography) */}
                      {showRomaji && token.romaji && (
                        <span
                          style={{
                            fontSize: '0.84rem',
                            fontWeight: 500,
                            color: 'var(--text-secondary)',
                            lineHeight: 1.2,
                            marginTop: '4px',
                            fontFamily: 'var(--font-sans)',
                            letterSpacing: '0.015em',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {token.romaji}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Speaker TTS Audio Button */}
              {showAudio && (
                <button
                  type="button"
                  onClick={() => handleSpeak(block.rawText, bIdx)}
                  title={t('chat.tts_listen_title')}
                  aria-label={t('chat.tts_listen_aria')}
                  style={{
                    background: playingIdx === bIdx ? 'var(--bg-selected)' : 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    color: playingIdx === bIdx ? 'var(--accent)' : 'var(--text-muted)',
                    borderRadius: 'var(--radius-sm)',
                    width: '30px',
                    height: '30px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    flexShrink: 0,
                    marginBottom: '2px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {playingIdx === bIdx ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M11 5L6 9H2v6h4l5 4V5z"/>
                      <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                    </svg>
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                      <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                    </svg>
                  )}
                </button>
              )}
            </div>

            {/* Translation in user language underneath the whole sentence */}
            {showTranslation && block.translation && (
              <div
                style={{
                  fontSize: '0.88rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5,
                  paddingTop: '6px',
                  fontStyle: 'normal',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                }}
              >
                <span
                  style={{
                    display: 'inline-block',
                    width: '3px',
                    height: '16px',
                    backgroundColor: 'var(--accent, #22c55e)',
                    borderRadius: '2px',
                    flexShrink: 0,
                    marginTop: '2px',
                  }}
                />
                <span style={{ color: 'var(--text-primary)' }}>{block.translation}</span>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

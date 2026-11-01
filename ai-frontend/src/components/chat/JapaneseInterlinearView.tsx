'use client';

import React, { useState } from 'react';
import {
  parsePedagogicalBlocks,
  speakJapaneseSpeech,
  JapaneseSentenceBlock,
  hasJapaneseText
} from '@/utils/japaneseParser';

interface JapaneseInterlinearViewProps {
  content: string;
  showTranslation?: boolean;
  showFurigana?: boolean;
  highlightGrammar?: boolean;
  showRomaji?: boolean;
  showAudio?: boolean;
  isStreaming?: boolean;
}

export default function JapaneseInterlinearView({
  content,
  showTranslation = true,
  showFurigana = true,
  highlightGrammar = true,
  showRomaji = true,
  showAudio = true,
  isStreaming = false,
}: JapaneseInterlinearViewProps) {
  const [playingIdx, setPlayingIdx] = useState<number | null>(null);

  const blocks: JapaneseSentenceBlock[] = parsePedagogicalBlocks(content);

  const handleSpeak = (text: string, idx: number) => {
    setPlayingIdx(idx);
    speakJapaneseSpeech(text);
    setTimeout(() => setPlayingIdx(null), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', width: '100%' }}>
      {blocks.map((block, bIdx) => {
        const isJp = hasJapaneseText(block.rawText);

        if (!isJp) {
          return (
            <div key={bIdx} style={{ fontSize: '0.92rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
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
              gap: '6px',
              padding: '6px 0',
              borderBottom: bIdx < blocks.length - 1 ? '1px dashed var(--border-subtle)' : 'none',
              paddingBottom: bIdx < blocks.length - 1 ? '12px' : '4px',
            }}
          >
            {/* Top row: Word tokens + Speaker button */}
            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '8px' }}>
              {/* Words row */}
              <div
                style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'flex-end',
                  columnGap: '12px',
                  rowGap: '10px',
                }}
              >
                {block.tokens.map((token, tIdx) => {
                  const isGreen = highlightGrammar && token.grammarHighlight === 'green';
                  const isOrange = highlightGrammar && token.grammarHighlight === 'orange';

                  return (
                    <div
                      key={tIdx}
                      style={{
                        display: 'inline-flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        minWidth: '20px',
                      }}
                    >
                      {/* 1. Furigana (Hiragana reading above Kanji) */}
                      {showFurigana && (
                        <span
                          style={{
                            fontSize: '0.68rem',
                            color: 'var(--text-secondary)',
                            lineHeight: 1,
                            minHeight: '13px',
                            fontWeight: 400,
                            letterSpacing: '0.02em',
                          }}
                        >
                          {token.furigana || ''}
                        </span>
                      )}

                      {/* 2. Main Japanese Word / Kanji */}
                      <span
                        style={{
                          fontSize: '1.18rem',
                          fontWeight: isGreen || isOrange ? 600 : 500,
                          color: isGreen
                            ? 'var(--accent, #16a34a)'
                            : isOrange
                            ? '#ea580c'
                            : 'var(--text-primary)',
                          lineHeight: 1.35,
                          padding: isGreen || isOrange ? '1px 7px' : '1px 2px',
                          borderRadius: isGreen || isOrange ? '6px' : '0',
                          border: isGreen ? '1.5px solid var(--accent, #22c55e)' : 'none',
                          backgroundColor: isGreen
                            ? 'rgba(34, 197, 94, 0.12)'
                            : isOrange
                            ? 'rgba(254, 215, 170, 0.75)'
                            : 'transparent',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        {token.text}
                      </span>

                      {/* 3. Romaji (Pronunciation underneath) */}
                      {showRomaji && token.romaji && (
                        <span
                          style={{
                            fontSize: '0.72rem',
                            color: 'var(--text-muted)',
                            lineHeight: 1,
                            marginTop: '3px',
                            fontFamily: 'var(--font-sans)',
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
                  title="Nghe phát âm tiếng Nhật chuẩn giọng Tokyo"
                  aria-label="Phát âm tiếng Nhật"
                  style={{
                    background: playingIdx === bIdx ? 'var(--bg-selected)' : 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-full)',
                    width: '28px',
                    height: '28px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    color: playingIdx === bIdx ? 'var(--accent)' : 'var(--text-muted)',
                    transition: 'all var(--transition-fast)',
                    flexShrink: 0,
                    marginBottom: '4px',
                  }}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
                  </svg>
                </button>
              )}
            </div>

            {/* 4. Display Language Translation (Below Japanese Sentence) */}
            {showTranslation && block.translation && (
              <div
                style={{
                  fontSize: '0.88rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5,
                  paddingLeft: '2px',
                  marginTop: '2px',
                }}
              >
                {block.translation}
              </div>
            )}
          </div>
        );
      })}

      {isStreaming && <span className="cursor-blink" aria-hidden="true" />}
    </div>
  );
}


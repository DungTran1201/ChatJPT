'use client';

import React from 'react';

export interface GrammarItem {
  term: string;
  category?: string;
  meaning: string;
  nuance?: string;
}

interface GrammarBreakdownCardProps {
  items?: GrammarItem[];
  rawText?: string;
  title?: string;
}

/**
 * Parses raw markdown text from LLM into structured grammar items
 */
export function parseGrammarItemsFromText(rawText: string): GrammarItem[] {
  if (!rawText || !rawText.trim()) return [];

  // Remove heading lines like "### 🔍 Phân tích Ngữ pháp & Từ vựng" or "---"
  const lines = rawText
    .split('\n')
    .map(l => l.trim())
    .filter(l => l && !l.startsWith('#') && l !== '---' && l !== '***');

  const items: GrammarItem[] = [];

  // Check if format is numbered: "1. **【term】**" or "1. **term**"
  let currentItem: Partial<GrammarItem> | null = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Check numbered header: "1. **...**" or "1. 【...】" or "1. ..."
    const numMatch = line.match(/^(\d+)\.\s+(\*\*.*?\*\*|【.*?】|.*)/);
    if (numMatch) {
      if (currentItem && currentItem.meaning) {
        items.push({
          term: currentItem.term || `Điểm ${items.length + 1}`,
          category: currentItem.category,
          meaning: currentItem.meaning,
          nuance: currentItem.nuance,
        });
      }

      let headerContent = numMatch[2].replace(/^\*\*/, '').replace(/\*\*$/, '').trim();
      let category: string | undefined = undefined;

      // Extract category in parentheses or asterisks if present, e.g. *(Khiêm nhường ngữ)* or (N2)
      const catMatch = headerContent.match(/[\(\*]+([^()\*]+)[\)\*]+$/);
      if (catMatch) {
        category = catMatch[1].trim();
        headerContent = headerContent.slice(0, catMatch.index).trim();
      }

      currentItem = {
        term: headerContent,
        category,
        meaning: '',
        nuance: '',
      };
      continue;
    }

    // Check meaning line: "- *Ý nghĩa:* ..." or "• *Ý nghĩa:* ..." or "Ý nghĩa: ..."
    const meaningMatch = line.match(/^[-*•]?\s*\*?(?:Ý nghĩa|Nghĩa|Meaning)\*?\s*:\s*(.*)/i);
    if (meaningMatch) {
      const text = meaningMatch[1].trim();
      if (!currentItem) {
        // Paired bullet format (Image 1 & 2): extract term if mentioned in parentheses
        let term = `Mục ${items.length + 1}`;
        let category: string | undefined = undefined;

        const parenMatch = text.match(/[\(（]([^\)）]+)[\)）]$/);
        if (parenMatch) {
          const parenContent = parenMatch[1].trim();
          term = parenContent.replace(/^(Trợ từ|Khiêm nhường ngữ của|Thể|Cấu trúc)\s*/i, '');
          if (!term.startsWith('【')) term = `【${term}】`;
          category = parenContent;
        }

        currentItem = {
          term,
          category,
          meaning: text,
          nuance: '',
        };
      } else {
        currentItem.meaning = text;
      }
      continue;
    }

    // Check nuance line: "- *Sắc thái:* ..." or "• *Sắc thái:* ..."
    const nuanceMatch = line.match(/^[-*•]?\s*\*?(?:Sắc thái|Cách dùng|Nuance|Usage)\*?\s*:\s*(.*)/i);
    if (nuanceMatch) {
      const text = nuanceMatch[1].trim();
      if (currentItem) {
        currentItem.nuance = text;
        items.push({
          term: currentItem.term || `Điểm ${items.length + 1}`,
          category: currentItem.category,
          meaning: currentItem.meaning || '',
          nuance: currentItem.nuance,
        });
        currentItem = null;
      }
      continue;
    }

    // Fallback bullet line
    if (line.startsWith('- ') || line.startsWith('• ') || line.startsWith('* ')) {
      const bulletContent = line.replace(/^[-•*]\s*/, '').trim();
      if (currentItem) {
        if (!currentItem.meaning) currentItem.meaning = bulletContent;
        else currentItem.nuance = (currentItem.nuance ? currentItem.nuance + ' ' : '') + bulletContent;
      } else {
        items.push({
          term: `【Điểm ngữ pháp ${items.length + 1}】`,
          meaning: bulletContent,
        });
      }
    }
  }

  if (currentItem && currentItem.meaning) {
    items.push({
      term: currentItem.term || `Điểm ${items.length + 1}`,
      category: currentItem.category,
      meaning: currentItem.meaning,
      nuance: currentItem.nuance,
    });
  }

  return items;
}

export default function GrammarBreakdownCard({
  items,
  rawText,
  title = 'PHÂN TÍCH NGỮ PHÁP & TỪ VỰNG',
}: GrammarBreakdownCardProps) {
  const grammarItems = items && items.length > 0 ? items : (rawText ? parseGrammarItemsFromText(rawText) : []);

  if (grammarItems.length === 0 && !rawText) return null;

  return (
    <div
      style={{
        marginTop: '1.25rem',
        marginBottom: '0.75rem',
        borderRadius: 'var(--radius-lg, 10px)',
        backgroundColor: 'var(--bg-surface)',
        border: '1.5px solid var(--border-default)',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.1))',
      }}
    >
      {/* Framed Header Banner */}
      <div
        style={{
          padding: '10px 16px',
          background: 'rgba(16, 185, 129, 0.08)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: 'var(--accent, #10b981)',
            fontWeight: 700,
            fontSize: '0.9rem',
            letterSpacing: '0.02em',
          }}
        >
          <span style={{ fontSize: '1.05rem' }}>🔍</span>
          <span>{title}</span>
        </div>
        <span
          style={{
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            backgroundColor: 'var(--bg-base)',
            padding: '2px 8px',
            borderRadius: '12px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          {grammarItems.length} cấu trúc trọng tâm
        </span>
      </div>

      {/* Framed Cards Body */}
      <div
        style={{
          padding: '12px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}
      >
        {grammarItems.map((item, idx) => (
          <div
            key={idx}
            style={{
              padding: '10px 14px',
              borderRadius: 'var(--radius-md, 8px)',
              backgroundColor: 'var(--bg-base)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
              transition: 'border-color 0.15s ease',
            }}
          >
            {/* Header: Number Badge + Term Tag + Category Pill */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  backgroundColor: 'var(--accent, #10b981)',
                  color: '#fff',
                  borderRadius: '50%',
                  width: '18px',
                  height: '18px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                {idx + 1}
              </span>
              <span
                style={{
                  fontSize: '0.94rem',
                  fontWeight: 600,
                  color: 'var(--accent, #10b981)',
                  backgroundColor: 'rgba(34, 197, 94, 0.12)',
                  border: '1px solid rgba(34, 197, 94, 0.3)',
                  borderRadius: '6px',
                  padding: '1px 8px',
                }}
              >
                {item.term}
              </span>
              {item.category && (
                <span
                  style={{
                    fontSize: '0.74rem',
                    color: 'var(--text-secondary)',
                    backgroundColor: 'var(--bg-elevated)',
                    padding: '2px 7px',
                    borderRadius: '4px',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  {item.category}
                </span>
              )}
            </div>

            {/* Meaning */}
            {item.meaning && (
              <div
                style={{
                  fontSize: '0.88rem',
                  lineHeight: 1.55,
                  color: 'var(--text-primary)',
                  paddingLeft: '2px',
                }}
              >
                <span style={{ fontWeight: 600, color: 'var(--text-secondary)', marginRight: '6px' }}>
                  Ý nghĩa:
                </span>
                <span>{item.meaning}</span>
              </div>
            )}

            {/* Nuance / Usage */}
            {item.nuance && (
              <div
                style={{
                  fontSize: '0.85rem',
                  lineHeight: 1.55,
                  color: 'var(--text-secondary)',
                  paddingLeft: '2px',
                }}
              >
                <span style={{ fontWeight: 600, color: 'var(--text-muted)', marginRight: '6px' }}>
                  Sắc thái & Cách dùng:
                </span>
                <span>{item.nuance}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

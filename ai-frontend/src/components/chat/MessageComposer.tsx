'use client';

import React, { useState, useRef, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { AgentModel, SystemPromptSummary } from '@/types';
import { SystemPromptService } from '@/services/systemPromptService';
import {
  AttachmentButton,
  ComposerAttachmentChips,
  StagedFile
} from '@/components/ui/AttachmentUploader';
import { AttachmentService } from '@/services/attachmentService';
import { useApp } from '@/context/AppContext';

interface MessageComposerProps {
  inputPrompt: string;
  onInputChange: (val: string) => void;
  onSend: (customPrompt?: string, attachmentIds?: string[]) => void;
  onStop?: () => void;
  isStreaming?: boolean;
  activeModels?: AgentModel[];
  selectedModelId?: string;
  onSelectModel?: (modelId: string) => void;
  selectedSenseiId?: string;
  onSelectSensei?: (senseiId: string) => void;
  placeholder?: string;
}

function getLevelBg(level?: string) {
  switch ((level || '').toUpperCase()) {
    case 'N5': return 'rgba(16, 185, 129, 0.15)'; // Emerald
    case 'N4': return 'rgba(59, 130, 246, 0.15)'; // Blue
    case 'N3': return 'rgba(245, 158, 11, 0.15)'; // Amber
    case 'N2': return 'rgba(139, 92, 246, 0.15)'; // Violet
    case 'N1': return 'rgba(244, 63, 94, 0.15)';  // Rose
    default:   return 'rgba(107, 114, 128, 0.15)';
  }
}

function getLevelColor(level?: string) {
  switch ((level || '').toUpperCase()) {
    case 'N5': return '#10b981';
    case 'N4': return '#3b82f6';
    case 'N3': return '#f59e0b';
    case 'N2': return '#8b5cf6';
    case 'N1': return '#f43f5e';
    default:   return '#9ca3af';
  }
}

export default function MessageComposer({
  inputPrompt,
  onInputChange,
  onSend,
  onStop,
  isStreaming = false,
  activeModels = [],
  selectedModelId = 'gemini-3.8-flash',
  onSelectModel,
  selectedSenseiId = 'sensei_sakura_n5',
  onSelectSensei,
  placeholder = 'Message AI-Chan…',
}: MessageComposerProps) {
  const { t } = useApp();
  const [isFocused, setIsFocused] = useState(false);
  const [showDualSelector, setShowDualSelector] = useState(false);
  const [stagedFiles, setStagedFiles] = useState<StagedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);

  // Sensei Guidance state
  const [senseis, setSenseis] = useState<SystemPromptSummary[]>([]);
  const [loadingSenseis, setLoadingSenseis] = useState(false);
  const [senseiSearch, setSenseiSearch] = useState('');
  const [senseiLevelFilter, setSenseiLevelFilter] = useState('ALL');

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Auto resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollH = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(Math.max(scrollH, 44), 160)}px`;
    }
  }, [inputPrompt]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDualSelector(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Fetch Senseis for composer selector
  useEffect(() => {
    let isCancelled = false;
    const fetchSenseis = async () => {
      try {
        setLoadingSenseis(true);
        const res = await SystemPromptService.getPrompts('', 'level_asc', 'ALL');
        if (!isCancelled) {
          setSenseis(res.items || res.prompts || []);
        }
      } catch (err) {
        console.error('Failed to load Senseis in composer:', err);
      } finally {
        if (!isCancelled) setLoadingSenseis(false);
      }
    };
    fetchSenseis();
    return () => { isCancelled = true; };
  }, []);

  // Filtered Senseis list
  const filteredSenseis = useMemo(() => {
    return senseis.filter(s => {
      const matchLevel = senseiLevelFilter === 'ALL' || (s.japanese_level || 'N5').toUpperCase() === senseiLevelFilter.toUpperCase();
      if (!matchLevel) return false;
      if (!senseiSearch.trim()) return true;
      const q = senseiSearch.toLowerCase().trim();
      return (
        s.name.toLowerCase().includes(q) ||
        (s.personality && s.personality.toLowerCase().includes(q)) ||
        (s.teaching_style && s.teaching_style.toLowerCase().includes(q)) ||
        (s.catchphrase && s.catchphrase.toLowerCase().includes(q)) ||
        (s.description && s.description.toLowerCase().includes(q))
      );
    });
  }, [senseis, senseiLevelFilter, senseiSearch]);

  const activeSensei = senseis.find(s => s.id === selectedSenseiId) || senseis[0] || {
    id: selectedSenseiId || 'sensei_sakura_n5',
    name: 'Sakura Sensei (桜先生)',
    japanese_level: 'N5',
    age: 24,
    gender: 'female',
    personality: 'Gentle, patient',
    avatar_url: 'https://api.dicebear.com/7.x/bottts/svg?seed=sakura',
  };

  const currentModel = activeModels.find(m => m.id === selectedModelId) || {
    id: selectedModelId,
    name: selectedModelId.includes('gemini') ? 'Gemini 2.5 Flash' : selectedModelId,
    provider: 'Google Gemini',
  };

  const handleUploadFiles = async (files: File[]) => {
    const BLOCKED_EXTS = ['.exe', '.bat', '.ps1', '.sh', '.cmd', '.dll', '.com'];
    const MAX_SIZE_BYTES = 20 * 1024 * 1024; // 20 MB

    for (const f of files) {
      const lowerName = f.name.toLowerCase();
      const isBlocked = BLOCKED_EXTS.some(ext => lowerName.endsWith(ext));
      if (isBlocked) {
        alert(`File '${f.name}' was blocked for safety reasons.`);
        continue;
      }
      if (f.size > MAX_SIZE_BYTES) {
        alert(`File '${f.name}' exceeds the maximum allowed size (20 MB).`);
        continue;
      }
      if (f.size === 0) {
        alert(`File '${f.name}' is empty (0 bytes).`);
        continue;
      }

      const tempId = `temp_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const newStaged: StagedFile = {
        id: tempId,
        file: f,
        name: f.name,
        size: f.size,
        mime: f.type || 'application/octet-stream',
        status: 'UPLOADING',
        progress: 0,
      };

      setStagedFiles(prev => [...prev, newStaged]);

      try {
        const att = await AttachmentService.uploadAttachment(
          f,
          'chat',
          undefined,
          (percent) => {
            setStagedFiles(prev =>
              prev.map(item => (item.id === tempId ? { ...item, progress: percent } : item))
            );
          }
        );
        setStagedFiles(prev =>
          prev.map(item =>
            item.id === tempId
              ? {
                  ...item,
                  id: att.id,
                  status: 'READY',
                  progress: 100,
                }
              : item
          )
        );
      } catch (err: any) {
        setStagedFiles(prev =>
          prev.map(item =>
            item.id === tempId
              ? {
                  ...item,
                  status: 'FAILED',
                  error: err.message || 'File upload failed',
                }
              : item
          )
        );
      }
    }
  };

  const handleRemoveStagedFile = (idx: number) => {
    setStagedFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const handleRetryStagedFile = (idx: number) => {
    const item = stagedFiles[idx];
    if (item.file) {
      handleRemoveStagedFile(idx);
      handleUploadFiles([item.file]);
    }
  };

  const handleSendMessageWithAttachments = () => {
    const isUploadingAny = stagedFiles.some(f => f.status === 'UPLOADING');
    if (isUploadingAny) {
      alert('Please wait for files to finish uploading.');
      return;
    }
    const readyIds = stagedFiles.filter(f => f.status === 'READY' && f.id).map(f => f.id!);
    onSend(undefined, readyIds.length > 0 ? readyIds : undefined);
    setStagedFiles([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const hasReady = stagedFiles.some(f => f.status === 'READY');
      if (!isStreaming && (inputPrompt.trim() || hasReady)) {
        handleSendMessageWithAttachments();
      }
    }
  };

  const hasInput = inputPrompt.trim().length > 0 || stagedFiles.some(f => f.status === 'READY');

  return (
    <div
      style={{
        width: '100%',
        maxWidth: '760px',
        margin: '0 auto',
        padding: '0 0 1.25rem',
        position: 'relative',
        zIndex: 20,
      }}
    >
      <div
        ref={dropdownRef}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleUploadFiles(Array.from(e.dataTransfer.files));
          }
        }}
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: isDragOver
            ? '1px dashed var(--accent)'
            : isFocused
            ? '1px solid var(--border-strong)'
            : '1px solid var(--border-default)',
          borderRadius: 'var(--radius-xl)',
          padding: '10px 14px 8px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          transition: 'border-color var(--transition-fast)',
          boxShadow: '0 4px 24px rgba(0,0,0,0.35)',
        }}
      >
        {/* Attached files preview chips */}
        <ComposerAttachmentChips
          files={stagedFiles}
          onRemove={handleRemoveStagedFile}
          onRetry={handleRetryStagedFile}
        />

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={inputPrompt}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          aria-label="Message input"
          rows={1}
          style={{
            width: '100%',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-primary)',
            fontSize: '0.9rem',
            lineHeight: 1.55,
            resize: 'none',
            outline: 'none',
            fontFamily: 'var(--font-sans)',
            minHeight: '44px',
            maxHeight: '160px',
            overflowY: 'auto',
          }}
        />

        {/* Toolbar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: '4px',
            borderTop: '1px solid var(--border-subtle)',
          }}
        >
          {/* Left: attachments */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <AttachmentButton onFilesSelected={handleUploadFiles} disabled={isStreaming} />
          </div>

          {/* Right: Dual Sensei & Model Selector + Send */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Dual Selector Trigger Button */}
            <div style={{ position: 'relative' }}>
              <button
                type="button"
                onClick={() => setShowDualSelector(v => !v)}
                title={t('composer.selector_title')}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  background: 'var(--bg-elevated)',
                  border: showDualSelector ? '1px solid var(--accent)' : '1px solid var(--border-subtle)',
                  color: 'var(--text-primary)',
                  fontSize: '0.76rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                  transition: 'color var(--transition-fast), border-color var(--transition-fast)',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--border-default)';
                }}
                onMouseLeave={e => {
                  if (!showDualSelector) e.currentTarget.style.borderColor = 'var(--border-subtle)';
                }}
              >
                {/* Sensei Avatar */}
                <img
                  src={activeSensei.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${activeSensei.id}`}
                  alt={activeSensei.name}
                  style={{ width: '18px', height: '18px', borderRadius: '50%', objectFit: 'cover' }}
                />

                {/* Sensei Name */}
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '110px' }}>
                  {activeSensei.name}
                </span>

                {/* Level badge */}
                <span
                  style={{
                    fontSize: '0.62rem',
                    fontWeight: 700,
                    padding: '1px 5px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: getLevelBg(activeSensei.japanese_level),
                    color: getLevelColor(activeSensei.japanese_level),
                  }}
                >
                  {activeSensei.japanese_level || 'N5'}
                </span>

                {/* Separator dot */}
                <span style={{ color: 'var(--text-disabled)', fontSize: '0.7rem' }}>•</span>

                {/* Model tag */}
                <span style={{ color: 'var(--accent)', fontSize: '0.72rem' }}>⚡</span>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100px', color: 'var(--text-secondary)' }}>
                  {currentModel.name || selectedModelId}
                </span>

                {/* Chevron */}
                <svg
                  width="10"
                  height="10"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden="true"
                  style={{
                    transform: showDualSelector ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform var(--transition-fast)',
                    color: 'var(--text-disabled)',
                  }}
                >
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>

              {/* ── Dual-Column Popover: Sensei List (Left) & Model List (Right) ── */}
              {showDualSelector && (
                <div
                  style={{
                    position: 'absolute',
                    bottom: '100%',
                    right: 0,
                    marginBottom: '8px',
                    width: '600px',
                    maxWidth: 'calc(100vw - 32px)',
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-xl)',
                    boxShadow: '0 16px 40px rgba(0,0,0,0.6)',
                    backdropFilter: 'blur(16px)',
                    zIndex: 60,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                  }}
                >
                  {/* Popover Header */}
                  <div
                    style={{
                      padding: '10px 14px',
                      borderBottom: '1px solid var(--border-subtle)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: 'var(--bg-elevated)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '1rem' }}>🎓</span>
                      <span style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {t('composer.selector_title')}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowDualSelector(false)}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-disabled)',
                        cursor: 'pointer',
                        padding: '2px 4px',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </div>

                  {/* Dual Column Layout */}
                  <div style={{ display: 'flex', minHeight: '330px' }}>
                    {/* ── Left Column: Sensei List (Independent Scroll) ── */}
                    <div
                      style={{
                        width: '340px',
                        borderRight: '1px solid var(--border-subtle)',
                        display: 'flex',
                        flexDirection: 'column',
                        padding: '10px 12px',
                        gap: '8px',
                      }}
                    >
                      {/* Column Header */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-disabled)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                          {t('composer.sensei_col_title')} ({filteredSenseis.length})
                        </span>
                        <Link
                          href="/prompts"
                          style={{ fontSize: '0.7rem', color: 'var(--accent)', textDecoration: 'none' }}
                          onClick={() => setShowDualSelector(false)}
                        >
                          {t('composer.manage_sensei')}
                        </Link>
                      </div>

                      {/* Search Bar */}
                      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                        <svg
                          width="12"
                          height="12"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          style={{ position: 'absolute', left: '8px', color: 'var(--text-disabled)', pointerEvents: 'none' }}
                        >
                          <circle cx="11" cy="11" r="8"/>
                          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                        </svg>
                        <input
                          type="text"
                          value={senseiSearch}
                          onChange={(e) => setSenseiSearch(e.target.value)}
                          placeholder={t('composer.search_sensei_placeholder')}
                          style={{
                            width: '100%',
                            padding: '5px 24px 5px 26px',
                            fontSize: '0.75rem',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid var(--border-default)',
                            backgroundColor: 'var(--bg-elevated)',
                            color: 'var(--text-primary)',
                            outline: 'none',
                          }}
                        />
                        {senseiSearch && (
                          <button
                            type="button"
                            onClick={() => setSenseiSearch('')}
                            style={{
                              position: 'absolute',
                              right: '6px',
                              background: 'transparent',
                              border: 'none',
                              color: 'var(--text-disabled)',
                              cursor: 'pointer',
                              fontSize: '0.75rem',
                              padding: 0,
                            }}
                          >
                            ✕
                          </button>
                        )}
                      </div>

                      {/* JLPT Level Filter Chips */}
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {['ALL', 'N5', 'N4', 'N3', 'N2', 'N1'].map((lvl) => {
                          const isChipActive = senseiLevelFilter === lvl;
                          return (
                            <button
                              key={lvl}
                              type="button"
                              onClick={() => setSenseiLevelFilter(lvl)}
                              style={{
                                padding: '2px 7px',
                                borderRadius: 'var(--radius-full)',
                                fontSize: '0.67rem',
                                fontWeight: 600,
                                cursor: 'pointer',
                                border: isChipActive ? '1px solid var(--accent)' : '1px solid var(--border-subtle)',
                                backgroundColor: isChipActive ? 'var(--accent)' : 'var(--bg-elevated)',
                                color: isChipActive ? 'var(--accent-fg)' : 'var(--text-secondary)',
                                transition: 'all var(--transition-fast)',
                              }}
                            >
                              {lvl === 'ALL' ? t('composer.all_levels') : lvl}
                            </button>
                          );
                        })}
                      </div>

                      {/* Independent Scrollable Sensei List */}
                      <div
                        className="custom-scrollbar"
                        onWheel={(e) => e.stopPropagation()}
                        style={{
                          flex: 1,
                          maxHeight: '230px',
                          overflowY: 'auto',
                          overscrollBehavior: 'contain',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                          paddingRight: '4px',
                        }}
                      >
                        {loadingSenseis ? (
                          <div style={{ padding: '20px', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-disabled)' }}>
                            {t('composer.loading_sensei')}
                          </div>
                        ) : filteredSenseis.length === 0 ? (
                          <div style={{ padding: '20px', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-disabled)' }}>
                            {t('composer.no_sensei_found')}
                          </div>
                        ) : (
                          filteredSenseis.map((s) => {
                            const isSelected = selectedSenseiId === s.id;
                            return (
                              <div
                                key={s.id}
                                onClick={() => onSelectSensei?.(s.id)}
                                role="option"
                                aria-selected={isSelected}
                                style={{
                                  display: 'flex',
                                  alignItems: 'flex-start',
                                  gap: '8px',
                                  padding: '7px 8px',
                                  borderRadius: 'var(--radius-md)',
                                  cursor: 'pointer',
                                  border: isSelected ? '1px solid var(--accent)' : '1px solid var(--border-subtle)',
                                  backgroundColor: isSelected ? 'var(--bg-selected)' : 'var(--bg-elevated)',
                                  transition: 'all var(--transition-fast)',
                                }}
                              >
                                <img
                                  src={s.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${s.id}`}
                                  alt={s.name}
                                  style={{ width: '32px', height: '32px', borderRadius: '50%', objectFit: 'cover', flexShrink: 0, marginTop: '2px' }}
                                />
                                <div style={{ flex: 1, minWidth: 0 }}>
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '4px' }}>
                                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                      {s.name}
                                    </span>
                                    <span
                                      style={{
                                        fontSize: '0.62rem',
                                        fontWeight: 700,
                                        padding: '1px 5px',
                                        borderRadius: 'var(--radius-full)',
                                        backgroundColor: getLevelBg(s.japanese_level),
                                        color: getLevelColor(s.japanese_level),
                                        flexShrink: 0,
                                      }}
                                    >
                                      {s.japanese_level || 'N5'}
                                    </span>
                                  </div>
                                  <div style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '1px' }}>
                                    {s.age ? `${s.age}t` : ''} {s.personality ? `• ${s.personality}` : ''}
                                  </div>
                                  {s.catchphrase && (
                                    <div style={{ fontSize: '0.65rem', color: 'var(--accent)', fontStyle: 'italic', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                      {s.catchphrase}
                                    </div>
                                  )}
                                </div>
                                {isSelected && (
                                  <div style={{ color: 'var(--accent)', marginTop: '4px', flexShrink: 0 }}>
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                      <polyline points="20 6 9 17 4 12"/>
                                    </svg>
                                  </div>
                                )}
                              </div>
                            );
                          })
                        )}
                      </div>
                    </div>

                    {/* ── Right Column: AI Model Engine (Independent Scroll) ── */}
                    <div
                      style={{
                        width: '260px',
                        display: 'flex',
                        flexDirection: 'column',
                        padding: '10px 12px',
                        gap: '8px',
                        backgroundColor: 'rgba(255, 255, 255, 0.01)',
                      }}
                    >
                      {/* Column Header */}
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-disabled)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                          {t('composer.model_col_title')} ({activeModels.length})
                        </span>
                        <span style={{ fontSize: '0.68rem', color: 'var(--accent)', fontWeight: 600 }}>
                          Auto Failover
                        </span>
                      </div>

                      {/* Independent Scrollable Model List */}
                      <div
                        className="custom-scrollbar"
                        onWheel={(e) => e.stopPropagation()}
                        style={{
                          flex: 1,
                          maxHeight: '280px',
                          overflowY: 'auto',
                          overscrollBehavior: 'contain',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                          paddingRight: '4px',
                        }}
                      >
                        {activeModels.length > 0 ? (
                          activeModels.map((m) => {
                            const isSelected = selectedModelId === m.id;
                            return (
                              <div
                                key={m.id}
                                onClick={() => onSelectModel?.(m.id)}
                                role="option"
                                aria-selected={isSelected}
                                style={{
                                  display: 'flex',
                                  flexDirection: 'column',
                                  gap: '2px',
                                  padding: '8px 10px',
                                  borderRadius: 'var(--radius-md)',
                                  cursor: 'pointer',
                                  border: isSelected ? '1px solid var(--accent)' : '1px solid var(--border-subtle)',
                                  backgroundColor: isSelected ? 'var(--bg-selected)' : 'var(--bg-elevated)',
                                  transition: 'all var(--transition-fast)',
                                }}
                              >
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                                    {m.name}
                                  </span>
                                  {isSelected && (
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ color: 'var(--accent)' }}>
                                      <polyline points="20 6 9 17 4 12"/>
                                    </svg>
                                  )}
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--text-disabled)' }}>
                                  <span>{m.provider || 'AI Provider'}</span>
                                  {m.id === 'offline-semantic-cache' ? (
                                    <span style={{ color: 'var(--accent)', fontWeight: 600 }}>0ms Offline</span>
                                  ) : (
                                    <span>{m.context_window ? `${(m.context_window/1000).toFixed(0)}k ctx` : '~100ms'}</span>
                                  )}
                                </div>
                              </div>
                            );
                          })
                        ) : (
                          <>
                            <div
                              onClick={() => onSelectModel?.('gemini-3.8-flash')}
                              style={{
                                padding: '8px 10px',
                                borderRadius: 'var(--radius-md)',
                                cursor: 'pointer',
                                border: selectedModelId === 'gemini-3.8-flash' ? '1px solid var(--accent)' : '1px solid var(--border-subtle)',
                                backgroundColor: selectedModelId === 'gemini-3.8-flash' ? 'var(--bg-selected)' : 'var(--bg-elevated)',
                              }}
                            >
                              <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>Gemini 2.5 Flash</div>
                              <div style={{ fontSize: '0.68rem', color: 'var(--text-disabled)' }}>Google Gemini • {t('composer.recommended')}</div>
                            </div>
                            <div
                              onClick={() => onSelectModel?.('gpt-4o-mini')}
                              style={{
                                padding: '8px 10px',
                                borderRadius: 'var(--radius-md)',
                                cursor: 'pointer',
                                border: selectedModelId === 'gpt-4o-mini' ? '1px solid var(--accent)' : '1px solid var(--border-subtle)',
                                backgroundColor: selectedModelId === 'gpt-4o-mini' ? 'var(--bg-selected)' : 'var(--bg-elevated)',
                              }}
                            >
                              <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>GPT-4o mini</div>
                              <div style={{ fontSize: '0.68rem', color: 'var(--text-disabled)' }}>OpenAI • {t('composer.fallback')}</div>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Popover Footer Bar */}
                  <div
                    style={{
                      padding: '8px 14px',
                      borderTop: '1px solid var(--border-subtle)',
                      background: 'var(--bg-elevated)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '0.75rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
                      <span>{t('composer.currently_selected')}</span>
                      <strong style={{ color: 'var(--text-primary)' }}>{activeSensei.name}</strong>
                      <span style={{ color: 'var(--text-disabled)' }}>•</span>
                      <strong style={{ color: 'var(--accent)' }}>{currentModel.name}</strong>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowDualSelector(false)}
                      style={{
                        padding: '4px 14px',
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--accent)',
                        border: 'none',
                        color: 'var(--accent-fg)',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      {t('composer.apply')}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Send / Stop Generation */}
            {isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                aria-label="Stop generation"
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: 'var(--danger-bg)',
                  border: '1px solid rgba(239,68,68,0.3)',
                  color: 'var(--danger)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'background var(--transition-fast)',
                }}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"/></svg>
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSendMessageWithAttachments}
                disabled={!hasInput}
                aria-label="Send message"
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: hasInput ? 'var(--text-primary)' : 'var(--bg-elevated)',
                  border: hasInput ? 'none' : '1px solid var(--border-subtle)',
                  color: hasInput ? 'var(--bg-base)' : 'var(--text-disabled)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: hasInput ? 'pointer' : 'default',
                  transition: 'background var(--transition-fast), color var(--transition-fast)',
                }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Footer hint */}
      <p style={{ textAlign: 'center', fontSize: '0.7rem', color: 'var(--text-disabled)', marginTop: '6px' }}>
        AI-Chan can make mistakes. Press <kbd style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', padding: '0 3px', border: '1px solid var(--border-subtle)', borderRadius: '3px' }}>Shift+Enter</kbd> for a new line.
      </p>
    </div>
  );
}

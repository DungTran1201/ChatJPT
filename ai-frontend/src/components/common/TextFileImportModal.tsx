'use client';

import React, { useState, useEffect, useRef } from 'react';
import Icon from '@/components/ui/Icon';
import SafeMarkdownViewer from '@/components/rules/SafeMarkdownViewer';
import {
  ALLOWED_TEXT_EXTENSIONS,
  readAndValidateTextFile,
  extractItemMetadata,
  ParsedItemMetadata,
  toKebabCase,
} from '@/lib/textImportParser';
import { RuleService } from '@/services/ruleService';
import { SystemPromptService } from '@/services/systemPromptService';
import { formatErrorMessage } from '@/lib/errors';

export interface TextFileImportModalProps {
  isOpen: boolean;
  target: 'rules' | 'prompts';
  existingNames?: string[];
  onClose: () => void;
  onSuccess: (importedItem: any) => void;
}

export default function TextFileImportModal({
  isOpen,
  target,
  existingNames = [],
  onClose,
  onSuccess,
}: TextFileImportModalProps) {
  const [dragOver, setDragOver] = useState(false);
  const [isReading, setIsReading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Parsed metadata state
  const [metadata, setMetadata] = useState<ParsedItemMetadata | null>(null);

  // Form edit fields
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [previewTab, setPreviewTab] = useState<'formatted' | 'raw'>('formatted');

  // Specific to Rules
  const [activationMode, setActivationMode] = useState<'always_on' | 'model_decision' | 'glob' | 'manual'>('always_on');
  const [globPatternsText, setGlobPatternsText] = useState('');
  const [tagsText, setTagsText] = useState('');
  const [priority, setPriority] = useState<number>(50);



  const fileInputRef = useRef<HTMLInputElement>(null);

  // Reset state on open/close
  useEffect(() => {
    if (!isOpen) {
      setMetadata(null);
      setError(null);
      setName('');
      setDescription('');
      setDragOver(false);
      setIsReading(false);
      setIsImporting(false);
    }
  }, [isOpen]);

  // Keyboard accessibility: Escape to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isImporting) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isImporting, onClose]);

  if (!isOpen) return null;

  const targetTitles = {
    rules: {
      modalTitle: 'Import Grammar Rule from File',
      itemType: 'Rule',
      hint: 'Supports Markdown (.md), text (.txt, .rst), or structured config (.yaml, .json).',
    },
    prompts: {
      modalTitle: 'Import Sensei Prompt from File',
      itemType: 'System Prompt',
      hint: 'Supports text or Markdown files. Preserves UTF-8 Unicode, Japanese kanji/kana, and emojis.',
    },
  };

  const currentConfig = targetTitles[target];

  // Process chosen file
  const handleFileProcess = async (file: File) => {
    try {
      setIsReading(true);
      setError(null);
      const readResult = await readAndValidateTextFile(file);
      const parsed = extractItemMetadata(target, readResult.filename, readResult.content, readResult.sizeBytes);

      setMetadata(parsed);
      setName(parsed.name);
      setDescription(parsed.description);

      if (target === 'rules') {
        setActivationMode(parsed.activation_mode || 'always_on');
        setGlobPatternsText(parsed.glob_patterns?.join(', ') || '');
        setTagsText(parsed.tags?.join(', ') || 'imported');
        setPriority(parsed.priority !== undefined ? parsed.priority : 50);
      }
    } catch (err: any) {
      setError(err.message || 'Error reading file.');
    } finally {
      setIsReading(false);
    }
  };

  const onFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileProcess(files[0]);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileProcess(files[0]);
    }
  };

  // Check collision with existing items
  const normalizedCurrentName = name.trim().toLowerCase();
  const isDuplicate = existingNames.some(n => n.trim().toLowerCase() === normalizedCurrentName);

  // Submit Handler
  const handleImportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!metadata || isImporting) return;

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError('Item name cannot be empty.');
      return;
    }

    try {
      setIsImporting(true);
      setError(null);

      let createdItem: any = null;

      if (target === 'rules') {
        const globs = globPatternsText
          .split(',')
          .map(s => s.trim())
          .filter(Boolean);
        const tags = tagsText
          .split(',')
          .map(s => s.trim())
          .filter(Boolean);

        createdItem = await RuleService.importRuleText({
          filename: metadata.filename,
          content: metadata.content,
          name: trimmedName,
          description: description.trim() || undefined,
          activation_mode: activationMode,
          glob_patterns: globs,
          tags: tags.length > 0 ? tags : ['imported'],
          priority: Number(priority) || 50,
        });
      } else {
        // Prompts
        createdItem = await SystemPromptService.importPromptText({
          filename: metadata.filename,
          content: metadata.content,
          name: trimmedName,
          description: description.trim() || undefined,
        });
      }

      onSuccess(createdItem);
      onClose();
    } catch (err: any) {
      setError(formatErrorMessage(err, `Failed to import ${currentConfig.itemType}.`));
    } finally {
      setIsImporting(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="import-modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.72)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1100,
        padding: '1rem',
      }}
      onClick={e => {
        if (e.target === e.currentTarget && !isImporting) onClose();
      }}
    >
      <div
        className="card"
        style={{
          width: '100%',
          maxWidth: metadata ? '760px' : '540px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          background: 'var(--bg-surface)',
          borderColor: 'var(--border-default)',
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.6)',
          padding: 0,
          overflow: 'hidden',
          transition: 'max-width 0.2s ease',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'var(--bg-elevated)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--accent-glow)',
                color: 'var(--accent)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Icon name="doc" size={16} />
            </div>
            <div>
              <h2
                id="import-modal-title"
                style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}
              >
                {currentConfig.modalTitle}
              </h2>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0, marginTop: '2px' }}>
                {currentConfig.hint}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isImporting}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: isImporting ? 'not-allowed' : 'pointer',
              padding: '6px',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            aria-label="Close dialog"
          >
            <Icon name="close" size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div
          className="custom-scrollbar"
          style={{
            padding: '1.5rem',
            overflowY: 'auto',
            flex: 1,
          }}
        >
          {/* Error Alert */}
          {error && (
            <div
              style={{
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--danger-bg)',
                border: '1px solid var(--danger-border)',
                color: 'var(--danger)',
                fontSize: '0.8125rem',
                marginBottom: '1.25rem',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
              }}
            >
              <Icon name="alert" size={16} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong style={{ fontWeight: 600 }}>Import Error:</strong> {error}
              </div>
            </div>
          )}

          {/* STEP 1: Select / Drop file */}
          {!metadata ? (
            <div>
              <div
                onDragOver={e => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${dragOver ? 'var(--accent)' : 'var(--border-default)'}`,
                  background: dragOver ? 'var(--accent-glow)' : 'var(--bg-elevated)',
                  borderRadius: 'var(--radius-md)',
                  padding: '2.5rem 1.5rem',
                  textAlign: 'center',
                  cursor: isReading ? 'wait' : 'pointer',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '12px',
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ALLOWED_TEXT_EXTENSIONS.join(',')}
                  onChange={onFileInputChange}
                  style={{ display: 'none' }}
                />
                <div
                  style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '50%',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent)',
                  }}
                >
                  <Icon name="upload" size={22} />
                </div>
                <div>
                  <div style={{ fontSize: '0.92rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {isReading ? 'Reading and parsing file...' : 'Drag and drop file here, or click to browse'}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Supported formats: {ALLOWED_TEXT_EXTENSIONS.join(', ')} • Max 5 MB
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  disabled={isReading}
                  style={{ marginTop: '6px' }}
                >
                  <Icon name="doc" size={13} />
                  <span>Select file from computer</span>
                </button>
              </div>
            </div>
          ) : (
            /* STEP 2: Preview & Confirm Metadata */
            <form onSubmit={handleImportSubmit}>
              {/* File details bar */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  marginBottom: '1.25rem',
                  gap: '10px',
                  flexWrap: 'wrap',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Icon name="doc" size={16} color="var(--accent)" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {metadata.filename}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Format: <span className="badge badge-secondary">{metadata.extension}</span> • Size:{' '}
                      {formatFileSize(metadata.sizeBytes)} • {metadata.hasFrontmatter ? 'YAML Frontmatter' : 'Plain Text'}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => {
                    setMetadata(null);
                    setError(null);
                  }}
                  disabled={isImporting}
                  style={{ fontSize: '0.75rem' }}
                >
                  <Icon name="refresh" size={12} />
                  <span>Change File</span>
                </button>
              </div>

              {/* Collision warning banner */}
              {isDuplicate && (
                <div
                  style={{
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(234, 179, 8, 0.12)',
                    border: '1px solid rgba(234, 179, 8, 0.35)',
                    color: '#eab308',
                    fontSize: '0.8125rem',
                    marginBottom: '1.25rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <Icon name="alert" size={15} />
                  <span>
                    The name <strong>&quot;{name.trim()}&quot;</strong> already exists in your library. Please edit the name below to avoid conflicts.
                  </span>
                </div>
              )}

              {/* Editable Fields */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.25rem' }}>
                {/* Title / Name */}
                <div>
                  <label
                    htmlFor="import-item-name"
                    style={{
                      display: 'block',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      marginBottom: '4px',
                    }}
                  >
                    Name of {currentConfig.itemType} <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <input
                    id="import-item-name"
                    type="text"
                    className="input"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    required
                    maxLength={100}
                    placeholder={`Memorable name for ${currentConfig.itemType}`}
                    style={{ width: '100%' }}
                  />

                </div>

                {/* Description */}
                <div>
                  <label
                    htmlFor="import-item-desc"
                    style={{
                      display: 'block',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      marginBottom: '4px',
                    }}
                  >
                    Summary Description
                  </label>
                  <textarea
                    id="import-item-desc"
                    className="input"
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    rows={2}
                    maxLength={500}
                    placeholder={`Purpose and scope of this ${currentConfig.itemType}`}
                    style={{ width: '100%', resize: 'vertical' }}
                  />
                </div>

                {/* Library-Specific Extra Controls */}
                {target === 'rules' && (
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                      gap: '12px',
                      background: 'var(--bg-elevated)',
                      padding: '12px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div>
                      <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '4px' }}>
                        Activation Mode
                      </label>
                      <select
                        className="input"
                        value={activationMode}
                        onChange={e => setActivationMode(e.target.value as any)}
                        style={{ width: '100%', height: '34px', fontSize: '0.8125rem' }}
                      >
                        <option value="always_on">Always On (Default)</option>
                        <option value="model_decision">Model Decision</option>
                        <option value="glob">Glob Pattern</option>
                        <option value="manual">Manual Trigger</option>
                      </select>
                    </div>

                    {activationMode === 'glob' && (
                      <div>
                        <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '4px' }}>
                          Glob Patterns (comma separated)
                        </label>
                        <input
                          type="text"
                          className="input"
                          value={globPatternsText}
                          onChange={e => setGlobPatternsText(e.target.value)}
                          placeholder="*.ts, src/**/*.py"
                          style={{ width: '100%', height: '34px', fontSize: '0.8125rem' }}
                        />
                      </div>
                    )}

                    <div>
                      <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '4px' }}>
                        Priority Level (0 - 100)
                      </label>
                      <input
                        type="number"
                        className="input"
                        min={0}
                        max={100}
                        value={priority}
                        onChange={e => setPriority(Number(e.target.value))}
                        style={{ width: '100%', height: '34px', fontSize: '0.8125rem' }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, marginBottom: '4px' }}>
                        Tags
                      </label>
                      <input
                        type="text"
                        className="input"
                        value={tagsText}
                        onChange={e => setTagsText(e.target.value)}
                        placeholder="architecture, security, coding"
                        style={{ width: '100%', height: '34px', fontSize: '0.8125rem' }}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Safe Content Preview Area */}
              <div style={{ marginTop: '1.25rem' }}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '8px',
                  }}
                >
                  <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Text Content Preview
                  </label>
                  <div className="segmented-control" role="tablist">
                    <button
                      type="button"
                      role="tab"
                      aria-selected={previewTab === 'formatted'}
                      className={`segmented-control-item ${previewTab === 'formatted' ? 'active' : ''}`}
                      onClick={() => setPreviewTab('formatted')}
                      style={{ fontSize: '0.75rem', padding: '3px 10px' }}
                    >
                      Preview Format
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={previewTab === 'raw'}
                      className={`segmented-control-item ${previewTab === 'raw' ? 'active' : ''}`}
                      onClick={() => setPreviewTab('raw')}
                      style={{ fontSize: '0.75rem', padding: '3px 10px' }}
                    >
                      Original Text ({metadata.content.length} chars)
                    </button>
                  </div>
                </div>

                <div
                  className="custom-scrollbar"
                  style={{
                    maxHeight: '260px',
                    overflowY: 'auto',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-elevated)',
                    padding: '12px',
                    fontSize: '0.8125rem',
                  }}
                >
                  {previewTab === 'formatted' ? (
                    <SafeMarkdownViewer content={metadata.body || metadata.content} />
                  ) : (
                    <pre
                      style={{
                        margin: 0,
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.78rem',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                        color: 'var(--text-secondary)',
                      }}
                    >
                      {metadata.content}
                    </pre>
                  )}
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  ℹ️ Safe Preview: Full UTF-8 content and line breaks will be preserved accurately in the database.
                </div>
              </div>

              {/* Action Buttons */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: '10px',
                  marginTop: '1.5rem',
                  paddingTop: '1rem',
                  borderTop: '1px solid var(--border-subtle)',
                }}
              >
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={onClose}
                  disabled={isImporting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isImporting || !name.trim()}
                >
                  {isImporting ? (
                    <>
                      <Icon name="refresh" size={14} className="spin" />
                      <span>Importing data...</span>
                    </>
                  ) : (
                    <>
                      <Icon name="upload" size={14} />
                      <span>Confirm Import into {currentConfig.itemType}</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

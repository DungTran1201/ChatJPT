'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  RuleDetail,
  RuleStatus,
  ActivationMode,
  RuleUpdatePayload,
  RuleAssociatedProject,
} from '@/types/rule';
import { RuleService } from '@/services/ruleService';
import PageHeader from '@/components/ui/PageHeader';
import Icon from '@/components/ui/Icon';
import Toast, { ToastMessage } from '@/components/ui/Toast';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import SafeMarkdownViewer from '@/components/rules/SafeMarkdownViewer';
import { formatErrorMessage } from '@/lib/errors';

export default function RuleDetailPage() {
  const params = useParams();
  const router = useRouter();
  const ruleId = params?.id as string;

  const [rule, setRule] = useState<RuleDetail | null>(null);
  const [associatedProjects, setAssociatedProjects] = useState<RuleAssociatedProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active tab: 'edit' | 'projects'
  const [activeTab, setActiveTab] = useState<'edit' | 'projects'>('edit');
  // Content view tab: 'write' | 'preview'
  const [contentTab, setContentTab] = useState<'write' | 'preview'>('write');

  // Form states
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState<RuleStatus>('active');
  const [priority, setPriority] = useState<number>(50);
  const [activationMode, setActivationMode] = useState<ActivationMode>('always_on');
  const [globPatternsInput, setGlobPatternsInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');

  // Dialog & Action states
  const [isSaving, setIsSaving] = useState(false);
  const [isCloning, setIsCloning] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [showExitConfirm, setShowExitConfirm] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Toast
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const showToast = (type: 'success' | 'error' | 'info', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3500);
  };

  const isSystemRule = Boolean(rule && (rule.scope === 'system' || !rule.is_editable));

  const initForm = (data: RuleDetail) => {
    setName(data.name || '');
    setDescription(data.description || '');
    setContent(data.content || '');
    setStatus(data.status || 'active');
    setPriority(data.priority ?? 50);
    setActivationMode(data.activation_mode || 'always_on');
    setTags(data.tags || []);
    setGlobPatternsInput(Array.isArray(data.glob_patterns) ? data.glob_patterns.join(', ') : '');
  };

  const loadRule = useCallback(async () => {
    if (!ruleId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await RuleService.getRule(ruleId);
      setRule(data);
      initForm(data);

      // Load associated projects
      try {
        const projects = await RuleService.getRuleAssociatedProjects(ruleId);
        setAssociatedProjects(projects);
      } catch {
        // Soft fail for projects list
      }
    } catch (err: any) {
      setError(formatErrorMessage(err, 'Failed to load rule configuration.'));
    } finally {
      setLoading(false);
    }
  }, [ruleId]);

  useEffect(() => {
    loadRule();
  }, [loadRule]);

  // Dirty state check
  const isDirty = Boolean(
    rule &&
    !isSystemRule &&
    (
      name !== (rule.name || '') ||
      description !== (rule.description || '') ||
      content !== (rule.content || '') ||
      status !== rule.status ||
      priority !== rule.priority ||
      activationMode !== rule.activation_mode ||
      JSON.stringify(tags) !== JSON.stringify(rule.tags || []) ||
      globPatternsInput !== (rule.glob_patterns?.join(', ') || '')
    )
  );

  const handleAddTag = () => {
    const trimmed = tagInput.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '');
    if (trimmed && !tags.includes(trimmed)) {
      if (tags.length >= 10) {
        setFormError('Maximum 10 tags per rule.');
        return;
      }
      setTags([...tags, trimmed]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(t => t !== tagToRemove));
  };

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!rule || isSystemRule) return;
    setFormError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setFormError('Rule name cannot be empty.');
      return;
    }
    if (trimmedName.length > 100) {
      setFormError('Rule name cannot exceed 100 characters.');
      return;
    }

    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setFormError('Rule content cannot be empty.');
      return;
    }
    if (content.length > 10000) {
      setFormError('Rule content cannot exceed 10,000 characters.');
      return;
    }

    let patterns: string[] = [];
    if (activationMode === 'glob') {
      patterns = globPatternsInput
        .split(/[,\n]/)
        .map(p => p.trim())
        .filter(Boolean);

      if (patterns.length === 0) {
        setFormError('File Pattern (Glob) mode requires at least 1 pattern.');
        return;
      }

      for (const p of patterns) {
        if (p.includes('..') || p.startsWith('/') || p.startsWith('\\')) {
          setFormError(`Pattern "${p}" is invalid: Directory traversal (..) and absolute paths are forbidden.`);
          return;
        }
      }
    }

    const payload: RuleUpdatePayload = {
      name: trimmedName,
      description: description.trim() || null,
      content: content,
      status: status,
      priority: Number(priority),
      activation_mode: activationMode,
      glob_patterns: patterns,
      tags: tags,
      version: rule.version,
    };

    try {
      setIsSaving(true);
      const updated = await RuleService.updateRule(ruleId, payload);
      setRule(updated);
      initForm(updated);
      showToast('success', 'Rule changes saved successfully.');
    } catch (err: any) {
      if (err?.status === 409 || err?.message?.includes('conflict') || err?.message?.includes('Version') || err?.message?.includes('Version')) {
        setShowConflictModal(true);
      } else {
        setFormError(formatErrorMessage(err, 'Failed to update rule.'));
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleClone = async () => {
    if (!rule) return;
    try {
      setIsCloning(true);
      const cloned = await RuleService.cloneRule(rule.id);
      showToast('success', `Duplicated as "${cloned.name}".`);
      router.push(`/rules/${cloned.id}`);
    } catch (err: any) {
      showToast('error', formatErrorMessage(err, 'Failed to duplicate rule.'));
    } finally {
      setIsCloning(false);
    }
  };

  const handleDelete = async () => {
    if (!rule || isSystemRule) return;
    try {
      setIsDeleting(true);
      await RuleService.deleteRule(rule.id, true);
      setShowDeleteConfirm(false);
      router.push('/rules');
    } catch (err: any) {
      setShowDeleteConfirm(false);
      showToast('error', formatErrorMessage(err, 'Failed to archive rule.'));
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="custom-scrollbar" style={{ flex: 1, overflowY: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <div style={{
            width: '32px',
            height: '32px',
            border: '3px solid var(--border-subtle)',
            borderTopColor: 'var(--accent)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            margin: '0 auto 1rem'
          }} />
          <p style={{ fontSize: '0.875rem' }}>Loading rule configuration...</p>
        </div>
      </div>
    );
  }

  if (error || !rule) {
    return (
      <div className="custom-scrollbar" style={{ flex: 1, overflowY: 'auto' }}>
        <div className="page-container" style={{ maxWidth: '840px', paddingTop: '3rem' }}>
          <div className="card" style={{ padding: '2.5rem', textAlign: 'center' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'var(--danger-bg)',
              color: 'var(--danger)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem'
            }}>
              <Icon name="alert" size={28} />
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Rule Not Found
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.5rem', maxWidth: '440px', margin: '0 auto 1.5rem' }}>
              {error || 'The requested rule does not exist or you do not have permission to view it.'}
            </p>
            <Link href="/rules" className="btn btn-secondary">
              <Icon name="chevronLeft" size={13} />
              <span>Back to Rules Library</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="custom-scrollbar" style={{ flex: 1, overflowY: 'auto' }}>
      <div className="page-container" style={{ maxWidth: '1000px' }}>
        {/* Header */}
        <PageHeader
          title={rule.name}
          description={`Version ${rule.version} • ID: ${rule.id}`}
        >
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                if (isDirty) {
                  setShowExitConfirm(true);
                } else {
                  router.push('/rules');
                }
              }}
            >
              <Icon name="chevronLeft" size={13} />
              <span>Rules Library</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleClone}
              disabled={isCloning}
            >
              <Icon name="copy" size={13} />
              <span>{isCloning ? 'Duplicating...' : 'Duplicate'}</span>
            </button>
            {!isSystemRule && (
              <button
                type="button"
                className="btn btn-danger btn-sm"
                onClick={() => setShowDeleteConfirm(true)}
              >
                <Icon name="trash" size={13} />
                <span>Archive</span>
              </button>
            )}
          </div>
        </PageHeader>

        {/* System Rule Read-only Warning Banner */}
        {isSystemRule && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            padding: '0.875rem 1.25rem',
            background: 'rgba(235, 184, 102, 0.1)',
            border: '1px solid rgba(235, 184, 102, 0.35)',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '1.25rem',
            color: 'var(--warning)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Icon name="shield" size={18} />
              <div style={{ fontSize: '0.8125rem' }}>
                <strong style={{ color: 'var(--text-primary)' }}>System Rule:</strong> This rule is protected by AI-Chan to guarantee standard pedagogical quality. It cannot be directly edited or deleted. Click Duplicate to create a customizable copy.
              </div>
            </div>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={handleClone}
              disabled={isCloning}
            >
              Duplicate to Edit
            </button>
          </div>
        )}

        {/* Form Error Alert */}
        {formError && (
          <div style={{
            padding: '0.75rem 1rem',
            background: 'var(--danger-bg)',
            border: '1px solid rgba(240, 113, 120, 0.4)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--danger)',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.8125rem'
          }}>
            <Icon name="alert" size={14} />
            <span>{formError}</span>
          </div>
        )}

        {/* Main Tabs Navigation */}
        <div style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-subtle)',
          marginBottom: '1.5rem',
          gap: '1.5rem'
        }}>
          <button
            type="button"
            onClick={() => setActiveTab('edit')}
            style={{
              padding: '0.625rem 0.25rem',
              border: 'none',
              background: 'transparent',
              fontSize: '0.875rem',
              fontWeight: 600,
              color: activeTab === 'edit' ? 'var(--accent)' : 'var(--text-muted)',
              borderBottom: activeTab === 'edit' ? '2px solid var(--accent)' : '2px solid transparent',
              cursor: 'pointer'
            }}
          >
            {isSystemRule ? 'Rule Specification' : 'Edit Rule'}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('projects')}
            style={{
              padding: '0.625rem 0.25rem',
              border: 'none',
              background: 'transparent',
              fontSize: '0.875rem',
              fontWeight: 600,
              color: activeTab === 'projects' ? 'var(--accent)' : 'var(--text-muted)',
              borderBottom: activeTab === 'projects' ? '2px solid var(--accent)' : '2px solid transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <span>Linked Projects</span>
            <span style={{
              fontSize: '0.7rem',
              padding: '1px 6px',
              borderRadius: '10px',
              background: 'var(--bg-elevated)',
              color: 'var(--text-secondary)'
            }}>
              {associatedProjects.length || rule.associated_projects_count || 0}
            </span>
          </button>
        </div>

        {/* Tab 1: Edit / Specification Form */}
        {activeTab === 'edit' && (
          <form onSubmit={handleSave} className="card" style={{ padding: '1.5rem' }}>
            {/* Rule Name */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label style={{ color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600 }}>
                  Rule Name {!isSystemRule && <span style={{ color: 'var(--danger)' }}>*</span>}
                </label>
                <span style={{ fontSize: '0.75rem', color: name.length > 100 ? 'var(--danger)' : 'var(--text-muted)' }}>
                  {name.length} / 100
                </span>
              </div>
              <input
                type="text"
                className="input"
                value={name}
                onChange={e => setName(e.target.value)}
                maxLength={100}
                disabled={isSystemRule}
                required
              />
            </div>

            {/* Description */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label style={{ color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600 }}>
                  Summary Description
                </label>
                <span style={{ fontSize: '0.75rem', color: description.length > 500 ? 'var(--danger)' : 'var(--text-muted)' }}>
                  {description.length} / 500
                </span>
              </div>
              <textarea
                rows={2}
                className="textarea"
                value={description}
                onChange={e => setDescription(e.target.value)}
                maxLength={500}
                disabled={isSystemRule}
              />
            </div>

            {/* Config Grid: Status, Activation, Priority */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              padding: '1rem',
              background: 'var(--bg-elevated)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
              marginBottom: '1.5rem'
            }}>
              <div>
                <label style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Scope
                </label>
                <div style={{
                  padding: '0.5rem 0.75rem',
                  background: 'var(--bg-surface)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8125rem',
                  color: 'var(--text-secondary)'
                }}>
                  {rule.scope === 'system' ? 'System (Default across workspace)' : 'User (Personal library)'}
                </div>
              </div>

              <div>
                <label style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Status
                </label>
                <select
                  className="input"
                  style={{ fontSize: '0.8125rem' }}
                  value={status}
                  onChange={e => setStatus(e.target.value as RuleStatus)}
                  disabled={isSystemRule}
                >
                  <option value="active">Active (Enabled)</option>
                  <option value="inactive">Inactive (Paused)</option>
                  <option value="archived">Archived</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.75rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                  Trigger Mode
                </label>
                <select
                  className="input"
                  style={{ fontSize: '0.8125rem' }}
                  value={activationMode}
                  onChange={e => setActivationMode(e.target.value as ActivationMode)}
                  disabled={isSystemRule}
                >
                  <option value="always_on">Always On</option>
                  <option value="glob">File Pattern (Glob)</option>
                  <option value="model_decision">Model Decision</option>
                  <option value="manual">Manual</option>
                </select>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <label style={{ color: 'var(--text-primary)', fontSize: '0.75rem', fontWeight: 600 }}>
                    Priority Level
                  </label>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent)' }}>
                    {priority} / 100
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={priority}
                  onChange={e => setPriority(Number(e.target.value))}
                  disabled={isSystemRule}
                  style={{ width: '100%', accentColor: 'var(--accent)' }}
                />
              </div>
            </div>

            {/* Conditional Glob Patterns */}
            {activationMode === 'glob' && (
              <div style={{ marginBottom: '1.25rem', padding: '0.875rem', background: 'rgba(92, 207, 230, 0.05)', border: '1px solid rgba(92, 207, 230, 0.2)', borderRadius: 'var(--radius-sm)' }}>
                <label style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                  File Match Patterns {!isSystemRule && <span style={{ color: 'var(--danger)' }}>*</span>}
                </label>
                <input
                  type="text"
                  className="input"
                  placeholder="*.ts, src/**/*.tsx"
                  value={globPatternsInput}
                  onChange={e => setGlobPatternsInput(e.target.value)}
                  disabled={isSystemRule}
                />
              </div>
            )}

            {/* Tags */}
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Category Tags
              </label>
              {!isSystemRule && (
                <div style={{ display: 'flex', gap: '8px', marginBottom: '0.5rem' }}>
                  <input
                    type="text"
                    className="input"
                    style={{ maxWidth: '240px' }}
                    placeholder="Add tag"
                    value={tagInput}
                    onChange={e => setTagInput(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddTag();
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleAddTag}
                    disabled={!tagInput.trim()}
                  >
                    Add
                  </button>
                </div>
              )}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {tags.map(tag => (
                  <span
                    key={tag}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '2px 8px',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-secondary)'
                    }}
                  >
                    #{tag}
                    {!isSystemRule && (
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0 }}
                      >
                        &times;
                      </button>
                    )}
                  </span>
                ))}
              </div>
            </div>

            {/* Content Editor / Preview Switcher */}
            <div style={{ marginBottom: '1.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <label style={{ color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600 }}>
                    Rule Instructions (Markdown)
                  </label>
                  <div style={{ display: 'flex', background: 'var(--bg-elevated)', padding: '2px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                    {!isSystemRule && (
                      <button
                        type="button"
                        onClick={() => setContentTab('write')}
                        style={{
                          padding: '2px 10px',
                          fontSize: '0.75rem',
                          borderRadius: '3px',
                          border: 'none',
                          background: contentTab === 'write' ? 'var(--bg-surface)' : 'transparent',
                          color: contentTab === 'write' ? 'var(--text-primary)' : 'var(--text-muted)',
                          fontWeight: contentTab === 'write' ? 600 : 400,
                          cursor: 'pointer'
                        }}
                      >
                        Editor
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => setContentTab('preview')}
                      style={{
                        padding: '2px 10px',
                        fontSize: '0.75rem',
                        borderRadius: '3px',
                        border: 'none',
                        background: contentTab === 'preview' || isSystemRule ? 'var(--bg-surface)' : 'transparent',
                        color: contentTab === 'preview' || isSystemRule ? 'var(--text-primary)' : 'var(--text-muted)',
                        fontWeight: contentTab === 'preview' || isSystemRule ? 600 : 400,
                        cursor: 'pointer'
                      }}
                    >
                      Safe Preview
                    </button>
                  </div>
                </div>
                <span style={{ fontSize: '0.75rem', color: content.length > 10000 ? 'var(--danger)' : 'var(--text-muted)', fontWeight: 500 }}>
                  {content.length.toLocaleString()} / 10,000 chars
                </span>
              </div>

              {contentTab === 'write' && !isSystemRule ? (
                <textarea
                  rows={16}
                  className="textarea"
                  style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', lineHeight: 1.6 }}
                  value={content}
                  onChange={e => setContent(e.target.value)}
                  maxLength={10000}
                  required
                />
              ) : (
                <div
                  style={{
                    minHeight: '280px',
                    maxHeight: '520px',
                    overflowY: 'auto',
                    padding: '1.25rem',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)'
                  }}
                >
                  <SafeMarkdownViewer content={content} />
                </div>
              )}
            </div>

            {/* Footer Actions */}
            {!isSystemRule && (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => initForm(rule)}
                  disabled={!isDirty || isSaving}
                >
                  Reset Changes
                </button>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!isDirty || isSaving || !name.trim() || !content.trim()}
                  >
                    {isSaving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            )}
          </form>
        )}

        {/* Tab 2: Associated Projects */}
        {activeTab === 'projects' && (
          <div className="card" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Projects Using This Rule
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', marginBottom: '1.25rem' }}>
              {isSystemRule
                ? 'System rules are loaded as standard defaults for all system agents.'
                : 'This rule is assigned to the following projects to guide model behavior.'}
            </p>

            {associatedProjects.length > 0 ? (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '8px 12px' }}>Project Name</th>
                      <th style={{ padding: '8px 12px' }}>Project Code</th>
                      <th style={{ padding: '8px 12px' }}>Assigned Date</th>
                      <th style={{ padding: '8px 12px', textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {associatedProjects.map((bp: RuleAssociatedProject) => (
                      <tr key={bp.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 500, color: 'var(--text-primary)' }}>
                          {bp.name || 'Project'}
                        </td>
                        <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {bp.id}
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--text-muted)' }}>
                          {bp.bound_at ? new Date(bp.bound_at).toLocaleDateString() : 'N/A'}
                        </td>
                        <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                          <Link href={`/projects`} className="btn btn-secondary btn-sm" style={{ textDecoration: 'none' }}>
                            Open Project
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '2.5rem', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)' }}>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                  No projects are currently linked to this rule.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Toast Notification */}
      {toast && <Toast toast={toast} onClose={() => setToast(null)} />}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Archive this rule?"
        message={
          associatedProjects.length > 0 ? (
            <div>
              <p style={{ marginBottom: '8px' }}>
                This rule is currently linked in <strong>{associatedProjects.length} projects</strong>.
              </p>
              <p style={{ color: 'var(--danger)', fontSize: '0.8125rem' }}>
                Archiving will detach the rule from linked projects and hide it from the active list.
              </p>
            </div>
          ) : (
            `Are you sure you want to archive "${rule.name}"? You can restore it later.`
          )
        }
        confirmLabel="Confirm Archive"
        cancelLabel="Keep Rule"
        isDestructive={true}
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      />

      {/* 409 Concurrency Conflict Dialog */}
      <ConfirmDialog
        isOpen={showConflictModal}
        title="Version Conflict (409 Conflict)"
        message="This rule was modified in another browser session or tab while you were editing. Please reload the latest data to avoid overwriting concurrent changes."
        confirmLabel="Reload Data"
        cancelLabel="Ignore"
        isDestructive={false}
        onConfirm={() => {
          setShowConflictModal(false);
          loadRule();
        }}
        onCancel={() => setShowConflictModal(false)}
      />

      {/* Exit confirmation dialog */}
      <ConfirmDialog
        isOpen={showExitConfirm}
        title="Discard unsaved changes?"
        message="You have unsaved changes on this rule. If you leave now, your edits will be discarded."
        confirmLabel="Leave"
        cancelLabel="Stay"
        isDestructive={true}
        onConfirm={() => router.push('/rules')}
        onCancel={() => setShowExitConfirm(false)}
      />
    </div>
  );
}

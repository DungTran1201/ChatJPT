'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { SystemPromptSummary } from '@/types';
import { SystemPromptService } from '@/services/systemPromptService';
import PageHeader from '@/components/ui/PageHeader';
import { useApp } from '@/context/AppContext';
import Icon from '@/components/ui/Icon';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import Toast, { ToastMessage } from '@/components/ui/Toast';
import Pagination from '@/components/ui/Pagination';
import TextFileImportModal from '@/components/common/TextFileImportModal';
import { formatErrorMessage } from '@/lib/errors';

export default function SenseiGuidanceListPage() {
  const { t } = useApp();
  const [prompts, setPrompts] = useState<SystemPromptSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Sorting
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [selectedLevel, setSelectedLevel] = useState<string>('ALL');
  const [sortOption, setSortOption] = useState('level_asc');
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(6);

  // Modals & Feedback
  const [promptToDelete, setPromptToDelete] = useState<SystemPromptSummary | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showTextImportModal, setShowTextImportModal] = useState(false);
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [cloningId, setCloningId] = useState<string | null>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const showToast = (type: 'success' | 'error' | 'info', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3000);
  };

  const loadPrompts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await SystemPromptService.getPrompts(debouncedQuery, sortOption, selectedLevel);
      setPrompts(res.items || res.prompts || []);
    } catch (err: any) {
      setError(formatErrorMessage(err, t('prompts.load_error') || 'Error loading Sensei roster'));
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, sortOption, selectedLevel]);

  useEffect(() => {
    loadPrompts();
  }, [loadPrompts]);

  const handleCopyContent = async (prompt: SystemPromptSummary) => {
    try {
      const detail = await SystemPromptService.getPrompt(prompt.id);
      await navigator.clipboard.writeText(detail.content);
      setCopiedId(prompt.id);
      showToast('success', `${t('common.copied')}: "${prompt.name}"`);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err: any) {
      showToast('error', formatErrorMessage(err, t('common.error')));
    }
  };

  const handleClone = async (prompt: SystemPromptSummary) => {
    try {
      setCloningId(prompt.id);
      const cloned = await SystemPromptService.clonePrompt(prompt.id);
      showToast('success', `${t('common.clone')}: "${cloned.name}"`);
      loadPrompts();
    } catch (err: any) {
      showToast('error', formatErrorMessage(err, t('common.error')));
    } finally {
      setCloningId(null);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!promptToDelete) return;
    try {
      setIsDeleting(true);
      await SystemPromptService.deletePrompt(promptToDelete.id);
      showToast('success', `${t('prompts.delete_title')}: "${promptToDelete.name}"`);
      setPromptToDelete(null);
      loadPrompts();
    } catch (err: any) {
      showToast('error', formatErrorMessage(err, t('common.error')));
    } finally {
      setIsDeleting(false);
    }
  };

  useEffect(() => {
    setPage(1);
  }, [debouncedQuery, sortOption, selectedLevel]);

  const paginatedPrompts = prompts.slice((page - 1) * pageSize, page * pageSize);

  // Helper for level colors
  const getLevelBadgeStyle = (level?: string) => {
    switch (level?.toUpperCase()) {
      case 'N5':
        return { color: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.3)' };
      case 'N4':
        return { color: '#0ea5e9', bg: 'rgba(14, 165, 233, 0.15)', border: 'rgba(14, 165, 233, 0.3)' };
      case 'N3':
        return { color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.15)', border: 'rgba(139, 92, 246, 0.3)' };
      case 'N2':
        return { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.3)' };
      case 'N1':
        return { color: '#f43f5e', bg: 'rgba(244, 63, 94, 0.15)', border: 'rgba(244, 63, 94, 0.3)' };
      default:
        return { color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.15)', border: 'rgba(56, 189, 248, 0.3)' };
    }
  };

  return (
    <div className="custom-scrollbar" style={{ flex: 1, overflowY: 'auto' }}>
      <Toast toast={toast} onClose={() => setToast(null)} />

      <div className="page-container">
        {/* Page Header */}
        <PageHeader
          title={t('prompts.title')}
          description={t('prompts.sub')}
        >
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setShowTextImportModal(true)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="upload" size={14} />
            <span>{t('common.import_from_file')}</span>
          </button>
          <Link href="/prompts/new" className="btn btn-primary" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <Icon name="plus" size={14} />
            <span>{t('prompts.new_sensei')}</span>
          </Link>
        </PageHeader>

        {/* Toolbar: Search, Level Filter Tabs, Sort */}
        <div
          className="card"
          style={{
            marginBottom: '1.5rem',
            padding: '1rem 1.25rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.875rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.875rem' }}>
            {/* Search Box */}
            <div style={{ position: 'relative', flex: 1, minWidth: '260px', maxWidth: '440px' }}>
              <span
                style={{
                  position: 'absolute',
                  left: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                  display: 'flex',
                }}
              >
                <Icon name="search" size={14} />
              </span>
              <input
                type="search"
                className="input"
                style={{ paddingLeft: '32px', height: '36px', fontSize: '0.8125rem' }}
                placeholder={t('prompts.search_placeholder') || 'Search Sensei by name, personality, or teaching style...'}
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Right controls: Sort & Refresh */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <label htmlFor="sortSelect" style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                  {t('common.sort_by')}
                </label>
                <select
                  id="sortSelect"
                  className="select"
                  value={sortOption}
                  onChange={e => setSortOption(e.target.value)}
                  style={{ height: '36px', padding: '0 0.5rem', fontSize: '0.8125rem', width: 'auto' }}
                >
                  <option value="level_asc">{t('prompts.sort_level')}</option>
                  <option value="updated_desc">{t('prompts.sort_updated')}</option>
                  <option value="name_asc">{t('prompts.sort_name')}</option>
                </select>
              </div>

              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={loadPrompts}
                title={t('prompts.refresh_tooltip')}
                style={{ height: '36px' }}
              >
                <Icon name="refresh" size={13} />
                <span>{t('common.refresh')}</span>
              </button>

              <span
                style={{
                  fontSize: '0.8rem',
                  color: 'var(--text-muted)',
                  paddingLeft: '8px',
                  borderLeft: '1px solid var(--border-subtle)',
                }}
              >
                {prompts.length} {t('prompts.count_suffix')}
              </span>
            </div>
          </div>

          {/* Level Filter Chips */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginRight: '4px' }}>{t('prompts.jlpt_level_label')}</span>
            {['ALL', 'N5', 'N4', 'N3', 'N2', 'N1'].map(lvl => {
              const active = selectedLevel === lvl;
              const badgeStyle = getLevelBadgeStyle(lvl);
              return (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setSelectedLevel(lvl)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-full, 16px)',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    background: active ? (lvl === 'ALL' ? 'var(--primary, #10b981)' : badgeStyle.bg) : 'var(--bg-elevated)',
                    color: active ? (lvl === 'ALL' ? '#ffffff' : badgeStyle.color) : 'var(--text-secondary)',
                    border: `1px solid ${active ? (lvl === 'ALL' ? 'var(--primary, #10b981)' : badgeStyle.border) : 'var(--border-subtle)'}`,
                  }}
                >
                  {lvl === 'ALL' ? t('common.all_levels') : `JLPT ${lvl}`}
                </button>
              );
            })}
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div
            style={{
              padding: '0.875rem 1rem',
              background: 'var(--danger-bg)',
              border: '1px solid rgba(240, 113, 120, 0.4)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--danger)',
              marginBottom: '1.5rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.875rem',
            }}
          >
            <div>{error}</div>
            <button
              type="button"
              className="btn btn-danger btn-sm"
              onClick={loadPrompts}
            >
              {t('common.retry')}
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div style={{ padding: '4rem 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            {t('prompts.loading')}
          </div>
        )}

        {/* Empty State */}
        {!loading && prompts.length === 0 && !debouncedQuery && (
          <div
            className="card"
            style={{
              padding: '3.5rem 2rem',
              textAlign: 'center',
              borderStyle: 'dashed',
            }}
          >
            <div style={{ color: 'var(--text-muted)', marginBottom: '0.75rem', display: 'flex', justifyContent: 'center' }}>
              <Icon name="user" size={36} />
            </div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
              {t('prompts.empty_title')}
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', maxWidth: '440px', margin: '0 auto 1.5rem auto' }}>
              {t('prompts.empty_desc')}
            </p>
            <Link href="/prompts/new" className="btn btn-primary" style={{ textDecoration: 'none' }}>
              <Icon name="plus" size={14} />
              <span>{t('prompts.new_sensei')}</span>
            </Link>
          </div>
        )}

        {/* No Search Results */}
        {!loading && prompts.length === 0 && debouncedQuery && (
          <div
            className="card"
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
            }}
          >
            <div style={{ color: 'var(--text-muted)', marginBottom: '0.75rem', display: 'flex', justifyContent: 'center' }}>
              <Icon name="search" size={28} />
            </div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
              {t('prompts.no_results_title')}
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem', marginBottom: '1.25rem' }}>
              {t('prompts.no_results_desc')}
            </p>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setSearchQuery('')}
            >
              {t('common.clear_search')}
            </button>
          </div>
        )}

        {/* Sensei Cards Grid */}
        {!loading && prompts.length > 0 && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
              gap: '1.25rem',
            }}
          >
            {paginatedPrompts.map(prompt => {
              const badgeStyle = getLevelBadgeStyle(prompt.japanese_level);
              const avatarSrc = prompt.avatar_url || `https://api.dicebear.com/7.x/bottts/svg?seed=${prompt.id}`;

              return (
                <div
                  key={prompt.id}
                  className="card"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    padding: '1.25rem',
                    position: 'relative',
                    border: prompt.is_default ? '1px solid var(--primary, #10b981)' : '1px solid var(--border-subtle)',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <div>
                    {/* Top row: Avatar + Name + Level Pill + Gender/Age */}
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '0.75rem' }}>
                      {/* Avatar */}
                      <div
                        style={{
                          width: '46px',
                          height: '46px',
                          borderRadius: '50%',
                          overflow: 'hidden',
                          flexShrink: 0,
                          border: `2px solid ${badgeStyle.color}`,
                          background: 'var(--bg-elevated)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={avatarSrc}
                          alt={prompt.name}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={(e) => {
                            // Fallback to text initials if image fails
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                      </div>

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                          <span
                            style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              padding: '1px 6px',
                              borderRadius: '4px',
                              background: badgeStyle.bg,
                              color: badgeStyle.color,
                              border: `1px solid ${badgeStyle.border}`,
                            }}
                          >
                            JLPT {prompt.japanese_level || 'N5'}
                          </span>

                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            {prompt.age || 25} {t('common.years_old')} • {prompt.gender === 'male' ? t('common.teacher_male') : t('common.teacher_female')}
                          </span>

                          {prompt.is_system_preset && (
                            <span
                              style={{
                                fontSize: '0.68rem',
                                padding: '1px 5px',
                                borderRadius: '4px',
                                background: 'rgba(56, 189, 248, 0.1)',
                                color: '#38bdf8',
                                border: '1px solid rgba(56, 189, 248, 0.25)',
                              }}
                            >
                              {t('common.system_preset')}
                            </span>
                          )}
                        </div>

                        <h3
                          style={{
                            fontSize: '1rem',
                            fontWeight: 600,
                            color: 'var(--text-primary)',
                            margin: '3px 0 0 0',
                            lineHeight: 1.3,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {prompt.name}
                        </h3>
                      </div>
                    </div>

                    {/* Personality & Teaching Style */}
                    {prompt.personality && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <span style={{ color: badgeStyle.color }}>✦</span>
                        <span style={{ fontWeight: 500 }}>{t('prompts.personality_prefix')}</span>
                        <span style={{ color: 'var(--text-primary)' }}>{prompt.personality}</span>
                      </div>
                    )}

                    {prompt.teaching_style && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', lineHeight: 1.4 }}>
                        <span style={{ fontWeight: 500, color: 'var(--text-muted)' }}>{t('prompts.style_prefix')} </span>
                        <span>{prompt.teaching_style}</span>
                      </div>
                    )}

                    {/* Catchphrase Bubble */}
                    {prompt.catchphrase && (
                      <div
                        style={{
                          background: 'rgba(255, 255, 255, 0.02)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: '6px',
                          padding: '6px 10px',
                          fontSize: '0.75rem',
                          fontStyle: 'italic',
                          color: 'var(--text-secondary)',
                          marginBottom: '0.75rem',
                          lineHeight: 1.4,
                        }}
                      >
                        <span style={{ color: badgeStyle.color, marginRight: '4px', fontStyle: 'normal' }}>💬</span>
                        &ldquo;{prompt.catchphrase}&rdquo;
                      </div>
                    )}

                    {/* Hobbies */}
                    {prompt.hobbies && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                        <span>{t('prompts.hobbies_prefix')} {prompt.hobbies}</span>
                      </div>
                    )}
                  </div>

                  {/* Footer: timestamp + actions */}
                  <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem', marginTop: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {/* Copy Persona */}
                      <button
                        type="button"
                        onClick={() => handleCopyContent(prompt)}
                        className={`btn btn-sm ${copiedId === prompt.id ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ flex: 1 }}
                        title={t('prompts.copy_persona_title')}
                      >
                        <Icon name={copiedId === prompt.id ? 'check' : 'copy'} size={13} />
                        <span>{copiedId === prompt.id ? t('common.copied') : t('common.copy')}</span>
                      </button>

                      {/* Clone */}
                      <button
                        type="button"
                        onClick={() => handleClone(prompt)}
                        disabled={cloningId === prompt.id}
                        className="btn btn-secondary btn-sm"
                        title={t('prompts.clone_title')}
                      >
                        <Icon name="doc" size={13} />
                        <span>{t('common.clone')}</span>
                      </button>

                      {/* Edit */}
                      <Link
                        href={`/prompts/${prompt.id}/edit`}
                        className="btn btn-secondary btn-sm"
                        style={{ textDecoration: 'none' }}
                        title={t('prompts.edit_title')}
                      >
                        <Icon name="edit" size={13} />
                        <span>{t('common.edit')}</span>
                      </Link>

                      {/* Delete */}
                      {!prompt.is_system_preset ? (
                        <button
                          type="button"
                          onClick={() => setPromptToDelete(prompt)}
                          className="btn-icon"
                          title={t('prompts.delete_title')}
                          aria-label={t('prompts.delete_title')}
                          style={{ color: 'var(--text-muted)' }}
                          onMouseEnter={e => { e.currentTarget.style.color = 'var(--danger)'; }}
                          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; }}
                        >
                          <Icon name="trash" size={14} />
                        </button>
                      ) : (
                        <span
                          title={t('prompts.delete_preset_title')}
                          style={{ color: 'var(--text-disabled)', display: 'flex', padding: '4px' }}
                        >
                          <Icon name="lock" size={13} />
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {!loading && prompts.length > pageSize && (
          <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'center' }}>
            <Pagination
              currentPage={page}
              totalItems={prompts.length}
              pageSize={pageSize}
              onPageChange={setPage}
            />
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <ConfirmDialog
        isOpen={Boolean(promptToDelete)}
        title={t('prompts.delete_dialog_title')}
        message={`${t('prompts.delete_dialog_msg')} ("${promptToDelete?.name}")`}
        confirmLabel={t('prompts.delete_title')}
        isDestructive
        isLoading={isDeleting}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setPromptToDelete(null)}
      />

      {/* Text/File Import Modal */}
      {showTextImportModal && (
        <TextFileImportModal
          isOpen={showTextImportModal}
          target="prompts"
          onClose={() => setShowTextImportModal(false)}
          onSuccess={() => {
            setShowTextImportModal(false);
            showToast('success', t('prompts.import_success') || 'Sensei imported successfully');
            loadPrompts();
          }}
        />
      )}
    </div>
  );
}

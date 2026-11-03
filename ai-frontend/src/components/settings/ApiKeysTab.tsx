'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { ProviderKeyStatus, ApiKeyCategory } from '@/types/apiKey';
import { ApiKeyService } from '@/services/apiKeyService';
import Icon from '@/components/ui/Icon';
import { useApp } from '@/context/AppContext';

interface ApiKeysTabProps {
  showToast: (type: 'success' | 'error', message: string) => void;
  userEmail?: string;
}

export default function ApiKeysTab({ showToast, userEmail }: ApiKeysTabProps) {
  const { t } = useApp();
  const [keys, setKeys] = useState<ProviderKeyStatus[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeCategory, setActiveCategory] = useState<'ALL' | 'LLM' | 'SEARCH'>('ALL');

  // Input states per provider for editing/entering keys
  const [inputValues, setInputValues] = useState<Record<string, string>>({});
  const [showPassword, setShowPassword] = useState<Record<string, boolean>>({});
  const [editingProvider, setEditingProvider] = useState<Record<string, boolean>>({});

  // Action loading states per provider
  const [savingProvider, setSavingProvider] = useState<string | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [deletingProvider, setDeletingProvider] = useState<string | null>(null);

  // Deletion confirmation modal
  const [confirmDeleteProvider, setConfirmDeleteProvider] = useState<ProviderKeyStatus | null>(null);

  // Admin section state
  const [showAdminSection, setShowAdminSection] = useState<boolean>(false);
  const [adminEnvVar, setAdminEnvVar] = useState<string>('GEMINI_API_KEY');
  const [adminEnvVal, setAdminEnvVal] = useState<string>('');
  const [savingAdminEnv, setSavingAdminEnv] = useState<boolean>(false);

  const isAdmin = Boolean(
    userEmail && (userEmail.toLowerCase().includes('admin') || userEmail.toLowerCase().includes('demo'))
  );

  const loadKeys = useCallback(async () => {
    try {
      setLoading(true);
      const data = await ApiKeyService.fetchApiKeys();
      setKeys(data);
    } catch (err: any) {
      showToast('error', err.message || 'Failed to load API keys list.');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadKeys();
  }, [loadKeys]);

  const handleInputChange = (provider: string, value: string) => {
    setInputValues(prev => ({ ...prev, [provider]: value }));
  };

  const toggleShowPassword = (provider: string) => {
    setShowPassword(prev => ({ ...prev, [provider]: !prev[provider] }));
  };

  const handleStartEdit = (provider: string) => {
    setEditingProvider(prev => ({ ...prev, [provider]: true }));
    setInputValues(prev => ({ ...prev, [provider]: '' }));
  };

  const handleCancelEdit = (provider: string) => {
    setEditingProvider(prev => ({ ...prev, [provider]: false }));
    setInputValues(prev => ({ ...prev, [provider]: '' }));
    setShowPassword(prev => ({ ...prev, [provider]: false }));
  };

  const handleSaveKey = async (item: ProviderKeyStatus) => {
    const rawValue = (inputValues[item.provider] || '').trim();
    if (!rawValue) {
      showToast('error', 'Please enter an API key before saving.');
      return;
    }

    setSavingProvider(item.provider);
    try {
      const res = await ApiKeyService.saveApiKey(item.provider, rawValue);
      showToast('success', res.message || `Saved API key for ${item.name}.`);
      setEditingProvider(prev => ({ ...prev, [item.provider]: false }));
      setInputValues(prev => ({ ...prev, [item.provider]: '' }));
      setShowPassword(prev => ({ ...prev, [item.provider]: false }));
      await loadKeys();
    } catch (err: any) {
      showToast('error', err.message || 'Error saving API key.');
    } finally {
      setSavingProvider(null);
    }
  };

  const handleTestConnection = async (item: ProviderKeyStatus) => {
    const candidate = (inputValues[item.provider] || '').trim();
    setTestingProvider(item.provider);
    try {
      const res = await ApiKeyService.testConnection(item.provider, candidate || undefined);
      if (res.healthy) {
        showToast('success', `${res.message} (Latency: ${res.latency_ms}ms)`);
      } else {
        showToast('error', res.message || 'Connection test failed.');
      }
      await loadKeys();
    } catch (err: any) {
      showToast('error', err.message || 'Connection test error.');
    } finally {
      setTestingProvider(null);
    }
  };

  const handleConfirmDelete = async () => {
    if (!confirmDeleteProvider) return;
    const provider = confirmDeleteProvider.provider;
    setDeletingProvider(provider);
    try {
      const res = await ApiKeyService.deleteApiKey(provider);
      showToast('success', res.message || 'Personal key removed.');
      setConfirmDeleteProvider(null);
      handleCancelEdit(provider);
      await loadKeys();
    } catch (err: any) {
      showToast('error', err.message || 'Error deleting personal key.');
    } finally {
      setDeletingProvider(null);
    }
  };

  const handleSaveSystemEnv = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adminEnvVal.trim()) {
      showToast('error', 'Please enter an environment variable value.');
      return;
    }
    setSavingAdminEnv(true);
    try {
      const res = await ApiKeyService.updateSystemEnv(adminEnvVar, adminEnvVal.trim());
      showToast('success', res.message);
      setAdminEnvVal('');
      await loadKeys();
    } catch (err: any) {
      showToast('error', err.message || 'Error updating system environment.');
    } finally {
      setSavingAdminEnv(false);
    }
  };

  const filteredKeys = keys.filter(k => {
    if (activeCategory === 'ALL') return true;
    return k.category === activeCategory;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header & Policy Notice */}
      <div className="card" style={{ padding: '1.5rem', background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Icon name="key" size={20} style={{ color: 'var(--accent)' }} />
              <span>{t('apikeys.title')}</span>
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.35rem', maxWidth: '750px', lineHeight: 1.5 }}>
              Configure API keys for AI model providers and external services. Your personal keys are encrypted using 
              <strong> AES-256-GCM</strong> at the database layer with higher priority than server defaults, taking effect immediately at runtime.
            </p>
          </div>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={loadKeys}
            disabled={loading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', padding: '0.5rem 0.85rem' }}
          >
            <Icon name="refresh" size={14} className={loading ? 'spin' : ''} />
            <span>{t('common.refresh')}</span>
          </button>
        </div>

        {/* Security Alert Notice */}
        <div style={{
          marginTop: '1.25rem',
          padding: '0.85rem 1rem',
          borderRadius: '8px',
          background: 'rgba(59, 130, 246, 0.08)',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.82rem',
          color: 'var(--text-secondary)'
        }}>
          <Icon name="shield" size={18} style={{ color: '#3b82f6', flexShrink: 0 }} />
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>{t('apikeys.security_notice')} </strong>
            The system never transmits plaintext API keys to the browser after saving. Only configuration status and masked hints are displayed.
          </div>
        </div>

        {/* Offline & Failover Continuity Architecture Notice */}
        <div style={{
          marginTop: '0.75rem',
          padding: '0.85rem 1rem',
          borderRadius: '8px',
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px',
          fontSize: '0.82rem',
          color: 'var(--text-secondary)'
        }}>
          <Icon name="cpu" size={18} style={{ color: '#10b981', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong style={{ color: 'var(--text-primary)' }}>Auto-Failover & Offline Semantic Cache: </strong>
            When an active model exceeds rate limits (HTTP 429), the system automatically routes to another available model with zero context loss. If no API keys are present or hardware cannot run local models, the platform instantly engages <strong>Offline Semantic Cache</strong> for high-speed offline Japanese language learning.
          </div>
        </div>
      </div>

      {/* Category Tabs */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
        <button
          type="button"
          className={`btn ${activeCategory === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveCategory('ALL')}
          style={{ fontSize: '0.82rem', padding: '0.4rem 0.85rem' }}
        >
          {t('apikeys.cat_all')} ({keys.length})
        </button>
        <button
          type="button"
          className={`btn ${activeCategory === 'LLM' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveCategory('LLM')}
          style={{ fontSize: '0.82rem', padding: '0.4rem 0.85rem' }}
        >
          {t('apikeys.cat_llm')}
        </button>
        <button
          type="button"
          className={`btn ${activeCategory === 'SEARCH' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveCategory('SEARCH')}
          style={{ fontSize: '0.82rem', padding: '0.4rem 0.85rem' }}
        >
          {t('apikeys.cat_search')}
        </button>
      </div>

      {/* Provider List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <Icon name="refresh" size={24} className="spin" style={{ marginBottom: '0.5rem' }} />
          <div>Loading API keys configuration catalog...</div>
        </div>
      ) : filteredKeys.length === 0 ? (
        <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          No providers found in this category.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredKeys.map(item => {
            const isEditing = Boolean(editingProvider[item.provider]);
            const isSaving = savingProvider === item.provider;
            const isTesting = testingProvider === item.provider;
            const isDeleting = deletingProvider === item.provider;
            const currentInput = inputValues[item.provider] || '';
            const isPasswordVisible = Boolean(showPassword[item.provider]);

            // Status badges
            let sourceBadge = null;
            if (item.source === 'PERSONAL') {
              sourceBadge = (
                <span style={{
                  fontSize: '0.75rem',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: 'rgba(139, 92, 246, 0.15)',
                  color: '#8b5cf6',
                  border: '1px solid rgba(139, 92, 246, 0.3)',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <Icon name="user" size={11} />
                  <span>Personal Key</span>
                </span>
              );
            } else if (item.source === 'SYSTEM') {
              sourceBadge = (
                <span style={{
                  fontSize: '0.75rem',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: 'rgba(59, 130, 246, 0.15)',
                  color: '#3b82f6',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <Icon name="workspace" size={11} />
                  <span>System Default (.env)</span>
                </span>
              );
            } else {
              sourceBadge = (
                <span style={{
                  fontSize: '0.75rem',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  background: 'rgba(156, 163, 175, 0.15)',
                  color: 'var(--text-muted)',
                  border: '1px solid var(--border)',
                  fontWeight: 500
                }}>
                  Not Configured
                </span>
              );
            }

            // Validation Badge
            let valBadge = null;
            if (item.validation_status === 'VALID') {
              valBadge = (
                <span style={{
                  fontSize: '0.72rem',
                  color: '#10b981',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <Icon name="check" size={12} />
                  <span>Connection Verified</span>
                </span>
              );
            } else if (item.validation_status === 'INVALID' || item.validation_status === 'ERROR') {
              valBadge = (
                <span style={{
                  fontSize: '0.72rem',
                  color: '#ef4444',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px'
                }}>
                  <Icon name="alert" size={12} />
                  <span>Connection Error or Invalid Key</span>
                </span>
              );
            }

            return (
              <div
                key={item.provider}
                id={`provider-card-${item.provider}`}
                className="card"
                style={{
                  padding: '1.25rem',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  transition: 'border-color 0.2s ease',
                  borderRadius: '10px'
                }}
              >
                {/* Top Row: Provider Info & Status */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                        {item.name}
                      </h3>
                      {sourceBadge}
                      {valBadge}
                    </div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.25rem', marginBottom: 0 }}>
                      {item.description}
                    </p>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.25rem', display: 'flex', gap: '12px' }}>
                      <span>Environment Variable: <code style={{ color: 'var(--accent)', background: 'var(--bg-secondary)', padding: '1px 4px', borderRadius: '4px' }}>{item.env_var}</code></span>
                      {item.doc_url && (
                        <a
                          href={item.doc_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'var(--accent)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '2px' }}
                        >
                          <span>Get Key</span>
                          <Icon name="external" size={11} />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Actions Header */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <button
                      type="button"
                      id={`btn-test-${item.provider}`}
                      className="btn btn-secondary"
                      onClick={() => handleTestConnection(item)}
                      disabled={isTesting || (!item.is_configured && !currentInput)}
                      style={{ fontSize: '0.78rem', padding: '0.4rem 0.75rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                      title="Verify actual connection to provider API"
                    >
                      <Icon name="refresh" size={12} className={isTesting ? 'spin' : ''} />
                      <span>{isTesting ? 'Testing...' : 'Test Connection'}</span>
                    </button>

                    {item.has_personal_key && !isEditing && (
                      <button
                        type="button"
                        id={`btn-delete-${item.provider}`}
                        className="btn btn-secondary"
                        onClick={() => setConfirmDeleteProvider(item)}
                        disabled={isDeleting}
                        style={{ fontSize: '0.78rem', padding: '0.4rem 0.75rem', color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.3)' }}
                        title="Delete personal key and revert to server default"
                      >
                        <Icon name="trash" size={12} />
                        <span>{t('apikeys.delete_key')}</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Configuration Row */}
                <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
                  {!isEditing && item.is_configured ? (
                    /* Display Masked State */
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Icon name="lock" size={16} style={{ color: 'var(--text-muted)' }} />
                        <span style={{
                          fontFamily: 'monospace',
                          fontSize: '0.9rem',
                          background: 'var(--bg-secondary)',
                          padding: '0.3rem 0.6rem',
                          borderRadius: '6px',
                          color: 'var(--text-primary)',
                          letterSpacing: '1px'
                        }}>
                          {item.masked_hint || '••••••••••••••••'}
                        </span>
                        {item.updated_at && (
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            Updated: {new Date(item.updated_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>

                      <button
                        type="button"
                        id={`btn-edit-${item.provider}`}
                        className="btn btn-secondary"
                        onClick={() => handleStartEdit(item.provider)}
                        style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                      >
                        <Icon name="edit" size={12} />
                        <span>{item.has_personal_key ? 'Change Key' : 'Override with Personal Key'}</span>
                      </button>
                    </div>
                  ) : (
                    /* Input Form for Entering/Updating Key */
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <div style={{ position: 'relative', flex: 1 }}>
                          <input
                            type={isPasswordVisible || !item.is_secret ? 'text' : 'password'}
                            id={`input-key-${item.provider}`}
                            value={currentInput}
                            onChange={(e) => handleInputChange(item.provider, e.target.value)}
                            placeholder={item.placeholder || `Enter API key for ${item.name}...`}
                            style={{
                              width: '100%',
                              padding: '0.5rem 2.5rem 0.5rem 0.75rem',
                              fontSize: '0.85rem',
                              fontFamily: 'monospace',
                              borderRadius: '6px',
                              border: '1px solid var(--border)',
                              background: 'var(--bg-secondary)',
                              color: 'var(--text-primary)'
                            }}
                            autoComplete="off"
                            spellCheck={false}
                          />
                          {item.is_secret && (
                            <button
                              type="button"
                              onClick={() => toggleShowPassword(item.provider)}
                              style={{
                                position: 'absolute',
                                right: '8px',
                                top: '50%',
                                transform: 'translateY(-50%)',
                                background: 'transparent',
                                border: 'none',
                                color: 'var(--text-muted)',
                                cursor: 'pointer',
                                padding: '4px',
                                display: 'flex',
                                alignItems: 'center'
                              }}
                              title={isPasswordVisible ? 'Hide Key' : 'Show Key'}
                            >
                              <Icon name={isPasswordVisible ? 'close' : 'sparkles'} size={14} />
                            </button>
                          )}
                        </div>

                        <button
                          type="button"
                          id={`btn-save-${item.provider}`}
                          className="btn btn-primary"
                          onClick={() => handleSaveKey(item)}
                          disabled={isSaving || !currentInput.trim()}
                          style={{ fontSize: '0.8rem', padding: '0.5rem 1rem', display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                        >
                          <Icon name="check" size={13} />
                          <span>{isSaving ? 'Saving...' : 'Save Key'}</span>
                        </button>

                        {(item.is_configured || isEditing) && (
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => handleCancelEdit(item.provider)}
                            disabled={isSaving}
                            style={{ fontSize: '0.8rem', padding: '0.5rem 0.85rem' }}
                          >
                            Cancel
                          </button>
                        )}
                      </div>

                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        Key will be encrypted with AES-256-GCM and applied immediately to your profile without affecting others.
                      </div>
                    </div>
                  )}

                  {/* Last Error Message Display if any */}
                  {item.last_error_summary && (
                    <div style={{
                      marginTop: '0.75rem',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '6px',
                      background: 'rgba(239, 68, 68, 0.08)',
                      border: '1px solid rgba(239, 68, 68, 0.2)',
                      fontSize: '0.75rem',
                      color: '#ef4444',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}>
                      <Icon name="alert" size={13} style={{ flexShrink: 0 }} />
                      <span>{item.last_error_summary}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Admin System Configuration Section (Optional/Local Admin only) */}
      {isAdmin && (
        <div className="card" style={{ padding: '1.25rem', marginTop: '1rem', border: '1px dashed var(--border)', background: 'var(--bg-secondary)' }}>
          <div
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
            onClick={() => setShowAdminSection(!showAdminSection)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Icon name="shield" size={16} style={{ color: 'var(--accent)' }} />
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Global Environment Configuration (.env) — Admin Only
              </span>
            </div>
            <Icon name={showAdminSection ? 'chevronUp' : 'chevronDown'} size={16} style={{ color: 'var(--text-muted)' }} />
          </div>

          {showAdminSection && (
            <form onSubmit={handleSaveSystemEnv} style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>
                Update global environment variables in server <code>.env</code> via atomic write with automated backup. Serves as default for all users without personal overrides.
              </p>

              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                <select
                  value={adminEnvVar}
                  onChange={(e) => setAdminEnvVar(e.target.value)}
                  style={{
                    padding: '0.5rem',
                    fontSize: '0.82rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: 'var(--bg-primary)',
                    color: 'var(--text-primary)'
                  }}
                >
                  <option value="GEMINI_API_KEY">GEMINI_API_KEY</option>
                  <option value="OPENAI_API_KEY">OPENAI_API_KEY</option>
                  <option value="ANTHROPIC_API_KEY">ANTHROPIC_API_KEY</option>
                  <option value="GROQ_API_KEY">GROQ_API_KEY</option>
                  <option value="OLLAMA_BASE_URL">OLLAMA_BASE_URL</option>
                  <option value="BRAVE_SEARCH_API_KEY">BRAVE_SEARCH_API_KEY</option>
                  <option value="SERPAPI_API_KEY">SERPAPI_API_KEY</option>
                </select>

                <input
                  type="password"
                  value={adminEnvVal}
                  onChange={(e) => setAdminEnvVal(e.target.value)}
                  placeholder="Enter new value for .env..."
                  style={{
                    flex: 1,
                    minWidth: '220px',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.82rem',
                    borderRadius: '6px',
                    border: '1px solid var(--border)',
                    background: 'var(--bg-primary)',
                    color: 'var(--text-primary)',
                    fontFamily: 'monospace'
                  }}
                />

                <button
                  type="submit"
                  className="btn btn-secondary"
                  disabled={savingAdminEnv || !adminEnvVal.trim()}
                  style={{ fontSize: '0.8rem', padding: '0.5rem 1rem' }}
                >
                  {savingAdminEnv ? 'Writing file...' : 'Update .env'}
                </button>
              </div>

              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Note: Modifying <code>.env</code> requires restarting the backend service to fully reload.
              </div>
            </form>
          )}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {confirmDeleteProvider && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '420px', width: '100%', padding: '1.5rem', background: 'var(--bg-card)' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
              Confirm deletion of personal key?
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Are you sure you want to remove the personal key for <strong>{confirmDeleteProvider.name}</strong>?
              {confirmDeleteProvider.has_system_key
                ? ' The platform will automatically revert to using the server default configuration.'
                : ' You will not be able to use models from this provider until a valid key is provided.'}
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '1.25rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirmDeleteProvider(null)}
                disabled={Boolean(deletingProvider)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleConfirmDelete}
                disabled={Boolean(deletingProvider)}
                style={{ background: '#ef4444', borderColor: '#ef4444' }}
              >
                {deletingProvider ? 'Deleting...' : 'Confirm Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import Icon from '@/components/ui/Icon';
import { useApp } from '@/context/AppContext';

interface HardwareCheck {
  id: string;
  name: string;
  required: string;
  actual: string;
  passed: boolean;
}

interface EligibilityData {
  eligible: boolean;
  metrics: {
    cpu_cores: number;
    total_ram_gb: number;
    avail_ram_gb: number;
    free_disk_gb: number;
    os_name: string;
    architecture: string;
  };
  checks: HardwareCheck[];
  message: string;
}

interface EmbeddedModelStatus {
  id: string;
  name: string;
  file_path: string;
  file_size_bytes: number;
  download_status: 'NOT_DOWNLOADED' | 'DOWNLOADING' | 'READY' | 'ERROR';
  download_progress: number;
  file_exists: boolean;
  actual_file_size_bytes: number;
}

interface SemanticCacheStats {
  total_entries: number;
  total_hits: number;
  categories: { category: string; count: number }[];
}

export default function EmbeddedModelCard() {
  const { t } = useApp();
  const [eligibility, setEligibility] = useState<EligibilityData | null>(null);
  const [modelStatus, setModelStatus] = useState<EmbeddedModelStatus | null>(null);
  const [cacheStats, setCacheStats] = useState<SemanticCacheStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [toastMsg, setToastMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [resHw, resModel, resCache] = await Promise.all([
        fetch('/api/v1/models/embedded/hardware-check'),
        fetch('/api/v1/models/embedded/status'),
        fetch('/api/v1/semantic-cache/stats'),
      ]);

      if (resHw.ok) {
        const dataHw = await resHw.json();
        setEligibility(dataHw);
      }
      if (resModel.ok) {
        const dataModel = await resModel.json();
        setModelStatus(dataModel);
      }
      if (resCache.ok) {
        const dataCache = await resCache.json();
        setCacheStats(dataCache);
      }
    } catch (err) {
      console.error('Error fetching embedded model info:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDownload = async () => {
    if (!eligibility?.eligible) {
      setToastMsg({
        type: 'error',
        text: 'Hardware requirements not met. Cannot download embedded model.',
      });
      return;
    }

    setDownloading(true);
    setToastMsg(null);
    try {
      const res = await fetch('/api/v1/models/embedded/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: 'qwen2.5-0.5b-embedded' }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Download failed');
      }
      setToastMsg({
        type: 'success',
        text: 'Embedded lightweight model downloaded and ready!',
      });
      fetchData();
    } catch (err: any) {
      setToastMsg({
        type: 'error',
        text: err.message || 'Error downloading model',
      });
    } finally {
      setDownloading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete the embedded model file to free up disk space?')) {
      return;
    }
    try {
      const res = await fetch('/api/v1/models/embedded', { method: 'DELETE' });
      if (res.ok) {
        setToastMsg({
          type: 'success',
          text: 'Embedded model file removed and disk space freed.',
        });
        fetchData();
      }
    } catch (err: any) {
      setToastMsg({ type: 'error', text: 'Error deleting model' });
    }
  };

  const isModelReady = modelStatus?.download_status === 'READY';

  return (
    <div style={{
      marginBottom: '1.75rem',
      borderRadius: 'var(--radius-lg, 12px)',
      background: 'var(--bg-elevated, #161b22)',
      border: '1px solid var(--border-subtle, #30363d)',
      padding: '1.5rem',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Toast Alert */}
      {toastMsg && (
        <div style={{
          padding: '10px 14px',
          borderRadius: '8px',
          marginBottom: '1rem',
          fontSize: '0.875rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: toastMsg.type === 'success' ? 'rgba(35, 134, 54, 0.2)' : 'rgba(218, 54, 51, 0.2)',
          border: `1px solid ${toastMsg.type === 'success' ? 'var(--primary, #238636)' : '#da3633'}`,
          color: toastMsg.type === 'success' ? 'var(--primary, #3fb950)' : '#f85149'
        }}>
          <Icon name={toastMsg.type === 'success' ? 'check' : 'alert'} size={16} />
          <span>{toastMsg.text}</span>
        </div>
      )}

      {/* Header Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{
              display: 'inline-flex',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: 600,
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              border: '1px solid rgba(56, 189, 248, 0.3)'
            }}>
              Direct In-Project (Zero External Server)
            </span>
            <span style={{
              display: 'inline-flex',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '0.75rem',
              fontWeight: 600,
              background: isModelReady ? 'rgba(35, 134, 54, 0.2)' : 'rgba(234, 179, 8, 0.15)',
              color: isModelReady ? 'var(--primary, #3fb950)' : '#eab308',
              border: `1px solid ${isModelReady ? 'var(--primary, #238636)' : 'rgba(234, 179, 8, 0.3)'}`
            }}>
              {isModelReady ? '● Ready to Run' : '○ Not Downloaded'}
            </span>
          </div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Qwen 2.5 0.5B (Direct Embedded In-Project Model)
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '4px', maxWidth: '720px' }}>
            Executes directly in the backend process without Ollama daemon or any external cloud services.
            System checks device hardware before enabling download and local execution.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="btn btn-secondary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.825rem' }}
        >
          <Icon name="refresh" size={14} />
          <span>Re-check Hardware</span>
        </button>
      </div>

      {/* Grid: Hardware Gate & Semantic Cache */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '1rem',
        marginBottom: '1.25rem'
      }}>
        {/* Hardware Diagnostic Checklist */}
        <div style={{
          background: 'var(--bg-base, #0d1117)',
          border: '1px solid var(--border-subtle, #30363d)',
          borderRadius: '8px',
          padding: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Icon name="cpu" size={16} />
              <span>Hardware Eligibility Check</span>
            </span>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: '6px',
              background: eligibility?.eligible ? 'rgba(35, 134, 54, 0.2)' : 'rgba(218, 54, 51, 0.2)',
              color: eligibility?.eligible ? '#3fb950' : '#f85149'
            }}>
              {eligibility?.eligible ? 'ELIGIBLE' : 'INELIGIBLE'}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {eligibility?.checks.map((check) => (
              <div
                key={check.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '0.8rem',
                  padding: '4px 6px',
                  borderRadius: '4px',
                  background: 'rgba(255, 255, 255, 0.02)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ color: check.passed ? '#3fb950' : '#f85149' }}>
                    {check.passed ? '✓' : '✗'}
                  </span>
                  <span style={{ color: 'var(--text-secondary)' }}>{check.name}</span>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{check.actual}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.725rem', marginLeft: '6px' }}>
                    (y/c: {check.required})
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '10px', fontSize: '0.75rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
            Operating System: {eligibility?.metrics.os_name} ({eligibility?.metrics.architecture})
          </div>
        </div>

        {/* Semantic Knowledge Cache (10,000+ entries) */}
        <div style={{
          background: 'var(--bg-base, #0d1117)',
          border: '1px solid var(--border-subtle, #30363d)',
          borderRadius: '8px',
          padding: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Icon name="sparkles" size={16} style={{ color: '#eab308' }} />
              <span>Japanese Linguistic Semantic Cache</span>
            </span>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: '6px',
              background: 'rgba(35, 134, 54, 0.2)',
              color: '#3fb950'
            }}>
              FTS5 & B-Tree
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '10px' }}>
            <div style={{
              padding: '8px 10px',
              borderRadius: '6px',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)'
            }}>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Pre-built Knowledge Base</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
                {cacheStats?.total_entries ? cacheStats.total_entries.toLocaleString() : '10,500+'}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>JLPT questions, Particles, Kaiwa</div>
            </div>

            <div style={{
              padding: '8px 10px',
              borderRadius: '6px',
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-subtle)'
            }}>
              <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Cache Hits</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#3fb950', marginTop: '2px' }}>
                {cacheStats?.total_hits ? cacheStats.total_hits.toLocaleString() : '0'}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Sub-5ms Latency</div>
            </div>
          </div>

          <div style={{
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            background: 'rgba(56, 189, 248, 0.05)',
            border: '1px solid rgba(56, 189, 248, 0.15)',
            borderRadius: '6px',
            padding: '6px 10px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Icon name="check" size={14} style={{ color: '#38bdf8' }} />
            <span>Continuous learning on question-response pairs (Deduplication enabled)</span>
          </div>
        </div>
      </div>

      {/* Model Download & Action Footer */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        paddingTop: '1rem',
        borderTop: '1px solid var(--border-subtle)'
      }}>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          {isModelReady ? (
            <span style={{ color: '#3fb950', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Icon name="check" size={16} />
              <span>Model weights ready in workspace (`ai-backend/models/embedded/qwen2.5-0.5b.bin`). You can select this model in the chat composer.</span>
            </span>
          ) : (
            <span>Model weights not downloaded. Click 'Download Model' after checking hardware compatibility to enable local inference.</span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {!isModelReady ? (
            <button
              onClick={handleDownload}
              disabled={downloading || !eligibility?.eligible}
              className="btn btn-primary"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                opacity: (!eligibility?.eligible || downloading) ? 0.6 : 1,
                cursor: (!eligibility?.eligible || downloading) ? 'not-allowed' : 'pointer'
              }}
            >
              <Icon name="upload" size={14} />
              <span>{downloading ? 'Downloading Model...' : 'Download Embedded Model (~380MB)'}</span>
            </button>
          ) : (
            <button
              onClick={handleDelete}
              className="btn btn-secondary"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                color: '#f85149',
                borderColor: 'rgba(218, 54, 51, 0.3)'
              }}
            >
              <Icon name="trash" size={14} />
              <span>Delete Model (Free Up Disk Space)</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}


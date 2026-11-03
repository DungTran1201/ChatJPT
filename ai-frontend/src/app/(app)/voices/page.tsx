'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { VoiceItem, VoiceEngineStatus } from '@/types';
import { VoiceService } from '@/services/voiceService';
import PageHeader from '@/components/ui/PageHeader';
import Icon from '@/components/ui/Icon';
import Toast, { ToastMessage } from '@/components/ui/Toast';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import { useApp } from '@/context/AppContext';

export default function VoiceManagementPage() {
  const { t } = useApp();
  const [voices, setVoices] = useState<VoiceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [engineStatus, setEngineStatus] = useState<VoiceEngineStatus | null>(null);
  const [checkingEngine, setCheckingEngine] = useState(false);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [genderFilter, setGenderFilter] = useState('all');
  const [styleFilter, setStyleFilter] = useState('all');

  // Audio Playback State
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const [synthesizingId, setSynthesizingId] = useState<string | null>(null);

  // Tuning Modal State
  const [tuningVoice, setTuningVoice] = useState<VoiceItem | null>(null);
  const [tuneSpeed, setTuneSpeed] = useState(1.0);
  const [tunePitch, setTunePitch] = useState(0.0);
  const [tuneIntonation, setTuneIntonation] = useState(1.0);
  const [tuneVolume, setTuneVolume] = useState(1.0);
  const [tuneSampleText, setTuneSampleText] = useState('');
  const [savingTuning, setSavingTuning] = useState(false);
  const [previewingTuning, setPreviewingTuning] = useState(false);

  // Create Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: '',
    character_name: '',
    speaker_id: 8,
    style_name: 'Normal',
    gender: 'female',
    description: '',
    speed_scale: 1.0,
    pitch_scale: 0.0,
    intonation_scale: 1.0,
    volume_scale: 1.0,
    sample_text: 'こんにちは！日本語の勉強を一緒に頑張りましょう。',
  });
  const [creating, setCreating] = useState(false);

  // Delete Confirm State
  const [voiceToDelete, setVoiceToDelete] = useState<VoiceItem | null>(null);

  // Toast
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const addToast = (type: 'success' | 'error' | 'info', message: string) => {
    setToast({ type, message });
  };

  // 1. Fetch Data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [voicesRes, statusRes] = await Promise.all([
        VoiceService.getVoices(),
        VoiceService.getEngineStatus(),
      ]);
      setVoices(voicesRes.items || []);
      setEngineStatus(statusRes);
    } catch (err: any) {
      addToast('error', err?.message || 'Failed to load voices data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Refresh Engine Status
  const handleRefreshEngine = async () => {
    setCheckingEngine(true);
    try {
      const statusRes = await VoiceService.getEngineStatus();
      setEngineStatus(statusRes);
      if (statusRes.engine_available) {
        if (statusRes.engine_mode === 'embedded_core') {
          addToast('success', `VoiceVox Core ready (${statusRes.loaded_models_count || 16} models VVM)!`);
        } else {
          addToast('success', `VoiceVox Engine connected (v${statusRes.version || '0.14'})!`);
        }
      } else {
        addToast('info', 'VoiceVox Engine offline. Using acoustic fallback mode.');
      }
    } catch (err: any) {
      addToast('error', 'Engine check error: ' + err?.message);
    } finally {
      setCheckingEngine(false);
    }
  };

  // 2. Play Sample Audio
  const handlePlaySample = async (voice: VoiceItem) => {
    if (playingVoiceId === voice.id) {
      VoiceService.stopAudio();
      setPlayingVoiceId(null);
      return;
    }

    setSynthesizingId(voice.id);
    try {
      const text = voice.sample_text || 'こんにちは！日本語の勉強を一緒に頑張りましょう。';
      const blob = await VoiceService.synthesizeByVoiceId(voice.id, text, {
        speed_scale: voice.speed_scale,
        pitch_scale: voice.pitch_scale,
        intonation_scale: voice.intonation_scale,
        volume_scale: voice.volume_scale,
      });

      setPlayingVoiceId(voice.id);
      setSynthesizingId(null);

      await VoiceService.playAudioBlob(blob);
      setPlayingVoiceId(null);
    } catch (err: any) {
      setSynthesizingId(null);
      setPlayingVoiceId(null);
      // Fallback to Web Speech if Audio Synthesis error
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(voice.sample_text || 'こんにちは！');
        u.lang = 'ja-JP';
        window.speechSynthesis.speak(u);
        addToast('info', 'Playing audio via Web Speech fallback');
      } else {
        addToast('error', 'Failed to play audio: ' + (err?.message || 'Error'));
      }
    }
  };

  // 3. Open Tuning Modal
  const handleOpenTuning = (voice: VoiceItem) => {
    setTuningVoice(voice);
    setTuneSpeed(voice.speed_scale);
    setTunePitch(voice.pitch_scale);
    setTuneIntonation(voice.intonation_scale);
    setTuneVolume(voice.volume_scale);
    setTuneSampleText(voice.sample_text || 'こんにちは！日本語の勉強を一緒に頑張りましょう。');
  };

  // Preview in Tuning Modal
  const handlePreviewTuning = async () => {
    if (!tuningVoice) return;
    setPreviewingTuning(true);
    try {
      const blob = await VoiceService.synthesizeAudio({
        text: tuneSampleText.trim() || 'こんにちは！',
        speaker_id: tuningVoice.speaker_id,
        speed_scale: tuneSpeed,
        pitch_scale: tunePitch,
        intonation_scale: tuneIntonation,
        volume_scale: tuneVolume,
      });
      await VoiceService.playAudioBlob(blob);
    } catch (err: any) {
      addToast('error', 'Audio test error: ' + err?.message);
    } finally {
      setPreviewingTuning(false);
    }
  };

  // Save Tuning
  const handleSaveTuning = async () => {
    if (!tuningVoice) return;
    setSavingTuning(true);
    try {
      const updated = await VoiceService.updateVoice(tuningVoice.id, {
        speed_scale: tuneSpeed,
        pitch_scale: tunePitch,
        intonation_scale: tuneIntonation,
        volume_scale: tuneVolume,
        sample_text: tuneSampleText.trim(),
      });
      setVoices((prev) => prev.map((v) => (v.id === updated.id ? updated : v)));
      addToast('success', `Saved acoustic parameters for '${updated.name}'`);
      setTuningVoice(null);
    } catch (err: any) {
      addToast('error', 'Failed to save parameters: ' + err?.message);
    } finally {
      setSavingTuning(false);
    }
  };

  // 4. Create Custom Voice
  const handleCreateVoice = async () => {
    if (!createForm.name.trim() || !createForm.character_name.trim()) {
      addToast('info', 'Please provide both Voice Name and Character Name.');
      return;
    }
    setCreating(true);
    try {
      const newVoice = await VoiceService.createVoice(createForm);
      setVoices((prev) => [newVoice, ...prev]);
      addToast('success', `Created voice '${newVoice.name}' successfully!`);
      setShowCreateModal(false);
      setCreateForm({
        name: '',
        character_name: '',
        speaker_id: 8,
        style_name: 'Normal',
        gender: 'female',
        description: '',
        speed_scale: 1.0,
        pitch_scale: 0.0,
        intonation_scale: 1.0,
        volume_scale: 1.0,
        sample_text: 'こんにちは！日本語の勉強を一緒に頑張りましょう。',
      });
    } catch (err: any) {
      addToast('error', 'Voice creation error: ' + err?.message);
    } finally {
      setCreating(false);
    }
  };

  // 5. Delete Custom Voice
  const handleDeleteVoice = async () => {
    if (!voiceToDelete) return;
    try {
      await VoiceService.deleteVoice(voiceToDelete.id);
      setVoices((prev) => prev.filter((v) => v.id !== voiceToDelete.id));
      addToast('success', `Deleted voice '${voiceToDelete.name}'.`);
    } catch (err: any) {
      addToast('error', 'Failed to delete voice: ' + err?.message);
    } finally {
      setVoiceToDelete(null);
    }
  };

  // Filtered Voices
  const filteredVoices = useMemo(() => {
    return voices.filter((v) => {
      // Search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = v.name?.toLowerCase().includes(q);
        const matchChar = v.character_name?.toLowerCase().includes(q);
        const matchDesc = v.description?.toLowerCase().includes(q);
        if (!matchName && !matchChar && !matchDesc) return false;
      }
      // Gender
      if (genderFilter !== 'all' && v.gender !== genderFilter) {
        return false;
      }
      // Style
      if (styleFilter !== 'all') {
        const style = (v.style_name || 'Normal').toLowerCase();
        if (style !== styleFilter.toLowerCase()) return false;
      }
      return true;
    });
  }, [voices, searchQuery, genderFilter, styleFilter]);

  // Unique Styles for Filter
  const availableStyles = useMemo(() => {
    const set = new Set<string>();
    voices.forEach((v) => {
      if (v.style_name) set.add(v.style_name);
    });
    return Array.from(set);
  }, [voices]);

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1440px', margin: '0 auto', minHeight: '100%' }}>
      {/* Page Header */}
      <PageHeader
        title={t('voices.title')}
        description={t('voices.sub')}
        actions={
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              onClick={handleRefreshEngine}
              disabled={checkingEngine}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '8px',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-default)',
                color: 'var(--text-primary)',
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              <Icon name="refresh" size={14} />
              {checkingEngine ? t('voices.checking_engine') : t('voices.check_engine')}
            </button>
            <button
              type="button"
              onClick={() => setShowCreateModal(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: '8px',
                background: 'var(--accent-color, #10b981)',
                color: '#fff',
                border: 'none',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Icon name="plus" size={14} />
              {t('voices.add_voice')}
            </button>
          </div>
        }
      />

      {/* Engine Status Banner */}
      <div
        style={{
          marginTop: '16px',
          padding: '14px 18px',
          borderRadius: '12px',
          backgroundColor: engineStatus?.engine_available
            ? 'rgba(16, 185, 129, 0.08)'
            : 'rgba(245, 158, 11, 0.08)',
          border: `1px solid ${
            engineStatus?.engine_available
              ? 'rgba(16, 185, 129, 0.25)'
              : 'rgba(245, 158, 11, 0.25)'
          }`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '20px' }}>
            {engineStatus?.engine_available ? '🟢' : '🟡'}
          </span>
          <div>
            <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--text-primary)' }}>
              {engineStatus?.engine_available
                ? engineStatus.engine_mode === 'embedded_core'
                  ? t('voices.engine_active_embedded') + ` (v${engineStatus.version || '0.17.1'})`
                  : t('voices.engine_active_server') + ` (v${engineStatus.version || '0.14'})`
                : t('voices.engine_offline')}
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              {engineStatus?.engine_available
                ? engineStatus.engine_mode === 'embedded_core'
                  ? t('voices.engine_embedded_desc').replace('{models}', String(engineStatus.loaded_models_count || 16)).replace('{speakers}', String(engineStatus.supported_speakers_count || 30)).replace('{cache}', String(engineStatus.cached_audio_count || 0))
                  : `${engineStatus.engine_url} | ${engineStatus.latency_ms || 15}ms | ${engineStatus.cached_audio_count} audio cache`
                : t('voices.engine_offline_desc')}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <Link
            href="/prompts"
            style={{
              fontSize: '12px',
              padding: '6px 12px',
              borderRadius: '6px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <Icon name="prompts" size={12} />
            {t('voices.to_sensei')}
          </Link>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div
        style={{
          marginTop: '20px',
          display: 'flex',
          gap: '12px',
          flexWrap: 'wrap',
          alignItems: 'center',
          backgroundColor: 'var(--bg-elevated)',
          padding: '12px 16px',
          borderRadius: '12px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        {/* Search Input */}
        <div style={{ flex: '1 1 240px', position: 'relative' }}>
          <Icon
            name="search"
            size={14}
            style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-muted)',
            }}
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t('voices.search_placeholder')}
            style={{
              width: '100%',
              padding: '8px 12px 8px 36px',
              borderRadius: '8px',
              border: '1px solid var(--border-default)',
              backgroundColor: 'var(--bg-base)',
              color: 'var(--text-primary)',
              fontSize: '13px',
              outline: 'none',
            }}
          />
        </div>

        {/* Gender Filter Chips */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginRight: '4px' }}>
            {t('prompts.age_gender')}:
          </span>
          {[
            { id: 'all', label: t('voices.gender_all') },
            { id: 'female', label: t('voices.gender_female') },
            { id: 'male', label: t('voices.gender_male') },
            { id: 'other', label: t('voices.gender_other') },
          ].map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setGenderFilter(item.id)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 500,
                cursor: 'pointer',
                border: 'none',
                background:
                  genderFilter === item.id
                    ? 'var(--accent-color, #10b981)'
                    : 'var(--bg-base)',
                color: genderFilter === item.id ? '#fff' : 'var(--text-secondary)',
              }}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Style Filter Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{t('prompts.teaching_style')}:</span>
          <select
            value={styleFilter}
            onChange={(e) => setStyleFilter(e.target.value)}
            style={{
              padding: '6px 10px',
              borderRadius: '6px',
              fontSize: '12px',
              backgroundColor: 'var(--bg-base)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-default)',
              outline: 'none',
            }}
          >
            <option value="all">{t('voices.style_all')}</option>
            {availableStyles.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Voice Cards Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          {t('common.loading')}
        </div>
      ) : filteredVoices.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 20px',
            backgroundColor: 'var(--bg-elevated)',
            borderRadius: '12px',
            marginTop: '20px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🎙️</div>
          <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {t('voices.empty_title') || 'No matching voices found'}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {t('voices.empty_desc') || 'Try adjusting your search query or gender/style filter.'}
          </div>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '16px',
            marginTop: '20px',
          }}
        >
          {filteredVoices.map((voice) => {
            const isPlaying = playingVoiceId === voice.id;
            const isSynthesizing = synthesizingId === voice.id;

            return (
              <div
                key={voice.id}
                style={{
                  backgroundColor: 'var(--bg-elevated)',
                  borderRadius: '12px',
                  border: isPlaying
                    ? '1px solid var(--accent-color, #10b981)'
                    : '1px solid var(--border-subtle)',
                  padding: '18px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  boxShadow: isPlaying ? '0 0 12px rgba(16, 185, 129, 0.2)' : 'none',
                  transition: 'all 0.2s ease',
                }}
              >
                {/* Header: Avatar, Name, Speaker ID */}
                <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--bg-base)',
                      border: '2px solid var(--border-default)',
                      overflow: 'hidden',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      fontSize: '22px',
                    }}
                  >
                    {voice.avatar_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={voice.avatar_url}
                        alt={voice.name}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    ) : (
                      <span>{voice.gender === 'female' ? '🌸' : '⚡'}</span>
                    )}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span
                        style={{
                          fontSize: '15px',
                          fontWeight: 700,
                          color: 'var(--text-primary)',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {voice.character_name}
                      </span>
                      <span
                        style={{
                          fontSize: '11px',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor:
                            voice.gender === 'female'
                              ? 'rgba(236, 72, 153, 0.15)'
                              : 'rgba(59, 130, 246, 0.15)',
                          color:
                            voice.gender === 'female'
                              ? '#ec4899'
                              : '#3b82f6',
                          fontWeight: 600,
                        }}
                      >
                        {voice.gender === 'female' ? t('voices.gender_female') : t('voices.gender_male')}
                      </span>
                    </div>

                    <div
                      style={{
                        fontSize: '12px',
                        color: 'var(--text-secondary)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        marginTop: '2px',
                      }}
                    >
                      {voice.name}
                    </div>
                  </div>

                  <div
                    style={{
                      fontSize: '11px',
                      padding: '3px 8px',
                      borderRadius: '12px',
                      backgroundColor: 'var(--bg-base)',
                      border: '1px solid var(--border-default)',
                      color: 'var(--text-muted)',
                      fontWeight: 600,
                    }}
                  >
                    ID: {voice.speaker_id}
                  </div>
                </div>

                {/* Description */}
                {voice.description && (
                  <div
                    style={{
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                      lineHeight: '1.4',
                      height: '34px',
                      overflow: 'hidden',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }}
                  >
                    {voice.description}
                  </div>
                )}

                {/* Acoustic Parameter Badges */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: '6px',
                    backgroundColor: 'var(--bg-base)',
                    padding: '8px',
                    borderRadius: '8px',
                    textAlign: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{t('voices.speed')}</div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {voice.speed_scale}x
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{t('voices.pitch')}</div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {voice.pitch_scale > 0 ? `+${voice.pitch_scale}` : voice.pitch_scale}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{t('voices.intonation')}</div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {voice.intonation_scale}x
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{t('voices.volume')}</div>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {voice.volume_scale}x
                    </div>
                  </div>
                </div>

                {/* Sample Sentence Preview */}
                <div
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    fontStyle: 'italic',
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    padding: '6px 10px',
                    borderRadius: '6px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  💬 &ldquo;{voice.sample_text || 'こんにちは！'}&rdquo;
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: '8px', marginTop: 'auto', paddingTop: '4px' }}>
                  <button
                    type="button"
                    onClick={() => handlePlaySample(voice)}
                    disabled={isSynthesizing}
                    style={{
                      flex: 1,
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      backgroundColor: isPlaying
                        ? '#ef4444'
                        : 'var(--accent-color, #10b981)',
                      color: '#fff',
                      border: 'none',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'background 0.2s',
                    }}
                  >
                    <Icon name={isPlaying ? 'stop' : 'voice'} size={14} />
                    {isSynthesizing
                      ? t('voices.synthesizing')
                      : isPlaying
                      ? 'Stop'
                      : t('voices.play_sample')}
                  </button>

                  <button
                    type="button"
                    onClick={() => handleOpenTuning(voice)}
                    style={{
                      padding: '8px 12px',
                      borderRadius: '8px',
                      backgroundColor: 'var(--bg-base)',
                      border: '1px solid var(--border-default)',
                      color: 'var(--text-primary)',
                      fontSize: '12px',
                      fontWeight: 500,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Icon name="edit" size={13} />
                    {t('voices.customize')}
                  </button>

                  {!voice.is_system_preset && (
                    <button
                      type="button"
                      onClick={() => setVoiceToDelete(voice)}
                      style={{
                        padding: '8px 10px',
                        borderRadius: '8px',
                        backgroundColor: 'var(--bg-base)',
                        border: '1px solid var(--border-default)',
                        color: '#ef4444',
                        fontSize: '12px',
                        cursor: 'pointer',
                      }}
                    >
                      <Icon name="trash" size={13} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Acoustic Parameter Tuning Modal */}
      {tuningVoice && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: '16px',
              width: '100%',
              maxWidth: '540px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '18px',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
            }}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {t('voices.tune_modal_title')}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {tuningVoice.character_name} - {tuningVoice.name}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setTuningVoice(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '4px',
                }}
              >
                <Icon name="close" size={18} />
              </button>
            </div>

            {/* Sliders */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {/* Speed */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                    {t('voices.speed')} (Speed Scale)
                  </span>
                  <span style={{ color: 'var(--accent-color, #10b981)', fontWeight: 600 }}>
                    {tuneSpeed.toFixed(2)}x
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.05"
                  value={tuneSpeed}
                  onChange={(e) => setTuneSpeed(parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-color, #10b981)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>0.5x (Slow)</span>
                  <span>1.0x (Normal)</span>
                  <span>2.0x (Fast)</span>
                </div>
              </div>

              {/* Pitch */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                    {t('voices.pitch')} (Pitch Scale)
                  </span>
                  <span style={{ color: 'var(--accent-color, #10b981)', fontWeight: 600 }}>
                    {tunePitch > 0 ? `+${tunePitch.toFixed(2)}` : tunePitch.toFixed(2)}
                  </span>
                </div>
                <input
                  type="range"
                  min="-0.15"
                  max="0.15"
                  step="0.01"
                  value={tunePitch}
                  onChange={(e) => setTunePitch(parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-color, #10b981)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>-0.15 (Low)</span>
                  <span>0.00 (Normal)</span>
                  <span>+0.15 (High)</span>
                </div>
              </div>

              {/* Intonation */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                    {t('voices.intonation')} (Intonation Scale)
                  </span>
                  <span style={{ color: 'var(--accent-color, #10b981)', fontWeight: 600 }}>
                    {tuneIntonation.toFixed(2)}x
                  </span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="2.0"
                  step="0.05"
                  value={tuneIntonation}
                  onChange={(e) => setTuneIntonation(parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-color, #10b981)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>0.0x (Flat)</span>
                  <span>1.0x (Natural)</span>
                  <span>2.0x (Expressive)</span>
                </div>
              </div>

              {/* Volume */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                    {t('voices.volume')} (Volume Scale)
                  </span>
                  <span style={{ color: 'var(--accent-color, #10b981)', fontWeight: 600 }}>
                    {tuneVolume.toFixed(2)}x
                  </span>
                </div>
                <input
                  type="range"
                  min="0.2"
                  max="2.0"
                  step="0.05"
                  value={tuneVolume}
                  onChange={(e) => setTuneVolume(parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent-color, #10b981)' }}
                />
              </div>

              {/* Sample Text */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: 'var(--text-primary)', fontWeight: 500, marginBottom: '6px' }}>
                  {t('voices.tune_sample_label')} (Japanese Sample Text)
                </label>
                <textarea
                  value={tuneSampleText}
                  onChange={(e) => setTuneSampleText(e.target.value)}
                  rows={2}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-default)',
                    backgroundColor: 'var(--bg-base)',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    outline: 'none',
                    resize: 'none',
                  }}
                />
              </div>
            </div>

            {/* Modal Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '10px', marginTop: '6px' }}>
              <button
                type="button"
                onClick={handlePreviewTuning}
                disabled={previewingTuning}
                style={{
                  padding: '9px 16px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--bg-base)',
                  border: '1px solid var(--border-default)',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Icon name="voice" size={14} />
                {previewingTuning ? t('voices.playing') : t('voices.play_sample')}
              </button>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setTuningVoice(null)}
                  style={{
                    padding: '9px 16px',
                    borderRadius: '8px',
                    backgroundColor: 'transparent',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    fontSize: '13px',
                    cursor: 'pointer',
                  }}
                >
                  {t('common.close')}
                </button>
                <button
                  type="button"
                  onClick={handleSaveTuning}
                  disabled={savingTuning}
                  style={{
                    padding: '9px 18px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--accent-color, #10b981)',
                    color: '#fff',
                    border: 'none',
                    fontSize: '13px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  {savingTuning ? t('voices.saving_params') : t('voices.save_params')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Custom Voice Modal */}
      {showCreateModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              borderRadius: '16px',
              width: '100%',
              maxWidth: '520px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {t('voices.create_modal_title')}
              </div>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <Icon name="close" size={18} />
              </button>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Display Name *
              </label>
              <input
                type="text"
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                placeholder="e.g. Tsumugi (Joyful / Natural)"
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-default)',
                  backgroundColor: 'var(--bg-base)',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Character Name *
                </label>
                <input
                  type="text"
                  value={createForm.character_name}
                  onChange={(e) => setCreateForm({ ...createForm, character_name: e.target.value })}
                  placeholder="e.g. 春日部つむぎ"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-default)',
                    backgroundColor: 'var(--bg-base)',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Speaker ID (VoiceVox) *
                </label>
                <input
                  type="number"
                  value={createForm.speaker_id}
                  onChange={(e) => setCreateForm({ ...createForm, speaker_id: parseInt(e.target.value) || 0 })}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-default)',
                    backgroundColor: 'var(--bg-base)',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                  }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Gender
                </label>
                <select
                  value={createForm.gender}
                  onChange={(e) => setCreateForm({ ...createForm, gender: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-default)',
                    backgroundColor: 'var(--bg-base)',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                  }}
                >
                  <option value="female">{t('voices.gender_female')} (Female)</option>
                  <option value="male">{t('voices.gender_male')} (Male)</option>
                  <option value="other">{t('voices.gender_other')} (Other)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Style
                </label>
                <input
                  type="text"
                  value={createForm.style_name}
                  onChange={(e) => setCreateForm({ ...createForm, style_name: e.target.value })}
                  placeholder="e.g. Normal, Sweet"
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: '1px solid var(--border-default)',
                    backgroundColor: 'var(--bg-base)',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                  }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                Voice Description
              </label>
              <textarea
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                rows={2}
                placeholder="Tone characteristics, target audience..."
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-default)',
                  backgroundColor: 'var(--bg-base)',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '8px',
                  backgroundColor: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-secondary)',
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                {t('common.cancel')}
              </button>
              <button
                type="button"
                onClick={handleCreateVoice}
                disabled={creating}
                style={{
                  padding: '8px 18px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--accent-color, #10b981)',
                  color: '#fff',
                  border: 'none',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {creating ? t('common.saving') : t('voices.add_voice')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={!!voiceToDelete}
        title={t('common.delete')}
        message={`Delete voice '${voiceToDelete?.name}'? This action cannot be undone.`}
        confirmLabel={t('common.delete')}
        cancelLabel={t('common.cancel')}
        isDestructive={true}
        onConfirm={handleDeleteVoice}
        onCancel={() => setVoiceToDelete(null)}
      />

      {/* Toast Notification */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
}

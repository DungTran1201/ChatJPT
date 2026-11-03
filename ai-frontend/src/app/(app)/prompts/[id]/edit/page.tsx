'use client';

import { useApp } from '@/context/AppContext';

import { VoiceService } from '@/services/voiceService';
import { VoiceItem } from '@/types';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { SystemPromptService } from '@/services/systemPromptService';
import PageHeader from '@/components/ui/PageHeader';
import Icon from '@/components/ui/Icon';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import { formatErrorMessage } from '@/lib/errors';
import { LibraryAssetManager } from '@/components/ui/AttachmentUploader';
import { AttachmentItem } from '@/services/attachmentService';

export default function EditSenseiPage() {
  const { t } = useApp();
  const router = useRouter();
  const params = useParams();
  const promptId = typeof params?.id === 'string' ? params.id : Array.isArray(params?.id) ? params.id[0] : '';

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [content, setContent] = useState('');
  const [age, setAge] = useState(25);
  const [gender, setGender] = useState('female');
  const [japaneseLevel, setJapaneseLevel] = useState('N5');
  const [voiceId, setVoiceId] = useState<string>('voice_kasukabe_tsumugi');
  const [availableVoices, setAvailableVoices] = useState<VoiceItem[]>([]);
  const [playingTestAudio, setPlayingTestAudio] = useState(false);
  const [personality, setPersonality] = useState('');
  const [teachingStyle, setTeachingStyle] = useState('');
  const [catchphrase, setCatchphrase] = useState('');
  const [hobbies, setHobbies] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [isDefault, setIsDefault] = useState(false);
  const [isSystemPreset, setIsSystemPreset] = useState(false);
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showExitConfirm, setShowExitConfirm] = useState(false);

  useEffect(() => {
    if (!promptId) return;

    const fetchDetail = async () => {
      try {
        setLoading(true);
        setLoadError(null);
        const data = await SystemPromptService.getPrompt(promptId);
        setName(data.name || '');
        setDescription(data.description || '');
        setContent(data.content || '');
        setAge(data.age || 25);
        setGender(data.gender || 'female');
        setJapaneseLevel(data.japanese_level || 'N5');
        setPersonality(data.personality || '');
        setTeachingStyle(data.teaching_style || '');
        setCatchphrase(data.catchphrase || '');
        setHobbies(data.hobbies || '');
        setAvatarUrl(data.avatar_url || '');
        setIsDefault(Boolean(data.is_default));
        if (data.voice_id) setVoiceId(data.voice_id);
        VoiceService.getVoices().then(res => setAvailableVoices(res.items || [])).catch(() => {});
        setIsSystemPreset(Boolean(data.is_system_preset));
        setAttachments(data.attachments || []);
      } catch (err: any) {
        setLoadError(formatErrorMessage(err, 'Sensei does not exist or you do not have permission to view it.'));
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [promptId]);

  const handleCancel = () => {
    router.push('/prompts');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setErrorMsg('Please enter a name for the Sensei.');
      return;
    }

    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setErrorMsg('Please enter core persona instructions.');
      return;
    }

    try {
      setIsSubmitting(true);
      await SystemPromptService.updatePrompt(promptId, {
        name: trimmedName,
        description: description.trim() || null,
        content: content,
        age: Number(age) || 25,
        gender: gender,
        japanese_level: japaneseLevel,
        voice_id: voiceId || undefined,
        personality: personality.trim() || null,
        teaching_style: teachingStyle.trim() || null,
        catchphrase: catchphrase.trim() || null,
        hobbies: hobbies.trim() || null,
        avatar_url: avatarUrl.trim() || null,
        is_default: isDefault,
      });

      router.push('/prompts');
    } catch (err: any) {
      setErrorMsg(formatErrorMessage(err, 'Failed to update Sensei guidance. Please try again.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '4rem 0', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading Sensei profile...
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="page-container" style={{ maxWidth: '860px', padding: '2rem 1rem' }}>
        <div className="card" style={{ padding: '2rem', textAlign: 'center', borderColor: 'var(--danger)' }}>
          <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{loadError}</p>
          <Link href="/prompts" className="btn btn-secondary">Back to Sensei Roster</Link>
        </div>
      </div>
    );
  }


  const handleTestVoice = async () => {
    if (!voiceId) return;
    setPlayingTestAudio(true);
    try {
      const selected = availableVoices.find(v => v.id === voiceId);
      const sample = selected?.sample_text || 'はじめまして、一緒に勉強しましょう！';
      const blob = await VoiceService.synthesizeByVoiceId(voiceId, sample);
      await VoiceService.playAudioBlob(blob);
    } catch (err) {
      console.error(err);
    } finally {
      setPlayingTestAudio(false);
    }
  };

  return (
    <div className="custom-scrollbar" style={{ flex: 1, overflowY: 'auto' }}>
      <div className="page-container" style={{ maxWidth: '860px' }}>
        {/* Page Header */}
        <PageHeader
          title={`Edit Sensei: ${name}`}
          description={isSystemPreset ? "System Preset Sensei - Modifications will be automatically duplicated as your customized personal version." : "Update pedagogical style, personality traits, target proficiency level, and system instructions."}
        >
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleCancel}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="chevronLeft" size={13} />
            <span>Back to Sensei Roster</span>
          </button>
        </PageHeader>

        {errorMsg && (
          <div
            style={{
              padding: '0.75rem 1rem',
              background: 'var(--danger-bg)',
              border: '1px solid rgba(240, 113, 120, 0.4)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--danger)',
              marginBottom: '1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.8125rem',
            }}
          >
            <Icon name="alert" size={14} />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="card" style={{ padding: '1.75rem' }}>
          {/* Section 1: Basic Identity */}
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
            1. Identity & Profile Information
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <label htmlFor="edit-name" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Sensei Name <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <input
                id="edit-name"
                type="text"
                className="input"
                value={name}
                onChange={e => setName(e.target.value)}
                maxLength={100}
                required
              />
            </div>

            <div>
              <label htmlFor="edit-level" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Target JLPT Proficiency Level
              </label>
              <select
                id="edit-level"
                className="select"
                value={japaneseLevel}
                onChange={e => setJapaneseLevel(e.target.value)}
              >
                <option value="N5">JLPT N5 (Beginner)</option>
                <option value="N4">JLPT N4 (Elementary & Kaiwa)</option>
                <option value="N3">JLPT N3 (Intermediate)</option>
                <option value="N2">JLPT N2 (Upper Intermediate & Business)</option>
                <option value="N1">JLPT N1 (Advanced & Keigo)</option>
                <option value="ALL">All Levels / General</option>
              </select>
            </div>

            <div>
              <label htmlFor="edit-age" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Age
              </label>
              <input
                id="edit-age"
                type="number"
                min={18}
                max={100}
                className="input"
                value={age}
                onChange={e => setAge(parseInt(e.target.value, 10) || 25)}
              />
            </div>

            <div>
              <label htmlFor="edit-voice" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                VoiceVox Character Voice
              </label>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <select
                  id="edit-voice"
                  className="select"
                  value={voiceId}
                  onChange={e => setVoiceId(e.target.value)}
                  style={{ flex: 1 }}
                >
                  <option value="">-- Default (Kasukabe Tsumugi) --</option>
                  {availableVoices.map(v => (
                    <option key={v.id} value={v.id}>
                      {v.character_name} - {v.name} ({v.gender === 'female' ? 'Female' : 'Male'})
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleTestVoice}
                  disabled={playingTestAudio}
                  title="Test Voice Sample"
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)',
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '12px',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}
                >
                  <Icon name="voice" size={14} />
                  {playingTestAudio ? 'Playing...' : 'Test Voice'}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="edit-gender" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Gender & Persona Pronoun
              </label>
              <select
                id="edit-gender"
                className="select"
                value={gender}
                onChange={e => setGender(e.target.value)}
              >
                <option value="female">Female Sensei (Watashi)</option>
                <option value="male">Male Sensei (Boku/Watashi)</option>
                <option value="other">Neutral / Other</option>
              </select>
            </div>
          </div>

          {/* Section 2: Personality & Teaching Style */}
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.25rem 0 1rem 0', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            2. Teaching Personality & Catchphrase
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <label htmlFor="edit-personality" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Personality Traits
              </label>
              <input
                id="edit-personality"
                type="text"
                className="input"
                value={personality}
                onChange={e => setPersonality(e.target.value)}
                maxLength={255}
              />
            </div>

            <div>
              <label htmlFor="edit-catchphrase" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Signature Catchphrase / Greeting
              </label>
              <input
                id="edit-catchphrase"
                type="text"
                className="input"
                value={catchphrase}
                onChange={e => setCatchphrase(e.target.value)}
                maxLength={255}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <label htmlFor="edit-teaching" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Teaching Methodology & Furigana
              </label>
              <textarea
                id="edit-teaching"
                className="input"
                rows={2}
                value={teachingStyle}
                onChange={e => setTeachingStyle(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="edit-hobbies" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Hobbies & Topics of Interest
              </label>
              <textarea
                id="edit-hobbies"
                className="input"
                rows={2}
                value={hobbies}
                onChange={e => setHobbies(e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label htmlFor="edit-avatar" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Avatar Image (URL)
            </label>
            <input
              id="edit-avatar"
              type="url"
              className="input"
              value={avatarUrl}
              onChange={e => setAvatarUrl(e.target.value)}
            />
          </div>

          {/* Section 3: AI Persona Core Instructions */}
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.25rem 0 1rem 0', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            3. Core Persona Instructions (AI System Prompt)
          </h4>

          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <label htmlFor="edit-content" style={{ color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600 }}>
                Persona System Prompt Instructions <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <span style={{ fontSize: '0.75rem', color: content.length > 10000 ? 'var(--danger)' : 'var(--text-muted)' }}>
                {content.length.toLocaleString()} / 10,000 chars
              </span>
            </div>
            <textarea
              id="edit-content"
              className="input"
              rows={8}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8125rem',
                lineHeight: 1.6,
                resize: 'vertical',
              }}
              value={content}
              onChange={e => setContent(e.target.value)}
              required
            />
          </div>

          {/* Default Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.5rem' }}>
            <input
              type="checkbox"
              id="edit-default"
              checked={isDefault}
              onChange={e => setIsDefault(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: 'var(--primary)' }}
            />
            <label htmlFor="edit-default" style={{ fontSize: '0.85rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
              Set as default companion Sensei for new conversations
            </label>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? t('common.saving') : t('common.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

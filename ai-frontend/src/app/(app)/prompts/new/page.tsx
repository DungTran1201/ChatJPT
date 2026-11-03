'use client';

import { useApp } from '@/context/AppContext';

import { VoiceService } from '@/services/voiceService';
import { VoiceItem } from '@/types';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { SystemPromptService } from '@/services/systemPromptService';
import PageHeader from '@/components/ui/PageHeader';
import Icon from '@/components/ui/Icon';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import { formatErrorMessage } from '@/lib/errors';

export default function CreateSenseiPage() {
  const { t } = useApp();
  const router = useRouter();

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

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showExitConfirm, setShowExitConfirm] = useState(false);

  useEffect(() => {
    VoiceService.getVoices().then(res => setAvailableVoices(res.items || [])).catch(() => {});
  }, []);


  const isDirty = Boolean(name.trim() || description.trim() || content.trim() || personality.trim());

  const handleCancel = () => {
    if (isDirty) {
      setShowExitConfirm(true);
    } else {
      router.push('/prompts');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setErrorMsg('Please enter a name for the Sensei.');
      return;
    }
    if (trimmedName.length > 100) {
      setErrorMsg('Sensei name cannot exceed 100 characters.');
      return;
    }

    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setErrorMsg('Please enter core persona instructions.');
      return;
    }
    if (content.length > 10000) {
      setErrorMsg('Instructions cannot exceed 10,000 characters.');
      return;
    }

    try {
      setIsSubmitting(true);
      await SystemPromptService.createPrompt({
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
      setErrorMsg(formatErrorMessage(err, 'Error saving Sensei profile.'));
    } finally {
      setIsSubmitting(false);
    }
  };


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
          title="New Sensei Guidance"
          description="Configure a new Japanese Sensei persona with customized level, personality, teaching style, and voice."
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
          {/* Section 1: Basic Human Identity */}
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
            1. Identity & Profile Information
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            {/* Field: Name */}
            <div>
              <label htmlFor="sensei-name" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Sensei Name <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <input
                id="sensei-name"
                type="text"
                className="input"
                placeholder="e.g. Sakura Sensei (桜先生)"
                value={name}
                onChange={e => setName(e.target.value)}
                maxLength={100}
                required
              />
            </div>

            {/* Field: Japanese Level */}
            <div>
              <label htmlFor="sensei-level" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Target JLPT Level <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <select
                id="sensei-level"
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

            {/* Field: Age */}
            <div>
              <label htmlFor="sensei-age" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Age
              </label>
              <input
                id="sensei-age"
                type="number"
                min={18}
                max={100}
                className="input"
                placeholder="25"
                value={age}
                onChange={e => setAge(parseInt(e.target.value, 10) || 25)}
              />
            </div>

            {/* Field: VoiceVox Character Voice */}
            <div>
              <label htmlFor="sensei-voice" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                VoiceVox Character Voice
              </label>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <select
                  id="sensei-voice"
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

            {/* Field: Gender / Pronoun */}
            <div>
              <label htmlFor="sensei-gender" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Gender & Persona Pronoun
              </label>
              <select
                id="sensei-gender"
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
            {/* Field: Personality */}
            <div>
              <label htmlFor="sensei-personality" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Personality Traits
              </label>
              <input
                id="sensei-personality"
                type="text"
                className="input"
                placeholder="e.g. Gentle, patient, encouraging"
                value={personality}
                onChange={e => setPersonality(e.target.value)}
                maxLength={255}
              />
            </div>

            {/* Field: Catchphrase */}
            <div>
              <label htmlFor="sensei-catchphrase" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Signature Catchphrase / Greeting
              </label>
              <input
                id="sensei-catchphrase"
                type="text"
                className="input"
                placeholder="e.g. 「一緒に一歩ずつ勉強しましょうね！」"
                value={catchphrase}
                onChange={e => setCatchphrase(e.target.value)}
                maxLength={255}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            {/* Field: Teaching Style */}
            <div>
              <label htmlFor="sensei-teaching" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Teaching Methodology & Furigana
              </label>
              <textarea
                id="sensei-teaching"
                className="input"
                rows={2}
                placeholder="e.g. Provide Furigana ruby, detailed grammar explanations, polite tone..."
                value={teachingStyle}
                onChange={e => setTeachingStyle(e.target.value)}
              />
            </div>

            {/* Field: Hobbies */}
            <div>
              <label htmlFor="sensei-hobbies" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Hobbies & Topics of Interest
              </label>
              <textarea
                id="sensei-hobbies"
                className="input"
                rows={2}
                placeholder="e.g. Wagashi sweets, tea ceremony, Kyoto travel, slice-of-life anime..."
                value={hobbies}
                onChange={e => setHobbies(e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label htmlFor="sensei-avatar" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Avatar Image (URL)
            </label>
            <input
              id="sensei-avatar"
              type="url"
              className="input"
              placeholder="https://... (Leave empty for automated anime avatar)"
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
              <label htmlFor="sensei-content" style={{ color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600 }}>
                Persona System Prompt Instructions <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <span style={{ fontSize: '0.75rem', color: content.length > 10000 ? 'var(--danger)' : 'var(--text-muted)' }}>
                {content.length.toLocaleString()} / 10,000 chars
              </span>
            </div>
            <textarea
              id="sensei-content"
              className="input"
              rows={8}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8125rem',
                lineHeight: 1.6,
                resize: 'vertical',
              }}
              placeholder={`You are Sakura-sensei, 24 years old, a gentle Japanese teacher specializing in JLPT N5...\n1. Always speak patiently and provide clear bilingual explanations.\n2. Include Furigana [漢字](かんじ) and breakdown key grammatical particles...`}
              value={content}
              onChange={e => setContent(e.target.value)}
              required
            />
          </div>

          {/* Default Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.5rem' }}>
            <input
              type="checkbox"
              id="sensei-default"
              checked={isDefault}
              onChange={e => setIsDefault(e.target.checked)}
              style={{ width: '16px', height: '16px', accentColor: 'var(--primary)' }}
            />
            <label htmlFor="sensei-default" style={{ fontSize: '0.85rem', color: 'var(--text-primary)', cursor: 'pointer' }}>
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

      <ConfirmDialog
        isOpen={showExitConfirm}
        title="Discard unsaved changes?"
        message="You have unsaved changes. Leaving now will discard all modifications."
        confirmLabel="Leave"
        isDestructive
        onConfirm={() => router.push('/prompts')}
        onCancel={() => setShowExitConfirm(false)}
      />
    </div>
  );
}

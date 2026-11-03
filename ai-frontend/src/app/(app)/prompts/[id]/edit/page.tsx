'use client';

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
        setLoadError(formatErrorMessage(err, 'Sensei không tồn tại hoặc bạn không có quyền truy cập.'));
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
      setErrorMsg('Vui lòng nhập tên cho Sensei.');
      return;
    }

    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setErrorMsg('Vui lòng nhập chỉ thị Persona cốt lõi cho AI.');
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
      setErrorMsg(formatErrorMessage(err, 'Lỗi khi cập nhật thông tin Sensei. Vui lòng thử lại.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '4rem 0', textAlign: 'center', color: 'var(--text-muted)' }}>
        Đang tải thông tin Sensei...
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="page-container" style={{ maxWidth: '860px', padding: '2rem 1rem' }}>
        <div className="card" style={{ padding: '2rem', textAlign: 'center', borderColor: 'var(--danger)' }}>
          <p style={{ color: 'var(--danger)', marginBottom: '1rem' }}>{loadError}</p>
          <Link href="/prompts" className="btn btn-secondary">Quay lại danh sách Sensei</Link>
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
          title={`Chỉnh Sửa Sensei: ${name}`}
          description={isSystemPreset ? "Sensei mẫu hệ thống - Khi sửa, hệ thống sẽ lưu thành phiên bản tùy chỉnh cá nhân của bạn." : "Cập nhật phong cách sư phạm, tính cách, cấp độ và chỉ thị Persona cho Sensei."}
        >
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleCancel}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <Icon name="chevronLeft" size={13} />
            <span>Quay lại danh sách Sensei</span>
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
            1. Thông Tin Nhận Diện & Nhân Bản Học
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <label htmlFor="edit-name" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Tên Sensei <span style={{ color: 'var(--danger)' }}>*</span>
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
                Trình Độ Tiếng Nhật Chuyên Trách
              </label>
              <select
                id="edit-level"
                className="select"
                value={japaneseLevel}
                onChange={e => setJapaneseLevel(e.target.value)}
              >
                <option value="N5">JLPT N5 (Sơ cấp cơ bản)</option>
                <option value="N4">JLPT N4 (Sơ cấp nâng cao & Kaiwa)</option>
                <option value="N3">JLPT N3 (Trung cấp & Sắc thái ngữ cảnh)</option>
                <option value="N2">JLPT N2 (Trung thượng cấp & Thương mại)</option>
                <option value="N1">JLPT N1 (Cao cấp & Kính ngữ thượng thừa)</option>
                <option value="ALL">Tổng Hợp Đa Cấp Độ</option>
              </select>
            </div>

            <div>
              <label htmlFor="edit-age" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Tuổi
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
                Giọng Nói VoiceVox Nhân Vật (Character Voice)
              </label>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <select
                  id="edit-voice"
                  className="select"
                  value={voiceId}
                  onChange={e => setVoiceId(e.target.value)}
                  style={{ flex: 1 }}
                >
                  <option value="">-- Mặc định (Kasukabe Tsumugi) --</option>
                  {availableVoices.map(v => (
                    <option key={v.id} value={v.id}>
                      {v.character_name} - {v.name} ({v.gender === 'female' ? 'Nữ' : 'Nam'})
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={handleTestVoice}
                  disabled={playingTestAudio}
                  title="Nghe thử giọng mẫu"
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
                  {playingTestAudio ? 'Đang phát...' : 'Nghe thử'}
                </button>
              </div>
            </div>

            <div>
              <label htmlFor="edit-gender" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Giới Tính & Xưng Hô
              </label>
              <select
                id="edit-gender"
                className="select"
                value={gender}
                onChange={e => setGender(e.target.value)}
              >
                <option value="female">Cô giáo (Nữ - Watashi)</option>
                <option value="male">Thầy giáo (Nam - Boku/Watashi)</option>
                <option value="other">Trung tính / Khác</option>
              </select>
            </div>
          </div>

          {/* Section 2: Personality & Teaching Style */}
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', margin: '1.25rem 0 1rem 0', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            2. Tính Cách Sư Phạm & Đặc Trưng Giao Tiếp
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <label htmlFor="edit-personality" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Nét Tính Cách Đặc Trưng
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
                Câu Nói Cửa Miệng / Lời Chào
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
                Phương Pháp Sư Phạm & Furigana
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
                Sở Thích & Đề Tài Quan Tâm
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
              Ảnh Đại Diện (Avatar URL)
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
            3. Chỉ Thị Persona Cốt Lõi (AI System Prompt)
          </h4>

          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <label htmlFor="edit-content" style={{ color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600 }}>
                Nội Dung Chỉ Dẫn Nhập Vai (System Prompt Instructions) <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <span style={{ fontSize: '0.75rem', color: content.length > 10000 ? 'var(--danger)' : 'var(--text-muted)' }}>
                {content.length.toLocaleString()} / 10,000 ký tự
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
              Đặt làm Sensei mặc định đồng hành trong các cuộc hội thoại mới
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
              Hủy
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Đang cập nhật Sensei...' : 'Lưu Thay Đổi'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

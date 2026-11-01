'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { SystemPromptService } from '@/services/systemPromptService';
import PageHeader from '@/components/ui/PageHeader';
import Icon from '@/components/ui/Icon';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import { formatErrorMessage } from '@/lib/errors';

export default function CreateSenseiPage() {
  const router = useRouter();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [content, setContent] = useState('');
  const [age, setAge] = useState(25);
  const [gender, setGender] = useState('female');
  const [japaneseLevel, setJapaneseLevel] = useState('N5');
  const [personality, setPersonality] = useState('');
  const [teachingStyle, setTeachingStyle] = useState('');
  const [catchphrase, setCatchphrase] = useState('');
  const [hobbies, setHobbies] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [isDefault, setIsDefault] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showExitConfirm, setShowExitConfirm] = useState(false);

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
      setErrorMsg('Vui lòng nhập tên cho Sensei.');
      return;
    }
    if (trimmedName.length > 100) {
      setErrorMsg('Tên Sensei không được vượt quá 100 ký tự.');
      return;
    }

    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setErrorMsg('Vui lòng nhập chỉ thị Persona cốt lõi cho AI.');
      return;
    }
    if (content.length > 10000) {
      setErrorMsg('Nội dung chỉ dẫn không được vượt quá 10.000 ký tự.');
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
        personality: personality.trim() || null,
        teaching_style: teachingStyle.trim() || null,
        catchphrase: catchphrase.trim() || null,
        hobbies: hobbies.trim() || null,
        avatar_url: avatarUrl.trim() || null,
        is_default: isDefault,
      });

      router.push('/prompts');
    } catch (err: any) {
      setErrorMsg(formatErrorMessage(err, 'Lỗi khi lưu thông tin Sensei. Vui lòng thử lại.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="custom-scrollbar" style={{ flex: 1, overflowY: 'auto' }}>
      <div className="page-container" style={{ maxWidth: '860px' }}>
        {/* Page Header */}
        <PageHeader
          title="Thêm Sensei Mới (New Sensei Guidance)"
          description="Thiết lập một trợ lý giáo viên tiếng Nhật mới với các thông tin nhân bản học, tính cách, cấp độ và chỉ thị sư phạm."
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
          {/* Section 1: Basic Human Identity */}
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.5rem' }}>
            1. Thông Tin Nhận Diện & Nhân Bản Học
          </h4>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
            {/* Field: Name */}
            <div>
              <label htmlFor="sensei-name" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Tên Sensei <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <input
                id="sensei-name"
                type="text"
                className="input"
                placeholder="Ví dụ: Sakura-sensei (桜先生)"
                value={name}
                onChange={e => setName(e.target.value)}
                maxLength={100}
                required
              />
            </div>

            {/* Field: Japanese Level */}
            <div>
              <label htmlFor="sensei-level" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Trình Độ Tiếng Nhật Chuyên Trách <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <select
                id="sensei-level"
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

            {/* Field: Age */}
            <div>
              <label htmlFor="sensei-age" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Tuổi
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

            {/* Field: Gender / Pronoun */}
            <div>
              <label htmlFor="sensei-gender" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Giới Tính & Xưng Hô
              </label>
              <select
                id="sensei-gender"
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
            {/* Field: Personality */}
            <div>
              <label htmlFor="sensei-personality" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Nét Tính Cách Đặc Trưng
              </label>
              <input
                id="sensei-personality"
                type="text"
                className="input"
                placeholder="Ví dụ: Dịu dàng, Kiên nhẫn, luôn khích lệ"
                value={personality}
                onChange={e => setPersonality(e.target.value)}
                maxLength={255}
              />
            </div>

            {/* Field: Catchphrase */}
            <div>
              <label htmlFor="sensei-catchphrase" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Câu Nói Cửa Miệng / Lời Chào
              </label>
              <input
                id="sensei-catchphrase"
                type="text"
                className="input"
                placeholder="Ví dụ: 「一緒に一歩ずつ勉強しましょうね！」"
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
                Phương Pháp Sư Phạm & Furigana
              </label>
              <textarea
                id="sensei-teaching"
                className="input"
                rows={2}
                placeholder="Ví dụ: Luôn cung cấp phiên âm Furigana, giải thích song ngữ Nhật - Việt chi tiết..."
                value={teachingStyle}
                onChange={e => setTeachingStyle(e.target.value)}
              />
            </div>

            {/* Field: Hobbies */}
            <div>
              <label htmlFor="sensei-hobbies" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                Sở Thích & Đề Tài Quan Tâm
              </label>
              <textarea
                id="sensei-hobbies"
                className="input"
                rows={2}
                placeholder="Ví dụ: Làm bánh ngọt Wagashi, trà đạo, du lịch Kyoto, anime đời thường..."
                value={hobbies}
                onChange={e => setHobbies(e.target.value)}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label htmlFor="sensei-avatar" style={{ display: 'block', color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600, marginBottom: '0.35rem' }}>
              Ảnh Đại Diện (Avatar URL)
            </label>
            <input
              id="sensei-avatar"
              type="url"
              className="input"
              placeholder="https://... (Để trống để tự động tạo avatar anime)"
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
              <label htmlFor="sensei-content" style={{ color: 'var(--text-primary)', fontSize: '0.8125rem', fontWeight: 600 }}>
                Nội Dung Chỉ Dẫn Nhập Vai (System Prompt Instructions) <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <span style={{ fontSize: '0.75rem', color: content.length > 10000 ? 'var(--danger)' : 'var(--text-muted)' }}>
                {content.length.toLocaleString()} / 10,000 ký tự
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
              placeholder={`Bạn là Sakura-sensei, 24 tuổi, giáo viên tiếng Nhật chuyên cấp độ N5...\n1. Luôn dịu dàng, kiên nhẫn và giải thích song ngữ Nhật - Việt.\n2. Mọi câu tiếng Nhật luôn kèm Furigana và phân tích trợ từ rõ ràng...`}
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
              {isSubmitting ? 'Đang lưu Sensei...' : 'Lưu Sensei Mới'}
            </button>
          </div>
        </form>
      </div>

      <ConfirmDialog
        isOpen={showExitConfirm}
        title="Bỏ các thay đổi chưa lưu?"
        message="Bạn có thông tin Sensei chưa được lưu. Nếu thoát bây giờ, các thay đổi sẽ bị mất."
        confirmLabel="Rời khỏi"
        isDestructive
        onConfirm={() => router.push('/prompts')}
        onCancel={() => setShowExitConfirm(false)}
      />
    </div>
  );
}

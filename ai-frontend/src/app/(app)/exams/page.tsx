'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import {
  ExamItem,
  ExamDetail,
  ExamSubmissionResult,
  ReferenceMaterialItem,
  RagKnowledgeItem,
  ExamLevel,
} from '@/types';
import { ExamService } from '@/services/examService';
import PageHeader from '@/components/ui/PageHeader';
import Icon from '@/components/ui/Icon';
import Toast, { ToastMessage } from '@/components/ui/Toast';

export default function ExamManagementPage() {
  const [activeTab, setActiveTab] = useState<'exams' | 'materials' | 'rag'>('exams');
  
  // Data states
  const [exams, setExams] = useState<ExamItem[]>([]);
  const [materials, setMaterials] = useState<ReferenceMaterialItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters for Exams
  const [selectedLevel, setSelectedLevel] = useState<ExamLevel>('ALL');
  const [examSearch, setExamSearch] = useState('');

  // Filters for Materials
  const [materialCategory, setMaterialCategory] = useState<string>('ALL');
  const [materialLevel, setMaterialLevel] = useState<string>('ALL');
  const [materialSearch, setMaterialSearch] = useState('');

  // RAG Search State
  const [ragQuery, setRagQuery] = useState('');
  const [ragLevel, setRagLevel] = useState<string>('ALL');
  const [ragResults, setRagResults] = useState<RagKnowledgeItem[]>([]);
  const [ragLoading, setRagLoading] = useState(false);

  // Interactive Test Runner Modal
  const [runningExamId, setRunningExamId] = useState<string | null>(null);
  const [activeExamDetail, setActiveExamDetail] = useState<ExamDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [userAnswers, setUserAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [examResult, setExamResult] = useState<ExamSubmissionResult | null>(null);

  // In-App Document Viewer Modal
  const [viewingMaterial, setViewingMaterial] = useState<ReferenceMaterialItem | null>(null);

  // Toast
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const addToast = (type: 'success' | 'error' | 'info', message: string) => {
    setToast({ id: Date.now().toString(), type, message });
  };

  // Fetch Exams
  const fetchExams = useCallback(async () => {
    try {
      setLoading(true);
      const res = await ExamService.getExams({
        level: selectedLevel !== 'ALL' ? selectedLevel : undefined,
        search: examSearch.trim() || undefined,
      });
      setExams(res.items || []);
    } catch (err: any) {
      addToast('error', err.message || 'Không thể tải danh sách đề thi');
    } finally {
      setLoading(false);
    }
  }, [selectedLevel, examSearch]);

  // Fetch Reference Materials
  const fetchMaterials = useCallback(async () => {
    try {
      setLoading(true);
      const res = await ExamService.getReferenceMaterials({
        category: materialCategory !== 'ALL' ? materialCategory : undefined,
        level: materialLevel !== 'ALL' ? materialLevel : undefined,
        search: materialSearch.trim() || undefined,
      });
      setMaterials(res.items || []);
    } catch (err: any) {
      addToast('error', err.message || 'Không thể tải kho tài liệu');
    } finally {
      setLoading(false);
    }
  }, [materialCategory, materialLevel, materialSearch]);

  // Fetch RAG Knowledge
  const fetchRag = useCallback(async (query: string = '', level: string = 'ALL') => {
    try {
      setRagLoading(true);
      const res = await ExamService.searchRag(query, level !== 'ALL' ? level : undefined);
      setRagResults(res.results || []);
    } catch (err: any) {
      addToast('error', err.message || 'Lỗi tra cứu tri thức RAG');
    } finally {
      setRagLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'exams') {
      fetchExams();
    } else if (activeTab === 'materials') {
      fetchMaterials();
    } else if (activeTab === 'rag') {
      fetchRag(ragQuery, ragLevel);
    }
  }, [activeTab, fetchExams, fetchMaterials, fetchRag, ragQuery, ragLevel]);

  // Open Interactive Exam
  const handleStartExam = async (examId: string) => {
    setRunningExamId(examId);
    setExamResult(null);
    setUserAnswers({});
    setLoadingDetail(true);
    try {
      const detail = await ExamService.getExamDetail(examId);
      setActiveExamDetail(detail);
    } catch (err: any) {
      addToast('error', err.message || 'Không thể mở bài thi');
      setRunningExamId(null);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSelectOption = (questionId: string, optionNumber: number) => {
    if (examResult) return;
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: optionNumber,
    }));
  };

  const handleSubmitExam = async () => {
    if (!runningExamId || !activeExamDetail) return;
    
    const answeredCount = Object.keys(userAnswers).length;
    if (answeredCount === 0) {
      addToast('info', 'Vui lòng chọn ít nhất một câu trả lời trước khi nộp bài!');
      return;
    }

    try {
      setSubmitting(true);
      const result = await ExamService.submitExam(runningExamId, userAnswers);
      setExamResult(result);
      if (result.passed) {
        addToast('success', `Chúc mừng! Bạn đã hoàn thành xuất sắc: ${result.score}/${result.max_score} điểm!`);
      } else {
        addToast('info', `Kết quả: ${result.score}/${result.max_score} điểm. Hãy tiếp tục cố gắng nhé!`);
      }
    } catch (err: any) {
      addToast('error', err.message || 'Lỗi khi nộp bài thi');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCloseExamModal = () => {
    setRunningExamId(null);
    setActiveExamDetail(null);
    setExamResult(null);
    setUserAnswers({});
  };

  // Level badge style helper
  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'N5':
        return { bg: 'rgba(62, 207, 142, 0.15)', color: '#3ecf8e', border: 'rgba(62, 207, 142, 0.35)' };
      case 'N4':
        return { bg: 'rgba(45, 212, 191, 0.15)', color: '#2dd4bf', border: 'rgba(45, 212, 191, 0.35)' };
      case 'N3':
        return { bg: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', border: 'rgba(245, 158, 11, 0.35)' };
      case 'N2':
        return { bg: 'rgba(249, 115, 22, 0.15)', color: '#f97316', border: 'rgba(249, 115, 22, 0.35)' };
      case 'N1':
        return { bg: 'rgba(168, 85, 247, 0.15)', color: '#a855f7', border: 'rgba(168, 85, 247, 0.35)' };
      case 'KAIWA':
        return { bg: 'rgba(236, 72, 153, 0.15)', color: '#ec4899', border: 'rgba(236, 72, 153, 0.35)' };
      default:
        return { bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', border: 'rgba(59, 130, 246, 0.35)' };
    }
  };

  return (
    <div
      style={{
        padding: '1.5rem 2rem',
        maxWidth: '1440px',
        margin: '0 auto',
        width: '100%',
        minHeight: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.5rem',
        overflowY: 'auto',
      }}
    >
      {/* Toast Notification */}
      {toast && <Toast toast={toast} onClose={() => setToast(null)} />}

      {/* Header Container */}
      <div
        style={{
          background: 'rgba(28, 28, 31, 0.88)',
          border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
          borderRadius: 'var(--radius-lg, 12px)',
          padding: '1.25rem 1.75rem',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.35)',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--accent, #3ecf8e)',
                background: 'rgba(62, 207, 142, 0.12)',
                padding: '2px 8px',
                borderRadius: '4px',
              }}
            >
              Học Liệu Khảo Thí & RAG
            </span>
          </div>
          <h1
            style={{
              fontSize: '1.45rem',
              fontWeight: 700,
              color: 'var(--text-primary, #eeeef0)',
              marginTop: '4px',
              letterSpacing: '-0.02em',
            }}
          >
            Kho Đề Thi & Giáo Trình Tham Khảo Bản Địa (JLPT & Kaiwa)
          </h1>
          <p
            style={{
              fontSize: '0.85rem',
              color: 'var(--text-secondary, #b4b4b8)',
              marginTop: '4px',
              maxWidth: '850px',
              lineHeight: 1.5,
            }}
          >
            Toàn bộ tài liệu chuẩn từ các cấp độ N5 đến N1 và Kaiwa đã được tải về lưu trữ trực tiếp trên máy chủ. Người học có thể làm bài thi trắc nghiệm trực tiếp, xem hoặc tải sách PDF, và tra cứu tri thức ngữ pháp hỗ trợ RAG tức thì.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            onClick={() => {
              if (activeTab === 'exams') fetchExams();
              else if (activeTab === 'materials') fetchMaterials();
              else fetchRag(ragQuery, ragLevel);
            }}
            className="btn btn-secondary btn-sm"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              height: '36px',
              padding: '0 14px',
            }}
          >
            <Icon name="refresh" size={13} />
            <span>Làm mới</span>
          </button>
          <Link
            href="/chat"
            className="btn btn-primary btn-sm"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              height: '36px',
              padding: '0 16px',
              fontWeight: 600,
            }}
          >
            <Icon name="chat" size={14} />
            <span>Vào Luyện Kaiwa</span>
          </Link>
        </div>
      </div>

      {/* Stat Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
        }}
      >
        <div
          style={{
            background: 'rgba(21, 21, 24, 0.85)',
            border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
            borderRadius: 'var(--radius-md, 8px)',
            padding: '1rem 1.25rem',
            backdropFilter: 'blur(12px)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #89898f)', fontWeight: 600 }}>
            Kho Đề Thi Trực Tuyến
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#3ecf8e', marginTop: '4px' }}>
            6 Bộ Đề Chuẩn
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #b4b4b8)', marginTop: '2px' }}>
            N5, N4, N3, N2, N1 & Kaiwa
          </div>
        </div>

        <div
          style={{
            background: 'rgba(21, 21, 24, 0.85)',
            border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
            borderRadius: 'var(--radius-md, 8px)',
            padding: '1rem 1.25rem',
            backdropFilter: 'blur(12px)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #89898f)', fontWeight: 600 }}>
            Tài Liệu Cục Bộ (Local Storage)
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#2dd4bf', marginTop: '4px' }}>
            90+ Đầu Sách & Đề
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #b4b4b8)', marginTop: '2px' }}>
            ~1.58 GB PDF trên Server
          </div>
        </div>

        <div
          style={{
            background: 'rgba(21, 21, 24, 0.85)',
            border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
            borderRadius: 'var(--radius-md, 8px)',
            padding: '1rem 1.25rem',
            backdropFilter: 'blur(12px)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #89898f)', fontWeight: 600 }}>
            Chấm Điểm & Lời Khuyên
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#f59e0b', marginTop: '4px' }}>
            Tự Động & Tức Thì
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #b4b4b8)', marginTop: '2px' }}>
            Kèm giải thích sư phạm tiếng Việt
          </div>
        </div>

        <div
          style={{
            background: 'rgba(21, 21, 24, 0.85)',
            border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
            borderRadius: 'var(--radius-md, 8px)',
            padding: '1rem 1.25rem',
            backdropFilter: 'blur(12px)',
            boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
          }}
        >
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted, #89898f)', fontWeight: 600 }}>
            Kho Tri Thức RAG
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#a855f7', marginTop: '4px' }}>
            Sẵn Sàng Tra Cứu
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary, #b4b4b8)', marginTop: '2px' }}>
            Hỗ trợ Chatbot truy xuất chính xác
          </div>
        </div>
      </div>

      {/* Main Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
          gap: '8px',
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab('exams')}
          style={{
            padding: '10px 18px',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            color: activeTab === 'exams' ? 'var(--accent, #3ecf8e)' : 'var(--text-secondary)',
            borderBottom: `2px solid ${activeTab === 'exams' ? 'var(--accent, #3ecf8e)' : 'transparent'}`,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'transparent',
            borderTop: 'none',
            borderLeft: 'none',
            borderRight: 'none',
          }}
        >
          <Icon name="exam" size={15} />
          <span>Kho Đề Thi & Làm Bài Trực Tuyến</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('materials')}
          style={{
            padding: '10px 18px',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            color: activeTab === 'materials' ? 'var(--accent, #3ecf8e)' : 'var(--text-secondary)',
            borderBottom: `2px solid ${activeTab === 'materials' ? 'var(--accent, #3ecf8e)' : 'transparent'}`,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'transparent',
            borderTop: 'none',
            borderLeft: 'none',
            borderRight: 'none',
          }}
        >
          <Icon name="doc" size={15} />
          <span>Kho Giáo Trình & Tài Liệu Cục Bộ ({materials.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('rag')}
          style={{
            padding: '10px 18px',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            color: activeTab === 'rag' ? 'var(--accent, #3ecf8e)' : 'var(--text-secondary)',
            borderBottom: `2px solid ${activeTab === 'rag' ? 'var(--accent, #3ecf8e)' : 'transparent'}`,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'transparent',
            borderTop: 'none',
            borderLeft: 'none',
            borderRight: 'none',
          }}
        >
          <Icon name="search" size={15} />
          <span>Trợ Lý Tra Cứu RAG (AI Sensei Knowledge)</span>
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: KHO ĐỀ THI & LÀM BÀI TRỰC TUYẾN */}
      {/* ========================================================================= */}
      {activeTab === 'exams' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Controls Bar */}
          <div
            style={{
              background: 'rgba(21, 21, 24, 0.85)',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
              borderRadius: 'var(--radius-md, 8px)',
              padding: '0.85rem 1.25rem',
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
              backdropFilter: 'blur(12px)',
            }}
          >
            {/* Level Chips */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
              {(['ALL', 'N5', 'N4', 'N3', 'N2', 'N1', 'KAIWA'] as ExamLevel[]).map(lvl => {
                const active = selectedLevel === lvl;
                const bStyle = getLevelBadge(lvl);
                return (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setSelectedLevel(lvl)}
                    style={{
                      padding: '5px 12px',
                      borderRadius: '16px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      background: active ? (lvl === 'ALL' ? 'var(--accent, #3ecf8e)' : bStyle.bg) : 'var(--bg-elevated, #1c1c1f)',
                      color: active ? (lvl === 'ALL' ? '#ffffff' : bStyle.color) : 'var(--text-secondary, #b4b4b8)',
                      border: `1px solid ${active ? (lvl === 'ALL' ? 'var(--accent, #3ecf8e)' : bStyle.border) : 'var(--border-subtle)'}`,
                    }}
                  >
                    {lvl === 'ALL' ? 'Tất cả cấp độ' : lvl === 'KAIWA' ? 'Giao tiếp Kaiwa' : `JLPT ${lvl}`}
                  </button>
                );
              })}
            </div>

            {/* Search Box */}
            <div style={{ minWidth: '280px', position: 'relative' }}>
              <input
                type="text"
                placeholder="Tìm kiếm đề thi..."
                value={examSearch}
                onChange={e => setExamSearch(e.target.value)}
                className="input"
                style={{
                  width: '100%',
                  height: '36px',
                  paddingLeft: '32px',
                  fontSize: '0.8125rem',
                  background: 'var(--bg-surface, #151516)',
                  border: '1px solid var(--border-default)',
                }}
              />
              <span style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }}>
                <Icon name="search" size={14} />
              </span>
            </div>
          </div>

          {/* Exam Cards Grid */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
              <Icon name="refresh" size={24} style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
              <div>Đang tải ngân hàng đề thi...</div>
            </div>
          ) : exams.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '4rem 0',
                background: 'rgba(21, 21, 24, 0.7)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <Icon name="info" size={32} style={{ color: 'var(--text-muted)', marginBottom: '8px' }} />
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                Không tìm thấy đề thi phù hợp với bộ lọc hiện tại.
              </p>
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
                gap: '1.25rem',
              }}
            >
              {exams.map(exam => {
                const bStyle = getLevelBadge(exam.level);
                return (
                  <div
                    key={exam.id}
                    style={{
                      background: 'rgba(28, 28, 31, 0.92)',
                      border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                      borderRadius: 'var(--radius-lg, 12px)',
                      padding: '1.25rem 1.5rem',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      backdropFilter: 'blur(16px)',
                      boxShadow: '0 6px 24px rgba(0, 0, 0, 0.3)',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span
                          style={{
                            padding: '3px 10px',
                            borderRadius: '12px',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            background: bStyle.bg,
                            color: bStyle.color,
                            border: `1px solid ${bStyle.border}`,
                          }}
                        >
                          {exam.level}
                        </span>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            color: 'var(--text-muted)',
                            background: 'var(--bg-surface)',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            border: '1px solid var(--border-subtle)',
                          }}
                        >
                          Đề thi khảo thí chuẩn
                        </span>
                      </div>

                      <h3
                        style={{
                          fontSize: '1rem',
                          fontWeight: 700,
                          color: 'var(--text-primary)',
                          lineHeight: 1.4,
                          marginBottom: '8px',
                        }}
                      >
                        {exam.title}
                      </h3>

                      <p
                        style={{
                          fontSize: '0.8rem',
                          color: 'var(--text-secondary)',
                          lineHeight: 1.5,
                          marginBottom: '14px',
                        }}
                      >
                        {exam.description || 'Đề thi khảo thí năng lực tiếng Nhật tiêu chuẩn.'}
                      </p>

                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        <span style={{ background: 'var(--bg-surface)', padding: '3px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                          ⏱️ {exam.duration_minutes} phút
                        </span>
                        <span style={{ background: 'var(--bg-surface)', padding: '3px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                          📝 {exam.total_questions} câu trắc nghiệm
                        </span>
                        <span style={{ background: 'var(--bg-surface)', padding: '3px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                          🎯 Điểm đỗ: {exam.passing_score}/{exam.max_score}
                        </span>
                      </div>
                    </div>

                    <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <button
                        type="button"
                        onClick={() => handleStartExam(exam.id)}
                        className="btn btn-primary"
                        style={{
                          width: '100%',
                          height: '38px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '8px',
                          fontSize: '0.8125rem',
                          fontWeight: 600,
                        }}
                      >
                        <Icon name="play" size={14} />
                        <span>Làm bài thi trực tiếp trên web</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: KHO GIÁO TRÌNH & TÀI LIỆU CỤC BỘ */}
      {/* ========================================================================= */}
      {activeTab === 'materials' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Controls Bar */}
          <div
            style={{
              background: 'rgba(21, 21, 24, 0.85)',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
              borderRadius: 'var(--radius-md, 8px)',
              padding: '0.85rem 1.25rem',
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
              backdropFilter: 'blur(12px)',
            }}
          >
            {/* Level Chips */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
              {['ALL', 'N5', 'N4', 'N3', 'N2', 'N1', 'KAIWA'].map(lvl => {
                const active = materialLevel === lvl;
                const bStyle = getLevelBadge(lvl);
                return (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setMaterialLevel(lvl)}
                    style={{
                      padding: '5px 12px',
                      borderRadius: '16px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      background: active ? (lvl === 'ALL' ? 'var(--accent, #3ecf8e)' : bStyle.bg) : 'var(--bg-elevated, #1c1c1f)',
                      color: active ? (lvl === 'ALL' ? '#ffffff' : bStyle.color) : 'var(--text-secondary, #b4b4b8)',
                      border: `1px solid ${active ? (lvl === 'ALL' ? 'var(--accent, #3ecf8e)' : bStyle.border) : 'var(--border-subtle)'}`,
                    }}
                  >
                    {lvl === 'ALL' ? 'Tất cả cấp độ' : lvl === 'KAIWA' ? 'Kaiwa' : lvl}
                  </button>
                );
              })}
            </div>

            {/* Search Box */}
            <div style={{ minWidth: '280px', position: 'relative' }}>
              <input
                type="text"
                placeholder="Tìm kiếm tài liệu, sách, giáo trình..."
                value={materialSearch}
                onChange={e => setMaterialSearch(e.target.value)}
                className="input"
                style={{
                  width: '100%',
                  height: '36px',
                  paddingLeft: '32px',
                  fontSize: '0.8125rem',
                  background: 'var(--bg-surface, #151516)',
                  border: '1px solid var(--border-default)',
                }}
              />
              <span style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }}>
                <Icon name="search" size={14} />
              </span>
            </div>
          </div>

          {/* Materials Grid */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
              <Icon name="refresh" size={24} style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
              <div>Đang tải kho tài liệu cục bộ...</div>
            </div>
          ) : materials.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '4rem 0',
                background: 'rgba(21, 21, 24, 0.7)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <Icon name="info" size={32} style={{ color: 'var(--text-muted)', marginBottom: '8px' }} />
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                Không tìm thấy tài liệu phù hợp.
              </p>
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
                gap: '1.25rem',
              }}
            >
              {materials.map(mat => {
                const bStyle = getLevelBadge(mat.level);
                return (
                  <div
                    key={mat.id}
                    style={{
                      background: 'rgba(28, 28, 31, 0.92)',
                      border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                      borderRadius: 'var(--radius-lg, 12px)',
                      padding: '1.25rem 1.5rem',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      backdropFilter: 'blur(16px)',
                      boxShadow: '0 6px 24px rgba(0, 0, 0, 0.3)',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                        <span
                          style={{
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            background: bStyle.bg,
                            color: bStyle.color,
                            border: `1px solid ${bStyle.border}`,
                          }}
                        >
                          {mat.level || 'ALL'}
                        </span>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            color: 'var(--accent, #3ecf8e)',
                            background: 'rgba(62, 207, 142, 0.1)',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            border: '1px solid rgba(62, 207, 142, 0.25)',
                          }}
                        >
                          ✓ Sẵn sàng cục bộ
                        </span>
                      </div>

                      <h3
                        style={{
                          fontSize: '0.95rem',
                          fontWeight: 700,
                          color: 'var(--text-primary)',
                          lineHeight: 1.4,
                          marginBottom: '8px',
                        }}
                      >
                        {mat.title}
                      </h3>

                      <p
                        style={{
                          fontSize: '0.78rem',
                          color: 'var(--text-secondary)',
                          lineHeight: 1.5,
                          marginBottom: '12px',
                        }}
                      >
                        {mat.description}
                      </p>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        <span>📁 Tệp PDF</span>
                        <span>•</span>
                        <span>{mat.size_display || 'Tài liệu'}</span>
                        <span>•</span>
                        <span>{mat.author || 'ChatJPT Server'}</span>
                      </div>
                    </div>

                    <div
                      style={{
                        marginTop: '1.25rem',
                        paddingTop: '1rem',
                        borderTop: '1px solid var(--border-subtle)',
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '8px',
                      }}
                    >
                      <button
                        type="button"
                        onClick={() => setViewingMaterial(mat)}
                        className="btn btn-primary btn-sm"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px',
                          fontSize: '0.78rem',
                          height: '34px',
                        }}
                      >
                        <Icon name="doc" size={13} />
                        <span>Xem trên Web</span>
                      </button>

                      <a
                        href={mat.download_url || mat.external_url}
                        download
                        className="btn btn-secondary btn-sm"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px',
                          fontSize: '0.78rem',
                          height: '34px',
                          textDecoration: 'none',
                        }}
                      >
                        <Icon name="upload" size={13} style={{ transform: 'rotate(180deg)' }} />
                        <span>Tải về máy</span>
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: TRỢ LÝ TRA CỨU RAG */}
      {/* ========================================================================= */}
      {activeTab === 'rag' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Controls Bar */}
          <div
            style={{
              background: 'rgba(21, 21, 24, 0.85)',
              border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
              borderRadius: 'var(--radius-md, 8px)',
              padding: '0.85rem 1.25rem',
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
              backdropFilter: 'blur(12px)',
            }}
          >
            {/* Level Chips */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
              {['ALL', 'N5', 'N4', 'N3', 'N2', 'N1', 'KAIWA'].map(lvl => {
                const active = ragLevel === lvl;
                const bStyle = getLevelBadge(lvl);
                return (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setRagLevel(lvl)}
                    style={{
                      padding: '5px 12px',
                      borderRadius: '16px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      background: active ? (lvl === 'ALL' ? 'var(--accent, #3ecf8e)' : bStyle.bg) : 'var(--bg-elevated, #1c1c1f)',
                      color: active ? (lvl === 'ALL' ? '#ffffff' : bStyle.color) : 'var(--text-secondary, #b4b4b8)',
                      border: `1px solid ${active ? (lvl === 'ALL' ? 'var(--accent, #3ecf8e)' : bStyle.border) : 'var(--border-subtle)'}`,
                    }}
                  >
                    {lvl === 'ALL' ? 'Tất cả cấp độ' : lvl === 'KAIWA' ? 'Kaiwa' : lvl}
                  </button>
                );
              })}
            </div>

            {/* Search Box */}
            <div style={{ minWidth: '320px', position: 'relative' }}>
              <input
                type="text"
                placeholder="Tra cứu điểm ngữ pháp, trợ từ, Hán tự, đệm từ..."
                value={ragQuery}
                onChange={e => setRagQuery(e.target.value)}
                className="input"
                style={{
                  width: '100%',
                  height: '36px',
                  paddingLeft: '32px',
                  fontSize: '0.8125rem',
                  background: 'var(--bg-surface, #151516)',
                  border: '1px solid var(--border-default)',
                }}
              />
              <span style={{ position: 'absolute', left: '10px', top: '10px', color: 'var(--text-muted)' }}>
                <Icon name="search" size={14} />
              </span>
            </div>
          </div>

          {/* RAG Results List */}
          {ragLoading ? (
            <div style={{ textAlign: 'center', padding: '4rem 0', color: 'var(--text-muted)' }}>
              <Icon name="refresh" size={24} style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
              <div>Đang tìm kiếm trong kho tri thức RAG...</div>
            </div>
          ) : ragResults.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '4rem 0',
                background: 'rgba(21, 21, 24, 0.7)',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <Icon name="info" size={32} style={{ color: 'var(--text-muted)', marginBottom: '8px' }} />
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                Không tìm thấy kết quả phù hợp. Hãy thử tìm các từ khóa như &quot;wa&quot;, &quot;te&quot;, &quot;tara&quot;, &quot;wake&quot;, &quot;kính ngữ&quot;...
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {ragResults.map(item => {
                const bStyle = getLevelBadge(item.level);
                return (
                  <div
                    key={item.id}
                    style={{
                      background: 'rgba(28, 28, 31, 0.92)',
                      border: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.08))',
                      borderRadius: 'var(--radius-lg, 12px)',
                      padding: '1.25rem 1.5rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem',
                      backdropFilter: 'blur(16px)',
                      boxShadow: '0 6px 24px rgba(0, 0, 0, 0.3)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span
                          style={{
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            background: bStyle.bg,
                            color: bStyle.color,
                            border: `1px solid ${bStyle.border}`,
                          }}
                        >
                          {item.level}
                        </span>
                        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {item.title}
                        </h3>
                      </div>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        {item.tags.map(t => (
                          <span
                            key={t}
                            style={{
                              fontSize: '0.68rem',
                              color: 'var(--text-muted)',
                              background: 'var(--bg-surface)',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              border: '1px solid var(--border-subtle)',
                            }}
                          >
                            #{t}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div
                      style={{
                        fontSize: '0.82rem',
                        color: 'var(--accent, #3ecf8e)',
                        fontWeight: 600,
                        background: 'rgba(62, 207, 142, 0.08)',
                        padding: '6px 10px',
                        borderRadius: '6px',
                        borderLeft: '3px solid var(--accent, #3ecf8e)',
                      }}
                    >
                      {item.summary}
                    </div>

                    <div
                      style={{
                        fontSize: '0.82rem',
                        color: 'var(--text-secondary)',
                        lineHeight: 1.6,
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      {item.content}
                    </div>

                    {item.examples && item.examples.length > 0 && (
                      <div
                        style={{
                          background: 'rgba(15, 15, 16, 0.6)',
                          border: '1px solid var(--border-subtle)',
                          borderRadius: '8px',
                          padding: '10px 14px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '6px',
                        }}
                      >
                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b' }}>
                          💡 Ví dụ ngữ cảnh:
                        </div>
                        {item.examples.map((ex, idx) => (
                          <div key={idx} style={{ fontSize: '0.8rem', lineHeight: 1.5 }}>
                            <div style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                              • {ex.jp}
                            </div>
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', paddingLeft: '12px' }}>
                              → {ex.vi}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 1: LÀM BÀI THI TRỰC TUYẾN (ONLINE EXAM RUNNER) */}
      {/* ========================================================================= */}
      {runningExamId && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(8px)',
            padding: '1.5rem',
            overflowY: 'auto',
          }}
        >
          <div
            style={{
              position: 'relative',
              width: '100%',
              maxWidth: '820px',
              maxHeight: '90vh',
              background: '#161619',
              border: '1px solid var(--border-default, rgba(255, 255, 255, 0.15))',
              borderRadius: 'var(--radius-lg, 14px)',
              boxShadow: '0 24px 60px rgba(0, 0, 0, 0.65)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Modal Header */}
            <div
              style={{
                padding: '1.25rem 1.5rem',
                borderBottom: '1px solid var(--border-subtle)',
                background: '#1c1c20',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: 'var(--accent, #3ecf8e)',
                    letterSpacing: '0.05em',
                  }}
                >
                  Khảo Thí Trực Tuyến
                </span>
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>
                  {activeExamDetail?.title || 'Đang chuẩn bị đề thi...'}
                </h2>
              </div>
              <button
                type="button"
                onClick={handleCloseExamModal}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '6px',
                  borderRadius: '6px',
                }}
              >
                <Icon name="close" size={18} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {loadingDetail ? (
                <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
                  <Icon name="refresh" size={24} style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
                  <div>Đang tải nội dung câu hỏi bài thi...</div>
                </div>
              ) : !activeExamDetail ? (
                <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--danger, #f07178)' }}>
                  Không tìm thấy nội dung câu hỏi cho đề thi này.
                </div>
              ) : (
                <>
                  {/* Results Banner if submitted */}
                  {examResult && (
                    <div
                      style={{
                        padding: '1.25rem 1.5rem',
                        borderRadius: 'var(--radius-md, 8px)',
                        background: examResult.passed ? 'rgba(62, 207, 142, 0.12)' : 'rgba(245, 158, 11, 0.12)',
                        border: `1px solid ${examResult.passed ? 'rgba(62, 207, 142, 0.35)' : 'rgba(245, 158, 11, 0.35)'}`,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: examResult.passed ? '#3ecf8e' : '#f59e0b' }}>
                          Kết Quả Bài Khảo Thí
                        </span>
                        <span
                          style={{
                            padding: '3px 10px',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            background: examResult.passed ? '#3ecf8e' : '#f59e0b',
                            color: '#ffffff',
                          }}
                        >
                          {examResult.passed ? 'ĐẠT (PASSED)' : 'CHƯA ĐẠT (TRY AGAIN)'}
                        </span>
                      </div>
                      <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#ffffff' }}>
                        {examResult.score} / {examResult.max_score} Điểm
                        <span style={{ fontSize: '0.85rem', fontWeight: 400, color: 'var(--text-secondary)', marginLeft: '8px' }}>
                          (Đúng {examResult.correct_count}/{examResult.total_questions} câu)
                        </span>
                      </div>
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontStyle: 'italic', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '8px' }}>
                        💬 Lời khuyên từ Sensei: {examResult.feedback_message}
                      </div>
                    </div>
                  )}

                  {/* Question Cards */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {activeExamDetail.questions.map(q => {
                      const userAns = userAnswers[q.id];
                      const qRes = examResult?.results.find(r => r.question_id === q.id);

                      return (
                        <div
                          key={q.id}
                          style={{
                            background: qRes
                              ? qRes.is_correct
                                ? 'rgba(62, 207, 142, 0.08)'
                                : 'rgba(240, 113, 120, 0.08)'
                              : '#1c1c20',
                            border: `1px solid ${
                              qRes
                                ? qRes.is_correct
                                  ? 'rgba(62, 207, 142, 0.35)'
                                  : 'rgba(240, 113, 120, 0.35)'
                                : 'var(--border-subtle)'
                            }`,
                            borderRadius: 'var(--radius-md, 8px)',
                            padding: '1.25rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.75rem',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span
                              style={{
                                fontSize: '0.72rem',
                                fontWeight: 700,
                                background: '#25252a',
                                color: 'var(--accent, #3ecf8e)',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                border: '1px solid var(--border-subtle)',
                              }}
                            >
                              Câu {q.question_number} [{q.section}]
                            </span>
                            {qRes && (
                              <span
                                style={{
                                  fontSize: '0.75rem',
                                  fontWeight: 700,
                                  color: qRes.is_correct ? '#3ecf8e' : '#f07178',
                                }}
                              >
                                {qRes.is_correct ? '✓ Đúng' : '✗ Chưa đúng'}
                              </span>
                            )}
                          </div>

                          <div
                            style={{
                              fontSize: '1rem',
                              fontWeight: 600,
                              color: 'var(--text-primary)',
                              lineHeight: 1.6,
                              whiteSpace: 'pre-wrap',
                            }}
                          >
                            {q.question_text}
                          </div>

                          {/* 4 Options Grid */}
                          <div
                            style={{
                              display: 'grid',
                              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                              gap: '8px',
                              marginTop: '4px',
                            }}
                          >
                            {[
                              { num: 1, text: q.option_1 },
                              { num: 2, text: q.option_2 },
                              { num: 3, text: q.option_3 },
                              { num: 4, text: q.option_4 },
                            ].map(opt => {
                              const isSelected = userAns === opt.num;
                              const isAnswerKey = qRes?.correct_answer === opt.num;

                              let btnBg = '#222226';
                              let btnBorder = 'var(--border-subtle)';
                              let btnColor = 'var(--text-primary)';

                              if (qRes) {
                                if (isAnswerKey) {
                                  btnBg = 'rgba(62, 207, 142, 0.25)';
                                  btnBorder = '#3ecf8e';
                                  btnColor = '#3ecf8e';
                                } else if (isSelected && !qRes.is_correct) {
                                  btnBg = 'rgba(240, 113, 120, 0.25)';
                                  btnBorder = '#f07178';
                                  btnColor = '#f07178';
                                }
                              } else if (isSelected) {
                                btnBg = 'rgba(62, 207, 142, 0.2)';
                                btnBorder = 'var(--accent, #3ecf8e)';
                                btnColor = '#3ecf8e';
                              }

                              return (
                                <button
                                  key={opt.num}
                                  type="button"
                                  disabled={!!examResult}
                                  onClick={() => handleSelectOption(q.id, opt.num)}
                                  style={{
                                    padding: '10px 14px',
                                    borderRadius: '6px',
                                    background: btnBg,
                                    border: `1px solid ${btnBorder}`,
                                    color: btnColor,
                                    cursor: examResult ? 'default' : 'pointer',
                                    textAlign: 'left',
                                    fontSize: '0.8125rem',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '10px',
                                    transition: 'all 0.15s ease',
                                  }}
                                >
                                  <span
                                    style={{
                                      width: '20px',
                                      height: '20px',
                                      borderRadius: '50%',
                                      border: `1px solid ${isSelected || isAnswerKey ? btnColor : 'var(--text-muted)'}`,
                                      background: isSelected ? btnColor : 'transparent',
                                      color: isSelected ? '#000000' : 'inherit',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'center',
                                      fontSize: '0.72rem',
                                      fontWeight: 700,
                                      flexShrink: 0,
                                    }}
                                  >
                                    {opt.num}
                                  </span>
                                  <span>{opt.text}</span>
                                </button>
                              );
                            })}
                          </div>

                          {/* Explanation */}
                          {qRes && qRes.explanation && (
                            <div
                              style={{
                                background: 'rgba(21, 21, 24, 0.75)',
                                border: '1px solid var(--border-subtle)',
                                borderRadius: '6px',
                                padding: '10px 12px',
                                fontSize: '0.78rem',
                                color: 'var(--text-secondary)',
                                lineHeight: 1.5,
                                marginTop: '4px',
                              }}
                            >
                              <strong style={{ color: '#f59e0b', display: 'block', marginBottom: '2px' }}>
                                💡 Giải thích từ Sensei:
                              </strong>
                              {qRes.explanation}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div
              style={{
                padding: '1rem 1.5rem',
                borderTop: '1px solid var(--border-subtle)',
                background: '#1c1c20',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {!examResult ? (
                  <span>
                    Đã hoàn thành:{' '}
                    <strong style={{ color: 'var(--accent, #3ecf8e)' }}>
                      {Object.keys(userAnswers).length}
                    </strong>
                    /{activeExamDetail?.questions.length || 0} câu
                  </span>
                ) : (
                  <span>Đã hoàn thành kiểm tra và tự động chấm điểm.</span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <button
                  type="button"
                  onClick={handleCloseExamModal}
                  className="btn btn-secondary btn-sm"
                  style={{ height: '36px', padding: '0 16px' }}
                >
                  Đóng
                </button>

                {!examResult ? (
                  <button
                    type="button"
                    disabled={submitting || loadingDetail}
                    onClick={handleSubmitExam}
                    className="btn btn-primary btn-sm"
                    style={{ height: '36px', padding: '0 20px', fontWeight: 600 }}
                  >
                    {submitting ? 'Đang chấm điểm...' : 'Nộp bài & Chấm điểm'}
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setExamResult(null);
                      setUserAnswers({});
                    }}
                    className="btn btn-primary btn-sm"
                    style={{ height: '36px', padding: '0 20px', fontWeight: 600 }}
                  >
                    Làm lại bài thi
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL 2: XEM TÀI LIỆU TRỰC TIẾP TRÊN WEB (IN-APP DOCUMENT VIEWER) */}
      {/* ========================================================================= */}
      {viewingMaterial && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.88)',
            backdropFilter: 'blur(8px)',
            padding: '1.5rem',
          }}
        >
          <div
            style={{
              position: 'relative',
              width: '100%',
              maxWidth: '1080px',
              height: '90vh',
              background: '#161619',
              border: '1px solid var(--border-default)',
              borderRadius: 'var(--radius-lg, 14px)',
              boxShadow: '0 24px 60px rgba(0, 0, 0, 0.75)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Viewer Header */}
            <div
              style={{
                padding: '1rem 1.5rem',
                borderBottom: '1px solid var(--border-subtle)',
                background: '#1c1c20',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase' }}>
                  {viewingMaterial.level} • {viewingMaterial.category}
                </span>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', marginTop: '2px' }}>
                  {viewingMaterial.title}
                </h3>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <a
                  href={viewingMaterial.download_url || viewingMaterial.external_url}
                  download
                  className="btn btn-secondary btn-sm"
                  style={{ height: '32px', padding: '0 12px', fontSize: '0.78rem', textDecoration: 'none' }}
                >
                  <Icon name="upload" size={13} style={{ transform: 'rotate(180deg)' }} />
                  <span>Tải tệp</span>
                </a>
                <button
                  type="button"
                  onClick={() => setViewingMaterial(null)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    padding: '6px',
                  }}
                >
                  <Icon name="close" size={18} />
                </button>
              </div>
            </div>

            {/* Viewer Frame */}
            <div style={{ flex: 1, background: '#0e0e10', position: 'relative' }}>
              <iframe
                src={viewingMaterial.view_url || viewingMaterial.external_url}
                title={viewingMaterial.title}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Link from 'next/link';
import {
  ExamItem,
  ExamDetail,
  ExamSubmissionResult,
  ReferenceMaterialItem,
  ExamLevel,
} from '@/types';
import { ExamService } from '@/services/examService';
import PageHeader from '@/components/ui/PageHeader';
import Icon from '@/components/ui/Icon';
import Toast, { ToastMessage } from '@/components/ui/Toast';

export default function ExamManagementPage() {
  const [activeTab, setActiveTab] = useState<'exams' | 'materials'>('exams');
  
  // Data states
  const [exams, setExams] = useState<ExamItem[]>([]);
  const [materials, setMaterials] = useState<ReferenceMaterialItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters for Exams
  const [selectedLevel, setSelectedLevel] = useState<ExamLevel>('ALL');
  const [examSearch, setExamSearch] = useState('');

  // Filters for Materials
  const [materialCategory, setMaterialCategory] = useState<string>('ALL');
  const [materialSearch, setMaterialSearch] = useState('');

  // Interactive Test Runner Modal
  const [runningExamId, setRunningExamId] = useState<string | null>(null);
  const [activeExamDetail, setActiveExamDetail] = useState<ExamDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [userAnswers, setUserAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [examResult, setExamResult] = useState<ExamSubmissionResult | null>(null);

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
        search: materialSearch.trim() || undefined,
      });
      setMaterials(res.items || []);
    } catch (err: any) {
      addToast('error', err.message || 'Không thể tải kho tài liệu tham khảo');
    } finally {
      setLoading(false);
    }
  }, [materialCategory, materialSearch]);

  useEffect(() => {
    if (activeTab === 'exams') {
      fetchExams();
    } else {
      fetchMaterials();
    }
  }, [activeTab, fetchExams, fetchMaterials]);

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
    if (examResult) return; // Prevent change after submit
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: optionNumber,
    }));
  };

  const handleSubmitExam = async () => {
    if (!runningExamId || !activeExamDetail) return;
    
    // Check if user answered at least one question
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

  const handleCloseModal = () => {
    setRunningExamId(null);
    setActiveExamDetail(null);
    setExamResult(null);
    setUserAnswers({});
  };

  // Level badge color helper
  const getLevelBadgeClass = (level: string) => {
    switch (level) {
      case 'N5':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'N4':
        return 'bg-teal-500/20 text-teal-400 border-teal-500/30';
      case 'N3':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'N2':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'N1':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'KAIWA':
        return 'bg-pink-500/20 text-pink-400 border-pink-500/30';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  return (
    <div className="min-h-screen bg-[#0e1117] text-gray-100 p-6 md:p-8 space-y-6">
      {/* Toast */}
      {toast && <Toast toast={toast} onClose={() => setToast(null)} />}

      {/* Header */}
      <PageHeader
        title="Kho Đề Thi & Tài Liệu Tham Khảo (JLPT & Kaiwa)"
        description="Ngân hàng đề thi chuẩn khảo thí các cấp độ N5 đến N1, bài kiểm tra tương tác có chấm điểm và Sensei giải thích, cùng toàn bộ tài liệu Google Drive, Cẩm nang Ngữ pháp Tae Kim và Từ điển."
        actions={
          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                if (activeTab === 'exams') fetchExams();
                else fetchMaterials();
              }}
              className="px-3.5 py-1.5 rounded-lg border border-gray-700 hover:border-gray-500 bg-gray-800/80 text-sm font-medium transition-colors flex items-center gap-2"
            >
              <Icon name="refresh" size={14} />
              <span>Làm mới</span>
            </button>
            <Link
              href="/chat"
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors flex items-center gap-2 shadow-sm"
            >
              <Icon name="chat" size={14} />
              <span>Vào Luyện Kaiwa</span>
            </Link>
          </div>
        }
      />

      {/* Stat Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-gray-800 bg-[#161b22]/70 shadow-sm">
          <div className="text-xs text-gray-400 font-medium">Tổng Đề Thi Chuẩn</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">6 Bộ Đề</div>
          <div className="text-xs text-gray-500 mt-0.5">JLPT N5..N1 & Kaiwa</div>
        </div>
        <div className="p-4 rounded-xl border border-gray-800 bg-[#161b22]/70 shadow-sm">
          <div className="text-xs text-gray-400 font-medium">Kho Google Drive</div>
          <div className="text-2xl font-bold text-teal-400 mt-1">6 Thư Mục</div>
          <div className="text-xs text-gray-500 mt-0.5">Đề thi, Sách & File Audio</div>
        </div>
        <div className="p-4 rounded-xl border border-gray-800 bg-[#161b22]/70 shadow-sm">
          <div className="text-xs text-gray-400 font-medium">Cẩm Nang & Từ Điển</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">3 Nguồn Chuẩn</div>
          <div className="text-xs text-gray-500 mt-0.5">Tae Kim, Jisho & Mazii</div>
        </div>
        <div className="p-4 rounded-xl border border-gray-800 bg-[#161b22]/70 shadow-sm">
          <div className="text-xs text-gray-400 font-medium">Chấm Điểm & Giải Thích</div>
          <div className="text-2xl font-bold text-purple-400 mt-1">Tức Thì</div>
          <div className="text-xs text-gray-500 mt-0.5">Sư phạm tiếng Việt chi tiết</div>
        </div>
      </div>

      {/* Main Tabs */}
      <div className="flex border-b border-gray-800">
        <button
          onClick={() => setActiveTab('exams')}
          className={`pb-3 px-5 text-sm font-semibold transition-colors flex items-center gap-2 relative ${
            activeTab === 'exams'
              ? 'text-emerald-400'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <Icon name="exam" size={16} />
          <span>Kho Đề Thi (Exam Bank)</span>
          {activeTab === 'exams' && (
            <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-400 rounded-full" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('materials')}
          className={`pb-3 px-5 text-sm font-semibold transition-colors flex items-center gap-2 relative ${
            activeTab === 'materials'
              ? 'text-emerald-400'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <Icon name="doc" size={16} />
          <span>Kho Tài Liệu Tham Khảo (Reference Materials)</span>
          {activeTab === 'materials' && (
            <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-400 rounded-full" />
          )}
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: KHO ĐỀ THI (EXAM BANK) */}
      {/* ========================================================================= */}
      {activeTab === 'exams' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
            {/* Level Pills */}
            <div className="flex flex-wrap items-center gap-1.5 p-1 bg-[#161b22] border border-gray-800 rounded-lg">
              {(['ALL', 'N5', 'N4', 'N3', 'N2', 'N1', 'KAIWA'] as ExamLevel[]).map(lvl => (
                <button
                  key={lvl}
                  onClick={() => setSelectedLevel(lvl)}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                    selectedLevel === lvl
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60'
                  }`}
                >
                  {lvl === 'ALL' ? 'Tất cả' : lvl}
                </button>
              ))}
            </div>

            {/* Search Box */}
            <div className="relative min-w-[280px]">
              <input
                type="text"
                placeholder="Tìm kiếm đề thi..."
                value={examSearch}
                onChange={e => setExamSearch(e.target.value)}
                className="w-full bg-[#161b22] border border-gray-800 rounded-lg pl-9 pr-3 py-1.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
              <span className="absolute left-3 top-2.5 text-gray-500">
                <Icon name="search" size={14} />
              </span>
            </div>
          </div>

          {/* Exam Grid */}
          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-400 gap-3">
              <Icon name="refresh" className="animate-spin" size={18} />
              <span>Đang tải danh sách đề thi...</span>
            </div>
          ) : exams.length === 0 ? (
            <div className="text-center py-20 bg-[#161b22]/40 rounded-xl border border-gray-800">
              <Icon name="info" size={32} className="mx-auto text-gray-500 mb-2" />
              <p className="text-gray-400 text-sm">Không tìm thấy đề thi phù hợp với bộ lọc hiện tại.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {exams.map(exam => (
                <div
                  key={exam.id}
                  className="rounded-xl border border-gray-800 bg-[#161b22] p-5 flex flex-col justify-between hover:border-gray-700 transition-all hover:shadow-md group"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getLevelBadgeClass(
                          exam.level
                        )}`}
                      >
                        {exam.level}
                      </span>
                      {exam.is_system_preset && (
                        <span className="text-[11px] text-gray-400 bg-gray-800/80 px-2 py-0.5 rounded">
                          Đề thi chuẩn
                        </span>
                      )}
                    </div>

                    <h3 className="font-semibold text-base text-gray-100 group-hover:text-emerald-400 transition-colors leading-snug">
                      {exam.title}
                    </h3>

                    <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">
                      {exam.description || 'Đề thi khảo thí năng lực tiếng Nhật tiêu chuẩn.'}
                    </p>

                    {/* Metadata tags */}
                    <div className="flex flex-wrap gap-2 pt-1 text-[11px] text-gray-400">
                      <span className="bg-gray-800/60 px-2 py-0.5 rounded border border-gray-800 flex items-center gap-1">
                        ⏱️ {exam.duration_minutes} phút
                      </span>
                      <span className="bg-gray-800/60 px-2 py-0.5 rounded border border-gray-800 flex items-center gap-1">
                        📝 {exam.total_questions} câu hỏi
                      </span>
                      <span className="bg-gray-800/60 px-2 py-0.5 rounded border border-gray-800 flex items-center gap-1">
                        🎯 Đỗ: {exam.passing_score}/{exam.max_score} điểm
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="pt-5 mt-4 border-t border-gray-800/80 flex flex-col gap-2">
                    <button
                      onClick={() => handleStartExam(exam.id)}
                      className="w-full py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-2 shadow-sm"
                    >
                      <Icon name="play" size={13} />
                      <span>Làm bài thi trực tuyến</span>
                    </button>

                    {exam.drive_folder_url && (
                      <a
                        href={exam.drive_folder_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full py-2 px-3 rounded-lg bg-[#21262d] hover:bg-gray-700 text-gray-300 hover:text-white text-xs font-medium transition-colors flex items-center justify-center gap-1.5 border border-gray-700"
                      >
                        <Icon name="external" size={13} />
                        <span>Mở Google Drive (Đề gốc & Audio)</span>
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: KHO TÀI LIỆU THAM KHẢO (REFERENCE MATERIALS) */}
      {/* ========================================================================= */}
      {activeTab === 'materials' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
            {/* Category Pills */}
            <div className="flex flex-wrap items-center gap-1.5 p-1 bg-[#161b22] border border-gray-800 rounded-lg">
              {[
                { key: 'ALL', label: 'Tất cả' },
                { key: 'JLPT_N5', label: 'Tài liệu N5' },
                { key: 'JLPT_N4', label: 'Tài liệu N4' },
                { key: 'JLPT_N3', label: 'Tài liệu N3' },
                { key: 'JLPT_N2', label: 'Tài liệu N2' },
                { key: 'JLPT_N1', label: 'Tài liệu N1' },
                { key: 'KAIWA', label: 'Giao tiếp Kaiwa' },
                { key: 'GRAMMAR_GUIDE', label: 'Ngữ pháp Tae Kim' },
                { key: 'VOCABULARY_DICT', label: 'Từ điển' },
              ].map(cat => (
                <button
                  key={cat.key}
                  onClick={() => setMaterialCategory(cat.key)}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                    materialCategory === cat.key
                      ? 'bg-teal-600 text-white shadow-sm'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/60'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Search Box */}
            <div className="relative min-w-[280px]">
              <input
                type="text"
                placeholder="Tìm kiếm tài liệu, giáo trình..."
                value={materialSearch}
                onChange={e => setMaterialSearch(e.target.value)}
                className="w-full bg-[#161b22] border border-gray-800 rounded-lg pl-9 pr-3 py-1.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-teal-500 transition-colors"
              />
              <span className="absolute left-3 top-2.5 text-gray-500">
                <Icon name="search" size={14} />
              </span>
            </div>
          </div>

          {/* Materials Grid */}
          {loading ? (
            <div className="flex items-center justify-center py-20 text-gray-400 gap-3">
              <Icon name="refresh" className="animate-spin" size={18} />
              <span>Đang tải kho tài liệu tham khảo...</span>
            </div>
          ) : materials.length === 0 ? (
            <div className="text-center py-20 bg-[#161b22]/40 rounded-xl border border-gray-800">
              <Icon name="info" size={32} className="mx-auto text-gray-500 mb-2" />
              <p className="text-gray-400 text-sm">Không tìm thấy tài liệu phù hợp.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {materials.map(mat => (
                <div
                  key={mat.id}
                  className="rounded-xl border border-gray-800 bg-[#161b22] p-5 flex flex-col justify-between hover:border-gray-700 transition-all hover:shadow-md group"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-800 text-gray-300 border border-gray-700">
                        {mat.source_type === 'GOOGLE_DRIVE'
                          ? '📁 Google Drive'
                          : mat.source_type === 'WEB_GUIDE'
                          ? '📖 Web Guide'
                          : '📚 Online Dictionary'}
                      </span>
                      {mat.level && mat.level !== 'ALL' && (
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-bold border ${getLevelBadgeClass(
                            mat.level
                          )}`}
                        >
                          {mat.level}
                        </span>
                      )}
                    </div>

                    <h3 className="font-semibold text-base text-gray-100 group-hover:text-teal-400 transition-colors leading-snug">
                      {mat.title}
                    </h3>

                    <p className="text-xs text-gray-400 line-clamp-3 leading-relaxed">
                      {mat.description}
                    </p>

                    {mat.author && (
                      <div className="text-[11px] text-gray-500">
                        Nguồn / Tác giả: <span className="text-gray-400">{mat.author}</span>
                      </div>
                    )}

                    {mat.tags && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {mat.tags.split(',').map((tag, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] bg-gray-800/50 text-gray-400 px-2 py-0.5 rounded"
                          >
                            #{tag.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="pt-5 mt-4 border-t border-gray-800/80">
                    <a
                      href={mat.external_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full py-2 px-3 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-semibold transition-colors flex items-center justify-center gap-1.5 shadow-sm"
                    >
                      <Icon name="external" size={13} />
                      <span>
                        {mat.source_type === 'GOOGLE_DRIVE'
                          ? 'Mở thư mục Google Drive'
                          : mat.source_type === 'WEB_GUIDE'
                          ? 'Mở hướng dẫn ngữ pháp'
                          : 'Truy cập từ điển trực tuyến'}
                      </span>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: INTERACTIVE ONLINE EXAM RUNNER */}
      {/* ========================================================================= */}
      {runningExamId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="relative w-full max-w-3xl bg-[#161b22] border border-gray-800 rounded-2xl shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-5 border-b border-gray-800 flex items-center justify-between bg-[#1f242c]">
              <div>
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                  Bài Kiểm Tra Trực Tuyến
                </span>
                <h2 className="text-lg font-bold text-white mt-0.5">
                  {activeExamDetail?.title || 'Đang tải bài thi...'}
                </h2>
              </div>
              <button
                onClick={handleCloseModal}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-700/60 transition-colors"
              >
                <Icon name="close" size={18} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              {loadingDetail ? (
                <div className="flex items-center justify-center py-20 text-gray-400 gap-3">
                  <Icon name="refresh" className="animate-spin" size={20} />
                  <span>Đang tải danh sách câu hỏi...</span>
                </div>
              ) : !activeExamDetail ? (
                <div className="text-center py-12 text-red-400 text-sm">
                  Không thể tải nội dung bài thi.
                </div>
              ) : (
                <>
                  {/* Result Banner if submitted */}
                  {examResult && (
                    <div
                      className={`p-5 rounded-xl border ${
                        examResult.passed
                          ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
                          : 'bg-amber-950/40 border-amber-500/40 text-amber-200'
                      } space-y-2`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase tracking-wider">
                          Kết quả bài thi
                        </span>
                        <span
                          className={`px-3 py-0.5 rounded-full text-xs font-bold ${
                            examResult.passed
                              ? 'bg-emerald-500 text-white'
                              : 'bg-amber-500 text-white'
                          }`}
                        >
                          {examResult.passed ? 'ĐẠT (PASSED)' : 'CHƯA ĐẠT (TRY AGAIN)'}
                        </span>
                      </div>
                      <div className="text-2xl font-black">
                        {examResult.score} / {examResult.max_score} điểm
                        <span className="text-sm font-normal ml-2 opacity-80">
                          (Đúng {examResult.correct_count}/{examResult.total_questions} câu)
                        </span>
                      </div>
                      <p className="text-xs leading-relaxed italic border-t border-emerald-500/20 pt-2 mt-2">
                        💬 Lời nhắn từ Sensei: {examResult.feedback_message}
                      </p>
                    </div>
                  )}

                  {/* Question List */}
                  <div className="space-y-6">
                    {activeExamDetail.questions.map((q, idx) => {
                      const userAns = userAnswers[q.id];
                      const qRes = examResult?.results.find(r => r.question_id === q.id);

                      return (
                        <div
                          key={q.id}
                          className={`p-5 rounded-xl border transition-all ${
                            qRes
                              ? qRes.is_correct
                                ? 'border-emerald-500/40 bg-emerald-950/10'
                                : 'border-red-500/40 bg-red-950/10'
                              : 'border-gray-800 bg-[#12161c]'
                          }`}
                        >
                          {/* Question Header */}
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-gray-800 text-emerald-400 border border-gray-700">
                              Câu {q.question_number} [{q.section}]
                            </span>
                            {qRes && (
                              <span
                                className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                                  qRes.is_correct
                                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                    : 'bg-red-500/20 text-red-400 border border-red-500/30'
                                }`}
                              >
                                {qRes.is_correct ? '✓ Chính xác' : '✗ Chưa chính xác'}
                              </span>
                            )}
                          </div>

                          {/* Question Text with Furigana */}
                          <div className="text-base font-medium text-gray-100 whitespace-pre-wrap leading-relaxed mb-4">
                            {q.question_text}
                          </div>

                          {/* Options */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                            {[
                              { num: 1, text: q.option_1 },
                              { num: 2, text: q.option_2 },
                              { num: 3, text: q.option_3 },
                              { num: 4, text: q.option_4 },
                            ].map(opt => {
                              const isSelected = userAns === opt.num;
                              const isAnswerKey = qRes?.correct_answer === opt.num;

                              let optClass =
                                'border-gray-800 bg-gray-900/60 hover:bg-gray-800/80 text-gray-300';
                              if (qRes) {
                                if (isAnswerKey) {
                                  optClass = 'border-emerald-500 bg-emerald-950/40 text-emerald-300 font-bold';
                                } else if (isSelected && !qRes.is_correct) {
                                  optClass = 'border-red-500 bg-red-950/40 text-red-300';
                                } else {
                                  optClass = 'border-gray-800/60 opacity-60 text-gray-400';
                                }
                              } else if (isSelected) {
                                optClass = 'border-emerald-500 bg-emerald-950/30 text-emerald-300 font-semibold';
                              }

                              return (
                                <button
                                  key={opt.num}
                                  type="button"
                                  disabled={!!examResult}
                                  onClick={() => handleSelectOption(q.id, opt.num)}
                                  className={`p-3 rounded-lg border text-left text-xs transition-all flex items-center gap-2.5 ${optClass}`}
                                >
                                  <span
                                    className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border ${
                                      isSelected
                                        ? 'bg-emerald-500 text-white border-emerald-500'
                                        : 'border-gray-700 text-gray-400'
                                    }`}
                                  >
                                    {opt.num}
                                  </span>
                                  <span className="flex-1">{opt.text}</span>
                                </button>
                              );
                            })}
                          </div>

                          {/* Pedagogical Explanation */}
                          {qRes && qRes.explanation && (
                            <div className="mt-4 p-3 rounded-lg bg-gray-900/80 border border-gray-800 text-xs text-gray-300 space-y-1">
                              <div className="text-[11px] font-bold text-amber-400 flex items-center gap-1">
                                💡 Giải thích từ Sensei:
                              </div>
                              <p className="leading-relaxed">{qRes.explanation}</p>
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
            <div className="p-4 border-t border-gray-800 flex items-center justify-between bg-[#1f242c]">
              <div className="text-xs text-gray-400">
                {!examResult ? (
                  <span>
                    Đã chọn:{' '}
                    <strong className="text-emerald-400">
                      {Object.keys(userAnswers).length}
                    </strong>
                    /{activeExamDetail?.questions.length || 0} câu
                  </span>
                ) : (
                  <span>Bài thi đã được chấm điểm tự động.</span>
                )}
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-4 py-2 rounded-lg border border-gray-700 hover:bg-gray-800 text-xs font-medium text-gray-300 transition-colors"
                >
                  Đóng
                </button>

                {!examResult ? (
                  <button
                    type="button"
                    disabled={submitting || loadingDetail}
                    onClick={handleSubmitExam}
                    className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold transition-colors flex items-center gap-2 shadow-sm"
                  >
                    {submitting && <Icon name="refresh" className="animate-spin" size={13} />}
                    <span>Nộp bài & Chấm điểm</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => {
                      setExamResult(null);
                      setUserAnswers({});
                    }}
                    className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors flex items-center gap-2 shadow-sm"
                  >
                    <Icon name="refresh" size={13} />
                    <span>Làm lại bài thi</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

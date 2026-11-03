import {
  ExamItem,
  ExamDetail,
  ExamSubmissionResult,
  ReferenceMaterialItem,
  RagSearchResponse,
} from '@/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/v1';

function getAuthHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('ai_chan_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return headers;
}

export class ExamService {
  /**
   * Fetch all exams with optional filtering.
   */
  static async getExams(params?: {
    level?: string;
    category?: string;
    search?: string;
  }): Promise<{ total: number; items: ExamItem[] }> {
    const q = new URLSearchParams();
    if (params?.level && params.level !== 'ALL') q.set('level', params.level);
    if (params?.category && params.category !== 'ALL') q.set('category', params.category);
    if (params?.search) q.set('search', params.search);

    const qs = q.toString() ? `?${q.toString()}` : '';
    const res = await fetch(`${BASE_URL}/exams${qs}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Không thể tải danh sách đề thi');
    }
    return res.json();
  }

  /**
   * Get single exam details with questions for interactive exam taking.
   */
  static async getExamDetail(
    examId: string,
    includeAnswers: boolean = false
  ): Promise<ExamDetail> {
    const qs = includeAnswers ? '?include_answers=true' : '';
    const res = await fetch(`${BASE_URL}/exams/${examId}${qs}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Không thể tải nội dung đề thi');
    }
    return res.json();
  }

  /**
   * Create custom mock exam.
   */
  static async createExam(payload: Partial<ExamItem>): Promise<ExamItem> {
    const res = await fetch(`${BASE_URL}/exams`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Không thể tạo đề thi mới');
    }
    return res.json();
  }

  /**
   * Delete custom mock exam.
   */
  static async deleteExam(examId: string): Promise<void> {
    const res = await fetch(`${BASE_URL}/exams/${examId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Không thể xóa đề thi');
    }
  }

  /**
   * Submit interactive test answers, calculate score & receive Sensei explanations.
   */
  static async submitExam(
    examId: string,
    answers: Record<string, number>
  ): Promise<ExamSubmissionResult> {
    const res = await fetch(`${BASE_URL}/exams/${examId}/submit`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ answers }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Lỗi khi nộp bài thi');
    }
    return res.json();
  }

  /**
   * List reference materials (Google Drive links, Tae Kim grammar guide, Dictionaries).
   */
  static async getReferenceMaterials(params?: {
    category?: string;
    level?: string;
    search?: string;
  }): Promise<{ total: number; items: ReferenceMaterialItem[] }> {
    const q = new URLSearchParams();
    if (params?.category && params.category !== 'ALL') q.set('category', params.category);
    if (params?.level && params.level !== 'ALL') q.set('level', params.level);
    if (params?.search) q.set('search', params.search);

    const qs = q.toString() ? `?${q.toString()}` : '';
    const res = await fetch(`${BASE_URL}/exams/materials${qs}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Không thể tải kho tài liệu');
    }
    return res.json();
  }

  /**
   * Search RAG pedagogical knowledge base.
   */
  static async searchRag(query: string, level?: string): Promise<RagSearchResponse> {
    const q = new URLSearchParams();
    if (query) q.set('query', query);
    if (level && level !== 'ALL') q.set('level', level);
    const qs = q.toString() ? `?${q.toString()}` : '';
    const res = await fetch(`${BASE_URL}/exams/rag/search${qs}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Không thể tra cứu tri thức');
    }
    return res.json();
  }

  /**
   * Add new reference material link.
   */
  static async createReferenceMaterial(
    payload: Partial<ReferenceMaterialItem>
  ): Promise<ReferenceMaterialItem> {
    const res = await fetch(`${BASE_URL}/exams/materials`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Không thể tạo liên kết tài liệu mới');
    }
    return res.json();
  }
}


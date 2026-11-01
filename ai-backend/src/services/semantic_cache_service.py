import re
import uuid
import unicodedata
from typing import Optional, Dict, Any, List
from src.db import query_one, query_all, execute_commit

class SemanticCacheService:
    """Service providing semantic similarity caching and offline AI Sensei responses."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes unicode (NFKC), lowercases, strips special characters for robust matching."""
        if not text:
            return ""
        # 1. Unicode NFKC normalization (handles Japanese full-width/half-width characters)
        normalized = unicodedata.normalize("NFKC", text)
        # 2. Lowercase
        normalized = normalized.lower().strip()
        # 3. Remove punctuation except essential Japanese particles/kanji
        cleaned = re.sub(r'[!?,.:;~`"\(\)\[\]\{\}\<\>\\/\-_*+=#@$%^&|]', ' ', normalized)
        # 4. Collapse extra whitespaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    @classmethod
    def get_tokens(cls, text: str) -> set:
        """Extracts individual tokens and bi-grams for semantic n-gram matching."""
        words = cls.normalize_text(text).split()
        tokens = set(words)
        # Add character bi-grams for Japanese text without whitespace
        raw_norm = cls.normalize_text(text).replace(" ", "")
        for i in range(len(raw_norm) - 1):
            tokens.add(raw_norm[i:i+2])
        return tokens

    @classmethod
    def compute_similarity(cls, query_norm: str, cached_norm: str, keywords_str: Optional[str] = None) -> float:
        """Calculates semantic similarity score based on Jaccard token overlap and keyword bonuses."""
        if query_norm == cached_norm:
            return 1.0

        q_tokens = cls.get_tokens(query_norm)
        c_tokens = cls.get_tokens(cached_norm)

        if not q_tokens or not c_tokens:
            return 0.0

        intersection = q_tokens.intersection(c_tokens)
        union = q_tokens.union(c_tokens)
        jaccard = len(intersection) / len(union) if union else 0.0

        # Keyword bonus
        keyword_bonus = 0.0
        if keywords_str:
            kw_list = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
            if kw_list:
                matched_kws = sum(1 for kw in kw_list if kw in query_norm)
                keyword_bonus = 0.35 * (matched_kws / len(kw_list))

        # Length ratio penalty to prevent tiny queries from matching long essays
        len_ratio = min(len(query_norm), len(cached_norm)) / max(len(query_norm), len(cached_norm))
        
        final_score = (jaccard * 0.7 + keyword_bonus) * (0.6 + 0.4 * len_ratio)
        return min(round(final_score, 3), 1.0)

    @classmethod
    def lookup(cls, prompt: str, threshold: float = 0.48) -> Optional[Dict[str, Any]]:
        """Searches semantic cache for similar Q&A pair above threshold."""
        query_norm = cls.normalize_text(prompt)
        if not query_norm:
            return None

        # Fetch all cache entries
        entries = query_all(
            "SELECT id, prompt_raw, prompt_normalized, category, response_text, keywords, hit_count FROM semantic_cache"
        )
        if not entries:
            return None

        best_match = None
        best_score = 0.0

        for entry in entries:
            score = cls.compute_similarity(query_norm, entry["prompt_normalized"], entry.get("keywords"))
            if score > best_score:
                best_score = score
                best_match = entry

        if best_match and best_score >= threshold:
            # Increment hit_count
            execute_commit(
                "UPDATE semantic_cache SET hit_count = hit_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (best_match["id"],)
            )
            return {
                "id": best_match["id"],
                "prompt_raw": best_match["prompt_raw"],
                "response_text": best_match["response_text"],
                "category": best_match["category"],
                "similarity": best_score,
                "hit_count": best_match["hit_count"] + 1,
                "cached": True
            }

        return None

    @classmethod
    def store(cls, prompt_raw: str, response_text: str, category: str = "general", keywords: str = "") -> str:
        """Stores a new Q&A pair in semantic cache."""
        c_id = str(uuid.uuid4())
        prompt_norm = cls.normalize_text(prompt_raw)
        execute_commit(
            """
            INSERT INTO semantic_cache (id, prompt_raw, prompt_normalized, category, response_text, keywords, similarity_score, hit_count)
            VALUES (?, ?, ?, ?, ?, ?, 1.0, 1)
            """,
            (c_id, prompt_raw, prompt_norm, category, response_text, keywords)
        )
        return c_id

    @classmethod
    def synthesize_offline_response(cls, prompt: str) -> str:
        """Synthesizes structured pedagogical Japanese explanation when offline or no API key is available."""
        p_low = prompt.lower()

        if any(w in p_low for w in ["chào", "hello", "hi", "konnichiwa", "ohayou"]):
            resp = (
                "Konnichiwa! (こんにちは!)\n\n"
                "Tôi là **AI-Chan Sensei (Chế độ Ngoại Tuyến / Offline Semantic Engine)**.\n\n"
                "Hệ thống hiện đang phản hồi ngoại tuyến tốc độ cao thông qua **Bộ Nhớ Đệm Ngữ Nghĩa (Semantic Cache)**.\n"
                "Tôi có thể hỗ trợ bạn:\n"
                "- Tra cứu và giải thích ngữ pháp tiếng Nhật JLPT (N5 - N1).\n"
                "- Hướng dẫn cách phân biệt trợ từ và cách đặt câu hội thoại hàng ngày.\n"
                "- Cung cấp từ vựng, Kanji, Furigana và mẫu câu giao tiếp cơ bản.\n\n"
                "Bạn muốn đặt câu hỏi hoặc luyện tập chủ đề gì hôm nay?"
            )
        elif "wa" in p_low and "ga" in p_low:
            resp = (
                "**Giải đáp trợ từ tiếng Nhật: は (wa) vs が (ga)**\n\n"
                "1. **は (wa) - Nhấn mạnh VỊ NGỮ / Đưa ra ĐỀ TÀI (Topic)**:\n"
                "   - Đứng sau danh từ để nói: *'Về vấn đề X này thì...'*.\n"
                "   - Trọng tâm câu nằm ở phần thông tin sau `は`.\n"
                "   - Ví dụ: 私は学生です (Watashi wa gakusei desu - Tôi là học sinh).\n\n"
                "2. **が (ga) - Nhấn mạnh CHỦ THỂ / Thông tin MỚI (Subject)**:\n"
                "   - Trọng tâm câu nằm ở chính đối tượng đứng trước `が`.\n"
                "   - Dùng cho mệnh đề phụ, miêu tả hiện tượng tự nhiên hoặc sau từ để hỏi (誰, 何).\n"
                "   - Ví dụ: 雨が降っています (Ame ga futte imasu - Trời đang mưa)."
            )
        elif any(w in p_low for w in ["ngữ pháp", "grammar", "jlpt", "mẫu câu"]):
            resp = (
                f"**Phân tích ngữ pháp tiếng Nhật cho câu hỏi của bạn: *\"{prompt}\"***\n\n"
                "1. **Quy tắc cơ bản**: Tiếng Nhật có cấu trúc câu SOV (Chủ ngữ + Bổ ngữ + Động từ vị ngữ ở cuối câu).\n"
                "2. **Sử dụng trợ từ**: Các trợ từ xác định chức năng ngữ pháp của danh từ:\n"
                "   - を (o): Chỉ đối tượng trực tiếp của hành động.\n"
                "   - に (ni): Chỉ thời gian xác định, điểm đến, hoặc đối tượng tiếp nhận.\n"
                "   - で (de): Chỉ địa điểm diễn ra hành động, phương tiện, hoặc cách thức.\n\n"
                "3. **Ví dụ thực hành**:\n"
                "   - 図書館で本を読みます (Toshokan de hon o yomimasu - Đọc sách tại thư viện)."
            )
        elif any(w in p_low for w in ["kaiwa", "hội thoại", "giao tiếp", "ăn", "nhà hàng"]):
            resp = (
                "**Mẫu câu hội thoại Kaiwa thông dụng:**\n\n"
                "1. **Kêu gọi phục vụ / Xin lỗi**: すみません！ (Sumimasen!)\n"
                "2. **Yêu cầu gọi món / nhờ vả**: 〜をお願いします (〜 o onegaishimasu) hoặc 〜をください (〜 o kudasai).\n"
                "3. **Hỏi giá tiền**: これはいくらですか？ (Kore wa ikura desu ka? - Cái này bao nhiêu tiền?)\n"
                "4. **Lời cảm ơn**: どうもありがとうございます (Doumo arigatou gozaimasu)."
            )
        else:
            resp = (
                f"**AI-Chan Sensei (Phản hồi từ Bộ Nhớ Đệm Ngữ Nghĩa Ngoại Tuyến)**\n\n"
                f"Sensei đã ghi nhận câu hỏi của bạn: *\"{prompt}\"*.\n\n"
                "- **Trạng thái**: Hệ thống đang vận hành ở chế độ ngoại tuyến độc lập không tiêu tốn GPU/CPU hay khóa API bên ngoài.\n"
                "- **Lời khuyên học tập**: Để đạt hiệu quả cao nhất trong tiếng Nhật, hãy kết hợp học từ vựng cùng Kanji và luyện tập đặt câu hoàn chỉnh hàng ngày.\n\n"
                "Nếu bạn muốn cấu hình thêm các mô hình đám mây tốc độ cao (Google Gemini, Groq LPU, OpenAI, Anthropic), hãy mở mục **Cài Đặt Hệ Thống -> Khóa API**."
            )

        # Store dynamically synthesized high-quality answer into semantic cache
        try:
            cls.store(prompt, resp, category="synthesized_offline", keywords="offline, sensei, ngu phap, kaiwa")
        except Exception:
            pass

        return resp

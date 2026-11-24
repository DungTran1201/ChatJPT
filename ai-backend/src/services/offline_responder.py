"""Offline Japanese Sensei Response Synthesizer (SRP).

Separates canned/domain pedagogical responses from SemanticCacheService storage logic.
Returns `(response_text, should_cache)` so generic fallback disclaimers never poison
the semantic cache while matched topic lessons can be cached safely.
"""

from typing import Tuple


class OfflineSenseiResponder:
    """Produces structured Japanese pedagogical explanations without cloud LLM keys."""

    @staticmethod
    def synthesize(prompt: str) -> Tuple[str, bool]:
        p_low = (prompt or "").lower()

        if any(w in p_low for w in ("chào", "hello", "hi", "konnichiwa", "ohayou")):
            return (
                "Konnichiwa! (こんにちは!)\n\n"
                "Tôi là **AI-Chan Sensei (Chế độ Ngoại Tuyến / Offline Semantic Engine)**.\n\n"
                "Hệ thống hiện đang phản hồi ngoại tuyến tốc độ cao thông qua **Bộ Nhớ Đệm Ngữ Nghĩa (Semantic Cache 10,000+ kiến thức tiếng Nhật)**.\n"
                "Tôi có thể hỗ trợ bạn:\n"
                "- Tra cứu và giải thích ngữ pháp tiếng Nhật JLPT (N5 - N1).\n"
                "- Hướng dẫn cách phân biệt trợ từ và cách đặt câu hội thoại hàng ngày.\n"
                "- Cung cấp từ vựng, Kanji, Furigana và mẫu câu giao tiếp cơ bản.\n\n"
                "Bạn muốn đặt câu hỏi hoặc luyện tập chủ đề gì hôm nay?",
                True,
            )

        if "wa" in p_low and "ga" in p_low:
            return (
                "**Giải đáp trợ từ tiếng Nhật: は (wa) vs が (ga)**\n\n"
                "1. **は (wa) - Nhấn mạnh VỊ NGỮ / Đưa ra ĐỀ TÀI (Topic)**:\n"
                "   - Đứng sau danh từ để nói: *'Về vấn đề X này thì...'*.\n"
                "   - Trọng tâm câu nằm ở phần thông tin sau `は`.\n"
                "   - Ví dụ: 私は学生です (Watashi wa gakusei desu - Tôi là học sinh).\n\n"
                "2. **が (ga) - Nhấn mạnh CHỦ THỂ / Thông tin MỚI (Subject)**:\n"
                "   - Trọng tâm câu nằm ở chính đối tượng đứng trước `が`.\n"
                "   - Dùng cho mệnh đề phụ, miêu tả hiện tượng tự nhiên hoặc sau từ để hỏi (誰, 何).\n"
                "   - Ví dụ: 雨が降っています (Ame ga futte imasu - Trời đang mưa).",
                True,
            )

        if any(w in p_low for w in ("ngữ pháp", "grammar", "jlpt", "mẫu câu")):
            return (
                f"**Phân tích ngữ pháp tiếng Nhật cho câu hỏi của bạn: *\"{prompt}\"***\n\n"
                "1. **Quy tắc cơ bản**: Tiếng Nhật có cấu trúc câu SOV (Chủ ngữ + Bổ ngữ + Động từ vị ngữ ở cuối câu).\n"
                "2. **Sử dụng trợ từ**: Các trợ từ xác định chức năng ngữ pháp của danh từ:\n"
                "   - を (o): Chỉ đối tượng trực tiếp của hành động.\n"
                "   - に (ni): Chỉ thời gian xác định, điểm đến, hoặc đối tượng tiếp nhận.\n"
                "   - で (de): Chỉ địa điểm diễn ra hành động, phương tiện, hoặc cách thức.\n\n"
                "3. **Ví dụ thực hành**:\n"
                "   - 図書館で本を読みます (Toshokan de hon o yomimasu - Đọc sách tại thư viện).",
                True,
            )

        if any(w in p_low for w in ("kaiwa", "hội thoại", "giao tiếp", "ăn", "nhà hàng")):
            return (
                "**Mẫu câu hội thoại Kaiwa thông dụng:**\n\n"
                "1. **Kêu gọi phục vụ / Xin lỗi**: すみません！ (Sumimasen!)\n"
                "2. **Yêu cầu gọi món / nhờ vả**: 〜をお願いします (〜 o onegaishimasu) hoặc 〜をください (〜 o kudasai).\n"
                "3. **Hỏi giá tiền**: これはいくらですか？ (Kore wa ikura desu ka? - Cái này bao nhiêu tiền?)\n"
                "4. **Lời cảm ơn**: どうもありがとうございます (Doumo arigatou gozaimasu).",
                True,
            )

        # Generic fallback disclaimer -> should_cache=False to prevent cache poisoning
        return (
            f"**AI-Chan Sensei (Phản hồi từ Bộ Nhớ Đệm Ngữ Nghĩa Ngoại Tuyến)**\n\n"
            f"Sensei đã ghi nhận câu hỏi của bạn: *\"{prompt}\"*.\n\n"
            "- **Trạng thái**: Hệ thống đang vận hành ở chế độ ngoại tuyến độc lập không tiêu tốn GPU/CPU hay khóa API bên ngoài.\n"
            "- **Lời khuyên học tập**: Để đạt hiệu quả cao nhất trong tiếng Nhật, hãy kết hợp học từ vựng cùng Kanji và luyện tập đặt câu hoàn chỉnh hàng ngày.\n\n"
            "Nếu bạn muốn cấu hình thêm các mô hình đám mây tốc độ cao (Google Gemini, Groq LPU, OpenAI, Anthropic), hãy mở mục **Cài Đặt Hệ Thống -> Khóa API**.",
            False,
        )

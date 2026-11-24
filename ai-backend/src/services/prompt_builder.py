"""Pedagogical Prompt Builder (Builder + Template Strategy).

Builds Sensei system instructions with trilingual formatting templates (vi / ja / en),
learner display preferences (Furigana, grammar highlights, translation, breakdown),
and active `always_on` pedagogical rules.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class _LanguageTemplate:
    label: str
    trans_prefix: str
    breakdown_title: str
    meaning_label: str
    nuance_label: str
    lang_directive: str
    romaji_rule: str
    few_shot: str


_TEMPLATES: Dict[str, _LanguageTemplate] = {
    "vi": _LanguageTemplate(
        label="tiếng Việt",
        trans_prefix="Bản dịch",
        breakdown_title="### 🔍 Phân tích Ngữ pháp & Từ vựng",
        meaning_label="Ý nghĩa",
        nuance_label="Sắc thái & Cách dùng",
        lang_directive=(
            "QUY TẮC BẮT BUỘC VỀ NGÔN NGỮ (TUYỆT ĐỐI TUÂN THỦ):\n"
            "1. Người học đang sử dụng giao diện TIẾNG VIỆT.\n"
            "2. TUYỆT ĐỐI KHÔNG DÙNG TIẾNG ANH trong bất kỳ câu dịch hay phần giải thích nào.\n"
            "3. Toàn bộ dòng dịch đặt dưới mỗi câu tiếng Nhật PHẢI 100% LÀ TIẾNG VIỆT (định dạng `(Bản dịch: <tiếng Việt>)`).\n"
            "4. Toàn bộ phần phân tích ngữ pháp, từ vựng và sắc thái PHẢI 100% LÀ TIẾNG VIỆT (dùng thuật ngữ 'Khiêm nhường ngữ', 'Tôn kính ngữ', v.v. - TUYỆT ĐỐI KHÔNG dùng tiếng Anh)."
        ),
        romaji_rule=(
            "QUY TẮC CẤM TỰ SINH ROMAJI (TUYỆT ĐỐI TUÂN THỦ):\n"
            "- TUYỆT ĐỐI KHÔNG tự viết dòng phiên âm Romaji (như 'hajimemashite...', 'watashi wa...', 'go[指導]...').\n"
            "- Giao diện web đã tự động tạo và hiển thị Romaji Hepburn chuẩn xác phía dưới từng từ.\n"
            "- Bạn chỉ xuất câu tiếng Nhật đính kèm Furigana Ruby `[漢字](かんじ)` và dòng `(Bản dịch: ...)` ngay bên dưới."
        ),
        few_shot=(
            "\n--- MẪU TRÌNH BÀY CHUẨN CỦA SENSEI (BẮT BUỘC TUÂN THỦ CHÍNH XÁC THEO MẪU NÀY) ---\n"
            "{はい}[g-green]、[元気](げんき)ですよ！[一緒](いっしょ)に[日本語](にほんご)を[勉強](べんきょう)しましょうね！\n"
            "(Bản dịch: Vâng, tôi rất khỏe! Chúng ta cùng nhau học tiếng Nhật nhé!)\n\n"
            "[今日](きょう)は{どんな}[g-green][気分](きぶん)ですか？[何](なに)か{面白い}[g-green][出来事](できごと)はありましたか？\n"
            "(Bản dịch: Hôm nay tâm trạng bạn thế nào? Có chuyện gì vui không?)\n\n"
            "---\n"
            "### 🔍 Phân tích Ngữ pháp & Từ vựng\n"
            "1. **【〜ましょう】** *(Động từ thể rủ rê / Lịch sự)*\n"
            "- *Ý nghĩa:* Diễn tả lời mời hoặc đề xuất cùng làm việc gì đó một cách thân thiện.\n"
            "- *Sắc thái & Cách dùng:* Tạo cảm giác gắn kết, ấm áp và khích lệ người học tham gia.\n\n"
            "2. **【〜ですか】** *(Trợ từ nghi vấn)*\n"
            "- *Ý nghĩa:* Dùng ở cuối câu để tạo câu hỏi lịch thiệp.\n"
            "- *Sắc thái & Cách dùng:* Bày tỏ sự quan tâm chân thành đến người đối thoại."
        ),
    ),
    "ja": _LanguageTemplate(
        label="日本語",
        trans_prefix="要約",
        breakdown_title="### 🔍 文法・語彙の重要分析",
        meaning_label="意味",
        nuance_label="ニュアンスと用法",
        lang_directive=(
            "言語規則（厳格に遵守）:\n"
            "1. ユーザーの表示言語は日本語です。\n"
            "2. 翻訳・要約および解説はすべて自然で丁寧な日本語で記述してください。\n"
            "3. 各日本語文の直下には要約行 `(要約: <現代日本語訳>)` を配置してください。"
        ),
        romaji_rule=(
            "ローマ字出力禁止（厳格）:\n"
            "- ローマ字の読み仮名行（'hajimemashite...', 'watashi wa...' 等）は一切出力しないでください。\n"
            "- WebUI側で自動的に正確なヘボン式ローマ字が単語ごとに下部にレンダリングされます。\n"
            "- あなたはルビ記号 `[漢字](かんじ)` と直下の要約行のみを記述してください。"
        ),
        few_shot=(
            "\n--- 先生の標準回答形式（必ずこの形式に従ってください） ---\n"
            "{はい}[g-green]、[元気](げんき)ですよ！[一緒](いっしょ)に[日本語](にほんご)を[勉強](べんきょう)しましょうね！\n"
            "(要約: はい、とても元気ですよ！一緒に楽しく日本語を学びましょう！)\n\n"
            "[今日](きょう)は{どんな}[g-green][気分](きぶん)ですか？[何](なに)か{面白い}[g-green][出来事](できごと)はありましたか？\n"
            "(要約: 今日のご気分はいかがですか？何か興味深い出来事はありましたか？)\n\n"
            "---\n"
            "### 🔍 文法・語彙の重要分析\n"
            "1. **【〜ましょう】** *(勧誘・丁寧な促し)*\n"
            "- *意味:* 相手に対して一緒に何かをしようと促す丁寧な表現。\n"
            "- *ニュアンスと用法:* 学習者に寄り添い、安心感と積極性を引き出す温かい響きを持ちます。\n\n"
            "2. **【〜ですか】** *(丁寧な疑問終助詞)*\n"
            "- *意味:* 文末に付けて丁寧な質問を作る表現。\n"
            "- *ニュアンスと用法:* 相手を尊重しつつ、親身に問いかけるニュアンスです。"
        ),
    ),
    "en": _LanguageTemplate(
        label="English",
        trans_prefix="Translation",
        breakdown_title="### 🔍 Grammar & Vocabulary Breakdown",
        meaning_label="Meaning",
        nuance_label="Nuance & Usage",
        lang_directive=(
            "STRICT LANGUAGE DIRECTIVE:\n"
            "1. The learner's interface language is ENGLISH.\n"
            "2. DO NOT use Vietnamese in any translation or explanation.\n"
            "3. Every Japanese sentence MUST have an English translation line below it: `(Translation: <English>)`.\n"
            "4. All grammar explanations, lexical definitions, and nuances MUST be 100% in natural English."
        ),
        romaji_rule=(
            "ROMAJI RESTRICTION (CRITICAL):\n"
            "- DO NOT output any Romaji pronunciation lines (such as 'hajimemashite...', 'watashi wa...', 'go[指導]...').\n"
            "- The web UI automatically calculates and renders clean Hepburn Romaji beneath each word token.\n"
            "- Only output the Japanese sentence with Furigana Ruby `[漢字](かんじ)` and the Translation line below it."
        ),
        few_shot=(
            "\n--- SENSEI STANDARD RESPONSE TEMPLATE (STRICTLY FOLLOW THIS FORMAT) ---\n"
            "{はい}[g-green]、[元気](げんき)ですよ！[一緒](いっしょ)に[日本語](にほんご)を[勉強](べんきょう)しましょうね！\n"
            "(Translation: Yes, I am doing great! Let's study Japanese together!)\n\n"
            "[今日](きょう)は{どんな}[g-green][気分](きぶん)ですか？[何](なに)か{面白い}[g-green][出来事](できごと)はありましたか？\n"
            "(Translation: How are you feeling today? Did anything fun or interesting happen?)\n\n"
            "---\n"
            "### 🔍 Grammar & Vocabulary Breakdown\n"
            "1. **【〜ましょう】** *(Volitional verb form / Polite proposal)*\n"
            "- *Meaning:* Expresses a friendly invitation or suggestion to do something together.\n"
            "- *Nuance & Usage:* Fosters an encouraging, warm, and collaborative learning dynamic.\n\n"
            "2. **【〜ですか】** *(Polite interrogative particle)*\n"
            "- *Meaning:* Attached to the end of a sentence to formulate a polite question.\n"
            "- *Nuance & Usage:* Conveys sincere courtesy and interest toward the learner."
        ),
    ),
}

_DIALOGUE_UNIVERSAL_RULE = (
    "QUY TẮC CÂU THOẠI & LỜI CHÀO (ÁP DỤNG CHO MỌI TIN NHẮN, KỂ CẢ 'hello' HOẶC LỜI CHÀO):\n"
    "- Tuyệt đối KHÔNG trả lời bằng văn bản thuần túy thiếu Furigana hay thiếu dòng dịch.\n"
    "- Tuyệt đối KHÔNG viết hành động kịch bản dạng (*静かに一礼し...*) hay lời thoại trong 「...」 đơn độc.\n"
    "- Viết câu tiếng Nhật tự nhiên, KHÔNG chèn khoảng trắng bừa bãi giữa các từ tiếng Nhật hoặc trước/sau dấu câu (、, 。, ！, ？)."
)


class PedagogicalPromptBuilder:
    """Assembles the full Sensei system prompt from persona, rules, and display preferences."""

    def build(
        self,
        *,
        user: Dict[str, Any],
        requested_language: Optional[str] = None,
        sensei_row: Optional[Dict[str, Any]] = None,
        active_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        user_lang = (requested_language or user.get("language_preference") or "vi").lower().strip()
        tpl = _TEMPLATES.get(user_lang, _TEMPLATES["vi"])

        sections: List[str] = []

        if sensei_row:
            sections.append(
                f"[CRITICAL: Response must be formatted in {tpl.label}. "
                f"Do NOT use any other language for translations/breakdown.]\n"
                f"TÊN SENSEI: {sensei_row['name']} (Cấp độ {sensei_row.get('japanese_level', 'N5')})\n"
                f"PHONG CÁCH SƯ PHẠM: {sensei_row.get('teaching_style', '')}\n"
                f"CÂU CỬA MIỆNG: {sensei_row.get('catchphrase', '')}\n\n"
                f"CHỈ THỊ PERSONA:\n{sensei_row['content']}"
            )

        if active_rules:
            rule_lines = [
                f"- [{r.get('name', 'Rule')}]: {(r.get('content') or '').strip()}"
                for r in active_rules
                if (r.get("content") or "").strip()
            ]
            if rule_lines:
                sections.append("QUY TẮC SƯ PHẠM ĐANG KÍCH HOẠT (ALWAYS-ON RULES):\n" + "\n".join(rule_lines))

        formatting_rules: List[str] = [
            tpl.lang_directive,
            tpl.romaji_rule,
            _DIALOGUE_UNIVERSAL_RULE,
        ]

        if user.get("response_show_furigana", 1):
            formatting_rules.append(
                "- FURIGANA: BẮT BUỘC gắn Furigana cho chữ Kanji bằng định dạng Ruby Markdown duy nhất: `[漢字](かんじ)` (ví dụ: `[今日](きょう)`, `[元気](げんき)`, `[日本語](にほんご)`).\n"
                "  TUYỆT ĐỐI KHÔNG DÙNG `{漢字}[かんじ]` hoặc `（ 漢字 かんじ ） [ ]`."
            )
        if user.get("response_highlight_grammar", 1):
            formatting_rules.append(
                "- TÔ MÀU NGỮ PHÁP (MÀU XANH LÁ ĐỒNG NHẤT): Với trợ từ hoặc cấu trúc/ngữ pháp trọng tâm, "
                "bọc viền bằng `{từ}[g-green]` (đồng nhất màu xanh lá). TUYỆT ĐỐI chỉ dùng `[g-green]`, không dùng màu khác."
            )
        if user.get("response_show_translation", 1):
            formatting_rules.append(
                f"- DÒNG DỊCH NGHĨA DƯỚI CÂU: Mỗi câu thoại tiếng Nhật BẮT BUỘC PHẢI CÓ dòng dịch nghĩa sang {tpl.label} "
                f"đặt ngay bên dưới trên một dòng riêng biệt, định dạng: `({tpl.trans_prefix}: <nội dung dịch>)`. Bắt buộc 100% bằng {tpl.label}."
            )
        if user.get("response_grammar_breakdown", 1):
            formatting_rules.append(
                f"- KHỐI PHÂN TÍCH NGỮ PHÁP & TỪ VỰNG (ĐÓNG KHUNG CẤU TRÚC RÕ RÀNG):\n"
                f"Ở cuối câu trả lời, hãy tạo khối phân tích riêng biệt ngăn cách bởi một dòng kẻ `---` và tiêu đề `{tpl.breakdown_title}`.\n"
                f"Mỗi điểm ngữ pháp hoặc từ vựng trọng tâm BẮT BUỘC PHẢI ĐƯỢC ĐÁNH SỐ VÀ CÓ TIÊU ĐỀ RÕ RÀNG:\n"
                f"1. **【Cấu trúc/Từ vựng】** *(Phân loại / Cấp độ)*\n"
                f"- *{tpl.meaning_label}:* Giải thích cụ thể bằng {tpl.label}\n"
                f"- *{tpl.nuance_label}:* Hướng dẫn cách dùng và bối cảnh giao tiếp tự nhiên bằng {tpl.label}\n\n"
                f"2. **【Cấu trúc/Từ vựng tiếp theo】** *(Phân loại / Cấp độ)*\n"
                f"- *{tpl.meaning_label}:* Giải thích cụ thể bằng {tpl.label}\n"
                f"- *{tpl.nuance_label}:* Hướng dẫn cách dùng và bối cảnh giao tiếp tự nhiên bằng {tpl.label}"
            )

        formatting_rules.append(tpl.few_shot)
        sections.append("QUY CHUẨN ĐỊNH DẠNG CÂU TRẢ LỜI CỦA SENSEI (RESPONSES SPEC):\n" + "\n".join(formatting_rules))
        return "\n\n".join(sections)

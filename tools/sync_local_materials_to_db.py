import sqlite3
import re
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "ai-backend" / "data"
MATERIALS_DIR = DATA_DIR / "reference_materials"

DB_PATHS = [
    BASE_DIR / "ai-backend" / "database" / "app.db",
    BASE_DIR / "ai-backend" / "app.db"
]

def clean_title(stem: str) -> str:
    t = stem.replace('_', ' ')
    for prefix in ['[Tailieutiengnhat.net]', '[Tiengnhatcoban.net]', 'Tailieuhoctiengnhat.com']:
        t = t.replace(prefix, '')
    t = re.sub(r'\s+', ' ', t).strip(' -')
    return t

def sync_to_db():
    manifest_file = DATA_DIR / "download_manifest.json"
    if not manifest_file.exists():
        print("Manifest not found")
        return

    with open(manifest_file, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    for db_path in DB_PATHS:
        if not db_path.exists():
            continue
        print(f"\nSyncing local materials into database: {db_path.name}")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Update reference_materials table schema if needed
        # Insert all downloaded local materials
        inserted = 0
        for lvl, items in manifest.items():
            lvl_code = lvl.upper()
            cat = f"JLPT_{lvl_code}" if lvl_code in ['N5', 'N4', 'N3', 'N2', 'N1'] else "KAIWA"
            for item in items:
                if not item.get("success"):
                    continue
                size = item.get("size_bytes", 0)
                if size < 3000:
                    continue # Skip small warning/error files

                safe_name = item.get("safe_name", "")
                stem = Path(safe_name).stem
                title = clean_title(stem)
                mat_id = f"loc_{lvl.lower()}_{re.sub(r'[^a-zA-Z0-9]', '_', stem)[:28].strip('_').lower()}"
                
                size_mb = f"{size / (1024*1024):.1f} MB" if size >= 1024*1024 else f"{size / 1024:.0f} KB"
                desc = f"Tài liệu {lvl_code} cục bộ trên máy chủ ({size_mb}). Tệp gốc chuẩn bị sẵn sàng cho người học tải về, đọc trực tuyến và trích xuất RAG."
                view_url = f"/api/v1/exams/materials/view/{mat_id}"
                
                is_pinned = 1 if any(k in title.lower() for k in ['de thi', 'đề thi', 'ngu phap', 'ngữ pháp', 'kanji', 'tu vung', 'từ vựng', 'kaiwa', 'shinkanzen', 'irodori', 'mimikara']) else 0

                cursor.execute("""
                    INSERT OR REPLACE INTO reference_materials (
                        id, title, description, category, level, source_type,
                        external_url, author, file_type, tags, is_pinned, is_system_preset, user_id
                    ) VALUES (?, ?, ?, ?, ?, 'LOCAL_FILE', ?, 'ChatJPT Server Storage', 'pdf', ?, ?, 1, 'system')
                """, (
                    mat_id, title, desc, cat, lvl_code, view_url, f"{lvl_code}, PDF, Bản địa, RAG", is_pinned
                ))
                inserted += 1

        # Also add Tae Kim's Grammar Guide and Dictionaries
        cursor.execute("""
            INSERT OR REPLACE INTO reference_materials (
                id, title, description, category, level, source_type,
                external_url, author, file_type, tags, is_pinned, is_system_preset, user_id
            ) VALUES (
                'mat_taekim_local',
                'Tae Kim Japanese Grammar Guide (Cẩm Nang Ngữ Pháp Toàn Diện)',
                'Toàn bộ kiến thức ngữ pháp từ căn bản đến nâng cao được phân tách thành dữ liệu số hóa RAG cho AI Sensei và người học tra cứu tức thì.',
                'GRAMMAR_GUIDE', 'ALL', 'WEB_GUIDE',
                'https://guidetojapanese.org/learn/', 'Tae Kim', 'document',
                'Ngữ pháp, Cốt lõi, RAG, Trực quan, Tae Kim', 1, 1, 'system'
            )
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO reference_materials (
                id, title, description, category, level, source_type,
                external_url, author, file_type, tags, is_pinned, is_system_preset, user_id
            ) VALUES (
                'mat_jisho_local',
                'Từ Điển Hán Tự & Từ Vựng Tiếng Nhật Jisho',
                'Tra cứu bộ thủ, nét viết Kanji, tra từ vựng JLPT N5 đến N1 kèm ví dụ đàm thoại thực tế.',
                'VOCABULARY_DICT', 'ALL', 'ONLINE_DICT',
                'https://jisho.org/', 'Jisho Team', 'website',
                'Từ điển, Kanji, Từ vựng, Tra cứu', 1, 1, 'system'
            )
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO reference_materials (
                id, title, description, category, level, source_type,
                external_url, author, file_type, tags, is_pinned, is_system_preset, user_id
            ) VALUES (
                'mat_mazii_local',
                'Từ Điển Tiếng Nhật Thông Minh Mazii (Việt - Nhật)',
                'Tra cứu ngữ pháp, Hán tự và cấu trúc câu dịch song ngữ Việt - Nhật chuyên sâu.',
                'VOCABULARY_DICT', 'ALL', 'ONLINE_DICT',
                'https://mazii.net/', 'Mazii Team', 'website',
                'Từ điển, Tiếng Việt, Ngữ pháp, Song ngữ', 1, 1, 'system'
            )
        """)

        # Add rich interactive questions for exams
        ADDITIONAL_QUESTIONS = [
            # N5 Questions
            {
                "id": "q_n5_07", "exam_id": "exam_seed_n5_full", "section": "GOI", "question_number": 7,
                "question_text": "えきまで ____ で いきますか。",
                "furigana_text": "えきまで ____ で いきますか。",
                "option_1": "なに", "option_2": "なん", "option_3": "だれ", "option_4": "どこ",
                "correct_option": 2,
                "explanation": "Đi đến nhà ga bằng phương tiện gì: なんで (nan de) là cách nói hỏi phương tiện di chuyển."
            },
            {
                "id": "q_n5_08", "exam_id": "exam_seed_n5_full", "section": "BUNPOU", "question_number": 8,
                "question_text": "きのうは あまり ____。",
                "furigana_text": "きのうは あまり ____。",
                "option_1": "さむいです", "option_2": "さむくなかったです", "option_3": "さむかったです", "option_4": "さむくないです",
                "correct_option": 2,
                "explanation": "Phó từ あまり đi với thể phủ định, kết hợp với thời điểm quá khứ きのう (hôm qua) -> さむくなかったです (không lạnh lắm)."
            },
            # N4 Questions
            {
                "id": "q_n4_03", "exam_id": "exam_seed_n4_full", "section": "BUNPOU", "question_number": 3,
                "question_text": "日本語を 話す ____ が できます。",
                "furigana_text": "にほんごを はなす ____ が できます。",
                "option_1": "こと", "option_2": "もの", "option_3": "ところ", "option_4": "わけ",
                "correct_option": 1,
                "explanation": "Cấu trúc danh từ hóa động từ thể từ điển: V-ru + ことができます biểu thị khả năng 'có thể làm gì'."
            },
            {
                "id": "q_n4_04", "exam_id": "exam_seed_n4_full", "section": "BUNPOU", "question_number": 4,
                "question_text": "試験に 合格する ____、いっしょうけんめい 勉強しています。",
                "furigana_text": "しけんに ごうかくする ____、いっしょうけんめい べんきょうしています。",
                "option_1": "ように", "option_2": "ために", "option_3": "とおりに", "option_4": "あとで",
                "correct_option": 1,
                "explanation": "V-khả năng / V-tự động từ (合格する trạng thái đỗ) + ように biểu thị mục tiêu 'để có thể đỗ kỳ thi'."
            },
            # N3 Questions
            {
                "id": "q_n3_01", "exam_id": "exam_seed_n3_full", "section": "BUNPOU", "question_number": 1,
                "question_text": "彼は 日本に 5年も 住んでいたのだから、日本の 習慣を よく 知っている ____ だ。",
                "furigana_text": "かれは にほんに 5ねんも すんでいたのだから、にほんの しゅうかんを よく しっている ____ だ。",
                "option_1": "わけ", "option_2": "はず", "option_3": "つもり", "option_4": "こと",
                "correct_option": 1,
                "explanation": "〜わけだ diễn tả một kết luận hợp lý mang tính nhân quả: 'Vì sống ở Nhật 5 năm nên hèn chi am hiểu phong tục là điều tất nhiên'."
            },
            {
                "id": "q_n3_02", "exam_id": "exam_seed_n3_full", "section": "DOKKAI", "question_number": 2,
                "question_text": "忙しい ____、健康管理を おろそかに しては ならない。",
                "furigana_text": "いそがしい ____、けんこうかんりを おろそかに しては ならない。",
                "option_1": "からといって", "option_2": "からには", "option_3": "ばかりに", "option_4": "につれて",
                "correct_option": 1,
                "explanation": "Aからといって Bてはならない: 'Không phải cứ vì lý do bận rộn mà được phép lơ là việc giữ gìn sức khỏe'."
            },
            # N2 Questions
            {
                "id": "q_n2_01", "exam_id": "exam_seed_n2_full", "section": "BUNPOU", "question_number": 1,
                "question_text": "新製品の 発売 ____、記者会見が 行われた。",
                "furigana_text": "しんせいひんの はつばい ____、きしゃかいけんが おこなわれた。",
                "option_1": "に際して", "option_2": "につれて", "option_3": "に基づいて", "option_4": "に沿って",
                "correct_option": 1,
                "explanation": "N + に際して biểu thị nhân dịp bước vào sự kiện trọng đại: 'Nhân dịp mở bán sản phẩm mới, buổi họp báo đã được tiến hành'."
            },
            {
                "id": "q_n2_02", "exam_id": "exam_seed_n2_full", "section": "BUNPOU", "question_number": 2,
                "question_text": "彼の 実力から すれば、今回の 合格は 当然の 結果と 言わざるを ____。",
                "furigana_text": "かれの じつりょくから すれば、こんかいの ごうかくは とうぜんの けっかと いわざるを ____。",
                "option_1": "得ない", "option_2": "かねない", "option_3": "ほかならない", "option_4": "すぎない",
                "correct_option": 1,
                "explanation": "V-nai (bỏ nai) + ざるを得ない: 'Đành phải / buộc phải công nhận rằng đó là kết quả tất nhiên'."
            },
            # N1 Questions
            {
                "id": "q_n1_01", "exam_id": "exam_seed_n1_full", "section": "BUNPOU", "question_number": 1,
                "question_text": "長年の ご支援に 対し、心より 感謝に ____ 次第でございます。",
                "furigana_text": "ながねんの ごしえんに たいし、こころより かんしゃに ____ しだいでございます。",
                "option_1": "たえない", "option_2": "やまない", "option_3": "きわまりない", "option_4": "あたらない",
                "correct_option": 1,
                "explanation": "Cụm thành ngữ trang trọng N1: 感謝にたえない (Kansha ni taenai) mang ý nghĩa 'vô cùng biết ơn khôn xiết'."
            },
            # Kaiwa Questions
            {
                "id": "q_kw_03", "exam_id": "exam_seed_kaiwa_practical", "section": "KAIWA", "question_number": 3,
                "question_text": "お客様:「この書類を 田中部長に 届けていただけますか。」\nあなた:「____。」",
                "furigana_text": "おきゃくさま:「このしょるいを たなかぶちょうに とどけていただけますか。」\nあなた:「____。」",
                "option_1": "かしこまりました。ただいまお届けいたします。",
                "option_2": "了解しました。持って行きます。",
                "option_3": "分かりました。あとで行きます。",
                "option_4": "どういたしまして。",
                "correct_option": 1,
                "explanation": "Khi khách hàng giao phó việc, câu trả lời chuẩn mực lịch sự của nhân viên là: 'かしこまりました。ただいまお届けいたします' (Dạ tôi đã rõ, tôi xin phép chuyển ngay bây giờ ạ). Tránh dùng 了解しました với khách hàng."
            }
        ]

        for q in ADDITIONAL_QUESTIONS:
            cursor.execute("""
                INSERT OR REPLACE INTO exam_questions (
                    id, exam_id, section, question_number, question_text, furigana_text,
                    option_1, option_2, option_3, option_4, correct_option, explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                q["id"], q["exam_id"], q["section"], q["question_number"],
                q["question_text"], q["furigana_text"], q["option_1"], q["option_2"],
                q["option_3"], q["option_4"], q["correct_option"], q["explanation"]
            ))

        # Update total questions count in exams table
        for ex_id in ['exam_seed_n5_full', 'exam_seed_n4_full', 'exam_seed_n3_full', 'exam_seed_n2_full', 'exam_seed_n1_full', 'exam_seed_kaiwa_practical']:
            cnt = cursor.execute("SELECT COUNT(*) FROM exam_questions WHERE exam_id = ?", (ex_id,)).fetchone()[0]
            cursor.execute("UPDATE exams SET total_questions = ? WHERE id = ?", (cnt, ex_id))

        conn.commit()
        total_mats = cursor.execute("SELECT COUNT(*) FROM reference_materials").fetchone()[0]
        total_qs = cursor.execute("SELECT COUNT(*) FROM exam_questions").fetchone()[0]
        print(f"Done {db_path.name}: {total_mats} reference materials ({inserted} local), {total_qs} questions.")
        conn.close()

if __name__ == '__main__':
    sync_to_db()


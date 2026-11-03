import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATHS = [
    BASE_DIR / "database" / "app.db",
    BASE_DIR / "app.db"
]

DDL = """
CREATE TABLE IF NOT EXISTS exams (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    level VARCHAR(20) NOT NULL CHECK (level IN ('N5', 'N4', 'N3', 'N2', 'N1', 'KAIWA', 'GENERAL')),
    category VARCHAR(50) DEFAULT 'JLPT_FULL',
    year INTEGER,
    duration_minutes INTEGER DEFAULT 60,
    total_questions INTEGER DEFAULT 0,
    passing_score INTEGER DEFAULT 90,
    max_score INTEGER DEFAULT 180,
    drive_folder_url VARCHAR(1000),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DRAFT', 'ARCHIVED')),
    is_system_preset BOOLEAN DEFAULT 1,
    user_id VARCHAR(36) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_exams_level ON exams(level);
CREATE INDEX IF NOT EXISTS idx_exams_category ON exams(category);
CREATE INDEX IF NOT EXISTS idx_exams_status ON exams(status);

CREATE TABLE IF NOT EXISTS exam_questions (
    id VARCHAR(50) PRIMARY KEY,
    exam_id VARCHAR(50) NOT NULL,
    section VARCHAR(50) NOT NULL,
    question_number INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    furigana_text TEXT,
    option_1 TEXT NOT NULL,
    option_2 TEXT NOT NULL,
    option_3 TEXT NOT NULL,
    option_4 TEXT NOT NULL,
    correct_option INTEGER NOT NULL CHECK (correct_option BETWEEN 1 AND 4),
    explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_exam_questions_exam_id ON exam_questions(exam_id);
CREATE INDEX IF NOT EXISTS idx_exam_questions_section ON exam_questions(section);

CREATE TABLE IF NOT EXISTS reference_materials (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL CHECK (category IN ('JLPT_N5', 'JLPT_N4', 'JLPT_N3', 'JLPT_N2', 'JLPT_N1', 'KAIWA', 'GRAMMAR_GUIDE', 'VOCABULARY_DICT')),
    level VARCHAR(20) DEFAULT 'ALL',
    source_type VARCHAR(50) DEFAULT 'GOOGLE_DRIVE',
    external_url VARCHAR(1000) NOT NULL,
    author VARCHAR(100),
    file_type VARCHAR(20) DEFAULT 'folder',
    tags VARCHAR(255),
    is_pinned BOOLEAN DEFAULT 0,
    is_system_preset BOOLEAN DEFAULT 1,
    user_id VARCHAR(36) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ref_mat_category ON reference_materials(category);
CREATE INDEX IF NOT EXISTS idx_ref_mat_level ON reference_materials(level);
CREATE INDEX IF NOT EXISTS idx_ref_mat_pinned ON reference_materials(is_pinned);
"""

REFERENCE_MATERIALS = [
    {
        "id": "mat_n5_drive",
        "title": "Kho Đề Thi & Giáo Trình JLPT N5 (Google Drive)",
        "description": "Toàn bộ tài liệu luyện thi, đề thi mẫu, đề chính thức qua các năm kèm file nghe Audio mp3 cho trình độ Sơ cấp N5.",
        "category": "JLPT_N5",
        "level": "N5",
        "source_type": "GOOGLE_DRIVE",
        "external_url": "https://drive.google.com/drive/folders/14cvGKUh4Gu7ojd2JE6FzWL5hCTSFwhaz?usp=sharing",
        "author": "Cộng đồng tiếng Nhật & Sensei",
        "file_type": "folder",
        "tags": "N5, Đề thi, Giáo trình, Audio, Từ vựng, Ngữ pháp",
        "is_pinned": 1
    },
    {
        "id": "mat_n4_drive",
        "title": "Kho Đề Thi & Giáo Trình JLPT N4 (Google Drive)",
        "description": "Tập hợp tài liệu luyện thi JLPT N4: Sách Try, Soumatome, Shinkanzen Masuta, đề thi mẫu và file nghe chất lượng cao.",
        "category": "JLPT_N4",
        "level": "N4",
        "source_type": "GOOGLE_DRIVE",
        "external_url": "https://drive.google.com/drive/folders/1HytgiK1tJaSGW4wUmHYQRbniPYu3-NLh?usp=sharing",
        "author": "Cộng đồng tiếng Nhật & Sensei",
        "file_type": "folder",
        "tags": "N4, Sách luyện thi, Try N4, Shinkanzen, Đọc hiểu",
        "is_pinned": 1
    },
    {
        "id": "mat_n3_drive",
        "title": "Kho Đề Thi & Tài Liệu JLPT N3 (Google Drive)",
        "description": "Bộ tài liệu Trung cấp JLPT N3: Đề thi khảo thí thật các năm, tài liệu Ngữ pháp chuyên đề, Đọc hiểu và bài tập tổng hợp.",
        "category": "JLPT_N3",
        "level": "N3",
        "source_type": "GOOGLE_DRIVE",
        "external_url": "https://drive.google.com/drive/folders/1lwUZCcGfAl2HwhrQVz-R4s-dXMEKpuZD?usp=sharing",
        "author": "Cộng đồng tiếng Nhật & Sensei",
        "file_type": "folder",
        "tags": "N3, Trung cấp, Đề thi thật, Đọc hiểu dài, Kanji N3",
        "is_pinned": 1
    },
    {
        "id": "mat_n2_drive",
        "title": "Kho Đề Thi & Giáo Trình JLPT N2 (Google Drive)",
        "description": "Kho tài liệu Thượng cấp JLPT N2: Chuyên sâu ngữ pháp thương mại, văn phong công sở, phân tích đọc hiểu văn bản tin tức báo chí.",
        "category": "JLPT_N2",
        "level": "N2",
        "source_type": "GOOGLE_DRIVE",
        "external_url": "https://drive.google.com/drive/folders/1lCVccq1e-dCWKR8CzZX7EbmRkuLPah7F?usp=sharing",
        "author": "Cộng đồng tiếng Nhật & Sensei",
        "file_type": "folder",
        "tags": "N2, Thượng cấp, Thương mại, Văn phong báo chí, Đề thi chuẩn",
        "is_pinned": 1
    },
    {
        "id": "mat_n1_drive",
        "title": "Kho Đề Thi & Chuyên Đề JLPT N1 (Google Drive)",
        "description": "Kho tài liệu Đỉnh cao JLPT N1: Đề thi khảo thí cấp cao nhất, thành ngữ 4 chữ Yojijukugo, kính ngữ cổ điển và đọc hiểu luận điểm phức tạp.",
        "category": "JLPT_N1",
        "level": "N1",
        "source_type": "GOOGLE_DRIVE",
        "external_url": "https://drive.google.com/drive/folders/1451604QICFd_zpWxYXLz5jJj6z2Xh4RI?usp=sharing",
        "author": "Cộng đồng tiếng Nhật & Sensei",
        "file_type": "folder",
        "tags": "N1, Chuyên sâu, Kính ngữ, Đọc hiểu nghị luận, Yojijukugo",
        "is_pinned": 1
    },
    {
        "id": "mat_kaiwa_drive",
        "title": "Kho Tài Liệu Luyện Giao Tiếp Kaiwa Thực Chiến (Google Drive)",
        "description": "Tổng hợp giáo trình Shadowing, hội thoại đời sống, phản xạ giao tiếp tự nhiên và các mẫu câu Kaiwa công sở thực tế.",
        "category": "KAIWA",
        "level": "ALL",
        "source_type": "GOOGLE_DRIVE",
        "external_url": "https://drive.google.com/drive/folders/17JFLZlqVgwxJFS0BkHAv1I_szVJz-aQB?usp=sharing",
        "author": "Cộng đồng tiếng Nhật & Sensei",
        "file_type": "folder",
        "tags": "Kaiwa, Shadowing, Phản xạ, Đời sống, Phỏng vấn xin việc",
        "is_pinned": 1
    },
    {
        "id": "mat_taekim_grammar",
        "title": "Tae Kim's Guide to Japanese Grammar",
        "description": "Cẩm nang hướng dẫn ngữ pháp tiếng Nhật toàn diện, giải thích trực quan từ tư duy ngữ hệ tiếng Nhật thay vì dịch gượng gạo sang tiếng Anh.",
        "category": "GRAMMAR_GUIDE",
        "level": "ALL",
        "source_type": "WEB_GUIDE",
        "external_url": "https://guidetojapanese.org/learn/",
        "author": "Tae Kim",
        "file_type": "website",
        "tags": "Ngữ pháp, Cốt lõi, Trợ từ, Chia động từ, Trực quan",
        "is_pinned": 1
    },
    {
        "id": "mat_jisho_dict",
        "title": "Jisho.org - Powerful Japanese Dictionary",
        "description": "Từ điển tiếng Nhật trực tuyến hàng đầu: Tra cứu Kanji, Hán tự, bộ thủ, tra cứu từ vựng theo romaji/kana và câu đối thoại thực tế.",
        "category": "VOCABULARY_DICT",
        "level": "ALL",
        "source_type": "ONLINE_DICT",
        "external_url": "https://jisho.org/",
        "author": "Kim Ahlström / Jisho Team",
        "file_type": "website",
        "tags": "Từ điển, Tra Kanji, Tra từ vựng, Romaji, Ví dụ mẫu",
        "is_pinned": 1
    },
    {
        "id": "mat_mazii_dict",
        "title": "Mazii Dictionary - Từ Điển Tiếng Nhật Đa Năng",
        "description": "Hệ thống từ điển tiếng Nhật cho người Việt: Tra cứu ngữ pháp JLPT theo cấp độ N5..N1, giải nghĩa chi tiết và dịch câu thông minh.",
        "category": "VOCABULARY_DICT",
        "level": "ALL",
        "source_type": "ONLINE_DICT",
        "external_url": "https://mazii.net/",
        "author": "Mazii Team",
        "file_type": "website",
        "tags": "Từ điển, Tiếng Việt, Ngữ pháp JLPT, Hán tự, Tổng hợp",
        "is_pinned": 0
    }
]

EXAMS = [
    {
        "id": "exam_seed_n5_full",
        "title": "Bộ Đề Thi Thử Toàn Diện JLPT N5 (Chính Thức Có Giải Thích)",
        "description": "Đề thi thử tiêu chuẩn JLPT cấp độ N5 bao gồm kiến thức Từ vựng (Goi), Ngữ pháp (Bunpou) và Đọc hiểu. Kèm giải thích chi tiết sư phạm tiếng Việt.",
        "level": "N5",
        "category": "JLPT_FULL",
        "year": 2024,
        "duration_minutes": 50,
        "total_questions": 6,
        "passing_score": 80,
        "max_score": 120,
        "drive_folder_url": "https://drive.google.com/drive/folders/14cvGKUh4Gu7ojd2JE6FzWL5hCTSFwhaz?usp=sharing",
        "status": "ACTIVE",
        "is_system_preset": 1
    },
    {
        "id": "exam_seed_n4_full",
        "title": "Bộ Đề Thi Thử Chuẩn JLPT N4 (Đọc Hiểu & Ngữ Pháp Trọng Tâm)",
        "description": "Đề thi khảo thí cấp độ N4 tập trung vào dạng chia thể động từ, trợ từ phức hợp và đọc hiểu đoản văn cuộc sống thường nhật.",
        "level": "N4",
        "category": "JLPT_FULL",
        "year": 2024,
        "duration_minutes": 60,
        "total_questions": 5,
        "passing_score": 90,
        "max_score": 180,
        "drive_folder_url": "https://drive.google.com/drive/folders/1HytgiK1tJaSGW4wUmHYQRbniPYu3-NLh?usp=sharing",
        "status": "ACTIVE",
        "is_system_preset": 1
    },
    {
        "id": "exam_seed_n3_full",
        "title": "Bộ Đề Thi Khảo Thí JLPT N3 (Trung Cấp Văn Cảnh)",
        "description": "Đề kiểm tra năng lực Trung cấp N3: Các mẫu ngữ pháp diễn đạt cảm xúc, nguyên nhân kết quả gián tiếp và từ đồng nghĩa.",
        "level": "N3",
        "category": "JLPT_FULL",
        "year": 2023,
        "duration_minutes": 70,
        "total_questions": 4,
        "passing_score": 95,
        "max_score": 180,
        "drive_folder_url": "https://drive.google.com/drive/folders/1lwUZCcGfAl2HwhrQVz-R4s-dXMEKpuZD?usp=sharing",
        "status": "ACTIVE",
        "is_system_preset": 1
    },
    {
        "id": "exam_seed_n2_full",
        "title": "Bộ Đề Thi Thử Thượng Cấp JLPT N2 (Thương Mại & Học Thuật)",
        "description": "Đề thi thử Thượng cấp N2: Bài tập đọc hiểu văn bản thương mại, bài nghị luận và các cấu trúc ngữ pháp trang trọng trong công việc.",
        "level": "N2",
        "category": "JLPT_FULL",
        "year": 2023,
        "duration_minutes": 105,
        "total_questions": 4,
        "passing_score": 90,
        "max_score": 180,
        "drive_folder_url": "https://drive.google.com/drive/folders/1lCVccq1e-dCWKR8CzZX7EbmRkuLPah7F?usp=sharing",
        "status": "ACTIVE",
        "is_system_preset": 1
    },
    {
        "id": "exam_seed_n1_full",
        "title": "Bộ Đề Thi Thử Đỉnh Cao JLPT N1 (Chuyên Sâu Báo Chí & Luận Điểm)",
        "description": "Đề thi thử Đỉnh cao N1: Bài tập đọc hiểu phân tích luận điểm sâu sắc của tác giả, ngữ pháp kính ngữ tuyệt đối và cụm 4 chữ Hán.",
        "level": "N1",
        "category": "JLPT_FULL",
        "year": 2024,
        "duration_minutes": 110,
        "total_questions": 4,
        "passing_score": 100,
        "max_score": 180,
        "drive_folder_url": "https://drive.google.com/drive/folders/1451604QICFd_zpWxYXLz5jJj6z2Xh4RI?usp=sharing",
        "status": "ACTIVE",
        "is_system_preset": 1
    },
    {
        "id": "exam_seed_kaiwa_practical",
        "title": "Bài Kiểm Tra Ứng Biến Kaiwa Thực Chiến (Hội Thoại Đời Sống & Công Sở)",
        "description": "Bộ câu hỏi kiểm tra phản xạ giao tiếp Kaiwa: Lựa chọn câu đối đáp phù hợp với ngữ cảnh, biểu đạt cảm xúc và xã giao chuẩn mực của người Nhật.",
        "level": "KAIWA",
        "category": "KAIWA",
        "year": 2024,
        "duration_minutes": 30,
        "total_questions": 5,
        "passing_score": 80,
        "max_score": 100,
        "drive_folder_url": "https://drive.google.com/drive/folders/17JFLZlqVgwxJFS0BkHAv1I_szVJz-aQB?usp=sharing",
        "status": "ACTIVE",
        "is_system_preset": 1
    }
]

EXAM_QUESTIONS = [
    # N5 Questions
    {
        "id": "q_n5_01",
        "exam_id": "exam_seed_n5_full",
        "section": "GOI",
        "question_number": 1,
        "question_text": "きょうは [天気] が いいですね。",
        "furigana_text": "きょうは [てんき] が いいですね。",
        "option_1": "てんき",
        "option_2": "でんき",
        "option_3": "げんき",
        "option_4": "ほんき",
        "correct_option": 1,
        "explanation": "Chữ Hán [天気] đọc là てんき (tenki) nghĩa là 'thời tiết'. Phương án 2 là điện (でんき), 3 là khỏe mạnh (げんき)."
    },
    {
        "id": "q_n5_02",
        "exam_id": "exam_seed_n5_full",
        "section": "BUNPOU",
        "question_number": 2,
        "question_text": "わたしは まいにち 日本語 ____ べんきょうします。",
        "furigana_text": "わたしは まいにち にほんご ____ べんきょうします。",
        "option_1": "に",
        "option_2": "を",
        "option_3": "で",
        "option_4": "へ",
        "correct_option": 2,
        "explanation": "Trợ từ を (o) dùng để chỉ tân ngữ/đối tượng chịu sự tác động trực tiếp của ngoại động từ べんきょうします (học cái gì -> học tiếng Nhật: 日本語を勉強します)."
    },
    {
        "id": "q_n5_03",
        "exam_id": "exam_seed_n5_full",
        "section": "GOI",
        "question_number": 3,
        "question_text": "つくえの [上] に 本が あります。",
        "furigana_text": "つくえの [うえ] に ほんが あります。",
        "option_1": "した",
        "option_2": "なか",
        "option_3": "うえ",
        "option_4": "まえ",
        "correct_option": 3,
        "explanation": "Chữ Hán [上] đọc là うえ (ue) có nghĩa là 'ở phía trên'. した (dưới), なか (trong), まえ (trước)."
    },
    {
        "id": "q_n5_04",
        "exam_id": "exam_seed_n5_full",
        "section": "BUNPOU",
        "question_number": 4,
        "question_text": "きのう デパートへ ____ いきました。",
        "furigana_text": "きのう デパートへ ____ いきました。",
        "option_1": "かいもの",
        "option_2": "かいものに",
        "option_3": "かいものを",
        "option_4": "かいもので",
        "correct_option": 2,
        "explanation": "Cấu trúc danh từ / V-masu (bỏ masu) + に + 行きます biểu thị mục đích của hành động di chuyển. かいものに行く = đi mua sắm."
    },
    {
        "id": "q_n5_05",
        "exam_id": "exam_seed_n5_full",
        "section": "DOKKAI",
        "question_number": 5,
        "question_text": "田中:「李さん、このペンを かりても いいですか。」\n李:「ええ、____。」",
        "furigana_text": "たなか:「りさん、このペンを かりても いいですか。」\nり:「ええ、____。」",
        "option_1": "いいえ、だめです",
        "option_2": "どうぞ",
        "option_3": "ありがとう",
        "option_4": "ごめんなさい",
        "correct_option": 2,
        "explanation": "Khi đối phương xin phép mượn đồ 「〜てもいいですか」 và người đáp đồng ý 「ええ」 thì câu tiếp theo tự nhiên nhất là 「どうぞ」 (Xin mời bạn)."
    },
    {
        "id": "q_n5_06",
        "exam_id": "exam_seed_n5_full",
        "section": "BUNPOU",
        "question_number": 6,
        "question_text": "この りんごは ひとつ 100円ですから、みっつで ____ 円です。",
        "furigana_text": "この りんごは ひとつ 100えんですから、みっつで ____ えんです。",
        "option_1": "200",
        "option_2": "300",
        "option_3": "400",
        "option_4": "500",
        "correct_option": 2,
        "explanation": "Một quả (ひとつ) giá 100 Yên, do đó 3 quả (みっつで - trợ từ で chỉ tổng mức) là 300 Yên (300円)."
    },

    # N4 Questions
    {
        "id": "q_n4_01",
        "exam_id": "exam_seed_n4_full",
        "section": "BUNPOU",
        "question_number": 1,
        "question_text": "あした 雨が ____、出かけません。",
        "furigana_text": "あした あめが ____、でかけません。",
        "option_1": "ふったら",
        "option_2": "ふると",
        "option_3": "ふれば",
        "option_4": "ふって",
        "correct_option": 1,
        "explanation": "Điều kiện giả định trong tương lai chỉ một sự việc chưa chắc chắn xảy ra kết hợp với ý chí/dự định của người nói 「出かけません」 dùng thể 〜たら (ふったら)."
    },
    {
        "id": "q_n4_02",
        "exam_id": "exam_seed_n4_full",
        "section": "BUNPOU",
        "question_number": 2,
        "question_text": "先生、このことばの 意味を ____ いただけませんか。",
        "furigana_text": "せんせい、このことばの いみを ____ いただけませんか。",
        "option_1": "おしえて",
        "option_2": "おしえたら",
        "option_3": "おしえる",
        "option_4": "おしえに",
        "correct_option": 1,
        "explanation": "Mẫu câu nhờ vả lịch sự với cấp trên: V-te + いただけませんか (おしえていただけませんか: Thầy có thể vui lòng giải thích giúp em được không ạ?)."
    },

    # Kaiwa Questions
    {
        "id": "q_kw_01",
        "exam_id": "exam_seed_kaiwa_practical",
        "section": "KAIWA",
        "question_number": 1,
        "question_text": "同僚:「お先に失礼します。」\nあなた:「____。」",
        "furigana_text": "どうりょう:「おさきにしつれいします。」\nあなた:「____。」",
        "option_1": "どういたしまして",
        "option_2": "お疲れ様でした",
        "option_3": "いってらっしゃい",
        "option_4": "ごちそうさまでした",
        "correct_option": 2,
        "explanation": "Khi đồng nghiệp xin phép về trước 「お先に失礼します」, câu đáp chuẩn mực trong văn hóa công sở Nhật Bản là 「お疲れ様でした」 (Anh/chị đã vất vả rồi ạ)."
    },
    {
        "id": "q_kw_02",
        "exam_id": "exam_seed_kaiwa_practical",
        "section": "KAIWA",
        "question_number": 2,
        "question_text": "店員:「いらっしゃいませ。何名様でしょうか。」\nあなた:「____。」",
        "furigana_text": "てんいん:「いらっしゃいませ。なんめいさまでしょうか。」\nあなた:「____。」",
        "option_1": "ふたりです",
        "option_2": "ふたつです",
        "option_3": "にほんのひとです",
        "option_4": "ふたつめです",
        "correct_option": 1,
        "explanation": "Nhân viên hỏi số lượng khách vào quán ăn 「何名様でしょうか」, trả lời 2 người dùng đơn vị đếm người 「ふたりです」 (2名 / 二人)."
    }
]

def migrate_and_seed():
    for db_path in DB_PATHS:
        if not db_path.exists():
            print(f"Skipping {db_path} (does not exist)")
            continue
        print(f"Migrating and seeding: {db_path}")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Execute DDL
        cursor.executescript(DDL)
        
        # Seed Reference Materials
        for m in REFERENCE_MATERIALS:
            cursor.execute("""
                INSERT OR REPLACE INTO reference_materials (
                    id, title, description, category, level, source_type,
                    external_url, author, file_type, tags, is_pinned, is_system_preset, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m["id"], m["title"], m["description"], m["category"], m["level"],
                m["source_type"], m["external_url"], m["author"], m["file_type"],
                m["tags"], m["is_pinned"], 1, "system"
            ))
            
        # Seed Exams
        for ex in EXAMS:
            cursor.execute("""
                INSERT OR REPLACE INTO exams (
                    id, title, description, level, category, year,
                    duration_minutes, total_questions, passing_score, max_score,
                    drive_folder_url, status, is_system_preset, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ex["id"], ex["title"], ex["description"], ex["level"], ex["category"],
                ex["year"], ex["duration_minutes"], ex["total_questions"],
                ex["passing_score"], ex["max_score"], ex["drive_folder_url"],
                ex["status"], ex["is_system_preset"], "system"
            ))
            
        # Seed Exam Questions
        for q in EXAM_QUESTIONS:
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

        conn.commit()
        
        # Verify counts
        m_count = cursor.execute("SELECT COUNT(*) FROM reference_materials").fetchone()[0]
        e_count = cursor.execute("SELECT COUNT(*) FROM exams").fetchone()[0]
        q_count = cursor.execute("SELECT COUNT(*) FROM exam_questions").fetchone()[0]
        print(f"Verification {db_path.name}: {m_count} reference materials, {e_count} exams, {q_count} questions.")
        conn.close()

if __name__ == "__main__":
    migrate_and_seed()

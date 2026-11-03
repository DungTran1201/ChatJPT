import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "ai-backend" / "data"
MATERIALS_DIR = DATA_DIR / "reference_materials"

# Built-in structured RAG Knowledge Base covering JLPT N5..N1 and Kaiwa
# Extracted from Tae Kim's Japanese Grammar Guide, Shinkanzen, Mimikara, and official exam archives
RAG_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    # --- N5 GRAMMAR & VOCABULARY ---
    {
        "id": "rag_n5_01",
        "title": "Trợ từ は (Wa) và が (Ga) - Phân biệt Chủ đề và Chủ ngữ",
        "level": "N5",
        "category": "GRAMMAR",
        "tags": ["Trợ từ", "は", "が", "N5", "Căn bản"],
        "summary": "は dùng để giới thiệu chủ đề của câu (nói về cái gì), trong khi が dùng để xác định chủ ngữ cụ thể của hành động hoặc thông tin mới.",
        "content": "Trong tiếng Nhật N5:\n1. [Chủ đề] + は: Đặt chủ đề cho toàn bộ câu. Trợ từ は được phát âm là 'wa'. Ví dụ: 私は学生です (Watashi wa gakusei desu - Tôi là học sinh).\n2. [Chủ ngữ] + が: Chỉ đích danh đối tượng thực hiện hành động hoặc xuất hiện trong trường nhìn. Ví dụ: 雨が降っています (Ame ga futte imasu - Trời đang mưa).\n3. Trong câu có tính từ biểu thị sở thích, khả năng: Aは Bが 好き/上手/下手/分かります. Ví dụ: 私は日本語が好きです (Tôi thích tiếng Nhật).",
        "examples": [
            {"jp": "誰が来ましたか。田中さんが来ました。", "vi": "Ai đã đến vậy? - Anh Tanaka đã đến."},
            {"jp": "猫がいます。", "vi": "Có một con mèo (nhấn mạnh sự xuất hiện của con mèo)."}
        ]
    },
    {
        "id": "rag_n5_02",
        "title": "Thể Te (〜て) của Động từ và các Mẫu câu Ứng dụng N5",
        "level": "N5",
        "category": "GRAMMAR",
        "tags": ["Thể Te", "Chia động từ", "N5", "てください", "ています"],
        "summary": "Thể Te là mắt xích quan trọng nhất của tiếng Nhật sơ cấp, dùng để nối các hành động liên tiếp, xin phép, cấm đoán hoặc diễn tả trạng thái đang diễn ra.",
        "content": "Quy tắc chia thể Te nhóm 1:\n- い、ち、り -> って (買う -> 買って, 待つ -> 待って, 帰る -> 帰って)\n- み、び、に -> んで (飲む -> 飲んで, 遊ぶ -> 遊んで, 死ぬ -> 死んで)\n- き -> いて (書く -> 書いて), riêng 行く -> 行って\n- ぎ -> いで (泳ぐ -> 泳いで)\n- し -> して (話す -> 話して)\nNhóm 2: Bỏ る thêm て (食べる -> 食べて, 見る -> 見て)\nNhóm 3: します -> して, 来ます -> きて\nCác mẫu câu chính: V-てください (Hãy làm V), V-てもいいですか (Được phép làm V không?), V-てはいけません (Cấm làm V), V-ています (Đang làm V hoặc trạng thái duy trì).",
        "examples": [
            {"jp": "窓を開けてください。", "vi": "Xin vui lòng mở cửa sổ ra."},
            {"jp": "ここで写真を撮ってもいいですか。", "vi": "Tôi có thể chụp ảnh ở đây được không?"}
        ]
    },

    # --- N4 GRAMMAR & VOCABULARY ---
    {
        "id": "rag_n4_01",
        "title": "Thể Điều Kiện: 〜たら, 〜ば, 〜なら, 〜と trong JLPT N4",
        "level": "N4",
        "category": "GRAMMAR",
        "tags": ["Điều kiện", "たら", "ば", "なら", "と", "N4"],
        "summary": "Bốn hình thức biểu thị điều kiện giả định 'Nếu... thì...' với sắc thái và điều kiện sử dụng chặt chẽ trong đề thi N4.",
        "content": "1. 〜たら (Tara): Linh hoạt nhất, dùng cho cả điều kiện thực tế lẫn giả định trong tương lai, vế sau có thể chứa ý chí, mệnh lệnh, rủ rê. Ví dụ: 時間があったら、映画を見に行きましょう (Nếu có thời gian thì cùng đi xem phim nhé).\n2. 〜と (To): Diễn tả quy luật tự nhiên, chân lý, thói quen bất biến hoặc chỉ dẫn đường đi. Vế sau TUYỆT ĐỐI không dùng mệnh lệnh/ý chí. Ví dụ: 春になると、桜が咲きます (Hễ mùa xuân đến thì hoa anh đào nở).\n3. 〜ば (Ba): Điều kiện giả thiết thuần túy, chú trọng vào điều kiện tiên quyết để kết quả xảy ra. Ví dụ: 安ければ、買います (Nếu rẻ thì tôi sẽ mua).\n4. 〜なら (Nara): Tiếp nhận chủ đề đối phương vừa nêu ra rồi đưa ra lời khuyên/ý kiến. Ví dụ: 日本へ行くなら、京都がおすすめです (Nếu đi Nhật Bản thì tôi khuyên bạn nên đi Kyoto).",
        "examples": [
            {"jp": "このボタンを押すと、お湯が出ます。", "vi": "Hễ bấm nút này thì nước nóng sẽ chảy ra."},
            {"jp": "雨が降ったら、行きません。", "vi": "Nếu trời mưa thì tôi sẽ không đi."}
        ]
    },
    {
        "id": "rag_n4_02",
        "title": "Mẫu câu Cho và Nhận: 〜てあげる, 〜てもらう, 〜てくれる",
        "level": "N4",
        "category": "GRAMMAR",
        "tags": ["Cho nhận", "あげる", "もらう", "くれる", "N4"],
        "summary": "Biểu thị hành vi giúp đỡ hoặc nhận ơn nghĩa giữa các ngôi trong giao tiếp tiếng Nhật.",
        "content": "1. V-てあげる: Người nói làm việc tốt cho người khác (lưu ý tránh dùng trực tiếp với người bề trên vì dễ bị xem là kể ơn). Ví dụ: 友達に傘を貸してあげました (Tôi đã cho bạn mượn ô).\n2. V-てくれる: Người khác làm việc tốt cho tôi hoặc người trong gia đình tôi (hướng ơn huệ chảy về phía mình). Ví dụ: 先生が日本語を教えてくれました (Thầy giáo đã dạy tiếng Nhật cho tôi).\n3. V-てもらう: Tôi tiếp nhận hành động tốt từ ai đó (Tôi được ai đó làm giúp). Ví dụ: 田中さんに手伝ってもらいました (Tôi đã được anh Tanaka giúp đỡ).",
        "examples": [
            {"jp": "母がセーターを編んでくれました。", "vi": "Mẹ đã đan áo len cho tôi."},
            {"jp": "鈴木さんに案内してもらいました。", "vi": "Tôi đã được anh Suzuki hướng dẫn tham quan."}
        ]
    },

    # --- N3 GRAMMAR & NUANCES ---
    {
        "id": "rag_n3_01",
        "title": "Ngữ pháp 〜わけだ và 〜わけではない (Lẽ dĩ nhiên vs Không hẳn là)",
        "level": "N3",
        "category": "GRAMMAR",
        "tags": ["わけだ", "わけではない", "N3", "Ngữ pháp trọng tâm"],
        "summary": "Biểu thị tính tất yếu theo logic nhân quả hoặc phủ định một phần quan niệm định kiến.",
        "content": "1. 〜わけだ (Wake da): 'Hèn chi, thảo nào, thảo nào mà...'. Dùng khi người nói hiểu ra lý do tất nhiên đằng sau một sự việc. Ví dụ: 暑いわけだ、気温が38度もある (Thảo nào mà nóng thế, nhiệt độ lên tới tận 38 độ C cơ mà).\n2. 〜わけではない (Wake dewa nai): 'Không hẳn là, không có nghĩa là...'. Phủ định một phần, tránh kết luận tuyệt đối. Ví dụ: 嫌いなわけではないが、あまり食べたくない (Không hẳn là tôi ghét món này, chỉ là hiện tại tôi không muốn ăn lắm thôi).",
        "examples": [
            {"jp": "日本に5年も住んでいたので、日本語が上手なわけです。", "vi": "Vì đã sống ở Nhật tận 5 năm, hèn chi tiếng Nhật giỏi thế."},
            {"jp": "お金があれば幸せというわけではない。", "vi": "Không hẳn cứ có tiền là sẽ hạnh phúc."}
        ]
    },
    {
        "id": "rag_n3_02",
        "title": "Ngữ pháp 〜に対して (Ni taishite) và 〜に関して (Ni kanshite)",
        "level": "N3",
        "category": "GRAMMAR",
        "tags": ["に対して", "に関して", "N3", "So sánh"],
        "summary": "Phân biệt giữa đối chiếu tương phản / đối tượng tác động (に対して) và phạm vi liên quan đến một đề tài (に関して).",
        "content": "1. N + に対して (Ni taishite):\n- Nghĩa 1: Trái ngược với... (so sánh 2 vế đối lập). Ví dụ: 兄が活発なのに対して、弟は物静かだ (Trái ngược với người anh hiếu động thì người em trai lại rất trầm tính).\n- Nghĩa 2: Thái độ/hành vi hướng vào đối tượng. Ví dụ: お客様に対して失礼な態度をとってはいけません (Không được có thái độ thất lễ đối với khách hàng).\n2. N + に関して (Ni kanshite): 'Liên quan đến, về vấn đề...'. Văn phong trang trọng hơn について. Ví dụ: この事件に関して、何か知っていますか (Anh có biết thông tin gì liên quan đến vụ việc này không?).",
        "examples": [
            {"jp": "都市部では人口が増えているのに対して、農村部では減少している。", "vi": "Trái với khu vực thành thị dân số gia tăng, khu vực nông thôn dân số lại suy giảm."},
            {"jp": "環境問題に関する報告書を読んだ。", "vi": "Tôi đã đọc bản báo cáo liên quan đến vấn đề môi trường."}
        ]
    },

    # --- N2 GRAMMAR & BUSINESS ---
    {
        "id": "rag_n2_01",
        "title": "Ngữ pháp 〜に際して (Ni saishite) và 〜を契機に (O keiki ni)",
        "level": "N2",
        "category": "GRAMMAR",
        "tags": ["に際して", "を契機に", "N2", "Thương mại", "Văn phong trang trọng"],
        "summary": "Các cấu trúc bắt buộc trong văn bản thương mại, diễn văn khai mạc và hợp đồng kinh tế cấp độ N2.",
        "content": "1. N / V-ru + に際して (Ni saishite): 'Nhân dịp, khi chuẩn bị bước vào...'. Dùng cho những sự kiện mang tính dấu mốc trang trọng (khai trương, xuất phát, kết hôn, ký hợp đồng). Ví dụ: 新規事業の立ち上げに際して、各部署の協力を仰ぎたい (Nhân dịp triển khai dự án kinh doanh mới, chúng tôi mong nhận được sự phối hợp của các phòng ban).\n2. N + を契機に / を契機として (O keiki ni): 'Nhân cơ hội, lấy mốc sự kiện X làm bước ngoặt chuyển biến...'. Thường dẫn tới một sự thay đổi lớn tích cực. Ví dụ: 転職を契機に、生活習慣を一新した (Lấy bước ngoặt chuyển việc làm cột mốc, tôi đã đổi mới hoàn toàn thói quen sinh hoạt).",
        "examples": [
            {"jp": "ご契約に際しまして、重要事項のご説明をいたします。", "vi": "Khi quý khách tiến hành ký kết hợp đồng, chúng tôi xin phép được giải thích các điều khoản quan trọng."},
            {"jp": "オリンピックの開催を契機に、インフラが急速に整備された。", "vi": "Nhân bước ngoặt tổ chức Thế vận hội, cơ sở hạ tầng đã nhanh chóng được nâng cấp đồng bộ."}
        ]
    },

    # --- N1 ADVANCED & ACADEMIC ---
    {
        "id": "rag_n1_01",
        "title": "Cấu trúc Kính Ngữ Tuyệt Đối và Ngữ pháp Cổ Điển N1: 〜つかまつる, 〜にたえない",
        "level": "N1",
        "category": "GRAMMAR",
        "tags": ["Kính ngữ", "Cổ điển", "N1", "つかまつる", "にたえない"],
        "summary": "Văn phong học thuật thượng thừa, luận văn và phát biểu nghi lễ ngoại giao cấp độ JLPT N1.",
        "content": "1. 〜つかまつる (Tsukamatsuru): Khiêm nhường ngữ cổ điển bậc cao của します (Shimasu), thường kết hợp: ご案内つかまつります, ご指導つかまつります (Kính cẩn hướng dẫn / chỉ đạo quý vị).\n2. N / V-ru + にたえない (Ni taenai):\n- Nghĩa 1: Tràn đầy cảm xúc không thể kìm nén được (Thường đi với 感謝 - biết ơn, 喜び - vui mừng, 遺憾 - lấy làm tiếc). Ví dụ: 皆様のご厚意には感謝にたえません (Trước thịnh tình của quý vị, tôi vô cùng xúc động và biết ơn khôn xiết).\n- Nghĩa 2: Không thể chịu đựng nổi, không đáng để xem/nghe. Ví dụ: 聞くにたえない暴言 (Những lời lăng mạ không thể nào nghe nổi).",
        "examples": [
            {"jp": "長年のご愛顧に対し、心より感謝にたえない次第でございます。", "vi": "Đối với sự ủng hộ quý báu suốt nhiều năm qua, chúng tôi xin bày tỏ lòng biết ơn sâu sắc vô bờ bến."},
            {"jp": "この度の大任、身命を賭してご奉公つかまつる所存でございます。", "vi": "Trọng trách lần này, tôi xin đem hết tâm sức và sinh mệnh để kính cẩn cống hiến."}
        ]
    },

    # --- KAIWA PRACTICAL SITUATIONS ---
    {
        "id": "rag_kaiwa_01",
        "title": "Nghệ thuật Đệm từ Aizuchi (相槌) và Phản xạ Hội thoại Tự nhiên",
        "level": "KAIWA",
        "category": "KAIWA",
        "tags": ["Kaiwa", "Aizuchi", "Hội thoại", "Giao tiếp đời sống"],
        "summary": "Bí quyết tạo sự kết nối cảm xúc và duy trì nhịp trò chuyện tự nhiên như người bản xứ.",
        "content": "Trong văn hóa giao tiếp Nhật Bản, nếu bạn chỉ im lặng lắng nghe, đối phương sẽ cảm thấy bạn không chú ý hoặc không hiểu. Do đó Aizuchi là bắt buộc:\n1. Tán đồng nhẹ nhàng: そうですね (Đúng vậy nhỉ), なるほど (Thì ra là thế), 確かに (Quả đúng là vậy).\n2. Ngạc nhiên / Thú vị: 本当ですか (Thật vậy sao?), そうなんですか (Thế cơ ạ?), まさか (Không thể nào!).\n3. Thể hiện sự chú ý: ええ (Vâng), はい (Dạ), うん (Ừ - thân mật).\n4. Khéo léo ngắt lời / xin phép: ちょっとよろしいでしょうか (Tôi xin phép một chút được không ạ?).",
        "examples": [
            {"jp": "A:「昨日、新しいカフェに行ったんですよ。」 B:「あ、そうなんですか！どこにあるんですか。」", "vi": "A: 'Hôm qua tôi vừa đến một quán cafe mới đấy.' B: 'Ô thế cơ ạ! Quán ở đâu thế bạn?'"},
            {"jp": "A:「このやり方だと時間が半分で済みます。」 B:「なるほど！それは効率的ですね。」", "vi": "A: 'Làm theo cách này chỉ mất nửa thời gian thôi.' B: 'Thì ra là thế! Hiệu quả thật đấy nhỉ.'"}
        ]
    }
]

class RagExamService:
    @staticmethod
    def get_local_materials_inventory() -> List[Dict[str, Any]]:
        """
        Scan all downloaded reference materials from disk and map them into structured items.
        """
        inventory = []
        if not MATERIALS_DIR.exists():
            return inventory

        level_map = {
            'n5': 'N5',
            'n4': 'N4',
            'n3': 'N3',
            'n2': 'N2',
            'n1': 'N1',
            'kaiwa': 'KAIWA'
        }

        for lvl_dir in MATERIALS_DIR.iterdir():
            if lvl_dir.is_dir() and lvl_dir.name.lower() in level_map:
                lvl = level_map[lvl_dir.name.lower()]
                for f in lvl_dir.glob("*.pdf"):
                    size_bytes = f.stat().st_size
                    # Filter out small corrupted HTML error files
                    if size_bytes < 3000:
                        continue
                    clean_title = f.stem.replace('_', ' ').replace('[Tailieutiengnhat.net]', '').replace('[Tiengnhatcoban.net]', '').strip()
                    cat = f"JLPT_{lvl}" if lvl != 'KAIWA' else "KAIWA"
                    inventory.append({
                        "id": f"mat_local_{f.stem[:24].lower()}_{lvl.lower()}",
                        "title": clean_title,
                        "filename": f.name,
                        "relative_path": f"data/reference_materials/{lvl_dir.name}/{f.name}",
                        "level": lvl,
                        "category": cat,
                        "file_type": "pdf",
                        "size_bytes": size_bytes,
                        "size_display": f"{size_bytes / (1024 * 1024):.1f} MB" if size_bytes > 1024 * 1024 else f"{size_bytes / 1024:.0f} KB",
                        "source_type": "LOCAL_FILE",
                        "is_local_available": True,
                        "is_pinned": True if 'kanji' in clean_title.lower() or 'ngu phap' in clean_title.lower() or 'de thi' in clean_title.lower() else False
                    })

        return sorted(inventory, key=lambda x: (x['level'], -x['size_bytes']))

    @staticmethod
    def search_rag(query: str, level: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query the pedagogical RAG knowledge base using keyword and semantic term matching.
        """
        q = query.lower().strip()
        results = []

        for item in RAG_KNOWLEDGE_BASE:
            if level and level.upper() != 'ALL' and item['level'] != level.upper():
                continue

            score = 0
            # Match title
            if q in item['title'].lower():
                score += 10
            # Match tags
            for tag in item['tags']:
                if q in tag.lower():
                    score += 5
            # Match summary & content
            if q in item['summary'].lower():
                score += 4
            if q in item['content'].lower():
                score += 2
            
            # Substring matches
            words = q.split()
            for w in words:
                if len(w) > 1:
                    if w in item['title'].lower() or w in item['content'].lower():
                        score += 1

            if score > 0 or not q:
                res_item = dict(item)
                res_item['relevance_score'] = score
                results.append(res_item)

        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return results[:limit]

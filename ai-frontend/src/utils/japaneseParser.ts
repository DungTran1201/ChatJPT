/**
 * Japanese Interlinear Parsing & Romaji Utilities
 * Handles Furigana, Ruby annotations, Unified Grammar Highlights, and Hepburn Romaji.
 */

const KANA_ROMAJI_MAP: Record<string, string> = {
  // Hiragana Monographs
  'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
  'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
  'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
  'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
  'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
  'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
  'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
  'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
  'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
  'わ': 'wa', 'を': 'o', 'ん': 'n',

  // Dakuten & Handakuten
  'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
  'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
  'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'де': 'de', 'で': 'de', 'ど': 'do',
  'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
  'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',

  // Digraphs (Yoon)
  'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo',
  'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho',
  'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho',
  'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
  'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo',
  'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
  'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
  'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
  'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
  'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
  'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo',

  // Katakana equivalents
  'ア': 'a', 'イ': 'i', 'ウ': 'u', 'エ': 'e', 'オ': 'o',
  'カ': 'ka', 'キ': 'ki', 'ク': 'ku', 'ケ': 'ke', 'コ': 'ko',
  'サ': 'sa', 'シ': 'shi', 'ス': 'su', 'セ': 'se', 'ソ': 'so',
  'タ': 'ta', 'チ': 'chi', 'ツ': 'tsu', 'テ': 'te', 'ト': 'to',
  'ナ': 'na', 'ニ': 'ni', 'ヌ': 'nu', 'ネ': 'ne', 'ノ': 'no',
  'ハ': 'ha', 'ヒ': 'hi', 'フ': 'fu', 'ヘ': 'he', 'ホ': 'ho',
  'マ': 'ma', 'ミ': 'mi', 'ム': 'mu', 'メ': 'me', 'モ': 'mo',
  'ヤ': 'ya', 'ユ': 'yu', 'ヨ': 'yo',
  'ラ': 'ra', 'リ': 'ri', 'ル': 'ru', 'レ': 're', 'ロ': 'ro',
  'ワ': 'wa', 'ヲ': 'o', 'ン': 'n',
  'ガ': 'ga', 'ギ': 'gi', 'グ': 'gu', 'ゲ': 'ge', 'ゴ': 'go',
  'ザ': 'za', 'ジ': 'ji', 'ズ': 'zu', 'ゼ': 'ze', 'ゾ': 'zo',
  'ダ': 'da', 'ヂ': 'ji', 'ヅ': 'zu', 'デ': 'de', 'ド': 'do',
  'バ': 'ba', 'ビ': 'bi', 'ブ': 'bu', 'ベ': 'be', 'ボ': 'bo',
  'パ': 'pa', 'ピ': 'pi', 'プ': 'pu', 'ペ': 'pe', 'ポ': 'po',
};

export const COMMON_PARTICLES = new Set([
  'は', 'が', 'を', 'に', 'で', 'へ', 'と', 'から', 'まで',
  'も', 'ね', 'よ', 'か', 'けど', 'わ', 'の', 'や', 'し', 'ば'
]);

export const COMMON_VOCAB_MAP: Record<string, { furigana: string; romaji: string }> = {
  '言葉': { furigana: 'ことば', romaji: 'kotoba' },
  '文化': { furigana: 'ぶんか', romaji: 'bunka' },
  '鏡': { furigana: 'かがみ', romaji: 'kagami' },
  '心': { furigana: 'こころ', romaji: 'kokoro' },
  '映し出す': { furigana: 'うつしだす', romaji: 'utsushidasu' },
  '美しく': { furigana: 'うつくしく', romaji: 'utsukushiku' },
  '深い': { furigana: 'ふかい', romaji: 'fukai' },
  '日本語': { furigana: 'にほんご', romaji: 'nihongo' },
  '極めましょう': { furigana: 'きわめましょう', romaji: 'kiwamemashou' },
  '私': { furigana: 'わたし', romaji: 'watashi' },
  'わたくし': { furigana: 'わたくし', romaji: 'watakushi' },
  '雪': { furigana: 'ゆき', romaji: 'yuki' },
  '申します': { furigana: 'もうします', romaji: 'moushimasu' },
  'はじめまして': { furigana: 'はじめまして', romaji: 'hajimemashite' },
  '研究': { furigana: 'けんきゅう', romaji: 'kenkyuu' },
  '携わりながら': { furigana: 'たずさわりながら', romaji: 'tazusawarinagara' },
  '最高峰': { furigana: 'さいこうほう', romaji: 'saikouhou' },
  '導くべく': { furigana: 'みちびくべく', romaji: 'michibikubeku' },
  '言霊': { furigana: 'ことだま', romaji: 'kotodama' },
  '奥義': { furigana: 'おうぎ', romaji: 'ougi' },
  '紐解いて': { furigana: 'ひもといて', romaji: 'himotoite' },
  '試験対策': { furigana: 'しけんたいさく', romaji: 'shikentaisaku' },
  '千変万化': { furigana: 'せんぺんばんか', romaji: 'senpenbanka' },
  '四字熟語': { furigana: 'よじじゅくご', romaji: 'yojijukugo' },
  '敬語体系': { furigana: 'けいごたいけい', romaji: 'keigotaitkei' },
  '裏側': { furigana: 'うらがわ', romaji: 'uragawa' },
  '日本人': { furigana: 'にほんじん', romaji: 'nihonjin' },
  '精神構造': { furigana: 'せいしんこうぞう', romaji: 'seishinkouzou' },
  '徹底的': { furigana: 'てっていてき', romaji: 'tetteiteki' },
  '指導': { furigana: 'しどう', romaji: 'shidou' },
  '知性': { furigana: 'ちせい', romaji: 'chisei' },
  '扉': { furigana: 'とびら', romaji: 'tobira' },
  '開けて': { furigana: 'あけて', romaji: 'akete' },
  '開く': { furigana: 'ひらく', romaji: 'hiraku' },
  '深奥': { furigana: 'しんおう', romaji: 'shin\'ou' },
  '世界': { furigana: 'せかい', romaji: 'sekai' },
  '足': { furigana: 'あし', romaji: 'ashi' },
  '踏み入れて': { furigana: 'ふみいれて', romaji: 'fumiirete' },
  'くださいませ': { furigana: 'くださいませ', romaji: 'kudasaimase' },
  '準備': { furigana: 'じゅんび', romaji: 'junbi' },
  '宜しい': { furigana: 'よろしい', romaji: 'yoroshii' },
  '先生': { furigana: 'せんせい', romaji: 'sensei' },
  '学生': { furigana: 'がくせい', romaji: 'gakusei' },
  '勉強': { furigana: 'べんきょう', romaji: 'benkyou' },
  '今日': { furigana: 'きょう', romaji: 'kyou' },
  '本日': { furigana: 'ほんじつ', romaji: 'honjitsu' },
  '探求': { furigana: 'たんきゅう', romaji: 'tankyuu' },
  '日常': { furigana: 'にちじょう', romaji: 'nichijou' },
  '荒波': { furigana: 'あらなみ', romaji: 'aranami' },
  '論文': { furigana: 'ろんぶん', romaji: 'ronbun' },
  '格調': { furigana: 'かくちょう', romaji: 'kakuchou' },
  '文体': { furigana: 'ぶんたい', romaji: 'buntai' },
  '難解': { furigana: 'なんかい', romaji: 'nankai' },
  '文法': { furigana: 'ぶんぽう', romaji: 'bunpou' },
  '語彙': { furigana: 'ごい', romaji: 'goi' },
  '語彙分析': { furigana: 'ごいぶんせき', romaji: 'goibunseki' },
  '質問': { furigana: 'しつもん', romaji: 'shitsumon' },
  '心ゆく': { furigana: 'こころゆく', romaji: 'kokoroyuku' },
  'お尋ね': { furigana: 'おたずね', romaji: 'otazune' },
  '静か': { furigana: 'しずか', romaji: 'shizuka' },
  '一礼': { furigana: 'いちれい', romaji: 'ichirei' },
  '端正': { furigana: 'たんせい', romaji: 'tansei' },
  '微笑み': { furigana: 'ほほえみ', romaji: 'hohoemi' },
  '浮べる': { furigana: 'うかべる', romaji: 'ukaberu' },
  'どうぞ': { furigana: 'どうぞ', romaji: 'douzo' },
  'ありがとう': { furigana: 'ありがとう', romaji: 'arigatou' },
  'ございます': { furigana: 'ございます', romaji: 'gozaimasu' },
  'つかまつります': { furigana: 'つかまつります', romaji: 'tsukamatsurimasu' },
  '大丈夫': { furigana: 'だいじょうぶ', romaji: 'daijoubu' },
  '一緒': { furigana: 'いっしょ', romaji: 'issho' },
  '一歩': { furigana: 'いっぽ', romaji: 'ippo' },
  '楽しく': { furigana: 'たのしく', romaji: 'tanoshiku' },
  '楽しい': { furigana: 'たのしい', romaji: 'tanoshii' },
  'しましょう': { furigana: 'しましょう', romaji: 'shimashou' },
  '大和': { furigana: 'やまと', romaji: 'yamato' },
  '国': { furigana: 'くに', romaji: 'kuni' },
  '来た': { furigana: 'きた', romaji: 'kita' },
  '桜': { furigana: 'さくら', romaji: 'sakura' },
  '桜先生': { furigana: 'さくらせんせい', romaji: 'sakurasensei' },
  'ビジネス': { furigana: 'ビジネス', romaji: 'bijinesu' },
  '場': { furigana: 'ば', romaji: 'ba' },
  '正確': { furigana: 'せいかく', romaji: 'seikaku' },
  '品格': { furigana: 'ひんかく', romaji: 'hinkaku' },
  'ある': { furigana: 'ある', romaji: 'aru' },
  '言葉遣い': { furigana: 'ことばづかい', romaji: 'kotobazukai' },
  'こそが': { furigana: 'こそが', romaji: 'kosoga' },
  '最大': { furigana: 'さいだい', romaji: 'saidai' },
  '信頼': { furigana: 'しんらい', romaji: 'shinrai' },
  '生みます': { furigana: 'うみます', romaji: 'umimasu' },
  '生む': { furigana: 'うむ', romaji: 'umu' },
  '皆': { furigana: 'みな', romaji: 'mina' },
  '皆様': { furigana: 'みなさま', romaji: 'minasama' },
  '高度': { furigana: 'こうど', romaji: 'koudo' },
  '上級': { furigana: 'じょうきゅう', romaji: 'joukyuu' },
  '表現': { furigana: 'ひょうげん', romaji: 'hyougen' },
  '習得': { furigana: 'しゅうとく', romaji: 'shuutoku' },
  'できる': { furigana: 'できる', romaji: 'dekiru' },
  'よう': { furigana: 'よう', romaji: 'you' },
  '全力': { furigana: 'ぜんりょく', romaji: 'zenryoku' },
  'サポート': { furigana: 'サポート', romaji: 'sapooto' },
  'いたします': { furigana: 'いたします', romaji: 'itashimasu' },
  'いたす': { furigana: 'いたす', romaji: 'itasu' },
  '竜': { furigana: 'りゅう', romaji: 'ryuu' },
  '竜先生': { furigana: 'りゅうせんせい', romaji: 'ryuusensei' },
  '葵': { furigana: 'あおい', romaji: 'aoi' },
  '健二': { furigana: 'けんじ', romaji: 'kenji' },
  '頑張りましょう': { furigana: 'がんばりましょう', romaji: 'ganbarimashou' },
  '的確': { furigana: 'てきかく', romaji: 'tekikaku' },
  'ずつ': { furigana: 'ずつ', romaji: 'zutsu' },
  'よろしく': { furigana: 'よろしく', romaji: 'yoroshiku' },
  'お願いします': { furigana: 'おねがいします', romaji: 'onegaishimasu' },
  'お願い': { furigana: 'おねがい', romaji: 'onegai' },
};

export interface JapaneseToken {
  text: string;
  furigana?: string;
  romaji?: string;
  grammarHighlight?: 'green' | null;
}

export interface JapaneseSentenceBlock {
  tokens: JapaneseToken[];
  translation?: string;
  rawText: string;
}

/**
 * Convert Kana string (Hiragana/Katakana) to standard Romaji.
 * Strictly ignores Kanji characters to avoid broken mixed strings.
 */
export function kanaToRomaji(kana: string): string {
  if (!kana) return '';
  let result = '';
  let i = 0;

  while (i < kana.length) {
    const char = kana[i];

    // Sokuon っ / ッ (geminate consonant)
    if (char === 'っ' || char === 'ッ') {
      if (i + 1 < kana.length) {
        const nextChar = kana[i + 1];
        const nextTwo = i + 2 < kana.length ? kana.slice(i + 1, i + 3) : '';
        const romajiNext = KANA_ROMAJI_MAP[nextTwo] || KANA_ROMAJI_MAP[nextChar] || '';
        if (romajiNext.length > 0) {
          result += romajiNext[0];
          i++;
          continue;
        }
      }
      i++;
      continue;
    }

    // Digraphs (e.g. しゃ, きょ)
    if (i + 1 < kana.length) {
      const two = kana.slice(i, i + 2);
      if (KANA_ROMAJI_MAP[two]) {
        result += KANA_ROMAJI_MAP[two];
        i += 2;
        continue;
      }
    }

    // Single kana
    if (KANA_ROMAJI_MAP[char]) {
      result += KANA_ROMAJI_MAP[char];
    } else if (char === 'ー') {
      const lastChar = result.slice(-1);
      if (lastChar) result += lastChar;
    } else if (/^[a-zA-Z0-9\s.,!?'"~-]/.test(char)) {
      result += char;
    }
    // Kanji characters are deliberately NOT appended here to prevent mixed Kanji-Romaji strings
    i++;
  }

  return cleanRomaji(result);
}

/**
 * Sanitize romaji to ensure zero Kanji characters leak through.
 */
export function cleanRomaji(str: string): string {
  if (!str) return '';
  // Remove any remaining Kanji or East Asian punctuation
  const cleaned = str.replace(/[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3000-\u303F]/g, '').trim();
  // If no Latin characters are left, return empty
  if (!/[a-zA-Z]/.test(cleaned)) return '';
  return cleaned;
}

/**
 * Check if text contains Japanese script (Kanji, Hiragana, Katakana)
 */
export function hasJapaneseText(text: string): boolean {
  return /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/.test(text);
}

/**
 * Check if a line is predominantly Japanese dialogue (vs a Vietnamese explanation with a Japanese quote)
 */
export function isPredominantlyJapanese(text: string): boolean {
  if (!text || !text.trim()) return false;
  let trimmed = text.trim();

  // If text starts with markdown headers, blockquotes, horizontal rules, or bullet lists
  if (/^(#{1,6}\s|>\s|---|\*\*\*)/.test(trimmed)) return false;

  // If line ends with parenthesized translation, e.g. "大丈夫ですよ... (Bản dịch: Không sao đâu...)"
  const trailingTransMatch = trimmed.match(/^(.*?)\s*[\(（](?:Bản dịch|Dịch)?\s*:?\s*[^\)）]+[\)）]\s*$/i);
  if (trailingTransMatch && trailingTransMatch[1].trim()) {
    trimmed = trailingTransMatch[1].trim();
  }

  // Explicit ruby markup or grammar highlight in dialogue is Japanese
  if (/\[[^\]]+\]\([^)]+\)|<ruby>|\{[^\}]+\}\[g-/.test(trimmed)) {
    // If it's a list item starting with "- *Sắc thái:*" or "- *Ý nghĩa:*", it is an explanation
    if (/^[-*•]\s+\*(Sắc thái|Ý nghĩa|Lưu ý|Giải thích|Nuance|Meaning):\*/i.test(trimmed)) {
      return false;
    }
    return true;
  }

  // Count characters
  const jpChars = (trimmed.match(/[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/g) || []).length;
  const latinChars = (trimmed.match(/[a-zA-ZÀ-ỹ]/g) || []).length;

  if (jpChars === 0) return false;
  // If latin/Vietnamese characters exceed Japanese characters, it's an explanation
  if (latinChars >= jpChars) return false;

  return true;
}

/**
 * Speak text in Japanese using native browser Web Speech API
 */
export function speakJapaneseSpeech(text: string): void {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const clean = text
    .replace(/<[^>]*>/g, '')
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
    .replace(/\{([^\}]+)\}\[[^\]]+\]/g, '$1')
    .replace(/\([^\)]+\)/g, '')
    .trim();
  if (!clean) return;

  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.lang = 'ja-JP';
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
}

/**
 * Parse a raw text paragraph into structured Japanese Interlinear blocks
 */
export function parsePedagogicalBlocks(text: string): JapaneseSentenceBlock[] {
  // First normalize and expand lines that have both Japanese dialogue AND inline translation
  const rawLines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const lines: string[] = [];

  for (const rawLine of rawLines) {
    const inlineMatch = rawLine.match(/^(.*?)\s*[\(（](?:Bản dịch|Dịch)?\s*:?\s*([^\)）]+)[\)）]\s*$/i);
    if (inlineMatch && hasJapaneseText(inlineMatch[1])) {
      lines.push(inlineMatch[1].trim());
      lines.push(`(Bản dịch: ${inlineMatch[2].trim()})`);
    } else {
      lines.push(rawLine);
    }
  }

  const blocks: JapaneseSentenceBlock[] = [];

  let i = 0;
  while (i < lines.length) {
    const currentLine = lines[i];

    // Only process lines that are predominantly Japanese dialogue
    if (isPredominantlyJapanese(currentLine)) {
      // Check if next line is a translation
      let translation: string | undefined = undefined;
      if (i + 1 < lines.length) {
        const nextLine = lines[i + 1];
        if (
          (nextLine.startsWith('(') && nextLine.endsWith(')')) ||
          (nextLine.startsWith('（') && nextLine.endsWith('）')) ||
          (nextLine.toLowerCase().startsWith('bản dịch:') || nextLine.toLowerCase().startsWith('dịch:')) ||
          (!hasJapaneseText(nextLine) && nextLine.length > 2 && !nextLine.startsWith('#') && !nextLine.startsWith('-') && !nextLine.startsWith('•') && !nextLine.startsWith('*'))
        ) {
          translation = nextLine
            .replace(/^[\(（]\s*(?:Bản dịch|Dịch)?\s*:?\s*/i, '')
            .replace(/[\)）]$/, '')
            .trim();
          i++; // Consume translation line
        }
      }

      // Check inline translation at the end of the current line if not found
      if (!translation) {
        const inlineTransMatch = currentLine.match(/[\(（]([^\)）]+)[\)）]$/);
        if (inlineTransMatch && !inlineTransMatch[1].includes('[') && !isPredominantlyJapanese(inlineTransMatch[1])) {
          translation = inlineTransMatch[1].replace(/^(?:Bản dịch|Dịch):\s*/i, '').trim();
        }
      }

      const tokens = tokenizeJapaneseLine(currentLine);
      blocks.push({
        tokens,
        translation,
        rawText: currentLine,
      });
    } else {
      // Regular markdown / non-dialogue line
      blocks.push({
        tokens: [{ text: currentLine }],
        rawText: currentLine,
      });
    }
    i++;
  }

  return blocks;
}

/**
 * Tokenize a Japanese line into word blocks with Furigana, Romaji, and Grammar Highlights
 */
export function tokenizeJapaneseLine(line: string): JapaneseToken[] {
  const tokens: JapaneseToken[] = [];

  // Match patterns:
  // 1. {word}[g-green] or {word}[green] or {word}[g-orange] or {word}[orange]
  // 2. <ruby>Kanji<rt>furigana</rt></ruby>
  // 3. [Kanji](furigana)
  const tokenRegex = /(\{([^\}]+)\}\[(g-green|green|g-orange|orange|particle|phrase)\])|(<ruby>([^<]+)<rt>([^<]+)<\/rt><\/ruby>)|(\[([^\]]+)\]\(([^)]+)\))/g;

  let lastIndex = 0;
  let match;

  while ((match = tokenRegex.exec(line)) !== null) {
    if (match.index > lastIndex) {
      const normalPart = line.slice(lastIndex, match.index).trim();
      if (normalPart) {
        tokens.push(...tokenizeNormalSegment(normalPart));
      }
    }

    if (match[1]) {
      // Highlighted grammar structure - unify all (green, orange) to green
      const word = match[2];

      const rubyMatch = word.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (rubyMatch) {
        const kanji = rubyMatch[1];
        const furigana = rubyMatch[2];
        tokens.push({
          text: kanji,
          furigana: furigana,
          romaji: kanaToRomaji(furigana),
          grammarHighlight: 'green',
        });
      } else {
        const vocab = COMMON_VOCAB_MAP[word];
        const furigana = vocab?.furigana || (!/[\u4E00-\u9FAF]/.test(word) ? word : undefined);
        const romaji = vocab?.romaji || kanaToRomaji(furigana || word);

        tokens.push({
          text: word,
          furigana: furigana,
          romaji: cleanRomaji(romaji) || undefined,
          grammarHighlight: 'green',
        });
      }
    } else if (match[4]) {
      // <ruby>Kanji<rt>furigana</rt></ruby>
      const kanji = match[5];
      const furigana = match[6];
      tokens.push({
        text: kanji,
        furigana: furigana,
        romaji: kanaToRomaji(furigana),
      });
    } else if (match[7]) {
      // [Kanji](furigana)
      const kanji = match[8];
      const furigana = match[9];
      tokens.push({
        text: kanji,
        furigana: furigana,
        romaji: kanaToRomaji(furigana),
      });
    }

    lastIndex = tokenRegex.lastIndex;
  }

  if (lastIndex < line.length) {
    const remaining = line.slice(lastIndex).trim();
    if (remaining) {
      tokens.push(...tokenizeNormalSegment(remaining));
    }
  }

  return tokens.length > 0 ? tokens : [{ text: line }];
}

/**
 * Split standard Japanese segment by spaces, punctuation, or known grammar units
 */
export function tokenizeNormalSegment(segment: string): JapaneseToken[] {
  // If explicit spaces exist, split by spaces
  if (segment.includes(' ')) {
    const words = segment.split(/\s+/).filter(Boolean);
    const result: JapaneseToken[] = [];
    for (const w of words) {
      result.push(...parseSingleOrCompoundWord(w));
    }
    return result;
  }

  // If no spaces, perform intelligent morphological segmenting
  return segmentJapaneseSentence(segment);
}

/**
 * Parse a single Japanese word or compound with dictionary lookup & Romaji
 */
function parseSingleOrCompoundWord(w: string): JapaneseToken[] {
  // Check markdown ruby [漢字](かんじ)
  const rubyMatch = w.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
  if (rubyMatch) {
    return [{
      text: rubyMatch[1],
      furigana: rubyMatch[2],
      romaji: kanaToRomaji(rubyMatch[2]),
    }];
  }

  // Check known vocab
  const vocab = COMMON_VOCAB_MAP[w];
  if (vocab) {
    return [{
      text: w,
      furigana: vocab.furigana,
      romaji: vocab.romaji,
      grammarHighlight: COMMON_PARTICLES.has(w) ? 'green' : null,
    }];
  }

  // Check if particle
  if (COMMON_PARTICLES.has(w)) {
    return [{
      text: w,
      romaji: kanaToRomaji(w),
      grammarHighlight: 'green',
    }];
  }

  // If pure Kana or Latin
  if (!/[\u4E00-\u9FAF]/.test(w)) {
    return [{
      text: w,
      romaji: kanaToRomaji(w) || undefined,
    }];
  }

  // Kanji present but no furigana found: DO NOT output mixed Kanji-Romaji!
  return [{
    text: w,
    furigana: undefined,
    romaji: undefined,
  }];
}

/**
 * Morphological segmentation for Japanese sentences without spaces
 */
function segmentJapaneseSentence(sentence: string): JapaneseToken[] {
  const tokens: JapaneseToken[] = [];
  let remaining = sentence;

  // Order vocab keys by length descending to match longest compounds first
  const sortedVocabKeys = Object.keys(COMMON_VOCAB_MAP).sort((a, b) => b.length - a.length);

  while (remaining.length > 0) {
    let matched = false;

    // 1. Check punctuation
    const punctMatch = remaining.match(/^([、。！？\s.,!?~])/);
    if (punctMatch) {
      tokens.push({ text: punctMatch[1] });
      remaining = remaining.slice(punctMatch[1].length);
      continue;
    }

    // 2. Check known vocab keys
    for (const key of sortedVocabKeys) {
      if (remaining.startsWith(key)) {
        const vocab = COMMON_VOCAB_MAP[key];
        tokens.push({
          text: key,
          furigana: vocab.furigana,
          romaji: vocab.romaji,
          grammarHighlight: COMMON_PARTICLES.has(key) ? 'green' : null,
        });
        remaining = remaining.slice(key.length);
        matched = true;
        break;
      }
    }
    if (matched) continue;

    // 3. Check particles (must be preceded by something or at start)
    for (const p of COMMON_PARTICLES) {
      if (remaining.startsWith(p)) {
        tokens.push({
          text: p,
          romaji: kanaToRomaji(p),
          grammarHighlight: 'green',
        });
        remaining = remaining.slice(p.length);
        matched = true;
        break;
      }
    }
    if (matched) continue;

    // 4. Kana chunk
    const kanaMatch = remaining.match(/^([\u3040-\u309F\u30A0-\u30FF]+)/);
    if (kanaMatch) {
      const kanaChunk = kanaMatch[1];
      tokens.push({
        text: kanaChunk,
        romaji: kanaToRomaji(kanaChunk) || undefined,
      });
      remaining = remaining.slice(kanaChunk.length);
      continue;
    }

    // 5. Kanji chunk fallback
    const kanjiMatch = remaining.match(/^([\u4E00-\u9FAF]+)/);
    if (kanjiMatch) {
      const kanjiChunk = kanjiMatch[1];
      tokens.push({
        text: kanjiChunk,
        furigana: undefined,
        romaji: undefined,
      });
      remaining = remaining.slice(kanjiChunk.length);
      continue;
    }

    // 6. Single character fallback
    const char = remaining[0];
    tokens.push({ text: char });
    remaining = remaining.slice(1);
  }

  return tokens.length > 0 ? tokens : [{ text: sentence }];
}

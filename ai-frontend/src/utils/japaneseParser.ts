/**
 * Japanese Interlinear Parsing & Romaji Utilities
 * Handles Furigana, Ruby annotations, Grammar Highlights, and Hepburn Romaji.
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
  'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
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

const COMMON_PARTICLES = new Set([
  'は', 'が', 'を', 'に', 'で', 'へ', 'と', 'から', 'まで',
  'も', 'ね', 'よ', 'か', 'けど', 'わ', 'の', 'や', 'し', 'ば'
]);

const COMMON_GRAMMAR_PHRASES = new Set([
  'どうぞ', 'ください', 'ありがとう', 'ございます', 'たい', 'たくない',
  'ている', 'てある', 'ておく', 'てみる', 'なければならない', 'わけではない',
  'んです', 'んだ', 'かもしれない', 'でしょう', 'と思う', 'ようになる'
]);

export interface JapaneseToken {
  text: string;
  furigana?: string;
  romaji?: string;
  grammarHighlight?: 'green' | 'orange' | null;
}

export interface JapaneseSentenceBlock {
  tokens: JapaneseToken[];
  translation?: string;
  rawText: string;
}

/**
 * Convert Kana string (Hiragana/Katakana) to standard Romaji
 */
export function kanaToRomaji(kana: string): string {
  if (!kana) return '';
  let result = '';
  let i = 0;

  while (i < kana.length) {
    // Sokuon っ / ッ (geminate consonant)
    if (kana[i] === 'っ' || kana[i] === 'ッ') {
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

    // Check two-char digraphs (e.g. しゃ, きょ)
    if (i + 1 < kana.length) {
      const two = kana.slice(i, i + 2);
      if (KANA_ROMAJI_MAP[two]) {
        result += KANA_ROMAJI_MAP[two];
        i += 2;
        continue;
      }
    }

    // Single kana
    const one = kana[i];
    if (KANA_ROMAJI_MAP[one]) {
      result += KANA_ROMAJI_MAP[one];
    } else if (one === 'ー') {
      // Long vowel extender
      const lastChar = result.slice(-1);
      if (lastChar) result += lastChar;
    } else {
      result += one;
    }
    i++;
  }

  return result;
}

/**
 * Check if text contains Japanese script (Kanji, Hiragana, Katakana)
 */
export function hasJapaneseText(text: string): boolean {
  return /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/.test(text);
}

/**
 * Speak text in Japanese using native browser Web Speech API
 */
export function speakJapaneseSpeech(text: string): void {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel(); // Stop any previous speech
  const clean = text
    .replace(/<[^>]*>/g, '')
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
    .replace(/\{([^\}]+)\}\[[^\]]+\]/g, '$1')
    .replace(/\([^\)]+\)/g, '')
    .trim();
  if (!clean) return;

  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.lang = 'ja-JP';
  utterance.rate = 0.9; // Slightly slower for language learners
  window.speechSynthesis.speak(utterance);
}

/**
 * Parse a raw text paragraph into structured Japanese Interlinear blocks
 */
export function parsePedagogicalBlocks(text: string): JapaneseSentenceBlock[] {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const blocks: JapaneseSentenceBlock[] = [];

  let i = 0;
  while (i < lines.length) {
    const currentLine = lines[i];

    // If currentLine has Japanese characters
    if (hasJapaneseText(currentLine)) {
      // Check if next line is a translation (e.g. starts with '(' or contains non-Japanese translation)
      let translation: string | undefined = undefined;
      if (i + 1 < lines.length) {
        const nextLine = lines[i + 1];
        if (
          (nextLine.startsWith('(') && nextLine.endsWith(')')) ||
          (nextLine.startsWith('（') && nextLine.endsWith('）')) ||
          (nextLine.toLowerCase().startsWith('bản dịch:') || nextLine.toLowerCase().startsWith('dịch:')) ||
          (!hasJapaneseText(nextLine) && nextLine.length > 2)
        ) {
          translation = nextLine
            .replace(/^[\(（]/, '')
            .replace(/[\)）]$/, '')
            .replace(/^(Bản dịch|Dịch):\s*/i, '')
            .trim();
          i++; // Consume translation line
        }
      }

      // Check inline translation at the end of the current line (e.g. "はい どうぞ (Của bạn đây)")
      const inlineTransMatch = currentLine.match(/[\(（]([^\)）]+)[\)）]$/);
      let japanesePart = currentLine;
      if (inlineTransMatch && !translation) {
        translation = inlineTransMatch[1].replace(/^(Bản dịch|Dịch):\s*/i, '').trim();
        japanesePart = currentLine.slice(0, inlineTransMatch.index).trim();
      }

      const tokens = tokenizeJapaneseLine(japanesePart);
      blocks.push({
        tokens,
        translation,
        rawText: currentLine,
      });
    } else {
      // Regular markdown / non-Japanese line
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
function tokenizeJapaneseLine(line: string): JapaneseToken[] {
  const tokens: JapaneseToken[] = [];

  // Match patterns:
  // 1. {word}[g-green] or {word}[green]
  // 2. {phrase}[g-orange] or {phrase}[orange]
  // 3. <ruby>Kanji<rt>furigana</rt></ruby>
  // 4. [Kanji](furigana)
  // 5. Normal text words separated by space or particles
  const tokenRegex = /(\{([^\}]+)\}\[(g-green|green|g-orange|orange|particle|phrase)\])|(<ruby>([^<]+)<rt>([^<]+)<\/rt><\/ruby>)|(\[([^\]]+)\]\(([^)]+)\))/g;

  let lastIndex = 0;
  let match;

  while ((match = tokenRegex.exec(line)) !== null) {
    // Process text preceding this match
    if (match.index > lastIndex) {
      const normalPart = line.slice(lastIndex, match.index).trim();
      if (normalPart) {
        tokens.push(...tokenizeNormalSegment(normalPart));
      }
    }

    if (match[1]) {
      // {word}[g-green] or {phrase}[g-orange]
      const word = match[2];
      const tag = match[3];
      const isGreen = tag.includes('green') || tag === 'particle';
      const isOrange = tag.includes('orange') || tag === 'phrase';

      // Check if word itself has furigana inside like [欲しい](ほしい)
      const rubyMatch = word.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (rubyMatch) {
        tokens.push({
          text: rubyMatch[1],
          furigana: rubyMatch[2],
          romaji: kanaToRomaji(rubyMatch[2]),
          grammarHighlight: isGreen ? 'green' : (isOrange ? 'orange' : null),
        });
      } else {
        tokens.push({
          text: word,
          romaji: kanaToRomaji(word),
          grammarHighlight: isGreen ? 'green' : (isOrange ? 'orange' : null),
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

  // Trailing segment
  if (lastIndex < line.length) {
    const remaining = line.slice(lastIndex).trim();
    if (remaining) {
      tokens.push(...tokenizeNormalSegment(remaining));
    }
  }

  return tokens.length > 0 ? tokens : [{ text: line }];
}

/**
 * Split standard Japanese segment by spaces or known grammar units
 */
function tokenizeNormalSegment(segment: string): JapaneseToken[] {
  // If separated by spaces, honor them
  const rawWords = segment.split(/\s+/).filter(Boolean);
  const result: JapaneseToken[] = [];

  for (const w of rawWords) {
    // Check if word has explicit markdown ruby [漢字](かんじ)
    const rubyMatch = w.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (rubyMatch) {
      result.push({
        text: rubyMatch[1],
        furigana: rubyMatch[2],
        romaji: kanaToRomaji(rubyMatch[2]),
      });
      continue;
    }

    // Check if grammar highlight
    let highlight: 'green' | 'orange' | null = null;
    if (COMMON_PARTICLES.has(w)) {
      highlight = 'green';
    } else if (COMMON_GRAMMAR_PHRASES.has(w)) {
      highlight = 'orange';
    }

    // Common words with known furigana
    const knownFurigana: Record<string, string> = {
      '欲しい': 'ほしい',
      '言葉': 'ことば',
      '文化': 'ぶんか',
      '鏡': 'かがみ',
      '心': 'こころ',
      '今日': 'きょう',
      '本日': 'ほんじつ',
      '探求': 'たんきゅう',
      '日常': 'にちじょう',
      '荒波': 'あらなみ',
      '論文': 'ろんぶん',
      '格調': 'かくちょう',
      '文体': 'ぶんたい',
      '難解': 'なんかい',
      '文法': 'ぶんぽう',
      '四字熟語': 'よじじゅくご',
      '深奥': 'しんおう',
      '質問': 'しつもん',
      '心ゆく': 'こころゆく',
      'お尋ね': 'おたずね',
      '準備': 'じゅんび',
      '私': 'わたし',
      '先生': 'せんせい',
      '学生': 'がくせい',
      '勉強': 'べんきょう',
      '日本語': 'にほんご',
      '一緒': 'いっしょ',
      '一歩': 'いっぽ',
      '静か': 'しずか',
      '一礼': 'いちれい',
      '端正': 'たんせい',
      '微笑み': 'ほほえみ',
      '浮べる': 'うかべる',
      '扉': 'とびら',
      '開く': 'ひらく'
    };

    const furigana = knownFurigana[w];
    const romaji = furigana ? kanaToRomaji(furigana) : (hasJapaneseText(w) ? kanaToRomaji(w) : undefined);

    result.push({
      text: w,
      furigana: furigana,
      romaji: romaji || undefined,
      grammarHighlight: highlight,
    });
  }

  return result;
}


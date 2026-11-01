export type Language = 'vi' | 'en' | 'ja';

export const translations: Record<Language, Record<string, string>> = {
  vi: {
    // Nav
    'nav.new_chat': 'Đoạn chat mới',
    'nav.kaiwa': 'Luyện Kaiwa (Chat)',
    'nav.sensei': 'Chỉ Dẫn Sensei',
    'nav.grammar': 'Quy Tắc Ngữ Pháp',
    'nav.overview': 'Tổng Quan Học Tập',
    'nav.settings': 'Cài Đặt Hệ Thống',

    // Header
    'header.back_to_chat': 'Quay lại Chat',
    'header.version': 'Phiên bản',
    'header.logout': 'Đăng xuất',

    // Settings tabs
    'settings.tab_profile': 'Hồ sơ',
    'settings.tab_security': 'Bảo mật',
    'settings.tab_preferences': 'Tùy chỉnh',
    'settings.tab_models': 'Mô hình AI',
    'settings.tab_api_keys': 'Khóa API',

    // Preferences content
    'settings.appearance_title': 'Tùy Chỉnh Giao Diện & Cá Nhân Hóa',
    'settings.appearance_sub': 'Tùy biến hình nền không gian học tập, độ trong suốt kính mờ, độ tối, bảng màu chủ đạo và mật độ hiển thị theo sở thích.',
    'settings.theme_mode': 'Chế độ màu giao diện (Theme Mode)',
    'settings.dark_mode': 'Dark Mode',
    'settings.dark_desc': 'Bề mặt tối trung tính dịu mắt',
    'settings.light_mode': 'Light Mode',
    'settings.light_desc': 'Bảng màu sáng tương phản cao',
    'settings.system_mode': 'Theo hệ điều hành',
    'settings.system_desc': 'Tự động đồng bộ cài đặt OS',

    'settings.accent_palette': 'Màu chủ đạo (Accent Palette)',
    'settings.accent_sub': 'Thay đổi màu các nút bấm, biểu tượng nổi bật và viền nhấn trong toàn bộ ứng dụng.',
    'settings.custom_rgb': 'Tùy chỉnh phổ màu RGB (Spectrum Slider):',

    'settings.wallpaper_title': 'Hình nền website tùy chỉnh (Custom Wallpaper)',
    'settings.wallpaper_sub': 'Cung cấp URL hình ảnh hoặc tải ảnh trực tiếp từ máy tính để làm hình nền cho không gian học tập.',
    'settings.clear_wallpaper': 'Xóa hình nền',
    'settings.upload_image': 'Tải ảnh từ máy',
    'settings.preset_label': 'Gợi ý hình nền Nhật Bản:',
    'settings.preview_label': 'Xem trước hình nền',

    'settings.bg_dim_title': 'Độ tối hình nền (Background Darkness / Dim)',
    'settings.bg_dim_sub': 'Làm tối bức ảnh nền để tăng độ tương phản giúp chữ và nội dung hội thoại rõ ràng hơn (0% - 100%).',

    'settings.layer_opacity': 'Độ đục lớp phủ (Layer Opacity)',
    'settings.layer_opacity_sub': 'Độ trong suốt của thanh điều hướng và khung nội dung trên ảnh nền (20% - 100%).',

    'settings.backdrop_blur': 'Độ mờ kính (Backdrop Blur)',
    'settings.backdrop_blur_sub': 'Hiệu ứng kính mờ (glassmorphism) làm nổi bật văn bản và hội thoại tiếng Nhật (0px - 40px).',

    'settings.font_size_title': 'Cỡ chữ & Mật độ hiển thị (Layout Density)',
    'settings.font_size_sub': 'Điều chỉnh tỉ lệ phông chữ và khoảng cách giao diện cho phù hợp với tầm nhìn.',
    'settings.font_small': 'Nhỏ (13px)',
    'settings.font_small_desc': 'Mật độ cao, hiển thị nhiều nội dung hơn',
    'settings.font_medium': 'Tiêu chuẩn (14px)',
    'settings.font_medium_desc': 'Cân bằng chuẩn',
    'settings.font_large': 'Lớn (15px)',
    'settings.font_large_desc': 'Dễ đọc, thoáng mắt',

    'settings.lang_title': 'Ngôn ngữ hiển thị (Interface Language)',
    'settings.lang_vi': 'Tiếng Việt (Mặc định)',
    'settings.lang_en': 'English',
    'settings.lang_ja': '日本語 (Japanese)',

    'settings.save_prefs': 'Lưu Thay Đổi Giao Diện',
    'settings.saving_prefs': 'Đang lưu tùy chỉnh...',
    'settings.prefs_saved_success': 'Đã lưu cấu hình tùy chỉnh giao diện thành công.',
  },

  en: {
    // Nav
    'nav.new_chat': 'New Chat',
    'nav.kaiwa': 'Kaiwa Practice (Chat)',
    'nav.sensei': 'Sensei Guidance',
    'nav.grammar': 'Grammar Rules',
    'nav.overview': 'Study Overview',
    'nav.settings': 'System Settings',

    // Header
    'header.back_to_chat': 'Back to Chat',
    'header.version': 'Version',
    'header.logout': 'Sign Out',

    // Settings tabs
    'settings.tab_profile': 'Profile',
    'settings.tab_security': 'Security',
    'settings.tab_preferences': 'Preferences',
    'settings.tab_models': 'AI Models',
    'settings.tab_api_keys': 'API Keys',

    // Preferences content
    'settings.appearance_title': 'Appearance & Personalization',
    'settings.appearance_sub': 'Customize wallpaper, glassmorphism, background darkness, accent color palette, and layout density.',
    'settings.theme_mode': 'Theme Mode',
    'settings.dark_mode': 'Dark Mode',
    'settings.dark_desc': 'Deep neutral dark surfaces',
    'settings.light_mode': 'Light Mode',
    'settings.light_desc': 'Clean high-contrast palette',
    'settings.system_mode': 'System Preference',
    'settings.system_desc': 'Follow OS preferences automatically',

    'settings.accent_palette': 'Accent Color Palette',
    'settings.accent_sub': 'Customize button colors, active indicators, and highlight borders across the app.',
    'settings.custom_rgb': 'Custom RGB Spectrum Slider:',

    'settings.wallpaper_title': 'Custom Website Wallpaper',
    'settings.wallpaper_sub': 'Provide an image URL or upload an image from your computer for your personalized learning space.',
    'settings.clear_wallpaper': 'Remove Wallpaper',
    'settings.upload_image': 'Upload Image',
    'settings.preset_label': 'Curated Japanese Presets:',
    'settings.preview_label': 'Wallpaper Preview',

    'settings.bg_dim_title': 'Background Darkness / Dim',
    'settings.bg_dim_sub': 'Darken the background image to enhance contrast for texts and conversation cards (0% - 100%).',

    'settings.layer_opacity': 'Layer Opacity',
    'settings.layer_opacity_sub': 'Opacity of surface panels and sidebar over the background image (20% - 100%).',

    'settings.backdrop_blur': 'Backdrop Blur',
    'settings.backdrop_blur_sub': 'Frosted glassmorphism effect making Japanese conversation cards sharp and readable (0px - 40px).',

    'settings.font_size_title': 'UI Font Size & Layout Density',
    'settings.font_size_sub': 'Adjust font scaling and interface spacing for comfortable reading.',
    'settings.font_small': 'Small (13px)',
    'settings.font_small_desc': 'High density, fits more content',
    'settings.font_medium': 'Medium (14px)',
    'settings.font_medium_desc': 'Balanced default',
    'settings.font_large': 'Large (15px)',
    'settings.font_large_desc': 'Easy to read, comfortable',

    'settings.lang_title': 'Interface Language',
    'settings.lang_vi': 'Tiếng Việt',
    'settings.lang_en': 'English (Default)',
    'settings.lang_ja': '日本語 (Japanese)',

    'settings.save_prefs': 'Save Preferences',
    'settings.saving_prefs': 'Saving preferences...',
    'settings.prefs_saved_success': 'Preferences updated successfully.',
  },

  ja: {
    // Nav
    'nav.new_chat': '新しいチャット',
    'nav.kaiwa': '会話練習 (チャット)',
    'nav.sensei': '先生の指導',
    'nav.grammar': '文法ルール',
    'nav.overview': '学習概要',
    'nav.settings': 'システム設定',

    // Header
    'header.back_to_chat': 'チャットに戻る',
    'header.version': 'バージョン',
    'header.logout': 'ログアウト',

    // Settings tabs
    'settings.tab_profile': 'プロフィール',
    'settings.tab_security': 'セキュリティ',
    'settings.tab_preferences': '環境設定',
    'settings.tab_models': 'AIモデル',
    'settings.tab_api_keys': 'APIキー',

    // Preferences content
    'settings.appearance_title': '外観とパーソナライズ',
    'settings.appearance_sub': '学習スペースの壁紙、すりガラス効果、背景の暗さ、アクセントカラー、表示密度をお好みに合わせてカスタマイズします。',
    'settings.theme_mode': 'テーマモード',
    'settings.dark_mode': 'ダークモード',
    'settings.dark_desc': '目に優しいニュートラルダーク',
    'settings.light_mode': 'ライトモード',
    'settings.light_desc': '高コントラストなクリーンパレット',
    'settings.system_mode': 'システム同期',
    'settings.system_desc': 'OSの設定に自動追従',

    'settings.accent_palette': 'アクセントカラーパレット',
    'settings.accent_sub': 'ボタン、ハイライト、枠線のアクセントカラーをアプリケーション全体で変更します。',
    'settings.custom_rgb': 'カスタムRGBスペクトルスライダー:',

    'settings.wallpaper_title': 'カスタム壁紙',
    'settings.wallpaper_sub': '画像URLを入力するか、パソコンから画像をアップロードして自分専用の学習スペースを作成できます。',
    'settings.clear_wallpaper': '壁紙を削除',
    'settings.upload_image': '画像をアップロード',
    'settings.preset_label': 'おすすめの日本風壁紙:',
    'settings.preview_label': '壁紙プレビュー',

    'settings.bg_dim_title': '背景の暗さ (ディム)',
    'settings.bg_dim_sub': '文字や会話カードのコントラストを高めるために背景画像を暗くします (0%〜100%)。',

    'settings.layer_opacity': 'レイヤー不透明度',
    'settings.layer_opacity_sub': '壁紙の上のパネルやサイドバーの不透明度 (20%〜100%)。',

    'settings.backdrop_blur': 'すりガラスぼかし効果',
    'settings.backdrop_blur_sub': '日本語のテキストを読みやすくするすりガラス効果 (0px〜40px)。',

    'settings.font_size_title': 'フォントサイズと表示密度',
    'settings.font_size_sub': '視認性に合わせてフォントサイズと間隔を調整します。',
    'settings.font_small': '小 (13px)',
    'settings.font_small_desc': '高密度、より多くの内容を表示',
    'settings.font_medium': '標準 (14px)',
    'settings.font_medium_desc': 'バランスの取れた標準サイズ',
    'settings.font_large': '大 (15px)',
    'settings.font_large_desc': '読みやすく快適な間隔',

    'settings.lang_title': '表示言語 (Interface Language)',
    'settings.lang_vi': 'Tiếng Việt (ベトナム語)',
    'settings.lang_en': 'English (英語)',
    'settings.lang_ja': '日本語 (Japanese)',

    'settings.save_prefs': '設定を保存',
    'settings.saving_prefs': '保存中...',
    'settings.prefs_saved_success': '設定が正常に保存されました。',
  }
};

export function getTranslation(lang: Language, key: string): string {
  const dict = translations[lang] || translations.vi;
  return dict[key] || translations.vi[key] || key;
}

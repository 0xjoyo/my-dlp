"""
Internationalization (i18n) Utility
Handles multiple languages for the UI.
"""
from src.utils.config_manager import load_config

# Dictionary of all translated strings
TRANSLATIONS = {
    # ── Sidebar ──
    "app_name": {"ar": "my-dlp", "en": "my-dlp"},
    "nav_downloader": {"ar": "⬇  التنزيل", "en": "⬇  Downloader"},
    "nav_spotify": {"ar": "🎵  بحث Spotify", "en": "🎵  Spotify Search"},
    "nav_lyrics": {"ar": "🎤  الكلمات المتزامنة", "en": "🎤  Synced Lyrics"},
    "nav_settings": {"ar": "⚙  الإعدادات", "en": "⚙  Settings"},
    "version_info": {"ar": "v1.0.0  •  مدعوم بـ yt-dlp", "en": "v1.0.0  •  Powered by yt-dlp"},

    # ── Downloader Tab ──
    "dl_title": {"ar": "⬇  التنزيل", "en": "⬇  Downloader"},
    "dl_subtitle": {"ar": "يوتيوب • سبوتيفاي • ساوندكلاود • تيك توك والمزيد", "en": "YouTube • Spotify • SoundCloud • TikTok & more"},
    "card_url": {"ar": "🔗  الرابط", "en": "🔗  URL"},
    "url_placeholder": {"ar": "الصق رابط الفيديو أو البلاي ليست هنا...", "en": "Paste video or playlist URL here..."},
    "btn_paste": {"ar": "📋 لصق", "en": "📋 Paste"},
    "btn_fetch": {"ar": "🔍 جلب المعلومات", "en": "🔍 Fetch Info"},
    
    "lbl_views": {"ar": "مشاهدة", "en": "views"},
    "lbl_playlist_badge": {"ar": "🎵 قائمة تشغيل • {count} عنصر", "en": "🎵 Playlist • {count} items"},
    
    "card_options": {"ar": "🎛  خيارات التنزيل", "en": "🎛  Download Options"},
    "lbl_type": {"ar": "النوع", "en": "Type"},
    "opt_video": {"ar": "🎬 فيديو", "en": "🎬 Video"},
    "opt_audio": {"ar": "🎵 صوت MP3", "en": "🎵 Audio MP3"},
    "lbl_quality": {"ar": "الجودة", "en": "Quality"},
    "lbl_folder": {"ar": "مجلد الحفظ", "en": "Save Folder"},
    
    "card_progress": {"ar": "📊  التقدم", "en": "📊  Progress"},
    "prog_ready": {"ar": "جاهز للتنزيل", "en": "Ready to download"},
    "btn_download": {"ar": "⬇  تنزيل الآن", "en": "⬇  Download Now"},
    
    "err_invalid_url": {"ar": "❌ رابط غير صالح", "en": "❌ Invalid URL"},
    "msg_fetching": {"ar": "⏳ جاري جلب المعلومات...", "en": "⏳ Fetching information..."},
    "msg_fetching_plat": {"ar": "⏳ جاري جلب المعلومات من {platform}...", "en": "⏳ Fetching from {platform}..."},
    "msg_fetch_done": {"ar": "✅ تم جلب المعلومات", "en": "✅ Information fetched"},
    "err_no_url": {"ar": "❌ يرجى إدخال رابط أولاً", "en": "❌ Please enter a URL first"},
    "err_invalid_folder": {"ar": "❌ مجلد الحفظ غير صالح", "en": "❌ Invalid save folder"},
    "msg_downloading": {"ar": "⏳ جاري التنزيل...", "en": "⏳ Downloading..."},
    "msg_processing": {"ar": "⚙️ جاري المعالجة والتحويل...", "en": "⚙️ Processing & converting..."},
    "msg_dl_done": {"ar": "✅ تم التنزيل بنجاح!", "en": "✅ Download complete!"},

    # ── Spotify Tab ──
    "sp_title": {"ar": "🎵  بحث Spotify", "en": "🎵  Spotify Search"},
    "sp_subtitle": {"ar": "ابحث عن أغانيك المفضلة وحملها مباشرة من يوتيوب", "en": "Search tracks and download directly via YouTube"},
    "sp_card_search": {"ar": "🔍  البحث", "en": "🔍  Search"},
    "sp_placeholder": {"ar": "ابحث عن أغنية، فنان، أو الصق رابط من سبوتيفاي...", "en": "Search track, artist, or paste Spotify link..."},
    "btn_search": {"ar": "بحث", "en": "Search"},
    "sp_card_results": {"ar": "📑  نتائج البحث", "en": "📑  Search Results"},
    "btn_dl_track": {"ar": "⬇ تنزيل كصوت", "en": "⬇ Download Audio"},
    "btn_dl_playlist": {"ar": "⬇ تنزيل البلاي ليست بالكامل", "en": "⬇ Download Full Playlist"},
    "msg_sp_no_keys": {"ar": "⚠️ يرجى إضافة Spotify Client ID و Secret من الإعدادات.", "en": "⚠️ Please add Spotify Client ID and Secret in Settings."},
    "msg_sp_searching": {"ar": "⏳ جاري البحث في سبوتيفاي...", "en": "⏳ Searching Spotify..."},
    "msg_sp_no_results": {"ar": "❌ لم يتم العثور على نتائج.", "en": "❌ No results found."},
    "lbl_tracks_count": {"ar": "{count} مسار", "en": "{count} tracks"},

    # ── Lyrics Tab ──
    "lyr_title": {"ar": "🎤  الكلمات المتزامنة (Karaoke)", "en": "🎤  Synced Lyrics (Karaoke)"},
    "lyr_subtitle": {"ar": "اختر ملفاً صوتياً لعرض الكلمات متزامنة مع التشغيل", "en": "Select an audio file to view synced lyrics"},
    "card_player": {"ar": "▶️  المشغل", "en": "▶️  Player"},
    "btn_choose_audio": {"ar": "📁  اختر ملف صوتي", "en": "📁  Choose Audio File"},
    "lyr_no_file": {"ar": "لم يتم اختيار ملف", "en": "No file selected"},
    "btn_play": {"ar": "▶", "en": "▶"},
    "btn_pause": {"ar": "⏸", "en": "⏸"},
    "card_lyrics": {"ar": "📝  الكلمات", "en": "📝  Lyrics"},
    "lyr_wait": {"ar": "الكلمات ستظهر هنا...", "en": "Lyrics will appear here..."},
    "lyr_searching": {"ar": "⏳ جاري البحث عن كلمات متزامنة عبر الإنترنت...", "en": "⏳ Searching for synced lyrics online..."},
    "lyr_not_found": {"ar": "❌ لم يتم العثور على كلمات متزامنة لهذه الأغنية.", "en": "❌ No synced lyrics found for this song."},

    # ── Settings Tab ──
    "set_title": {"ar": "⚙  الإعدادات", "en": "⚙  Settings"},
    "set_subtitle": {"ar": "تخصيص مظهر البرنامج وإعدادات التنزيل", "en": "Customize app appearance and download settings"},
    
    "card_dl_set": {"ar": "📁  إعدادات التنزيل", "en": "📁  Download Settings"},
    "set_dl_path": {"ar": "مجلد التنزيل الافتراضي", "en": "Default Download Folder"},
    "set_vid_fmt": {"ar": "تنسيق الفيديو الافتراضي", "en": "Default Video Format"},
    "set_aud_fmt": {"ar": "تنسيق الصوت الافتراضي", "en": "Default Audio Format"},
    "btn_browse": {"ar": "📁 استعراض", "en": "📁 Browse"},
    "set_ffmpeg": {"ar": "مسار ffmpeg (اختياري — إذا لم يكن في PATH)", "en": "ffmpeg path (Optional - if not in PATH)"},
    "set_ffmpeg_ph": {"ar": "مثال: C:\\ffmpeg\\bin\\ffmpeg.exe", "en": "e.g., C:\\ffmpeg\\bin\\ffmpeg.exe"},
    "chk_thumb": {"ar": "تضمين الصورة المصغرة في الملف الصوتي", "en": "Embed thumbnail in audio file"},
    "chk_meta": {"ar": "تضمين بيانات الميتاداتا في الملف", "en": "Embed metadata in file"},
    
    "card_sp_set": {"ar": "🎵  Spotify API", "en": "🎵  Spotify API"},
    "sp_info_lbl": {"ar": "أنشئ تطبيقاً مجانياً على developer.spotify.com وأدخل بياناته هنا:", "en": "Create a free app on developer.spotify.com and enter details here:"},
    
    "card_lyr_set": {"ar": "🎤  إعدادات الكلمات", "en": "🎤  Lyrics Settings"},
    "set_lyr_prov": {"ar": "مزود الكلمات المفضّل", "en": "Preferred Lyrics Provider"},
    
    "card_app_set": {"ar": "🎨  المظهر واللغة", "en": "🎨  Appearance & Language"},
    "set_theme": {"ar": "وضع المظهر", "en": "Appearance Mode"},
    "set_lang": {"ar": "لغة واجهة البرنامج", "en": "Interface Language"},
    "lang_ar": {"ar": "العربية", "en": "Arabic"},
    "lang_en": {"ar": "English", "en": "English"},
    
    "btn_save": {"ar": "💾  حفظ الإعدادات", "en": "💾  Save Settings"},
    "msg_saved": {"ar": "✅ تم حفظ الإعدادات بنجاح!", "en": "✅ Settings saved successfully!"},
    "msg_save_err": {"ar": "❌ فشل حفظ الإعدادات", "en": "❌ Failed to save settings"},
}

def get_text(key: str, **kwargs) -> str:
    """
    Returns the translated string for the given key based on current config language.
    Pass kwargs to format strings like {count} or {platform}.
    """
    config = load_config()
    lang = config.get("language", "ar")
    if lang not in ["ar", "en"]:
        lang = "ar"
        
    text_dict = TRANSLATIONS.get(key, {})
    text = text_dict.get(lang, key)
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
            
    return text

def _(key: str, **kwargs) -> str:
    """Shorthand for get_text."""
    return get_text(key, **kwargs)

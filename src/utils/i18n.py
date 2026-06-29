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
    "nav_history": {"ar": "🕒  سجل التحميلات", "en": "🕒  Download History"},
    "nav_settings": {"ar": "⚙  الإعدادات", "en": "⚙  Settings"},
    "nav_stats":    {"ar": "📊  الإحصائيات", "en": "📊  Statistics"},
    "version_info": {"ar": "v1.0.0  •  مدعوم بـ yt-dlp", "en": "v1.0.0  •  Powered by yt-dlp"},
    
    # ── History Tab ──
    "hist_subtitle": {"ar": "سجل بكل الملفات اللي تم تنزيلها", "en": "Log of all downloaded files"},
    "hist_search_ph": {"ar": "🔍 بحث في السجل...", "en": "🔍 Search history..."},
    "hist_all":        {"ar": "الكل", "en": "All"},
    "btn_clear_hist": {"ar": "🗑 مسح السجل", "en": "🗑 Clear History"},
    "hist_empty": {"ar": "السجل فارغ حالياً.", "en": "History is currently empty."},
    "btn_open_folder": {"ar": "📁 فتح المجلد", "en": "📁 Open Folder"},

    # ── Downloader / Batch / Tag Editor ──
    "dl_batch_hint": {"ar": "يمكنك لصق أكثر من رابط (كل رابط في سطر)", "en": "You can paste multiple links (one per line)"},
    "lbl_tag_title": {"ar": "اسم الأغنية:", "en": "Title:"},
    "lbl_tag_artist": {"ar": "الفنان:", "en": "Artist:"},
    
    # ── Settings / Updater ──
    "btn_update_ytdlp": {"ar": "🔄 تحديث yt-dlp", "en": "🔄 Update yt-dlp"},
    "msg_updating": {"ar": "⏳ جاري التحديث...", "en": "⏳ Updating..."},
    "msg_update_done": {"ar": "✅ تم التحديث بنجاح!", "en": "✅ Update complete!"},
    "msg_update_err": {"ar": "❌ فشل التحديث", "en": "❌ Update failed"},
    
    # ── Mini Player ──
    "btn_mini_player": {"ar": "🗔 المشغل المصغر", "en": "🗔 Mini Player"},
    "btn_close_mini": {"ar": "❌ إغلاق", "en": "❌ Close"},

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
    "set_accent": {"ar": "لون التمييز:", "en": "Accent Color:"},
    "set_sub":   {"ar": "📜  تحميل الترجمة مع الفيديو", "en": "📜  Download subtitles with video"},
    "set_clip":  {"ar": "📋  مراقبة الحافظة لروابط يوتيوب", "en": "📋  Watch clipboard for YouTube URLs"},
    "set_lang": {"ar": "لغة واجهة البرنامج", "en": "Interface Language"},
    "lang_ar": {"ar": "العربية", "en": "Arabic"},
    "lang_en": {"ar": "English", "en": "English"},
    
    "btn_save": {"ar": "💾  حفظ الإعدادات", "en": "💾  Save Settings"},
    "msg_saved": {"ar": "✅ تم حفظ الإعدادات بنجاح!", "en": "✅ Settings saved successfully!"},
    "msg_save_err": {"ar": "❌ فشل حفظ الإعدادات", "en": "❌ Failed to save settings"},
    
    # ── Speed Limiter ──
    "set_speed_limit": {"ar": "حد السرعة (KB/s — 0 = بلا حدود)", "en": "Speed Limit (KB/s — 0 = unlimited)"},
    "set_fn_template": {"ar": "📝  تنسيق اسم الملف:", "en": "📝  File name template:"},
    "set_fn_vars":     {"ar": "متغيرات متاحة: %(title)s, %(uploader)s, %(id)s, %(ext)s", "en": "Variables: %(title)s, %(uploader)s, %(id)s, %(ext)s"},

    # ── Statistics ──
    "stats_subtitle":     {"ar": "إحصائيات التنزيلات واستخدام التخزين", "en": "Download stats and storage usage"},
    "card_stats_overview": {"ar": "📊  نظرة عامة", "en": "📊  Overview"},
    "card_stats_recent":   {"ar": "🕐  آخر التنزيلات", "en": "🕐  Recent Downloads"},
    "stats_total":         {"ar": "إجمالي التنزيلات:", "en": "Total Downloads:"},
    "stats_videos":        {"ar": "فيديو:", "en": "Video:"},
    "stats_audio":         {"ar": "صوت:", "en": "Audio:"},
    "stats_storage":       {"ar": "المساحة المستخدمة:", "en": "Storage Used:"},
    "stats_date":          {"ar": "التاريخ", "en": "Date"},
    "stats_file":          {"ar": "الملف", "en": "File"},

    # ── Presets ──
    "card_presets":    {"ar": "⚡  إعدادات سريعة", "en": "⚡  Quick Presets"},
    "preset_mp3":      {"ar": "🎵 MP3", "en": "🎵 MP3"},
    "preset_hd":       {"ar": "🎬 HD", "en": "🎬 HD"},
    "preset_4k":       {"ar": "🎬 4K", "en": "🎬 4K"},
    "preset_best_audio":{"ar": "🎧 أقصى جودة صوت", "en": "🎧 Hi-Q Audio"},

    # ── Search ──
    "dl_search":         {"ar": "بحث", "en": "Search"},
    "dl_search_ph":      {"ar": "ابحث في يوتيوب…", "en": "Search YouTube…"},
    "dl_search_results": {"ar": "نتائج البحث", "en": "Search Results"},
    "dl_search_paste":   {"ar": "اختيار", "en": "Select"},
    "msg_searching":     {"ar": "جاري البحث…", "en": "Searching…"},
    "err_no_results":    {"ar": "لا توجد نتائج", "en": "No results found"},

    # ── Playlist browser ──
    "dl_pl_title":    {"ar": "متصفح قائمة التشغيل", "en": "Playlist Browser"},
    "dl_pl_count":    {"ar": "{count} فيديو في القائمة", "en": "{count} videos in playlist"},
    "dl_pl_sel_all":  {"ar": "اختيار الكل", "en": "Select All"},
    "dl_pl_unsel_all":{"ar": "إلغاء الكل", "en": "Deselect All"},

    # ── Duplicate Check ──
    "dup_title": {"ar": "⚠️  ملف موجود", "en": "⚠️  File Exists"},
    "dup_warn":  {"ar": "الملفات دي موجودة قبل كده: \n{files}\n\nهل تريد تنزيلها تاني وتجاوز القديم؟", "en": "These files already exist:\n{files}\n\nDownload again and overwrite?"},

    # ── Export ──
    "btn_export_csv": {"ar": "📥  تصدير CSV", "en": "📥  Export CSV"},
    "msg_export_done": {"ar": "✅ تم تصدير السجل", "en": "✅ History exported"},

    # ── Keyboard shortcuts ──
    "key_title": {"ar": "⌨  اختصارات لوحة المفاتيح", "en": "⌨  Keyboard Shortcuts"},
    "key_list":  {"ar": "Ctrl+1-7 → التبديل بين التبويبات\nCtrl+D    → التحميل\nCtrl+V    → لصق الرابط\nCtrl+U    → التحقق من التحديثات\nCtrl+/    → إظهار الاختصارات\nCtrl+L    → نقل التركيز لصندوق تحميل", "en": "Ctrl+1-7 → Switch tabs\nCtrl+D    → Download tab\nCtrl+V    → Paste URL\nCtrl+U    → Check for updates\nCtrl+/    → Show shortcuts\nCtrl+L    → Focus download box"},
    
    # ── Maintenance ──
    "card_maintenance": {"ar": "🛠  الصيانة والتحديثات", "en": "🛠  Maintenance & Updates"},
    
    # ── Converter Tab ──
    "nav_converter": {"ar": "🔄  محول الصوت", "en": "🔄  Audio Converter"},
    "conv_title": {"ar": "🔄  محول الصوتيات", "en": "🔄  Audio Converter"},
    "conv_subtitle": {"ar": "حوّل ملفاتك الصوتية بين الصيغ المختلفة بسهولة", "en": "Convert your audio files between formats easily"},
    "conv_card_input": {"ar": "📂  الملف المصدر", "en": "📂  Source File"},
    "btn_choose_file": {"ar": "📁  اختر ملف", "en": "📁  Choose File"},
    "conv_no_file": {"ar": "لم يتم اختيار ملف", "en": "No file selected"},
    "conv_card_output": {"ar": "🎯  إعدادات الإخراج", "en": "🎯  Output Settings"},
    "conv_out_format": {"ar": "صيغة الإخراج", "en": "Output Format"},
    "conv_out_quality": {"ar": "الجودة", "en": "Quality"},
    "btn_convert": {"ar": "🔄  تحويل الآن", "en": "🔄  Convert Now"},
    "conv_ready": {"ar": "جاهز للتحويل", "en": "Ready to convert"},
    "conv_converting": {"ar": "⏳ جاري التحويل...", "en": "⏳ Converting..."},
    "conv_done": {"ar": "✅ تم التحويل بنجاح!", "en": "✅ Conversion complete!"},
    "conv_err": {"ar": "❌ فشل التحويل", "en": "❌ Conversion failed"},
    
    # ── Drag & Drop ──
    "drag_drop_hint": {"ar": "🖱️ اسحب الروابط هنا مباشرة", "en": "🖱️ Drag & drop links here"},

    # ── Spotify Search History ──
    "sp_recent_searches": {"ar": "عمليات البحث الأخيرة", "en": "Recent searches"},
    "sp_clear_history":  {"ar": "🗑 مسح السجل", "en": "🗑 Clear history"},
    "sp_no_history":     {"ar": "ما فيه عمليات بحث سابقة.", "en": "No recent searches yet."},

    # ── Update Dialog (v1.2.0) ──
    "upd_dialog_title": {"ar": "تحديث جديد متاح", "en": "Update Available"},
    "upd_title":         {"ar": "🎉 يوجد إصدار جديد من my-dlp", "en": "A new my-dlp version is available"},
    "upd_subtitle":      {"ar": "الإصدار الحالي: {current}  •  الإصدار الجديد: {latest}",
                          "en": "Current version: {current}  •  Latest version: {latest}"},
    "upd_release_label": {"ar": "الإصدار:", "en": "Release:"},
    "upd_no_notes":      {"ar": "لا توجد ملاحظات لهذا الإصدار.", "en": "No release notes for this version."},
    "upd_btn_update":    {"ar": "⬇  تحديث الآن", "en": "⬇  Update Now"},
    "upd_btn_later":     {"ar": "⏰ لاحقاً", "en": "⏰ Later"},
    "upd_btn_skip":      {"ar": "🚫 تجاهل هذا الإصدار", "en": "🚫 Skip this version"},

    # ── In-app download & install ──
    "upd_btn_dl_install": {"ar": "📥 تنزيل وتثبيت", "en": "📥 Download & Install"},
    "upd_dl_status_downloading": {"ar": "يتم تنزيل التحديث... {downloaded} / {total}", "en": "Downloading update... {downloaded} / {total}"},
    "upd_dl_status_verifying": {"ar": "يتم التحقق من التحديث...", "en": "Verifying download..."},
    "upd_dl_status_running": {"ar": "يتم تشغيل المثبت...", "en": "Starting installer..."},
    "upd_dl_confirm_close": {"ar": "التحديث جاهز للتثبيت. سيتم إغلاق البرنامج لتثبيت التحديث.\n\nهل تريد المتابعة؟", "en": "The update is ready to install. The app will close to apply the update.\n\nDo you want to continue?"},
    "upd_dl_confirm_title": {"ar": "تأكيد التثبيت", "en": "Confirm Installation"},
    "upd_dl_error": {"ar": "فشل التنزيل: {error}", "en": "Download failed: {error}"},
    "upd_dl_retry": {"ar": "إعادة المحاولة", "en": "Retry"},
    "upd_dl_btn_yes": {"ar": "نعم، قم بالتثبيت", "en": "Yes, Install"},
    "upd_dl_btn_no": {"ar": "إلغاء", "en": "Cancel"},

    # ── Sidebar update badge ──
    "upd_badge_tooltip": {"ar": "يوجد تحديث جديد", "en": "Update available"},

    # ── System tray ──
    "tray_show":        {"ar": "إظهار النافذة", "en": "Show Window"},
    "tray_hide":        {"ar": "إخفاء النافذة", "en": "Hide Window"},
    "tray_check_update":{"ar": "🔄 التحقق من التحديثات", "en": "🔄 Check for Updates"},
    "tray_quit":        {"ar": "❌ إغلاق البرنامج", "en": "❌ Quit my-dlp"},
    "tray_running_in":  {"ar": "my-dlp يعمل في الخلفية", "en": "my-dlp is running in the background"},

    # ── YouTube Account / Cookies ──
    "card_yt_account":  {"ar": "حساب يوتيوب", "en": "YouTube Account"},
    "yt_auth_note":     {"ar": "سجّل الدخول ليوتيوب عشان تشوف فيديوهات 18+ أو المحتوى المحدود. اختار متصفح أو ملف cookies.", "en": "Sign in to YouTube for age-restricted or private content. Choose a browser or a cookies.txt file."},
    "yt_cookies_browser": {"ar": "استخراج الكوكيز من المتصفح", "en": "Extract cookies from browser"},
    "yt_cookies_browser_none": {"ar": "بدون", "en": "None"},
    "yt_cookies_file":  {"ar": "ملف cookies.txt", "en": "cookies.txt file"},
    "yt_cookies_file_ph": {"ar": "اختر ملف cookies.txt...", "en": "Select cookies.txt..."},
    "yt_cookies_browse": {"ar": "📂 اختيار ملف", "en": "📂 Browse"},
    "yt_cookies_clear":  {"ar": "🗑 مسح", "en": "🗑 Clear"},
    "yt_auth_ok":       {"ar": "✅ تم تفعيل الكوكيز", "en": "✅ Cookies configured"},
    "yt_auth_none":     {"ar": "⚠️ لم يتم تفعيل الكوكيز", "en": "⚠️ No cookies configured"},
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

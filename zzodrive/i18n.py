"""Simple i18n for zzoDrive."""


TRANSLATIONS = {
    "en": {
        # Sidebar
        "files": "Files",
        "upload": "Upload",
        "settings": "Settings",
        "setup": "Setup",
        "stat_files": "Files",
        "stat_size": "Size",
        "stat_encrypted": "Encrypted",

        # Setup page
        "welcome": "Welcome to zzoDrive",
        "welcome_sub": "Turn your Telegram into a personal cloud drive.",
        "step1_title": "Create a bot",
        "step1_desc": "Message @BotFather on Telegram, send /newbot, and copy the token.",
        "step2_title": "Create a private channel",
        "step2_desc": "Create a channel, add your bot as an admin.",
        "step3_title": "Get the channel ID",
        "step3_desc": "Forward a message from the channel to @username_to_id_bot.",
        "label_token": "Bot token",
        "label_channel": "Channel ID",
        "label_password": "Encryption password",
        "label_password_optional": "(optional)",
        "placeholder_password": "leave empty to skip",
        "btn_save_connect": "Save & Connect",

        # Dashboard
        "my_files": "My Files",
        "search_placeholder": "Search files...",
        "loading": "Loading files...",
        "no_files": "No files yet. Click Upload to get started.",
        "loading_short": "Loading...",
        "encrypted_badge": "Encrypted",

        # Upload modal
        "upload_title": "Upload files",
        "drop_title": "Drop files here",
        "drop_sub": "or click to browse",
        "encrypt_toggle": "Encrypt before upload",
        "status_waiting": "waiting...",
        "status_uploading": "uploading...",
        "status_done": "done",
        "status_failed": "failed",
        "toast_upload_done": "Upload complete",

        # Settings modal
        "settings_title": "Settings",
        "settings_pwd_title": "Encryption password",
        "settings_pwd_desc": "Used to encrypt and decrypt sensitive files.",
        "settings_pwd_placeholder": "Enter new password",
        "settings_pwd_set": "(set)",
        "btn_save": "Save",
        "btn_clear_pwd": "Clear password",
        "settings_danger_title": "Danger zone",
        "settings_danger_desc": "Reset the local index (does not delete Telegram files).",
        "btn_reset": "Reset index",

        # Toasts
        "toast_pwd_saved": "Password saved",
        "toast_pwd_cleared": "Password cleared",
        "toast_file_deleted": "File deleted",
        "toast_index_reset": "Index reset",
        "confirm_delete": "Delete this file permanently?",
        "confirm_clear_pwd": "Clear encryption password?",
        "confirm_reset": "Reset local index? Files on Telegram will NOT be deleted.",

        # Misc
        "proxy": "Proxy",
        "proxy_title": "Proxy settings",
        "proxy_current": "Current proxy",
        "proxy_change": "Change proxy",
        "proxy_help": "Enter a proxy URL. This affects uploads and downloads.",
        "proxy_help_title": "Supported formats",
        "btn_test": "Test connection",
        "btn_clear_proxy": "Remove proxy",
        "toast_proxy_saved": "Proxy saved and tested",
        "toast_proxy_cleared": "Proxy removed",
        "toast_proxy_test_ok": "Connection OK",
        "toast_proxy_test_fail": "Connection failed",
        "confirm_clear_proxy": "Remove proxy?",
        "download_title": "Downloading",
        "dl_preparing": "Preparing…",
        "dl_done": "Done! Saving file…",
        "dl_error": "Download failed",
        "proxy_enabled": "Enable proxy",
        "proxy_enabled_help": "Turn the proxy on or off without deleting its address.",
        "about": "About",
        "about_role": "Creator & Developer",
        "about_project": "About the project",
        "about_version": "Version",
        "about_license": "License",
        "about_support": "Support the project",
        "about_buy_coffee": "Buy me a coffee",
        "about_contribute": "Contribute",
        "about_contribute_text": "Found a bug or have a feature idea? Contributions are welcome!",
        "about_report_bug": "Report a bug",
        "lang_switch": "فارسی",
        "version": "Version",
    },
    "fa": {
        # Sidebar
        "files": "فایل‌ها",
        "upload": "آپلود",
        "settings": "تنظیمات",
        "setup": "راه‌اندازی",
        "stat_files": "تعداد فایل",
        "stat_size": "حجم",
        "stat_encrypted": "رمز شده",

        # Setup page
        "welcome": "به zzoDrive خوش آمدید",
        "welcome_sub": "تلگرام خود را به یک درایو شخصی تبدیل کنید.",
        "step1_title": "یک ربات بسازید",
        "step1_desc": "در تلگرام به @BotFather پیام دهید، /newbot بفرستید و توکن را کپی کنید.",
        "step2_title": "یک کانال خصوصی بسازید",
        "step2_desc": "یک کانال بسازید و ربات را به عنوان ادمین اضافه کنید.",
        "step3_title": "آیدی کانال را بگیرید",
        "step3_desc": "یک پیام از کانال را به @username_to_id_bot فوروارد کنید.",
        "label_token": "توکن ربات",
        "label_channel": "آیدی کانال",
        "label_password": "رمز رمزنگاری",
        "label_password_optional": "(اختیاری)",
        "placeholder_password": "برای رد کردن خالی بگذارید",
        "btn_save_connect": "ذخیره و اتصال",

        # Dashboard
        "my_files": "فایل‌های من",
        "search_placeholder": "جستجوی فایل‌ها...",
        "loading": "در حال بارگذاری...",
        "no_files": "هنوز فایلی ندارید. روی دکمه‌ی آپلود بزنید.",
        "loading_short": "در حال بارگذاری...",
        "encrypted_badge": "رمز شده",

        # Upload modal
        "upload_title": "آپلود فایل‌ها",
        "drop_title": "فایل‌ها را اینجا رها کنید",
        "drop_sub": "یا کلیک کنید",
        "encrypt_toggle": "قبل از آپلود رمزنگاری شود",
        "status_waiting": "در انتظار...",
        "status_uploading": "در حال آپلود...",
        "status_done": "انجام شد",
        "status_failed": "خطا",
        "toast_upload_done": "آپلود کامل شد",

        # Settings modal
        "settings_title": "تنظیمات",
        "settings_pwd_title": "رمز رمزنگاری",
        "settings_pwd_desc": "برای رمزنگاری و رمزگشایی فایل‌های حساس استفاده می‌شود.",
        "settings_pwd_placeholder": "رمز جدید را وارد کنید",
        "settings_pwd_set": "(تنظیم شده)",
        "btn_save": "ذخیره",
        "btn_clear_pwd": "پاک کردن رمز",
        "settings_danger_title": "منطقه‌ی خطر",
        "settings_danger_desc": "ریست کردن ایندکس محلی (فایل‌های تلگرام پاک نمی‌شوند).",
        "btn_reset": "ریست ایندکس",

        # Toasts
        "toast_pwd_saved": "رمز ذخیره شد",
        "toast_pwd_cleared": "رمز پاک شد",
        "toast_file_deleted": "فایل حذف شد",
        "toast_index_reset": "ایندکس ریست شد",
        "confirm_delete": "این فایل برای همیشه حذف شود؟",
        "confirm_clear_pwd": "رمز رمزنگاری پاک شود؟",
        "confirm_reset": "ایندکس محلی ریست شود؟ فایل‌های تلگرام پاک نمی‌شوند.",

        # Misc
        "proxy": "پروکسی",
        "proxy_title": "تنظیمات پروکسی",
        "proxy_current": "پروکسی فعلی",
        "proxy_change": "تغییر پروکسی",
        "proxy_help": "آدرس پروکسی را وارد کنید. روی آپلود و دانلود اثر می‌گذارد.",
        "proxy_help_title": "فرمت‌های پشتیبانی‌شده",
        "btn_test": "تست اتصال",
        "btn_clear_proxy": "حذف پروکسی",
        "toast_proxy_saved": "پروکسی ذخیره و تست شد",
        "toast_proxy_cleared": "پروکسی حذف شد",
        "toast_proxy_test_ok": "اتصال برقرار است",
        "toast_proxy_test_fail": "اتصال برقرار نشد",
        "confirm_clear_proxy": "پروکسی حذف شود؟",
        "download_title": "در حال دانلود",
        "dl_preparing": "در حال آماده‌سازی...",
        "dl_done": "کامل شد! در حال ذخیره فایل...",
        "dl_error": "دانلود ناموفق بود",
        "proxy_enabled": "فعال بودن پروکسی",
        "proxy_enabled_help": "پروکسی را بدون حذف آدرس، روشن یا خاموش کنید.",
        "about": "درباره",
        "about_role": "سازنده و توسعه‌دهنده",
        "about_project": "درباره پروژه",
        "about_version": "نسخه",
        "about_license": "مجوز",
        "about_support": "حمایت از پروژه",
        "about_buy_coffee": "یه قهوه مهمونم کن",
        "about_contribute": "مشارکت",
        "about_contribute_text": "باگ پیدا کردی یا ایده‌ای داری؟ خوشحال می‌شم کمک کنی!",
        "about_report_bug": "گزارش باگ",
        "lang_switch": "English",
        "version": "نسخه",
    },
}


def get_lang(request):
    """Get current language from session or Accept-Language."""
    lang = request.cookies.get("lang")
    if not lang:
        accept = request.headers.get("Accept-Language", "")
        if accept.startswith("fa"):
            lang = "fa"
        else:
            lang = "en"
    if lang not in TRANSLATIONS:
        lang = "en"
    return lang


def t(lang, key):
    """Translate a key. Falls back to key itself."""
    return TRANSLATIONS.get(lang, {}).get(key, TRANSLATIONS["en"].get(key, key))


def all_strings(lang):
    """Return the full dictionary for use in templates as a JS object."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])

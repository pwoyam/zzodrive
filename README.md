================================================================
                          zzoDrive
        Turn your Telegram into a personal cloud drive
        تلگرام خودتان را به یک درایو ابری شخصی تبدیل کنید
================================================================

  [1] English ............ (below / پایین)
  [2] فارسی .............. (further down / ادامه‌ی فایل)

  Repository / مخزن پروژه: https://github.com/pwoyam/zzodrive
  License / مجوز: MIT


################################################################
#                         ENGLISH                              #
################################################################


----------------------------------------------------------------
1. WHAT IS ZZODRIVE?
----------------------------------------------------------------

zzoDrive is a free, open-source desktop application that turns your
Telegram account into a personal cloud drive.

No servers. No subscriptions. No third-party services.
Everything stays between YOUR computer and YOUR Telegram.

Store your files (encrypted or plain) and manage them through a
clean web interface that runs locally on your machine.


----------------------------------------------------------------
2. FEATURES
----------------------------------------------------------------

  * Drag & Drop Upload ....... upload files by dropping them in
  * Fast Download ............ live speed and progress display
  * Parallel Transfers ....... 8 simultaneous connections
  * End-to-End Encryption .... AES-256-CTR + HMAC-SHA256
  * Proxy Support ............ MTProxy, SOCKS5, SOCKS4, HTTP
  * Bilingual UI ............. Persian (RTL) and English
  * Folder Upload ............ keeps your directory structure
  * Search & Stats ........... find your files instantly
  * Cross-platform ........... macOS, Linux, Windows


----------------------------------------------------------------
3. QUICK START
----------------------------------------------------------------

Option 1: Download the executable (recommended)
-----------------------------------------------

  1. Open the "Releases" page of the repository.
  2. Download the file that matches your system:

       Platform          File
       ----------------  --------------------------
       macOS (Intel)     zzodrive-macos-x64.zip
       Linux             zzodrive-linux-x64.zip
       Windows           zzodrive-windows-x64.zip

  3. Extract the ZIP file.
  4. Run the "zzodrive" executable.

  No Python installation is needed.


Option 2: Run from source
-------------------------

  macOS / Linux:

      git clone https://github.com/pwoyam/zzodrive.git
      cd zzodrive
      bash install.sh
      ./start.sh

  Windows:

      git clone https://github.com/pwoyam/zzodrive.git
      cd zzodrive
      install.bat
      start.bat

  Your browser opens automatically at:

      http://127.0.0.1:8765


----------------------------------------------------------------
4. ONE-TIME SETUP
----------------------------------------------------------------

You need a Telegram bot and a private channel. This takes about
two minutes.

Step 1 - Create a Telegram bot
    - Open Telegram and message @BotFather
    - Send /newbot and choose a name
    - Copy the bot token you receive

Step 2 - Create a private channel
    - Create a new PRIVATE channel in Telegram
    - Add your bot to the channel as an ADMINISTRATOR

Step 3 - Get the channel ID
    - Forward any message from your channel to @username_to_id_bot
    - Copy the channel ID it gives you

Step 4 - (Optional) Configure a proxy
    If Telegram is blocked or slow on your network, use a proxy:

      MTProxy : tg://proxy?server=...&port=...&secret=...
      SOCKS5  : socks5://127.0.0.1:1080
      HTTP    : http://127.0.0.1:8080

Step 5 - (Optional) Set an encryption password
    Choose a strong password to encrypt your files.

    WARNING: If you forget this password, your encrypted files
    CANNOT be recovered.

Finally, enter the bot token, channel ID and (optionally) proxy
and password in the zzoDrive web interface, then start uploading.


----------------------------------------------------------------
5. ENCRYPTION
----------------------------------------------------------------

Encryption is opt-in per file, so you choose what gets encrypted.

  - AES-256-CTR ......... file encryption
  - HMAC-SHA256 ......... integrity and tamper detection
  - PBKDF2 .............. key derivation, 200,000 iterations
  - Unique IV ........... a new random IV for every file


----------------------------------------------------------------
6. PRIVACY
----------------------------------------------------------------

  - All data stays between your computer and your Telegram account.
  - No telemetry, no tracking, no third-party servers.
  - 100% open source: read the code and verify it yourself.


----------------------------------------------------------------
7. PROJECT STRUCTURE
----------------------------------------------------------------

  zzodrive/          application source code
  run.py             application entry point
  install.sh/.bat    dependency installers (macOS/Linux, Windows)
  start.sh/.bat      launchers (macOS/Linux, Windows)
  requirements.txt   Python dependencies
  pyproject.toml     project metadata
  zzodrive.spec      PyInstaller build configuration
  .github/workflows  automated build workflows
  LICENSE            MIT license


----------------------------------------------------------------
8. CONTRIBUTING
----------------------------------------------------------------

Contributions are welcome!

  1. Fork the repository
  2. Create a feature branch:  git checkout -b my-feature
  3. Commit your changes
  4. Push the branch and open a Pull Request

Found a bug or have an idea? Open an Issue on GitHub.


----------------------------------------------------------------
9. LICENSE
----------------------------------------------------------------

MIT License - free for personal and commercial use.


################################################################
#                          فارسی                               #
################################################################


----------------------------------------------------------------
۱. zzoDrive چیست؟
----------------------------------------------------------------

zzoDrive یک اپلیکیشن دسکتاپ رایگان و متن‌باز است که اکانت تلگرام
شما را به یک درایو شخصی ابری تبدیل می‌کند.

بدون سرور. بدون اشتراک. بدون سرویس شخص ثالث.
همه‌چیز فقط بین کامپیوتر شما و تلگرام شما می‌ماند.

فایل‌هایتان را (رمزنگاری‌شده یا معمولی) ذخیره کنید و از طریق یک
رابط وب تمیز که روی سیستم خودتان اجرا می‌شود، مدیریت کنید.


----------------------------------------------------------------
۲. قابلیت‌ها
----------------------------------------------------------------

  * آپلود کشیدنی ............ فایل را بکشید و رها کنید
  * دانلود سریع ............. نمایش زنده‌ی سرعت و پیشرفت
  * انتقال موازی ............ ۸ اتصال همزمان
  * رمزنگاری سرتاسری ........ AES-256-CTR + HMAC-SHA256
  * پشتیبانی از پروکسی ...... MTProxy، SOCKS5، SOCKS4، HTTP
  * رابط دو زبانه ........... فارسی (راست‌به‌چپ) و انگلیسی
  * آپلود پوشه .............. ساختار پوشه‌ها حفظ می‌شود
  * جستجو و آمار ............ پیدا کردن سریع فایل‌ها
  * چندسکویی ................ مک، لینوکس، ویندوز


----------------------------------------------------------------
۳. شروع سریع
----------------------------------------------------------------

روش اول: دانلود فایل اجرایی (پیشنهادی)
--------------------------------------

  ۱. به صفحه‌ی Releases مخزن پروژه بروید.
  ۲. فایل مناسب سیستم خود را دانلود کنید:

       پلتفرم            فایل
       ----------------  --------------------------
       مک (Intel)        zzodrive-macos-x64.zip
       لینوکس            zzodrive-linux-x64.zip
       ویندوز            zzodrive-windows-x64.zip

  ۳. فایل ZIP را Extract کنید.
  ۴. فایل اجرایی zzodrive را اجرا کنید.

  نیازی به نصب پایتون نیست.


روش دوم: اجرا از روی سورس
-------------------------

  مک / لینوکس:

      git clone https://github.com/pwoyam/zzodrive.git
      cd zzodrive
      bash install.sh
      ./start.sh

  ویندوز:

      git clone https://github.com/pwoyam/zzodrive.git
      cd zzodrive
      install.bat
      start.bat

  مرورگر شما به‌صورت خودکار در این آدرس باز می‌شود:

      http://127.0.0.1:8765


----------------------------------------------------------------
۴. تنظیمات اولیه (فقط یک‌بار)
----------------------------------------------------------------

به یک ربات تلگرام و یک کانال خصوصی نیاز دارید. حدود دو دقیقه
زمان می‌برد.

مرحله ۱ - ساخت ربات تلگرام
    - در تلگرام به @BotFather پیام بدهید
    - دستور /newbot را بفرستید و یک نام انتخاب کنید
    - توکنی که دریافت می‌کنید را کپی کنید

مرحله ۲ - ساخت کانال خصوصی
    - یک کانال خصوصی (Private) جدید بسازید
    - ربات را به‌عنوان ادمین (Administrator) به کانال اضافه کنید

مرحله ۳ - گرفتن آیدی کانال
    - یک پیام از کانال را به @username_to_id_bot فوروارد کنید
    - آیدی کانالی که می‌دهد را کپی کنید

مرحله ۴ - (اختیاری) تنظیم پروکسی
    اگر تلگرام در شبکه‌ی شما فیلتر یا کند است، از پروکسی
    استفاده کنید:

      MTProxy : tg://proxy?server=...&port=...&secret=...
      SOCKS5  : socks5://127.0.0.1:1080
      HTTP    : http://127.0.0.1:8080

مرحله ۵ - (اختیاری) تعیین رمز رمزنگاری
    یک رمز قوی برای رمزنگاری فایل‌هایتان انتخاب کنید.

    هشدار: اگر این رمز را فراموش کنید، فایل‌های رمزنگاری‌شده
    قابل بازیابی نخواهند بود.

در پایان، توکن ربات، آیدی کانال و (در صورت نیاز) پروکسی و رمز
را در رابط وب zzoDrive وارد کنید و آپلود را شروع کنید.


----------------------------------------------------------------
۵. رمزنگاری
----------------------------------------------------------------

رمزنگاری برای هر فایل اختیاری است؛ خودتان تصمیم می‌گیرید کدام
فایل‌ها رمز شوند.

  - AES-256-CTR ......... رمزنگاری فایل
  - HMAC-SHA256 ......... بررسی سلامت و تشخیص دستکاری
  - PBKDF2 .............. تولید کلید، با ۲۰۰,۰۰۰ تکرار
  - IV منحصربه‌فرد ....... برای هر فایل یک IV تصادفی جدید


----------------------------------------------------------------
۶. حریم خصوصی
----------------------------------------------------------------

  - تمام داده‌ها بین کامپیوتر شما و اکانت تلگرام شما می‌ماند.
  - بدون تلمتری، بدون ردیابی، بدون سرور شخص ثالث.
  - ۱۰۰٪ متن‌باز: کد را ببینید و خودتان بررسی کنید.


----------------------------------------------------------------
۷. ساختار پروژه
----------------------------------------------------------------

  zzodrive/          سورس اصلی برنامه
  run.py             نقطه‌ی شروع برنامه
  install.sh/.bat    نصب وابستگی‌ها (مک/لینوکس، ویندوز)
  start.sh/.bat      اجرای برنامه (مک/لینوکس، ویندوز)
  requirements.txt   وابستگی‌های پایتون
  pyproject.toml     مشخصات پروژه
  zzodrive.spec      تنظیمات ساخت با PyInstaller
  .github/workflows  ورک‌فلوهای ساخت خودکار
  LICENSE            مجوز MIT


----------------------------------------------------------------
۸. مشارکت در پروژه
----------------------------------------------------------------

مشارکت شما خوش‌آمد است!

  ۱. مخزن را Fork کنید
  ۲. یک برنچ جدید بسازید:  git checkout -b my-feature
  ۳. تغییرات را Commit کنید
  ۴. برنچ را Push کنید و یک Pull Request باز کنید

باگ پیدا کردید یا ایده‌ای دارید؟ یک Issue در گیت‌هاب باز کنید.


----------------------------------------------------------------
۹. مجوز
----------------------------------------------------------------

مجوز MIT - رایگان برای استفاده‌ی شخصی و تجاری.


================================================================
  Made with love by Pouya  |  https://github.com/pwoyam
  اگر این پروژه برایتان مفید بود، یک ستاره بدهید!
  If you find this project useful, please give it a star!
================================================================

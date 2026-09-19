# 🚀 zzoDrive

> **Turn your Telegram into a personal cloud drive.**
> **تلگرام خود را به یک درایو شخصی تبدیل کنید.**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)]()

A simple, cross-platform desktop app that stores your files on **Telegram** — for free, forever. No server needed. Runs entirely on your own computer.

یک اپلیکیشن ساده و چندسکویی که فایل‌های شما را روی **تلگرام** ذخیره می‌کند — رایگان و همیشگی. بدون نیاز به سرور. کاملاً روی کامپیوتر خودتان اجرا می‌شود.

---

## ✨ Features / قابلیت‌ها

| Feature | قابلیت |
|---------|--------|
| 📤 Upload files via drag & drop | آپلود فایل با کشیدن و رها کردن |
| 📥 Download with live speed & progress | دانلود با نمایش زنده سرعت و پیشرفت |
| ⚡ Parallel transfers (8 connections) | انتقال موازی (۸ اتصال همزمان) |
| 🔐 End-to-end encryption (AES-256-CTR + HMAC-SHA256) | رمزنگاری سرتاسری |
| 🌐 Proxy support (MTProxy / SOCKS5 / HTTP) | پشتیبانی پروکسی |
| 🌍 Persian / English UI | رابط کاربری فارسی / انگلیسی |
| 📁 Folder upload with structure | آپلود پوشه با ساختار درختی |
| 🔍 Search & Stats | جستجو و آمار |
| 🔄 Sync — bidirectional incremental | سینک دوطرفه |
| 💾 Restore — rebuild everything | بازیابی کامل |
| 🖥️ WebDAV Gateway | درایو WebDAV |

---

## 🚀 Quick Start / شروع سریع

### macOS / Linux

    git clone https://github.com/pwoyam/zzodrive.git
    cd zzodrive
    bash install.sh
    ./start.sh

### Windows

    git clone https://github.com/pwoyam/zzodrive.git
    cd zzodrive
    install.bat
    start.bat

Your browser opens automatically at **http://127.0.0.1:8765**

مرورگر شما به‌صورت خودکار باز می‌شود.

---

## 🛠️ First-time Setup / تنظیم اولیه

On first launch you'll see a setup wizard. You need three things:

در اولین اجرا، صفحه‌ی راه‌اندازی باز می‌شود. سه چیز لازم دارید:

### 1️⃣ Create a Telegram bot / ساخت ربات تلگرام

1. Open Telegram, message @BotFather
2. Send /newbot, pick a name and username
3. Copy the token (looks like `123456:ABC-DEF...`)

### 2️⃣ Create a private channel / ساخت کانال خصوصی

1. Create a **new private channel**
2. Add your bot as an **administrator**

### 3️⃣ Get the channel ID / گرفتن آیدی کانال

Forward a message from the channel to @username_to_id_bot. It will reply with the channel ID (e.g. `-1001234567890`).

### 4️⃣ (Optional) Proxy / پروکسی (اختیاری)

If you're in a country where Telegram is blocked, enter your proxy:

    MTProxy: mtproxy://host:port?secret=dd...
             or tg://proxy?server=...&port=...&secret=...
    SOCKS5:  socks5://127.0.0.1:1080
    HTTP:    http://127.0.0.1:8080

### 5️⃣ (Optional) Encryption password / رمز رمزنگاری

Set a password to encrypt sensitive files.

⚠️ **If you lose it, encrypted files cannot be recovered.**

---

## 🔐 Encryption / رمزنگاری

Encryption is **opt-in per file**. Tick the checkbox before uploading.

- **AES-256-CTR** for encryption
- **HMAC-SHA256** for integrity
- **PBKDF2** with 200,000 iterations
- Unique IV per file

Telegram cannot read your encrypted files. Only you can.

> ⚠️ **Warning:** If you lose your password, encrypted files are gone forever.

---

## 📂 Project Structure / ساختار پروژه

    zzodrive/
    ├── run.py                     # launcher
    ├── install.sh / install.bat   # installers
    ├── start.sh / start.bat       # quick launchers
    ├── requirements.txt
    ├── zzodrive/
    │   ├── config.py              # configuration
    │   ├── crypto.py              # encryption
    │   ├── index.py               # local file index
    │   ├── i18n.py                # Persian / English
    │   ├── proxy.py               # proxy support
    │   ├── progress.py            # progress tracking
    │   ├── fast_upload.py         # parallel uploader
    │   ├── telegram_client.py     # Telegram wrapper
    │   └── web/
    │       ├── app.py             # Flask app
    │       ├── templates/         # HTML
    │       └── static/            # CSS + JS

---

## 🔒 Privacy / حریم خصوصی

- All data stays between **your computer** and **your Telegram**.
- No third-party server, no telemetry, no tracking.
- Everything is open source.

تمام داده‌ها فقط بین **کامپیوتر شما** و **تلگرام شما** رد و بدل می‌شود. هیچ سرور واسطه‌ای وجود ندارد.

---

## 🤝 Contributing / مشارکت

Pull requests are welcome! Feel free to open an issue for bugs or feature requests.

---

## 📜 License / مجوز

MIT — free for personal and commercial use.

---

**Made with ❤️ for people who care about their data.**

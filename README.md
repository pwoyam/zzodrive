```
<div align="center">

# 🚀 zzoDrive

### Turn your Telegram into a personal cloud drive

*Free · Open Source · No server · Runs entirely on your computer*

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-64748b?style=for-the-badge)]()
[![Release](https://img.shields.io/github/v/release/pwoyam/zzodrive?style=for-the-badge&color=4f8dff)](https://github.com/pwoyam/zzodrive/releases)

[English](#-english) · [فارسی](#-فارسی)

</div>

---

# 🇬🇧 English

## 💡 What is zzoDrive?

**zzoDrive** turns your **personal Telegram account** into a **private cloud drive**.

No subscriptions. No servers. No third-party services.
Your files live in **your own Telegram account** — and nowhere else.

Think of it as a **personal Dropbox**, powered by the storage you already have.

| ✅ Free forever | 🔒 E2E encrypted | 🚀 Blazing fast |
|:---:|:---:|:---:|
| Use Telegram's storage | Files stay on your device | 8× parallel transfers |

---

## ✨ Features

### 📤 Upload
- **Drag & drop** from Finder / Explorer
- **Folder upload** (preserves structure)
- **Parallel uploads** — 8 connections
- **Live progress** with speed indicator

### 📥 Download
- **One-click** downloads
- **Live speed & progress** modal
- **Automatic MD5** integrity check
- **Bulk download** with multi-select

### 🔐 Security
- **AES-256-CTR** encryption
- **HMAC-SHA256** integrity
- **PBKDF2** with 600K iterations
- **Zero-knowledge** — Telegram cannot read

### 🎨 Beautiful UI
- **Glassmorphism** design
- **Persian & English** (auto RTL)
- **Power Save** mode
- **Responsive** on mobile

---

## 🎨 User Interface

zzoDrive comes with a **stunning glassmorphism UI** inspired by macOS Big Sur:

- 🌄 **Atmospheric SVG background** — sunset landscape, zero file size
- 🪟 **Frosted glass panels** — real backdrop-filter with 3-column layout
- ⚡ **Liquid Glass modals** — smooth scale + blur animation
- 🎯 **SVG icons** — crisp at any size, no emoji
- 🌗 **Dark theme** — optimized for long sessions
- 🎚️ **Power Save mode** — reduce GPU load with one click
- 📊 **Live progress** — upload/download with speed indicator
- 🔍 **Preview** — images, videos, PDFs, audio in browser

---

## 🚀 Quick Start

### Option 1 — Download the app (recommended)

> **No Python needed.** Just download and double-click.

| 🍎 macOS | 🐧 Linux | 🪟 Windows |
|:---:|:---:|:---:|
| [Download](https://github.com/pwoyam/zzodrive/releases/latest/download/zzodrive-macos-x64.zip) | [Download](https://github.com/pwoyam/zzodrive/releases/latest/download/zzodrive-linux-x64.zip) | [Download](https://github.com/pwoyam/zzodrive/releases/latest/download/zzodrive-windows-x64.zip) |
| zzodrive-macos-x64.zip | zzodrive-linux-x64.zip | zzodrive-windows-x64.zip |

**Steps:**
1. Download the ZIP for your system
2. Extract it anywhere
3. Run zzodrive (double-click)
4. Your browser opens automatically

### Option 2 — One-line auto install

**macOS / Linux** — paste this in Terminal:

```bash
git clone https://github.com/pwoyam/zzodrive.git && cd zzodrive && bash install.sh && ./start.sh
```

**Windows** — paste this in PowerShell:

```powershell
git clone https://github.com/pwoyam/zzodrive.git; cd zzodrive; install.bat; start.bat
```

Browser opens at http://127.0.0.1:8765

### Option 3 — Manual install

**macOS / Linux:**

```bash
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
bash install.sh
./start.sh
```

**Windows:**

```bat
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
install.bat
start.bat
```

---

## 🛠️ First-Time Setup

### 1. Create a Telegram bot
- Open Telegram, message **@BotFather**
- Send /newbot — pick a name and username
- Copy the token

### 2. Create a private channel
- In Telegram, create a new private channel
- Add your bot as administrator

### 3. Get the channel ID
- Forward a message to **@username_to_id_bot**
- Copy the ID

### 4. Optional — Add a proxy

```
MTProxy: tg://proxy?server=...&port=...&secret=...
SOCKS5:  socks5://127.0.0.1:1080
HTTP:    http://127.0.0.1:8080
```

Save multiple proxies and switch with one click.

---

## 🔐 Encryption

| Layer | Algorithm |
|-------|-----------|
| Encryption | **AES-256-CTR** |
| Authentication | **HMAC-SHA256** |
| Key derivation | **PBKDF2** (600,000 iterations) |
| Key separation | **HKDF** |
| Per-file | **Unique salt + IV** |

Telegram servers see only encrypted bytes.
Only you, with the password, can read your files.

---

## 🎯 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl/Cmd + U | Upload file |
| Ctrl/Cmd + F | Focus search |
| Ctrl/Cmd + N | New folder |
| Esc | Close modal |
| Delete | Delete selected |

---

## 📂 Project Structure

```
zzodrive/
├── run.py                     # Launcher
├── install.sh / install.bat   # Installers
├── start.sh / start.bat       # Quick launchers
├── requirements.txt
├── zzodrive/
│   ├── config.py              # Settings
│   ├── crypto.py              # AES + HMAC
│   ├── index.py               # File index
│   ├── folders.py             # Virtual folders
│   ├── proxies.py             # Multi-proxy manager
│   ├── auth.py                # LAN access
│   ├── i18n.py                # Persian / English
│   ├── fast_upload.py         # Parallel uploader
│   ├── client_manager.py      # Persistent client
│   ├── telegram_client.py     # Telethon wrapper
│   └── web/
│       ├── app.py             # Flask backend
│       ├── templates/         # HTML
│       └── static/            # CSS + JS + SVG
└── ~/.zzodrive/               # Config & session
```

---

## 🔒 Privacy

- All data stays between **your computer** and **your Telegram**.
- **No telemetry. No tracking. No analytics.**
- **100% open source** — inspect every line.

---

## 🤝 Contributing

- 🐛 [Report a bug](https://github.com/pwoyam/zzodrive/issues/new)
- 💡 [Suggest a feature](https://github.com/pwoyam/zzodrive/issues/new)
- ⭐ **Star the repo** — it means a lot!

---

## 📜 License

**MIT License** — free for personal and commercial use.

---

<div dir="rtl">

# 🇮🇷 فارسی

## 💡 zzoDrive چیه؟

**zzoDrive** اکانت **تلگرام شخصی‌ت** رو به یه **درایو ابری خصوصی** تبدیل می‌کنه.

بدون اشتراک. بدون سرور. بدون سرویس واسطه.
فایل‌هات توی **اکانت تلگرام خودت** ذخیره می‌شن — و جای دیگه‌ای نه.

| ✅ همیشه رایگان | 🔒 رمزنگاری E2E | 🚀 فوق سریع |
|:---:|:---:|:---:|
| فضای تلگرام | فایل‌ها روی دستگاه خودت | انتقال موازی ۸ اتصال |

---

## ✨ قابلیت‌ها

### 📤 آپلود
- **کشیدن و رها کردن** از Finder
- **آپلود پوشه** با حفظ ساختار درختی
- **آپلود موازی** — ۸ اتصال همزمان
- **نمایش زنده** سرعت و درصد

### 📥 دانلود
- دانلود با **یه کلیک**
- **پنجره‌ی سرعت و پیشرفت** زنده
- **چک خودکار MD5** برای صحت فایل
- **دانلود گروهی** با انتخاب چندتایی

### 🔐 امنیت
- رمزنگاری **AES-256-CTR**
- بررسی **HMAC-SHA256**
- **PBKDF2** با ۶۰۰ هزار تکرار
- **تلگرام نمی‌تونه بخونه**

### 🎨 رابط کاربری
- طراحی **Glassmorphism**
- **فارسی و انگلیسی** (RTL خودکار)
- حالت **کم‌مصرف** برای سیستم‌های ضعیف
- **واکنش‌گرا** روی موبایل

---

## 🎨 رابط کاربری

zzoDrive با یه **طراحی شیشه‌ای Glassmorphism** مثل macOS Big Sur ساخته شده:

- 🌄 **پس‌زمینه SVG اتمسفریک** — غروب، بدون فایل عکس
- 🪟 **پنل‌های شیشه‌ای** — سه ستونه با blur واقعی
- ⚡ **پنجره‌های Liquid Glass** — انیمیشن نرم
- 🎯 **آیکون‌های SVG** — بدون emoji
- 🌗 **تم تیره** — مناسب استفاده‌ی طولانی
- 🎚️ **حالت کم‌مصرف** — با یه کلیک
- 📊 **پیشرفت زنده** — سرعت و درصد
- 🔍 **پیش‌نمایش** — عکس، ویدیو، PDF، صدا

---

## 🚀 شروع سریع

### روش ۱ — دانلود اپ (پیشنهادی)

> نیازی به نصب پایتون نیست. فقط دانلود کن و دوبار کلیک کن.

| 🍎 مک | 🐧 لینوکس | 🪟 ویندوز |
|:---:|:---:|:---:|
| [دانلود](https://github.com/pwoyam/zzodrive/releases/latest/download/zzodrive-macos-x64.zip) | [دانلود](https://github.com/pwoyam/zzodrive/releases/latest/download/zzodrive-linux-x64.zip) | [دانلود](https://github.com/pwoyam/zzodrive/releases/latest/download/zzodrive-windows-x64.zip) |

**مراحل:**
۱. ZIP رو دانلود کن
۲. Extract کن
۳. دوبار کلیک روی zzodrive
۴. مرورگر باز می‌شه

### روش ۲ — نصب خودکار با یه دستور

**مک / لینوکس** — توی ترمینال این رو پیست کن:

```bash
git clone https://github.com/pwoyam/zzodrive.git && cd zzodrive && bash install.sh && ./start.sh
```

**ویندوز** — توی PowerShell:

```powershell
git clone https://github.com/pwoyam/zzodrive.git; cd zzodrive; install.bat; start.bat
```

مرورگر باز می‌شه روی http://127.0.0.1:8765

### روش ۳ — نصب دستی

**مک / لینوکس:**

```bash
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
bash install.sh
./start.sh
```

**ویندوز:**

```bat
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
install.bat
start.bat
```

---

## 🛠️ تنظیمات اولیه

### ۱. ساخت ربات تلگرام
- به **@BotFather** پیام بده
- بزن /newbot — یه اسم انتخاب کن
- توکن رو کپی کن

### ۲. ساخت کانال خصوصی
- کانال خصوصی جدید بساز
- ربات رو ادمین کن

### ۳. گرفتن آیدی کانال
- به **@username_to_id_bot** فوروارد کن
- آیدی رو کپی کن

### ۴. اختیاری — پروکسی

```
MTProxy: tg://proxy?server=...&port=...&secret=...
SOCKS5:  socks5://127.0.0.1:1080
HTTP:    http://127.0.0.1:8080
```

می‌تونی چند پروکسی ذخیره کنی و با یه کلیک جابجا شی.

---

## 🔐 رمزنگاری

| لایه | الگوریتم |
|------|-----------|
| رمزنگاری | **AES-256-CTR** |
| تأیید یکپارچگی | **HMAC-SHA256** |
| مشتق کلید | **PBKDF2** (۶۰۰,۰۰۰ تکرار) |
| هر فایل | **salt + IV منحصربه‌فرد** |

سرورهای تلگرام فقط بایت‌های رمز شده رو می‌بینن.
فقط خودت با پسورد می‌تونی فایل‌هات رو بخونی.

---

## 🎯 کلیدهای میان‌بر

| میان‌بر | عملکرد |
|--------|--------|
| Ctrl/Cmd + U | آپلود فایل |
| Ctrl/Cmd + F | جستجو |
| Ctrl/Cmd + N | پوشه جدید |
| Esc | بستن پنجره |
| Delete | حذف انتخاب شده‌ها |

---

## 🔒 حریم خصوصی

- تمام داده‌ها بین **کامپیوتر خودت** و **تلگرام خودت**.
- **بدون تلمتری. بدون ردیابی. بدون تحلیل.**
- **۱۰۰٪ متن‌باز** — هر خط رو می‌تونی ببینی.

---

## 🤝 مشارکت

از مشارکت استقبال می‌کنیم!

- 🐛 [گزارش باگ](https://github.com/pwoyam/zzodrive/issues/new)
- 💡 [پیشنهاد قابلیت](https://github.com/pwoyam/zzodrive/issues/new)
- ⭐ **ستاره دادن به پروژه**
- 📢 با دوستات share کن

---

## 📜 مجوز

**مجوز MIT** — رایگان برای استفاده‌ی شخصی و تجاری.

</div>

---

<div align="center">

**Made with ❤️ by [Pouya](https://github.com/pwoyam)**

⭐ اگه zzoDrive به کارت میاد، یه ستاره بده! ⭐

</div>
```
cd ~/Projects/zzodrive

printf '%s\n' \
'<div align="center">' \
'' \
'# 🚀 zzoDrive' \
'' \
'**Turn your Telegram into a personal cloud drive**' \
'' \
'[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/)' \
'[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)' \
'[![Release](https://img.shields.io/github/v/release/pwoyam/zzodrive)](https://github.com/pwoyam/zzodrive/releases)' \
'' \
'[English](#-english) · [فارسی](#-فارسی)' \
'' \
'</div>' \
'' \
'---' \
'' \
'# 🇬🇧 English' \
'' \
'## What is zzoDrive?' \
'' \
'**zzoDrive** is a free, open-source desktop application that turns your **Telegram account** into a **personal cloud drive**. No servers, no subscriptions, no third-party services — everything stays between **your computer** and **your Telegram**.' \
'' \
'Store unlimited files, encrypted or plain, and access them from anywhere through a clean, simple web interface that runs locally on your computer.' \
'' >> README.md

echo "OK part 1"
<div align="center">

# 🚀 zzoDrive

**Turn your Telegram into a personal cloud drive**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/pwoyam/zzodrive)](https://github.com/pwoyam/zzodrive/releases)

[English](#-english) · [فارسی](#-فارسی)

</div>

---

# 🇬🇧 English

## What is zzoDrive?

**zzoDrive** is a free, open-source desktop application that turns your **Telegram account** into a **personal cloud drive**. No servers, no subscriptions, no third-party services — everything stays between **your computer** and **your Telegram**.

Store unlimited files, encrypted or plain, and access them from anywhere through a clean, simple web interface that runs locally on your computer.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📤 **Drag & Drop Upload** | Upload files with a simple drag and drop |
| 📥 **Fast Download** | Download with live speed and progress |
| ⚡ **Parallel Transfers** | 8 simultaneous connections for maximum speed |
| 🔐 **End-to-End Encryption** | AES-256-CTR + HMAC-SHA256 (opt-in) |
| 🌐 **Proxy Support** | MTProxy, SOCKS5, SOCKS4, HTTP |
| 🌍 **Bilingual UI** | Persian (RTL) and English |
| 📁 **Folder Upload** | Preserves directory structure |
| 🔍 **Search & Stats** | Find files instantly |
| 💻 **Cross-platform** | macOS, Linux, Windows |

## 🚀 Quick Start

### Option 1: Download the executable (recommended)

Go to [**Releases**](https://github.com/pwoyam/zzodrive/releases/latest) and download the file for your system:

| Platform | File |
|----------|------|
| 🍎 macOS (Intel) | `zzodrive-macos-x64.zip` |
| 🐧 Linux | `zzodrive-linux-x64.zip` |
| 🪟 Windows | `zzodrive-windows-x64.zip` |

Extract the ZIP and run the `zzodrive` executable. **No Python needed.**

### Option 2: Run from source

```bash
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
bash install.sh
./start.sh
```

On Windows:

```bat
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
install.bat
start.bat
```

Your browser opens automatically at **http://127.0.0.1:8765**

## 🛠️ Setup (One Time)

### 1. A Telegram bot
- Message [@BotFather](https://t.me/BotFather)
- Send `/newbot`, pick a name
- Copy the token

### 2. A private channel
- Create a **private channel**
- Add your bot as **administrator**

### 3. The channel ID
- Forward a message to [@username_to_id_bot](https://t.me/username_to_id_bot)

### 4. (Optional) Proxy
```
MTProxy: tg://proxy?server=...&port=...&secret=...
SOCKS5:  socks5://127.0.0.1:1080
HTTP:    http://127.0.0.1:8080
```

## 🔐 Encryption

Encryption is **opt-in per file**.

- **AES-256-CTR** for encryption
- **HMAC-SHA256** for integrity
- **PBKDF2** with 200,000 iterations
- **Unique IV** for every file

> ⚠️ **Warning**: If you forget your password, encrypted files cannot be recovered.

## 🔒 Privacy

- All data stays between **your computer** and **your Telegram account**.
- **No telemetry**, no tracking, no third-party servers.
- **100% open source**

## 📜 License

**MIT License** — free for personal and commercial use.

---

# 🇮🇷 فارسی

## zzoDrive چیست؟

**zzoDrive** یک اپلیکیشن دسکتاپ رایگان و متن‌باز است که **اکانت تلگرام شما** را به یک **درایو شخصی ابری** تبدیل می‌کند. بدون سرور، بدون اشتراک، بدون سرویس‌های واسطه.

## ✨ قابلیت‌ها

| قابلیت | توضیح |
|--------|-------|
| 📤 **آپلود کشیدنی** | فقط فایل را بکشید و رها کنید |
| 📥 **دانلود سریع** | با نمایش زنده‌ی سرعت و پیشرفت |
| ⚡ **انتقال موازی** | ۸ اتصال همزمان |
| 🔐 **رمزنگاری سرتاسری** | AES-256-CTR + HMAC-SHA256 |
| 🌐 **پشتیبانی پروکسی** | MTProxy، SOCKS5، HTTP |
| 🌍 **رابط دو زبانه** | فارسی (راست‌چین) و انگلیسی |
| 💻 **چندسکویی** | مک، لینوکس، ویندوز |

## 🚀 شروع سریع

برو به [**Releases**](https://github.com/pwoyam/zzodrive/releases/latest) و فایل مربوط به سیستم‌ت رو دانلود کن:

| پلتفرم | فایل |
|--------|------|
| 🍎 مک (Intel) | `zzodrive-macos-x64.zip` |
| 🐧 لینوکس | `zzodrive-linux-x64.zip` |
| 🪟 ویندوز | `zzodrive-windows-x64.zip` |

فایل ZIP را Extract کن و فایل اجرایی `zzodrive` را اجرا کن. **نیازی به نصب پایتون نیست.**

## 🛠️ تنظیمات اولیه

### ۱. یک ربات تلگرام بسازید
- در تلگرام به [@BotFather](https://t.me/BotFather) پیام دهید
- دستور `/newbot` را بفرستید
- توکن را کپی کنید

### ۲. یک کانال خصوصی بسازید
- کانال خصوصی جدید بسازید
- ربات را به عنوان **ادمین** اضافه کنید

### ۳. آیدی کانال
- یک پیام از کانال را به [@username_to_id_bot](https://t.me/username_to_id_bot) فوروارد کنید

### ۴. (اختیاری) پروکسی
```
MTProxy: tg://proxy?server=...&port=...&secret=...
SOCKS5:  socks5://127.0.0.1:1080
HTTP:    http://127.0.0.1:8080
```

## 🔐 رمزنگاری

رمزنگاری **برای هر فایل اختیاری** است.

- **AES-256-CTR** برای رمزنگاری
- **HMAC-SHA256** برای بررسی سلامت
- **PBKDF2** با ۲۰۰,۰۰۰ تکرار
- **IV منحصربه‌فرد** برای هر فایل

> ⚠️ **هشدار**: اگر پسورد را فراموش کنید، فایل‌های رمز شده از دست می‌روند.

## 🔒 حریم خصوصی

- تمام داده‌ها بین **کامپیوتر شما** و **اکانت تلگرام شما** می‌ماند.
- **بدون تلمتری**، بدون ردیابی.
- **۱۰۰٪ متن‌باز**

## 📜 مجوز

**مجوز MIT** — رایگان برای استفاده‌ی شخصی و تجاری.

---

<div align="center">

**Made with ❤️ by [Pouya](https://github.com/pwoyam)**

⭐ اگر این پروژه برایتان مفید بود، یک ستاره بدهید! ⭐

</div>

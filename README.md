# 🚀 zzoDrive

**Turn your Telegram into a personal cloud drive**

[English](#-english) · [فارسی](#-فارسی)

---

# 🇬🇧 English

## What is zzoDrive?

**zzoDrive** is a free, open-source desktop application that turns your **Telegram account** into a **personal cloud drive**. No servers, no subscriptions, no third-party services — everything stays between **your computer** and **your Telegram**.

Store your files, encrypted or plain, and manage them through a clean web interface that runs locally on your machine.

## ✨ Features

| Feature                      | Description                              |
| ---------------------------- | ---------------------------------------- |
| 📤 **Drag & Drop Upload**    | Upload files with a simple drag and drop |
| 📥 **Fast Download**         | Download with live speed and progress    |
| ⚡ **Parallel Transfers**    | 8 simultaneous connections               |
| 🔐 **End-to-End Encryption** | AES-256-CTR + HMAC-SHA256                |
| 🌐 **Proxy Support**         | MTProxy, SOCKS5, SOCKS4, HTTP            |
| 🌍 **Bilingual UI**          | Persian (RTL) and English                |
| 📁 **Folder Upload**         | Preserves directory structure            |
| 🔍 **Search & Stats**        | Find files instantly                     |
| 💻 **Cross-platform**        | macOS, Linux, Windows                    |

## 🚀 Quick Start

### Option 1: Download the executable (recommended)

Go to [**Releases**](https://github.com/pwoyam/zzodrive/releases) and download the file for your system:

| Platform         | File                       |
| ---------------- | -------------------------- |
| 🍎 macOS (Intel) | `zzodrive-macos-x64.zip`   |
| 🐧 Linux         | `zzodrive-linux-x64.zip`   |
| 🪟 Windows       | `zzodrive-windows-x64.zip` |

Extract the ZIP and run the `zzodrive` executable. **No Python needed.**

### Option 2: Run from source

**macOS / Linux**

```bash
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
bash install.sh
./start.sh
```

**Windows**

```bat
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
install.bat
start.bat
```

Your browser opens automatically at **http://127.0.0.1:8765**

## 🛠️ Setup (One Time)

You need a Telegram bot and a private channel. It takes about two minutes.

### 1. Create a Telegram bot

- Message [@BotFather](https://t.me/BotFather)
- Send `/newbot` and pick a name
- Copy the bot token

### 2. Create a private channel

- Create a new **private channel**
- Add your bot as an **administrator**

### 3. Get the channel ID

- Forward a message from your channel to `@username_to_id_bot`
- Copy the channel ID

### 4. (Optional) Proxy

If Telegram is blocked or slow on your network, use a proxy:

```text
MTProxy : tg://proxy?server=...&port=...&secret=...
SOCKS5  : socks5://127.0.0.1:1080
HTTP    : http://127.0.0.1:8080
```

### 5. (Optional) Encryption password

Choose a strong password to encrypt your files.

> [!WARNING]
> If you forget your password, encrypted files **cannot be recovered**.

Finally, enter the bot token, channel ID and (optionally) proxy and password in zzoDrive, then start uploading.

## 🔐 Encryption

Encryption is **opt-in per file**.

- **AES-256-CTR** for encryption
- **HMAC-SHA256** for integrity
- **PBKDF2** with 200,000 iterations
- **Unique IV** for every file

## 🔒 Privacy

- All data stays between **your computer** and **your Telegram account**.
- **No telemetry**, no tracking, no third-party servers.
- **100% open source**

## 📜 License

**MIT License** — free for personal and commercial use.

---

# 🇮🇷 فارسی

<div dir="rtl">

## zzoDrive چیست؟

**zzoDrive** یک اپلیکیشن دسکتاپ رایگان و متن‌باز است که **اکانت تلگرام شما** را به یک **درایو شخصی ابری** تبدیل می‌کند. بدون سرور، بدون اشتراک، بدون سرویس شخص ثالث؛ همه‌چیز فقط بین **کامپیوتر شما** و **تلگرام شما** می‌ماند.

فایل‌هایتان را (رمزنگاری‌شده یا معمولی) ذخیره کنید و از طریق یک رابط وب تمیز که روی سیستم خودتان اجرا می‌شود، مدیریت کنید.

## ✨ قابلیت‌ها

| قابلیت                  | توضیح                                  |
| ----------------------- | -------------------------------------- |
| 📤 **آپلود کشیدنی**      | فقط فایل را بکشید و رها کنید           |
| 📥 **دانلود سریع**       | با نمایش زنده‌ی سرعت و پیشرفت          |
| ⚡ **انتقال موازی**      | ۸ اتصال همزمان                         |
| 🔐 **رمزنگاری سرتاسری**  | AES-256-CTR + HMAC-SHA256              |
| 🌐 **پشتیبانی از پروکسی** | MTProxy، SOCKS5، SOCKS4، HTTP          |
| 🌍 **رابط دو زبانه**     | فارسی (راست‌به‌چپ) و انگلیسی           |
| 📁 **آپلود پوشه**        | ساختار پوشه‌ها حفظ می‌شود              |
| 🔍 **جستجو و آمار**      | پیدا کردن سریع فایل‌ها                 |
| 💻 **چندسکویی**          | مک، لینوکس، ویندوز                     |

## 🚀 شروع سریع

### روش اول: دانلود فایل اجرایی (پیشنهادی)

به صفحه‌ی [**Releases**](https://github.com/pwoyam/zzodrive/releases) بروید و فایل مناسب سیستم خود را دانلود کنید:

| پلتفرم        | فایل                       |
| ------------- | -------------------------- |
| 🍎 مک (Intel)  | `zzodrive-macos-x64.zip`   |
| 🐧 لینوکس      | `zzodrive-linux-x64.zip`   |
| 🪟 ویندوز      | `zzodrive-windows-x64.zip` |

فایل ZIP را Extract کنید و فایل اجرایی `zzodrive` را اجرا کنید. **نیازی به نصب پایتون نیست.**

### روش دوم: اجرا از روی سورس

**مک / لینوکس**

<div dir="ltr">

```bash
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
bash install.sh
./start.sh
```

</div>

**ویندوز**

<div dir="ltr">

```bat
git clone https://github.com/pwoyam/zzodrive.git
cd zzodrive
install.bat
start.bat
```

</div>

مرورگر شما به‌صورت خودکار در آدرس **http://127.0.0.1:8765** باز می‌شود.

## 🛠️ تنظیمات اولیه (فقط یک‌بار)

به یک ربات تلگرام و یک کانال خصوصی نیاز دارید. حدود دو دقیقه زمان می‌برد.

### ۱. ساخت ربات تلگرام

- در تلگرام به [@BotFather](https://t.me/BotFather) پیام بدهید
- دستور `/newbot` را بفرستید و یک نام انتخاب کنید
- توکن ربات را کپی کنید

### ۲. ساخت کانال خصوصی

- یک **کانال خصوصی** جدید بسازید
- ربات را به‌عنوان **ادمین** به کانال اضافه کنید

### ۳. گرفتن آیدی کانال

- یک پیام از کانال را به `@username_to_id_bot` فوروارد کنید
- آیدی کانال را کپی کنید

### ۴. (اختیاری) پروکسی

اگر تلگرام در شبکه‌ی شما فیلتر یا کند است، از پروکسی استفاده کنید:

<div dir="ltr">

```text
MTProxy : tg://proxy?server=...&port=...&secret=...
SOCKS5  : socks5://127.0.0.1:1080
HTTP    : http://127.0.0.1:8080
```

</div>

### ۵. (اختیاری) رمز رمزنگاری

یک رمز قوی برای رمزنگاری فایل‌هایتان انتخاب کنید.

> ⚠️ **هشدار:** اگر رمز را فراموش کنید، فایل‌های رمزنگاری‌شده **قابل بازیابی نیستند**.

در پایان، توکن ربات، آیدی کانال و (در صورت نیاز) پروکسی و رمز را در zzoDrive وارد کنید و آپلود را شروع کنید.

## 🔐 رمزنگاری

رمزنگاری **برای هر فایل اختیاری** است.

- **AES-256-CTR** برای رمزنگاری
- **HMAC-SHA256** برای بررسی سلامت
- **PBKDF2** با ۲۰۰٬۰۰۰ تکرار
- **IV منحصربه‌فرد** برای هر فایل

## 🔒 حریم خصوصی

- تمام داده‌ها بین **کامپیوتر شما** و **اکانت تلگرام شما** می‌ماند.
- **بدون تلمتری**، بدون ردیابی، بدون سرور شخص ثالث.
- **۱۰۰٪ متن‌باز**

## 📜 مجوز

**مجوز MIT** — رایگان برای استفاده‌ی شخصی و تجاری.

</div>

---

**Made with ❤️ by [Pouya](https://github.com/pwoyam)**

⭐ If you find this project useful, give it a star! · اگر این پروژه برایتان مفید بود، یک ستاره بدهید! ⭐

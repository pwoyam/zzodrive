"""Information about the creator and project.

Edit this file to customize the "About" page.
"""

# ---------- Project info ----------
PROJECT_NAME = "zzoDrive"
PROJECT_DESCRIPTION = "Turn your Telegram into a personal cloud drive."
PROJECT_VERSION = "1.0.0"
PROJECT_LICENSE = "MIT"
PROJECT_YEAR = "2026"

# ---------- Creator info ----------
# 👇 CHANGE THESE VALUES to your own.
CREATOR_NAME = "Pouya"  # <-- نام خودت
CREATOR_USERNAME = "pwoyam"  # <-- یوزرنیم گیت‌هاب
CREATOR_EMAIL = ""  # اختیاری
CREATOR_WEBSITE = ""  # اختیاری

# Social links — leave empty string to hide
CREATOR_GITHUB = "https://github.com/pwoyam"
CREATOR_TELEGRAM = "https://t.me/pwoyam"  # مثال: "https://t.me/your_username"
CREATOR_TWITTER = ""  # مثال: "https://twitter.com/your_handle"
CREATOR_LINKEDIN = ""  # مثال: "https://linkedin.com/in/your_profile"
CREATOR_INSTAGRAM = ""  # مثال: "https://instagram.com/your_handle"

# ---------- Support ----------
# اگه می‌خوای کاربرا حمایت کنن، لینک‌ها رو بذار
SUPPORT_COFFEE = ""  # مثال: "https://buymeacoffee.com/your_handle"
SUPPORT_CRYPTO = ""  # آدرس ولت (اختیاری)
SUPPORT_MESSAGE = ""  # پیام دلخواه

# ---------- Contributing ----------
REPO_URL = "https://github.com/pwoyam/zzodrive"
ISSUES_URL = "https://github.com/pwoyam/zzodrive/issues"


def as_dict():
    return {
        "project_name": PROJECT_NAME,
        "project_description": PROJECT_DESCRIPTION,
        "project_version": PROJECT_VERSION,
        "project_license": PROJECT_LICENSE,
        "project_year": PROJECT_YEAR,
        "creator_name": CREATOR_NAME,
        "creator_username": CREATOR_USERNAME,
        "creator_email": CREATOR_EMAIL,
        "creator_website": CREATOR_WEBSITE,
        "github": CREATOR_GITHUB,
        "telegram": CREATOR_TELEGRAM,
        "twitter": CREATOR_TWITTER,
        "linkedin": CREATOR_LINKEDIN,
        "instagram": CREATOR_INSTAGRAM,
        "support_coffee": SUPPORT_COFFEE,
        "support_crypto": SUPPORT_CRYPTO,
        "support_message": SUPPORT_MESSAGE,
        "repo_url": REPO_URL,
        "issues_url": ISSUES_URL,
    }

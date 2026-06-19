# تنظیمات پیش‌فرض برنامه Focus Mentor

# فاصله بررسی پنجره فعال (ثانیه)
DEFAULT_MONITOR_INTERVAL_SECONDS = 5

# آستانه زمانی برای ابزارهای soft blacklist (ثانیه)
DEFAULT_SOFT_BLACKLIST_THRESHOLD_SECONDS = 20

# آستانه زمانی برای ابزارهای ناشناخته (ثانیه)
DEFAULT_UNKNOWN_THRESHOLD_SECONDS = 90

# حداکثر تعداد overlay در هر 30 دقیقه
DEFAULT_MAX_OVERLAYS_PER_30_MINUTES = 3

# حداکثر تعداد تغییر پروژه در روز
DEFAULT_MAX_PROJECT_SWITCHES_PER_DAY = 2

# مدت زمان Pause (دقیقه)
DEFAULT_PAUSE_MINUTES = 10

# حداکثر نسبت Pause به زمان کاری روزانه
DEFAULT_MAX_DAILY_PAUSE_RATIO = 0.2

# لیست سفید پیش‌فرض (ابزارهای مجاز)
DEFAULT_WHITELIST = [
    "illustrator.exe",
    "photoshop.exe",
    "figma.exe",
    "notepad.exe",
    "explorer.exe",
    "code.exe",
    "sublime_text.exe",
    "atom.exe",
    "inkscape.exe",
    "gimp.exe",
    "blender.exe",
]

# لیست سیاه نرم پیش‌فرض (ابزارهای حواس‌پرتی)
DEFAULT_SOFT_BLACKLIST = [
    "chrome.exe",
    "firefox.exe",
    "msedge.exe",
    "youtube.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "pinterest.com",
    "midjourney",
    "leonardo.ai",
    "ideogram",
    "canva.com",
    "webflow.com",
    "framer.com",
    "telegram.exe",
    "whatsapp.exe",
]

# مسیر ذخیره‌سازی داده‌ها
DATA_DIR = "focus_mentor_data"
DB_FILENAME = "focus_mentor.db"

# لحن و پیام‌های پیش‌فرض
MESSAGES = {
    "welcome": "به منتور تمرکز خوش آمدی. بیا امروز را با تمرکز شروع کنیم.",
    "project_locked": "پروژه امروز قفل شد. موفق باشی.",
    "distraction_detected": "این فعالیت مستقیماً به هدف امروز وصل نیست.",
    "return_to_work": "خوب است. حالا به پروژه‌ی قفل‌شده‌ی امروز برگرد.",
    "too_many_claims": "در مدت کوتاهی چند بار فعالیت‌های مشکوک را به‌عنوان کار اصلی تأیید کرده‌ای. ممکن است تعریف «کار اصلی» در حال بیش از حد گسترده شدن باشد.",
    "project_switch_warning": "تغییر پروژه در میانه‌ی روز معمولاً می‌تواند نوعی فرار از شروع یا ادامه‌ی کار اصلی باشد.",
    "project_switch_warning_2": "این دومین تلاش برای تغییر پروژه امروز است. اگر مشکل اصلی سخت بودن شروع کار است، تغییر پروژه احتمالاً مسئله را حل نمی‌کند.",
    "pause_limit_warning": "زمان Pause امروز زیاد بود. اگر واقعاً به استراحت نیاز داشتی، برنامه فردا باید سبک‌تر تنظیم شود.",
    "low_focus_ratio": "نسبت زمان کار اصلی امروز پایین بود. پیشنهاد می‌شود فردا پروژه را کوچک‌تر و هدف روز را دقیق‌تر تعریف کنی.",
    "privacy_notice": "این برنامه فقط نام برنامه فعال، عنوان پنجره و مدت‌زمان استفاده را ثبت می‌کند. هیچ متن تایپ‌شده، محتوای صفحه، رمز، اسکرین‌شات یا داده‌ی شخصی حساس ذخیره نمی‌شود.",
}

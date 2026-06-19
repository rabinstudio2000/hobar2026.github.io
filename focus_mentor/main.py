# نقطه شروع برنامه Focus Mentor

import sys
import os

# افزودن مسیر فعلی به sys.path برای import ماژول‌ها
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tray_app import FocusMentorTrayApp


def main():
    """تابع اصلی اجرای برنامه"""
    print("=" * 50)
    print("Focus Mentor / منتور تمرکز")
    print("=" * 50)
    print()
    print("در حال بارگذاری...")
    print()
    
    # ایجاد و اجرای برنامه
    app = FocusMentorTrayApp()
    
    print("برنامه با موفقیت راه‌اندازی شد.")
    print("آیکون برنامه در System Tray (کنار ساعت ویندوز) ظاهر می‌شود.")
    print()
    print("برای خروج، روی آیکون کلیک راست کرده و 'خروج' را انتخاب کنید.")
    print()
    
    app.run()


if __name__ == "__main__":
    main()

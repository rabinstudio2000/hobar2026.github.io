# پایش پنجره فعال برای Focus Mentor

import time
from datetime import datetime
from typing import Tuple, Optional
from enum import Enum

try:
    import win32gui
    import win32process
    import psutil
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False


class WindowCategory(Enum):
    """دسته‌بندی پنجره"""
    MAIN_WORK = "main_work"
    ALLOWED = "allowed"
    SOFT_BLACKLIST = "soft_blacklist"
    UNKNOWN = "unknown"


class WindowMonitor:
    """پایش پنجره فعال ویندوز"""
    
    def __init__(self, storage=None):
        self.storage = storage
        self.last_window_info = None
        self.last_check_time = None
        self.current_duration = 0.0
    
    def get_active_window(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        دریافت پنجره فعال فعلی
        
        Returns:
            Tuple of (process_name, window_title, full_title)
        """
        if not WINDOWS_AVAILABLE:
            return ("simulation.exe", "Simulation Mode - Focus Mentor", "simulation")
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return (None, None, None)
            
            # دریافت عنوان پنجره
            window_title = win32gui.GetWindowText(hwnd)
            
            # دریافت process id
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # دریافت نام process
            process_name = None
            try:
                process = psutil.Process(pid)
                process_name = process.name().lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            return (process_name, window_title, f"{process_name}: {window_title}" if process_name else window_title)
        
        except Exception as e:
            return (None, None, None)
    
    def categorize_window(self, process_name: str, window_title: str, 
                          project_name: str = None) -> WindowCategory:
        """
        دسته‌بندی پنجره بر اساس لیست‌های سفید و سیاه
        
        Args:
            process_name: نام پردازنده
            window_title: عنوان پنجره
            project_name: نام پروژه امروز (اختیاری)
        
        Returns:
            WindowCategory
        """
        if not process_name and not window_title:
            return WindowCategory.UNKNOWN
        
        # دریافت لیست‌ها از storage
        whitelist = []
        soft_blacklist = []
        
        if self.storage:
            whitelist = self.storage.get_whitelist()
            soft_blacklist = self.storage.get_soft_blacklist()
        
        check_string = f"{process_name} {window_title}".lower()
        process_lower = process_name.lower() if process_name else ""
        title_lower = window_title.lower() if window_title else ""
        
        # بررسی Main Work (اگر عنوان شامل نام پروژه باشد)
        if project_name and project_name.lower() in check_string:
            return WindowCategory.MAIN_WORK
        
        # بررسی whitelist
        for item in whitelist:
            item_lower = item.lower()
            if item_lower in process_lower or item_lower in title_lower:
                # اگر در whitelist است و شامل نام پروژه هم هست، Main Work است
                if project_name and project_name.lower() in check_string:
                    return WindowCategory.MAIN_WORK
                return WindowCategory.ALLOWED
        
        # بررسی soft blacklist
        for item in soft_blacklist:
            item_lower = item.lower()
            if item_lower in process_lower or item_lower in title_lower:
                return WindowCategory.SOFT_BLACKLIST
        
        # اگر به اینجا رسیدیم، ناشناخته است
        return WindowCategory.UNKNOWN
    
    def check_and_log(self, project_name: str = None) -> Optional[dict]:
        """
        بررسی پنجره فعال و ثبت رویداد در صورت تغییر
        
        Args:
            project_name: نام پروژه امروز
        
        Returns:
            dict containing window info and category, or None if no change
        """
        current_time = time.time()
        process_name, window_title, _ = self.get_active_window()
        
        if not process_name and not window_title:
            return None
        
        category = self.categorize_window(process_name, window_title, project_name)
        
        # بررسی تغییر پنجره
        window_key = f"{process_name}:{window_title}"
        
        if self.last_window_info != window_key:
            # پنجره تغییر کرده است
            
            # محاسبه مدت زمان پنجره قبلی
            if self.last_check_time and self.last_window_info:
                duration = current_time - self.last_check_time
                self.current_duration = duration
                
                # ثبت رویداد اگر storage موجود باشد
                if self.storage:
                    from models import WindowEvent
                    event = WindowEvent(
                        timestamp=datetime.fromtimestamp(self.last_check_time),
                        process_name=self.last_process_name or "",
                        window_title=self.last_window_title or "",
                        category=self.last_category.value if self.last_category else "unknown",
                        duration_seconds=duration
                    )
                    self.storage.save_window_event(event)
            
            # ذخیره اطلاعات جدید
            self.last_window_info = window_key
            self.last_process_name = process_name
            self.last_window_title = window_title
            self.last_category = category
            self.last_check_time = current_time
            self.current_duration = 0.0
            
            return {
                "process_name": process_name,
                "window_title": window_title,
                "category": category,
                "is_new": True,
                "duration": 0.0
            }
        else:
            # همان پنجره قبلی، محاسبه مدت زمان
            if self.last_check_time:
                self.current_duration = current_time - self.last_check_time
            
            return {
                "process_name": process_name,
                "window_title": window_title,
                "category": category,
                "is_new": False,
                "duration": self.current_duration
            }
    
    def get_current_duration_on_window(self) -> float:
        """دریافت مدت زمان فعلی روی پنجره جاری"""
        return self.current_duration
    
    def reset(self):
        """بازنشانی وضعیت پایش"""
        self.last_window_info = None
        self.last_check_time = None
        self.current_duration = 0.0
        self.last_process_name = None
        self.last_window_title = None
        self.last_category = None

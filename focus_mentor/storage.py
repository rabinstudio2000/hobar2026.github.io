# ذخیره‌سازی و بازیابی داده‌ها برای Focus Mentor

import json
import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from models import (
    DailyProject, WindowEvent, InterventionEvent, 
    ProjectSwitch, PauseEvent, DailyReport, WeeklyReport
)
from config import DATA_DIR, DB_FILENAME


class Storage:
    """مدیریت ذخیره‌سازی داده‌ها با استفاده از JSON"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = DATA_DIR
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # فایل‌های اصلی
        self.daily_projects_file = self.data_dir / "daily_projects.json"
        self.window_events_file = self.data_dir / "window_events.json"
        self.interventions_file = self.data_dir / "interventions.json"
        self.project_switches_file = self.data_dir / "project_switches.json"
        self.pause_events_file = self.data_dir / "pause_events.json"
        self.daily_reports_file = self.data_dir / "daily_reports.json"
        self.weekly_reports_file = self.data_dir / "weekly_reports.json"
        self.settings_file = self.data_dir / "settings.json"
        
        # بارگذاری داده‌ها
        self.daily_projects = self._load_json(self.daily_projects_file, {})
        self.window_events = self._load_json(self.window_events_file, [])
        self.interventions = self._load_json(self.interventions_file, [])
        self.project_switches = self._load_json(self.project_switches_file, [])
        self.pause_events = self._load_json(self.pause_events_file, [])
        self.daily_reports = self._load_json(self.daily_reports_file, {})
        self.weekly_reports = self._load_json(self.weekly_reports_file, {})
        self.settings = self._load_json(self.settings_file, self._default_settings())
    
    def _load_json(self, filepath: Path, default: Any) -> Any:
        """بارگذاری فایل JSON یا برگرداندن مقدار پیش‌فرض"""
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return default
        return default
    
    def _save_json(self, filepath: Path, data: Any):
        """ذخیره داده در فایل JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _default_settings(self) -> Dict:
        """تنظیمات پیش‌فرض"""
        from config import (
            DEFAULT_WHITELIST, DEFAULT_SOFT_BLACKLIST,
            DEFAULT_MONITOR_INTERVAL_SECONDS,
            DEFAULT_SOFT_BLACKLIST_THRESHOLD_SECONDS,
            DEFAULT_UNKNOWN_THRESHOLD_SECONDS,
            DEFAULT_MAX_OVERLAYS_PER_30_MINUTES,
            DEFAULT_MAX_PROJECT_SWITCHES_PER_DAY,
            DEFAULT_PAUSE_MINUTES,
            DEFAULT_MAX_DAILY_PAUSE_RATIO,
        )
        return {
            "whitelist": DEFAULT_WHITELIST.copy(),
            "soft_blacklist": DEFAULT_SOFT_BLACKLIST.copy(),
            "monitor_interval_seconds": DEFAULT_MONITOR_INTERVAL_SECONDS,
            "soft_blacklist_threshold_seconds": DEFAULT_SOFT_BLACKLIST_THRESHOLD_SECONDS,
            "unknown_threshold_seconds": DEFAULT_UNKNOWN_THRESHOLD_SECONDS,
            "max_overlays_per_30_minutes": DEFAULT_MAX_OVERLAYS_PER_30_MINUTES,
            "max_project_switches_per_day": DEFAULT_MAX_PROJECT_SWITCHES_PER_DAY,
            "pause_minutes": DEFAULT_PAUSE_MINUTES,
            "max_daily_pause_ratio": DEFAULT_MAX_DAILY_PAUSE_RATIO,
        }
    
    # ========== مدیریت پروژه روزانه ==========
    
    def save_daily_project(self, project: DailyProject):
        """ذخیره پروژه روزانه"""
        self.daily_projects[project.date] = project.to_dict()
        self._save_json(self.daily_projects_file, self.daily_projects)
    
    def get_daily_project(self, date_str: str) -> Optional[DailyProject]:
        """دریافت پروژه روزانه بر اساس تاریخ"""
        data = self.daily_projects.get(date_str)
        if data:
            return DailyProject.from_dict(data)
        return None
    
    def get_today_project(self) -> Optional[DailyProject]:
        """دریافت پروژه امروز"""
        today = date.today().isoformat()
        return self.get_daily_project(today)
    
    # ========== مدیریت رویدادهای پنجره ==========
    
    def save_window_event(self, event: WindowEvent):
        """ذخیره رویداد پنجره"""
        self.window_events.append(event.to_dict())
        # محدود کردن تعداد رویدادها برای جلوگیری از بزرگ شدن فایل
        if len(self.window_events) > 10000:
            self.window_events = self.window_events[-5000:]
        self._save_json(self.window_events_file, self.window_events)
    
    def get_window_events_for_date(self, date_str: str) -> List[WindowEvent]:
        """دریافت رویدادهای پنجره برای یک تاریخ خاص"""
        events = []
        for event_data in self.window_events:
            event_timestamp = datetime.fromisoformat(event_data["timestamp"])
            if event_timestamp.date().isoformat() == date_str:
                events.append(WindowEvent.from_dict(event_data))
        return events
    
    # ========== مدیریت مداخله‌ها ==========
    
    def save_intervention(self, event: InterventionEvent):
        """ذخیره رویداد مداخله"""
        self.interventions.append(event.to_dict())
        self._save_json(self.interventions_file, self.interventions)
    
    def get_interventions_for_date(self, date_str: str) -> List[InterventionEvent]:
        """دریافت مداخله‌های یک تاریخ خاص"""
        events = []
        for event_data in self.interventions:
            event_timestamp = datetime.fromisoformat(event_data["timestamp"])
            if event_timestamp.date().isoformat() == date_str:
                events.append(InterventionEvent.from_dict(event_data))
        return events
    
    def get_recent_interventions(self, minutes: int = 30) -> List[InterventionEvent]:
        """دریافت مداخله‌های اخیر در بازه زمانی مشخص"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        events = []
        for event_data in self.interventions:
            event_timestamp = datetime.fromisoformat(event_data["timestamp"])
            if event_timestamp >= cutoff:
                events.append(InterventionEvent.from_dict(event_data))
        return events
    
    # ========== مدیریت تغییر پروژه ==========
    
    def save_project_switch(self, switch: ProjectSwitch):
        """ذخیره تغییر پروژه"""
        self.project_switches.append(switch.to_dict())
        self._save_json(self.project_switches_file, self.project_switches)
    
    def get_project_switches_for_date(self, date_str: str) -> List[ProjectSwitch]:
        """دریافت تغییرات پروژه برای یک تاریخ خاص"""
        switches = []
        for switch_data in self.project_switches:
            switch_timestamp = datetime.fromisoformat(switch_data["timestamp"])
            if switch_timestamp.date().isoformat() == date_str:
                switches.append(ProjectSwitch.from_dict(switch_data))
        return switches
    
    def count_project_switches_today(self) -> int:
        """تعداد تغییرات پروژه امروز"""
        today = date.today().isoformat()
        return len(self.get_project_switches_for_date(today))
    
    # ========== مدیریت Pause ==========
    
    def save_pause_event(self, event: PauseEvent):
        """ذخیره رویداد Pause"""
        self.pause_events.append(event.to_dict())
        self._save_json(self.pause_events_file, self.pause_events)
    
    def get_pause_events_for_date(self, date_str: str) -> List[PauseEvent]:
        """دریافت رویدادهای Pause برای یک تاریخ خاص"""
        events = []
        for event_data in self.pause_events:
            event_timestamp = datetime.fromisoformat(event_data["start_time"])
            if event_timestamp.date().isoformat() == date_str:
                events.append(PauseEvent.from_dict(event_data))
        return events
    
    def total_pause_minutes_today(self) -> int:
        """مجموع دقایق Pause امروز"""
        today = date.today().isoformat()
        events = self.get_pause_events_for_date(today)
        return sum(e.duration_minutes for e in events)
    
    # ========== مدیریت گزارش‌های روزانه ==========
    
    def save_daily_report(self, report: DailyReport):
        """ذخیره گزارش روزانه"""
        self.daily_reports[report.date] = report.to_dict()
        self._save_json(self.daily_reports_file, self.daily_reports)
    
    def get_daily_report(self, date_str: str) -> Optional[DailyReport]:
        """دریافت گزارش روزانه"""
        data = self.daily_reports.get(date_str)
        if data:
            return DailyReport.from_dict(data)
        return None
    
    def get_recent_daily_reports(self, days: int = 7) -> List[DailyReport]:
        """دریافت گزارش‌های روزانه اخیر"""
        reports = []
        today = date.today()
        for i in range(days):
            d = today - timedelta(days=i)
            report = self.get_daily_report(d.isoformat())
            if report:
                reports.append(report)
        return reports
    
    # ========== مدیریت گزارش‌های هفتگی ==========
    
    def save_weekly_report(self, report: WeeklyReport):
        """ذخیره گزارش هفتگی"""
        key = f"{report.week_start_date}_{report.week_end_date}"
        self.weekly_reports[key] = report.to_dict()
        self._save_json(self.weekly_reports_file, self.weekly_reports)
    
    def get_weekly_report(self, week_start: str, week_end: str) -> Optional[WeeklyReport]:
        """دریافت گزارش هفتگی"""
        key = f"{week_start}_{week_end}"
        data = self.weekly_reports.get(key)
        if data:
            return WeeklyReport.from_dict(data)
        return None
    
    # ========== مدیریت تنظیمات ==========
    
    def save_settings(self):
        """ذخیره تنظیمات"""
        self._save_json(self.settings_file, self.settings)
    
    def get_whitelist(self) -> List[str]:
        """دریافت لیست سفید"""
        return self.settings.get("whitelist", [])
    
    def set_whitelist(self, whitelist: List[str]):
        """تنظیم لیست سفید"""
        self.settings["whitelist"] = whitelist
        self.save_settings()
    
    def get_soft_blacklist(self) -> List[str]:
        """دریافت لیست سیاه نرم"""
        return self.settings.get("soft_blacklist", [])
    
    def set_soft_blacklist(self, blacklist: List[str]):
        """تنظیم لیست سیاه نرم"""
        self.settings["soft_blacklist"] = blacklist
        self.save_settings()
    
    def add_to_whitelist(self, item: str):
        """افزودن آیتم به لیست سفید"""
        if item not in self.settings["whitelist"]:
            self.settings["whitelist"].append(item)
            self.save_settings()
    
    def add_to_soft_blacklist(self, item: str):
        """افزودن آیتم به لیست سیاه نرم"""
        if item not in self.settings["soft_blacklist"]:
            self.settings["soft_blacklist"].append(item)
            self.save_settings()
    
    def remove_from_whitelist(self, item: str):
        """حذف آیتم از لیست سفید"""
        if item in self.settings["whitelist"]:
            self.settings["whitelist"].remove(item)
            self.save_settings()
    
    def remove_from_soft_blacklist(self, item: str):
        """حذف آیتم از لیست سیاه نرم"""
        if item in self.settings["soft_blacklist"]:
            self.settings["soft_blacklist"].remove(item)
            self.save_settings()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """دریافت یک تنظیم خاص"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """تنظیم یک مقدار خاص"""
        self.settings[key] = value
        self.save_settings()

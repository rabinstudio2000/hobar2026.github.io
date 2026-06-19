# موتور مداخله برای Focus Mentor

from datetime import datetime, timedelta
from typing import Optional, Tuple
from config import MESSAGES


class InterventionEngine:
    """تصمیم‌گیری درباره زمان نمایش overlay مداخله"""
    
    def __init__(self, storage=None):
        self.storage = storage
        self.last_intervention_time = None
        self.interventions_in_last_30_min = 0
        self.consecutive_work_claims = 0
        self.last_window_category = None
        self.current_suspicious_duration = 0.0
        self.suspicious_window_start = None
    
    def should_intervene(self, window_info: dict) -> Tuple[bool, str]:
        """
        تصمیم‌گیری درباره نیاز به مداخله
        
        Args:
            window_info: dict containing process_name, window_title, category, duration
        
        Returns:
            Tuple of (should_intervene: bool, reason: str)
        """
        from monitor import WindowCategory
        
        category = window_info.get("category")
        duration = window_info.get("duration", 0.0)
        process_name = window_info.get("process_name", "")
        window_title = window_info.get("window_title", "")
        
        # اگر پنجره مجاز یا کار اصلی است، نیازی به مداخله نیست
        if category in [WindowCategory.MAIN_WORK, WindowCategory.ALLOWED]:
            self.current_suspicious_duration = 0.0
            self.suspicious_window_start = None
            self.last_window_category = category
            return (False, "")
        
        # دریافت آستانه‌ها از تنظیمات
        soft_blacklist_threshold = self.storage.get_setting("soft_blacklist_threshold_seconds", 20) if self.storage else 20
        unknown_threshold = self.storage.get_setting("unknown_threshold_seconds", 90) if self.storage else 90
        max_overlays_per_30_min = self.storage.get_setting("max_overlays_per_30_minutes", 3) if self.storage else 3
        
        # تعیین آستانه بر اساس دسته‌بندی
        if category == WindowCategory.SOFT_BLACKLIST:
            threshold = soft_blacklist_threshold
        elif category == WindowCategory.UNKNOWN:
            threshold = unknown_threshold
        else:
            threshold = soft_blacklist_threshold  # پیش‌فرض
        
        # بررسی محدودیت نرخ مداخله
        recent_interventions = self._get_recent_interventions_count(30)
        if recent_interventions >= max_overlays_per_30_min:
            # بیش از حد مجاز، عدم نمایش overlay جدید
            return (False, "rate_limited")
        
        # بررسی مدت زمان روی پنجره مشکوک
        if self.last_window_category != category:
            # تغییر دسته‌بندی، بازنشانی تایمر
            self.current_suspicious_duration = 0.0
            self.suspicious_window_start = datetime.now()
        
        self.current_suspicious_duration = duration
        
        if self.current_suspicious_duration >= threshold:
            # زمان آستانه عبور کرده، نیاز به مداخله
            self.last_intervention_time = datetime.now()
            self.consecutive_work_claims = 0
            
            if category == WindowCategory.SOFT_BLACKLIST:
                reason = MESSAGES.get("distraction_detected", "این فعالیت مستقیماً به هدف امروز وصل نیست.")
            else:
                reason = "این ابزار در لیست ابزارهای روزانه نیست. آیا برای کار امروز ضروری است؟"
            
            return (True, reason)
        
        self.last_window_category = category
        return (False, "")
    
    def _get_recent_interventions_count(self, minutes: int = 30) -> int:
        """تعداد مداخله‌های اخیر"""
        if not self.storage:
            return 0
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        count = 0
        
        for intervention_data in self.storage.interventions[-100:]:  # بررسی آخرین ۱۰۰ مورد
            try:
                event_time = datetime.fromisoformat(intervention_data["timestamp"])
                if event_time >= cutoff:
                    count += 1
            except (ValueError, KeyError):
                continue
        
        return count
    
    def record_user_response(self, response: str, reason: str = None):
        """
        ثبت پاسخ کاربر به مداخله
        
        Args:
            response: "yes_claim_work" یا "no_return_to_work"
            reason: دلیل کاربر (اختیاری)
        """
        if response == "yes_claim_work":
            self.consecutive_work_claims += 1
        else:
            self.consecutive_work_claims = 0
    
    def get_work_claim_warning(self) -> Optional[str]:
        """
        بررسی نیاز به هشدار درباره ادعاهای مکرر کار اصلی
        
        Returns:
            پیام هشدار یا None
        """
        if self.consecutive_work_claims >= 3:
            return MESSAGES.get("too_many_claims", 
                "در مدت کوتاهی چند بار فعالیت‌های مشکوک را به‌عنوان کار اصلی تأیید کرده‌ای. "
                "ممکن است تعریف «کار اصلی» در حال بیش از حد گسترده شدن باشد.")
        return None
    
    def reset(self):
        """بازنشانی وضعیت موتور مداخله"""
        self.last_intervention_time = None
        self.interventions_in_last_30_min = 0
        self.consecutive_work_claims = 0
        self.last_window_category = None
        self.current_suspicious_duration = 0.0
        self.suspicious_window_start = None

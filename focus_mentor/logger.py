# ثبت رویدادها و گزارش‌دهی برای Focus Mentor

from datetime import datetime, date, timedelta
from typing import List, Dict
from collections import defaultdict

from models import DailyReport, WeeklyReport
from config import MESSAGES


class Logger:
    """ثبت رویدادها و تولید گزارش"""
    
    def __init__(self, storage=None):
        self.storage = storage
    
    def generate_daily_report(self, day_date: str = None) -> DailyReport:
        """
        تولید گزارش روزانه
        
        Args:
            day_date: تاریخ به صورت ISO format، یا امروز اگر None باشد
        
        Returns:
            DailyReport
        """
        if day_date is None:
            day_date = date.today().isoformat()
        
        # دریافت پروژه روزانه
        project = self.storage.get_daily_project(day_date) if self.storage else None
        project_name = project.project_name if project else "نامشخص"
        daily_goal = project.daily_goal if project else "هدف نامشخص"
        
        # دریافت رویدادهای پنجره
        window_events = self.storage.get_window_events_for_date(day_date) if self.storage else []
        
        # محاسبه زمان‌ها
        total_seconds = 0.0
        main_work_seconds = 0.0
        allowed_seconds = 0.0
        soft_blacklist_seconds = 0.0
        unknown_seconds = 0.0
        
        app_durations = defaultdict(float)
        
        for event in window_events:
            duration = event.duration_seconds
            total_seconds += duration
            app_durations[event.process_name] += duration
            
            if event.category == "main_work":
                main_work_seconds += duration
            elif event.category == "allowed":
                allowed_seconds += duration
            elif event.category == "soft_blacklist":
                soft_blacklist_seconds += duration
            else:
                unknown_seconds += duration
        
        # دریافت مداخله‌ها
        interventions = self.storage.get_interventions_for_date(day_date) if self.storage else []
        overlay_count = len(interventions)
        work_claim_count = sum(1 for i in interventions if i.user_response == "yes_claim_work")
        
        # دریافت تغییرات پروژه
        project_switches = self.storage.get_project_switches_for_date(day_date) if self.storage else []
        project_switch_count = len(project_switches)
        
        # دریافت Pauseها
        pause_events = self.storage.get_pause_events_for_date(day_date) if self.storage else []
        total_pause_minutes = sum(e.duration_minutes for e in pause_events)
        
        # پیدا کردن برنامه‌های حواس‌پرتی برتر
        distracting_apps = sorted(
            [(app, dur) for app, dur in app_durations.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        top_distracting_apps = [app for app, _ in distracting_apps]
        
        # تولید هشدارهای تحلیلی
        analytical_warnings = []
        
        # هشدار Work-Claim زیاد
        if work_claim_count >= 3:
            analytical_warnings.append(MESSAGES.get("too_many_claims"))
        
        # هشدار Focus Ratio پایین
        if total_seconds > 0:
            focus_ratio = main_work_seconds / total_seconds
            if focus_ratio < 0.5:
                analytical_warnings.append(MESSAGES.get("low_focus_ratio"))
        
        # هشدار تغییر پروژه زیاد
        if project_switch_count >= 2:
            analytical_warnings.append(
                "امروز چند بار پروژه را تغییر دادی. این می‌تواند نشانه‌ی فرار از شروع یا سختی پروژه‌ی اصلی باشد."
            )
        
        # هشدار Pause زیاد
        estimated_work_minutes = total_seconds / 60
        if estimated_work_minutes > 0 and total_pause_minutes / estimated_work_minutes > 0.2:
            analytical_warnings.append(MESSAGES.get("pause_limit_warning"))
        
        # ساخت گزارش
        report = DailyReport(
            date=day_date,
            project_name=project_name,
            daily_goal=daily_goal,
            total_tracked_seconds=total_seconds,
            main_work_seconds=main_work_seconds,
            allowed_tool_seconds=allowed_seconds,
            soft_blacklist_seconds=soft_blacklist_seconds,
            unknown_seconds=unknown_seconds,
            focus_ratio=main_work_seconds / total_seconds if total_seconds > 0 else 0.0,
            overlay_count=overlay_count,
            work_claim_count=work_claim_count,
            project_switch_count=project_switch_count,
            total_pause_minutes=total_pause_minutes,
            top_distracting_apps=top_distracting_apps,
            analytical_warnings=analytical_warnings
        )
        
        return report
    
    def generate_weekly_report(self, end_date: date = None) -> WeeklyReport:
        """
        تولید گزارش هفتگی
        
        Args:
            end_date: تاریخ پایان هفته، یا امروز اگر None باشد
        
        Returns:
            WeeklyReport
        """
        if end_date is None:
            end_date = date.today()
        
        # محاسبه شروع هفته (شنبه در ایران، اما اینجا از دوشنبه استفاده می‌کنیم)
        days_since_monday = end_date.weekday()
        start_date = end_date - timedelta(days=days_since_monday)
        
        week_start_str = start_date.isoformat()
        week_end_str = end_date.isoformat()
        
        # دریافت گزارش‌های روزانه
        daily_reports = []
        current_date = start_date
        while current_date <= end_date:
            report = self.storage.get_daily_report(current_date.isoformat()) if self.storage else None
            if report:
                daily_reports.append(report)
            current_date += timedelta(days=1)
        
        if not daily_reports:
            return WeeklyReport(
                week_start_date=week_start_str,
                week_end_date=week_end_str
            )
        
        # محاسبات
        total_main_work = sum(r.main_work_seconds for r in daily_reports)
        total_distraction = sum(r.soft_blacklist_seconds + r.unknown_seconds for r in daily_reports)
        total_overlays = sum(r.overlay_count for r in daily_reports)
        total_work_claims = sum(r.work_claim_count for r in daily_reports)
        total_project_switches = sum(r.project_switch_count for r in daily_reports)
        
        average_focus_ratio = sum(r.focus_ratio for r in daily_reports) / len(daily_reports)
        
        # پیدا کردن برنامه‌های حواس‌پرتی برتر در هفته
        app_weekly_durations = defaultdict(float)
        for report in daily_reports:
            for app in report.top_distracting_apps:
                # تقریباً اضافه می‌کنیم
                app_weekly_durations[app] += 1
        
        most_distracting_apps = sorted(
            app_weekly_durations.keys(),
            key=lambda x: app_weekly_durations[x],
            reverse=True
        )[:5]
        
        # بهترین و بدترین روزها از نظر تمرکز
        sorted_by_focus = sorted(daily_reports, key=lambda r: r.focus_ratio, reverse=True)
        best_focus_days = [r.date for r in sorted_by_focus[:2]] if len(sorted_by_focus) >= 2 else [sorted_by_focus[0].date] if sorted_by_focus else []
        worst_focus_days = [r.date for r in sorted_by_focus[-2:]] if len(sorted_by_focus) >= 2 else [sorted_by_focus[0].date] if sorted_by_focus else []
        
        return WeeklyReport(
            week_start_date=week_start_str,
            week_end_date=week_end_str,
            average_focus_ratio=average_focus_ratio,
            total_main_work_seconds=total_main_work,
            total_distraction_seconds=total_distraction,
            most_distracting_apps=most_distracting_apps,
            total_overlay_count=total_overlays,
            total_work_claim_count=total_work_claims,
            total_project_switch_count=total_project_switches,
            best_focus_days=best_focus_days,
            worst_focus_days=worst_focus_days
        )
    
    def format_daily_report_text(self, report: DailyReport) -> str:
        """فرمت کردن گزارش روزانه به صورت متنی"""
        lines = [
            "=" * 50,
            "گزارش پایان روز کاری",
            "=" * 50,
            f"تاریخ: {report.date}",
            f"پروژه: {report.project_name}",
            f"هدف: {report.daily_goal}",
            "",
            "⏱️ زمان‌بندی:",
            f"  کل زمان پایش‌شده: {self._format_seconds(report.total_tracked_seconds)}",
            f"  زمان کار اصلی: {self._format_seconds(report.main_work_seconds)}",
            f"  زمان ابزارهای مجاز: {self._format_seconds(report.allowed_tool_seconds)}",
            f"  زمان ابزارهای مشکوک: {self._format_seconds(report.soft_blacklist_seconds)}",
            f"  زمان ناشناخته: {self._format_seconds(report.unknown_seconds)}",
            "",
            f"📊 Focus Ratio: {report.focus_ratio:.1%}",
            "",
            "📈 آمار:",
            f"  تعداد overlayها: {report.overlay_count}",
            f"  تعداد تأییدیه‌های کار اصلی: {report.work_claim_count}",
            f"  تعداد تغییر پروژه: {report.project_switch_count}",
            f"  مجموع Pause: {report.total_pause_minutes} دقیقه",
            "",
        ]
        
        if report.top_distracting_apps:
            lines.append("🔝 پرحاشیه‌ترین برنامه‌ها:")
            for i, app in enumerate(report.top_distracting_apps[:5], 1):
                lines.append(f"  {i}. {app}")
            lines.append("")
        
        if report.analytical_warnings:
            lines.append("⚠️ هشدارهای تحلیلی:")
            for warning in report.analytical_warnings:
                lines.append(f"  • {warning}")
            lines.append("")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def _format_seconds(self, seconds: float) -> str:
        """فرمت کردن ثانیه به ساعت و دقیقه"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours} ساعت و {minutes} دقیقه"
        else:
            return f"{minutes} دقیقه"

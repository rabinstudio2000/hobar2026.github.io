# برنامه System Tray برای Focus Mentor

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime, date
from typing import Optional

try:
    import pystray
    from pystray import Icon, MenuItem, Menu
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

from models import DailyProject, InterventionEvent, ProjectSwitch
from config import MESSAGES
from storage import Storage
from monitor import WindowMonitor, WindowCategory
from intervention import InterventionEngine
from timer import WorkTimer, TimerMode
from overlay import InterventionOverlay, ReturnToWorkNotification
from settings_ui import SettingsWindow
from logger import Logger


class FocusMentorTrayApp:
    """برنامه System Tray منتور تمرکز"""
    
    def __init__(self):
        self.storage = Storage()
        self.monitor = WindowMonitor(self.storage)
        self.intervention_engine = InterventionEngine(self.storage)
        self.timer = WorkTimer(self.storage)
        self.logger = Logger(self.storage)
        
        self.is_workday_started = False
        self.current_project: Optional[DailyProject] = None
        self.is_paused = False
        self.pause_end_time = None
        
        self.icon = None
        self.monitor_thread = None
        self.stop_monitoring = False
        
        # بررسی پروژه امروز
        self._check_existing_project()
    
    def _check_existing_project(self):
        """بررسی وجود پروژه از روز قبل"""
        today = date.today().isoformat()
        project = self.storage.get_today_project()
        
        if project and not project.end_time:
            # روز کاری قبلی تمام نشده، ادامه می‌دهیم
            self.is_workday_started = True
            self.current_project = project
    
    def run(self):
        """اجرای برنامه"""
        if not PYSTRAY_AVAILABLE:
            # حالت fallback بدون pystray
            self._run_fallback_mode()
            return
        
        # ایجاد منوی tray
        menu = Menu(
            MenuItem("شروع روز کاری", self._on_start_workday, enabled=not self.is_workday_started),
            MenuItem("پایان روز کاری", self._on_end_workday, enabled=self.is_workday_started),
            MenuItem("Pause موقت", self._on_pause, enabled=self.is_workday_started and not self.is_paused),
            MenuItem("ادامه", self._on_resume, enabled=self.is_paused),
            Menu.SEPARATOR,
            MenuItem("مشاهده گزارش امروز", self._on_show_today_report, enabled=self.is_workday_started),
            MenuItem("تنظیمات", self._on_settings),
            Menu.SEPARATOR,
            MenuItem("خروج", self._on_exit)
        )
        
        # ایجاد آیکون
        self.icon = Icon("FocusMentor", menu=menu, title="منتور تمرکز")
        
        # اجرای آیکون در thread جداگانه
        self.icon.run_detached()
        
        # اگر روز کاری از قبل شروع شده، پایش را شروع کن
        if self.is_workday_started:
            self._start_monitoring()
        
        # نگه داشتن برنامه
        try:
            while True:
                time.sleep(1)
                if not self.icon.visible:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()
    
    def _run_fallback_mode(self):
        """حالت fallback وقتی pystray موجود نیست"""
        root = tk.Tk()
        root.withdraw()
        
        messagebox.showinfo(
            "منتور تمرکز",
            "pystray نصب نیست. لطفاً دستور pip install pystray را اجرا کنید.\n\n"
            "در حال حاضر برنامه در حالت محدود اجرا می‌شود."
        )
        
        # ایجاد پنجره ساده
        window = tk.Toplevel(root)
        window.title("منتور تمرکز")
        window.geometry("400x300")
        
        label = ttk.Label(
            window,
            text="منتور تمرکز در حال اجرا است\n\nبرای نصب کامل:\npip install pystray pywin32 psutil",
            justify='center'
        )
        label.pack(expand=True)
        
        start_btn = ttk.Button(
            window,
            text="شروع روز کاری",
            command=lambda: self._show_lockin_dialog(window)
        )
        start_btn.pack(pady=10)
        
        report_btn = ttk.Button(
            window,
            text="گزارش امروز",
            command=self._on_show_today_report
        )
        report_btn.pack(pady=5)
        
        settings_btn = ttk.Button(
            window,
            text="تنظیمات",
            command=self._on_settings
        )
        settings_btn.pack(pady=5)
        
        exit_btn = ttk.Button(
            window,
            text="خروج",
            command=self._on_exit
        )
        exit_btn.pack(pady=10)
        
        root.mainloop()
    
    def _show_lockin_dialog(self, parent=None):
        """نمایش فرم Daily Lock-in"""
        dialog = tk.Toplevel(parent or tk.Tk())
        dialog.title("شروع روز کاری - قفل پروژه")
        dialog.geometry("500x400")
        dialog.transient(dialog.master)
        dialog.grab_set()
        
        # عنوان
        title_label = ttk.Label(
            dialog,
            text="برنامه‌ریزی روز کاری",
            font=('Segoe UI', 14, 'bold')
        )
        title_label.pack(pady=(20, 10))
        
        # حریم خصوصی
        privacy_label = ttk.Label(
            dialog,
            text=MESSAGES.get("privacy_notice"),
            wraplength=450,
            justify='center',
            foreground='#666',
            font=('Segoe UI', 9)
        )
        privacy_label.pack(pady=(0, 20))
        
        # فرم
        form_frame = ttk.Frame(dialog, padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # نام پروژه
        ttk.Label(form_frame, text="نام پروژه امروز (*):").pack(anchor='w', pady=(0, 5))
        project_entry = ttk.Entry(form_frame, width=50)
        project_entry.pack(fill=tk.X, pady=(0, 15))
        
        # هدف روز
        ttk.Label(form_frame, text="هدف مشخص امروز (*):").pack(anchor='w', pady=(0, 5))
        goal_entry = ttk.Entry(form_frame, width=50)
        goal_entry.pack(fill=tk.X, pady=(0, 15))
        
        # مدت زمان تقریبی
        ttk.Label(form_frame, text="مدت‌زمان تقریبی کار (دقیقه):").pack(anchor='w', pady=(0, 5))
        duration_var = tk.IntVar(value=180)
        duration_spinbox = ttk.Spinbox(form_frame, from_=30, to=720, textvariable=duration_var, width=20)
        duration_spinbox.pack(anchor='w', pady=(0, 15))
        
        # ابزارهای اصلی
        ttk.Label(form_frame, text="ابزارهای اصلی (اختیاری):").pack(anchor='w', pady=(0, 5))
        tools_entry = ttk.Entry(form_frame, width=50)
        tools_entry.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(
            form_frame,
            text="مثال: illustrator, figma, photoshop",
            foreground='#666',
            font=('Segoe UI', 8)
        ).pack(anchor='w', pady=(0, 5))
        
        # فعالیت‌های ممنوعه
        ttk.Label(form_frame, text="فعالیت‌هایی که نباید منحرف شوی (اختیاری):").pack(anchor='w', pady=(0, 5))
        forbidden_entry = ttk.Entry(form_frame, width=50)
        forbidden_entry.pack(fill=tk.X, pady=(0, 15))
        
        def on_submit():
            project_name = project_entry.get().strip()
            daily_goal = goal_entry.get().strip()
            
            if not project_name or not daily_goal:
                messagebox.showerror("خطا", "لطفاً نام پروژه و هدف روز را وارد کنید.")
                return
            
            # ایجاد پروژه
            today = date.today().isoformat()
            main_tools = [t.strip().lower() for t in tools_entry.get().split(',') if t.strip()]
            forbidden = [f.strip().lower() for f in forbidden_entry.get().split(',') if f.strip()]
            
            self.current_project = DailyProject(
                date=today,
                project_name=project_name,
                daily_goal=daily_goal,
                estimated_duration_minutes=duration_var.get(),
                main_tools=main_tools,
                forbidden_activities=forbidden,
                start_time=datetime.now()
            )
            
            # ذخیره
            self.storage.save_daily_project(self.current_project)
            
            # افزودن ابزارهای اصلی به whitelist اگر خواسته شود
            for tool in main_tools:
                if tool and not tool.endswith('.exe'):
                    self.storage.add_to_whitelist(f"{tool}.exe")
            
            self.is_workday_started = True
            
            messagebox.showinfo("موفق", MESSAGES.get("project_locked", "پروژه امروز قفل شد. موفق باشی."))
            dialog.destroy()
            
            # شروع پایش
            self._start_monitoring()
            
            # بروزرسانی منو
            if self.icon:
                self.icon.update_menu()
        
        # دکمه‌ها
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=(10, 20))
        
        submit_btn = ttk.Button(btn_frame, text="شروع روز کاری", command=on_submit)
        submit_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = ttk.Button(btn_frame, text="لغو", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT)
        
        dialog.mainloop()
    
    def _start_monitoring(self):
        """شروع پایش پنجره‌ها"""
        self.stop_monitoring = False
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
    
    def _monitoring_loop(self):
        """حلقه پایش پنجره‌ها"""
        interval = self.storage.get_setting("monitor_interval_seconds", 5)
        
        while not self.stop_monitoring:
            if self.is_paused:
                # بررسی پایان Pause
                if self.pause_end_time and datetime.now() >= self.pause_end_time:
                    self._on_pause_end()
                else:
                    time.sleep(1)
                    continue
            
            if not self.is_workday_started or not self.current_project:
                time.sleep(interval)
                continue
            
            # بررسی پنجره فعال
            window_info = self.monitor.check_and_log(self.current_project.project_name)
            
            if window_info:
                # بررسی نیاز به مداخله
                should_intervene, reason = self.intervention_engine.should_intervene(window_info)
                
                if should_intervene and reason != "rate_limited":
                    # نمایش overlay
                    self._show_intervention_overlay(reason)
            
            time.sleep(interval)
    
    def _show_intervention_overlay(self, message: str):
        """نمایش overlay مداخله"""
        def show():
            overlay = InterventionOverlay(
                project_name=self.current_project.project_name if self.current_project else "",
                daily_goal=self.current_project.daily_goal if self.current_project else ""
            )
            
            response, reason = overlay.show(message)
            
            if response:
                # ثبت پاسخ
                intervention = InterventionEvent(
                    timestamp=datetime.now(),
                    process_name=self.monitor.last_process_name or "",
                    window_title=self.monitor.last_window_title or "",
                    user_response=response,
                    user_reason=reason
                )
                self.storage.save_intervention(intervention)
                
                # ثبت در موتور مداخله
                self.intervention_engine.record_user_response(response, reason)
                
                # نمایش پیام بازگشت به کار اگر کاربر "نه" را انتخاب کرد
                if response == "no_return_to_work":
                    ReturnToWorkNotification.show()
                
                # بررسی هشدار work-claim
                warning = self.intervention_engine.get_work_claim_warning()
                if warning:
                    messagebox.showwarning("هشدار منتور", warning)
        
        # اجرا در thread اصلی
        if threading.current_thread() is threading.main_thread():
            show()
        else:
            threading.Thread(target=show).start()
    
    def _on_start_workday(self, icon=None, item=None):
        """شروع روز کاری"""
        self._show_lockin_dialog()
    
    def _on_end_workday(self, icon=None, item=None):
        """پایان روز کاری"""
        if not self.is_workday_started:
            return
        
        # توقف پایش
        self.stop_monitoring = True
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        # توقف تایمر
        self.timer.stop()
        
        # ثبت پایان پروژه
        if self.current_project:
            self.current_project.end_time = datetime.now()
            self.storage.save_daily_project(self.current_project)
        
        # تولید گزارش
        report = self.logger.generate_daily_report()
        self.storage.save_daily_report(report)
        
        # نمایش گزارش
        report_text = self.logger.format_daily_report_text(report)
        
        dialog = tk.Tk()
        dialog.title("گزارش پایان روز")
        dialog.geometry("600x500")
        
        text_widget = tk.Text(dialog, wrap=tk.WORD, padx=20, pady=20, font=('Segoe UI', 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert('1.0', report_text)
        text_widget.config(state='disabled')
        
        close_btn = ttk.Button(dialog, text="بستن", command=dialog.destroy)
        close_btn.pack(pady=10)
        
        # بازنشانی وضعیت
        self.is_workday_started = False
        self.current_project = None
        self.is_paused = False
        self.monitor.reset()
        self.intervention_engine.reset()
        
        # بروزرسانی منو
        if self.icon:
            self.icon.update_menu()
        
        dialog.mainloop()
    
    def _on_pause(self, icon=None, item=None):
        """شروع Pause"""
        if not self.is_workday_started or self.is_paused:
            return
        
        pause_minutes = self.storage.get_setting("pause_minutes", 10)
        self.is_paused = True
        self.pause_end_time = datetime.now() + threading.timedelta(minutes=pause_minutes)
        
        self.timer.pause()
        self.monitor.reset()
        
        if self.icon:
            self.icon.update_menu()
        
        messagebox.showinfo(
            "Pause",
            f"برنامه به مدت {pause_minutes} دقیقه متوقف شد.\n"
            f"پس از این مدت، پایش خودکار возобновится."
        )
    
    def _on_resume(self, icon=None, item=None):
        """پایان Pause"""
        if not self.is_paused:
            return
        
        self.is_paused = False
        self.pause_end_time = None
        self.timer.resume()
        
        if self.icon:
            self.icon.update_menu()
    
    def _on_pause_end(self):
        """پایان زمان Pause"""
        self.is_paused = False
        self.pause_end_time = None
        self.timer.resume()
        
        if self.icon:
            self.icon.update_menu()
    
    def _on_show_today_report(self, icon=None, item=None):
        """نمایش گزارش امروز"""
        if not self.is_workday_started:
            messagebox.showinfo("گزارش", "روز کاری هنوز شروع نشده است.")
            return
        
        report = self.logger.generate_daily_report()
        report_text = self.logger.format_daily_report_text(report)
        
        dialog = tk.Tk()
        dialog.title("گزارش امروز")
        dialog.geometry("600x500")
        
        text_widget = tk.Text(dialog, wrap=tk.WORD, padx=20, pady=20, font=('Segoe UI', 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert('1.0', report_text)
        text_widget.config(state='disabled')
        
        close_btn = ttk.Button(dialog, text="بستن", command=dialog.destroy)
        close_btn.pack(pady=10)
        
        dialog.mainloop()
    
    def _on_settings(self, icon=None, item=None):
        """نمایش تنظیمات"""
        def on_save():
            # اعمال تنظیمات جدید
            pass
        
        settings_window = SettingsWindow(self.storage, on_save)
        settings_window.show()
    
    def _on_exit(self, icon=None, item=None):
        """خروج از برنامه"""
        self.stop_monitoring = True
        
        # اگر روز کاری شروع شده، هشدار بده
        if self.is_workday_started:
            result = messagebox.askyesno(
                "تأیید خروج",
                "روز کاری هنوز تمام نشده است. آیا مطمئنی می‌خواهی خارج شوی؟\n"
                "پیشنهاد می‌شود ابتدا روز کاری را پایان دهی."
            )
            if not result:
                return
        
        self._cleanup()
        
        if self.icon:
            self.icon.stop()
    
    def _cleanup(self):
        """پاکسازی منابع"""
        self.stop_monitoring = True
        self.timer.stop()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

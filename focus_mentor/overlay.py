# نمایش Overlay مداخله برای Focus Mentor

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import Optional, Callable
import threading


class InterventionOverlay:
    """نمایش پنجره مداخله روی صفحه"""
    
    def __init__(self, project_name: str = "", daily_goal: str = ""):
        self.project_name = project_name
        self.daily_goal = daily_goal
        self.root = None
        self.result = None
        self.reason = None
    
    def show(self, message: str, on_yes: Callable = None, on_no: Callable = None) -> tuple:
        """
        نمایش overlay و دریافت پاسخ کاربر
        
        Args:
            message: پیام اصلی overlay
            on_yes: callback برای گزینه بله
            on_no: callback برای گزینه نه
        
        Returns:
            Tuple of (response: str, reason: str or None)
        """
        self.result = None
        self.reason = None
        
        # ایجاد پنجره در thread اصلی
        if threading.current_thread() is threading.main_thread():
            self._create_overlay(message)
        else:
            # استفاده از invoke برای اجرای در thread اصلی
            event = threading.Event()
            def create():
                self._create_overlay(message)
                event.set()
            threading.Thread(target=create).start()
            event.wait()
        
        return (self.result, self.reason)
    
    def _create_overlay(self, message: str):
        """ایجاد پنجره overlay"""
        self.root = tk.Tk()
        self.root.title("منتور تمرکز - توجه")
        
        # تنظیمات پنجره
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(False)  # حفظ نوار عنوان
        self.root.resizable(False, False)
        
        # مرکزیت پنجره
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 500
        window_height = 350
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # رنگ پس‌زمینه
        self.root.configure(bg='#f5f5f5')
        
        # فریم اصلی
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # عنوان
        title_label = ttk.Label(
            main_frame,
            text="⚠️ منتور تمرکز",
            font=('Segoe UI', 16, 'bold'),
            background='#f5f5f5',
            foreground='#c62828'
        )
        title_label.pack(pady=(0, 15))
        
        # پیام اصلی
        message_label = ttk.Label(
            main_frame,
            text=message,
            font=('Segoe UI', 11),
            background='#f5f5f5',
            wraplength=450,
            justify='center'
        )
        message_label.pack(pady=(0, 15))
        
        # اطلاعات پروژه
        if self.project_name or self.daily_goal:
            info_frame = ttk.LabelFrame(main_frame, text="پروژه امروز", padding="10")
            info_frame.pack(fill=tk.X, pady=(0, 15))
            
            if self.project_name:
                project_label = ttk.Label(
                    info_frame,
                    text=f"پروژه: {self.project_name}",
                    font=('Segoe UI', 10),
                    background='#f5f5f5'
                )
                project_label.pack(anchor='w')
            
            if self.daily_goal:
                goal_label = ttk.Label(
                    info_frame,
                    text=f"هدف: {self.daily_goal}",
                    font=('Segoe UI', 10),
                    background='#f5f5f5'
                )
                goal_label.pack(anchor='w')
        
        # سوال
        question_label = ttk.Label(
            main_frame,
            text="آیا این کاری که الان انجام می‌دهی واقعاً بخشی از هدف امروز است؟",
            font=('Segoe UI', 10, 'italic'),
            background='#f5f5f5',
            wraplength=450,
            justify='center'
        )
        question_label.pack(pady=(0, 15))
        
        # دکمه‌ها
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        yes_btn = ttk.Button(
            button_frame,
            text="بله، بخشی از کار اصلی است",
            command=self._on_yes_click,
            width=25
        )
        yes_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        no_btn = ttk.Button(
            button_frame,
            text="نه، برگردم به کار اصلی",
            command=self._on_no_click,
            width=25
        )
        no_btn.pack(side=tk.LEFT)
        
        # شروع حلقه اصلی
        self.root.mainloop()
    
    def _on_yes_click(self):
        """دکمه بله کلیک شد"""
        # درخواست دلیل کوتاه
        reason = simpledialog.askstring(
            "ثبت دلیل",
            "لطفاً دلیل کوتاهی بنویسید که چرا این فعالیت بخشی از کار اصلی است:",
            parent=self.root
        )
        
        if reason is not None:  # کاربر کنسل نکرد
            self.result = "yes_claim_work"
            self.reason = reason.strip() if reason else ""
        
        self.root.destroy()
    
    def _on_no_click(self):
        """دکمه نه کلیک شد"""
        self.result = "no_return_to_work"
        self.reason = None
        self.root.destroy()


class ReturnToWorkNotification:
    """نمایش پیام کوتاه بازگشت به کار"""
    
    @staticmethod
    def show(message: str = None):
        """نمایش پیام کوتاه"""
        if message is None:
            message = "خوب است. حالا به پروژه‌ی قفل‌شده‌ی امروز برگرد."
        
        root = tk.Tk()
        root.withdraw()  # مخفی کردن پنجره اصلی
        
        # ایجاد پنجره کوچک
        notify = tk.Toplevel(root)
        notify.title("منتور تمرکز")
        notify.attributes('-topmost', True)
        notify.overrideredirect(True)
        notify.resizable(False, False)
        
        # تنظیمات
        screen_width = notify.winfo_screenwidth()
        screen_height = notify.winfo_screenheight()
        window_width = 350
        window_height = 80
        x = screen_width - window_width - 20
        y = screen_height - window_height - 100
        notify.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        notify.configure(bg='#4caf50')
        
        label = tk.Label(
            notify,
            text=message,
            font=('Segoe UI', 11),
            background='#4caf50',
            foreground='white',
            wraplength=330,
            justify='center'
        )
        label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # بستن خودکار بعد از ۳ ثانیه
        notify.after(3000, lambda: notify.destroy())
        root.after(3000, lambda: root.destroy())
        
        root.mainloop()

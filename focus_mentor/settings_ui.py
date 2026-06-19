# رابط کاربری تنظیمات برای Focus Mentor

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable


class SettingsWindow:
    """پنجره تنظیمات برنامه"""
    
    def __init__(self, storage, on_save: Callable = None):
        self.storage = storage
        self.on_save = on_save
        self.root = None
    
    def show(self):
        """نمایش پنجره تنظیمات"""
        self.root = tk.Tk()
        self.root.title("تنظیمات منتور تمرکز")
        
        # تنظیمات پنجره
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 600
        window_height = 500
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.root.resizable(True, True)
        
        # ایجاد TabControl
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # تب‌های مختلف
        general_frame = ttk.Frame(notebook, padding="10")
        whitelist_frame = ttk.Frame(notebook, padding="10")
        blacklist_frame = ttk.Frame(notebook, padding="10")
        thresholds_frame = ttk.Frame(notebook, padding="10")
        
        notebook.add(general_frame, text="عمومی")
        notebook.add(whitelist_frame, text="لیست سفید")
        notebook.add(blacklist_frame, text="لیست سیاه نرم")
        notebook.add(thresholds_frame, text="آستانه‌ها")
        
        # ========== تب عمومی ==========
        self._setup_general_tab(general_frame)
        
        # ========== تب لیست سفید ==========
        self._setup_whitelist_tab(whitelist_frame)
        
        # ========== تب لیست سیاه ==========
        self._setup_blacklist_tab(blacklist_frame)
        
        # ========== تب آستانه‌ها ==========
        self._setup_thresholds_tab(thresholds_frame)
        
        # دکمه ذخیره
        save_btn = ttk.Button(
            self.root,
            text="ذخیره تنظیمات",
            command=self._on_save_click
        )
        save_btn.pack(pady=(0, 10))
        
        self.root.mainloop()
    
    def _setup_general_tab(self, frame):
        """تنظیم تب عمومی"""
        # حالت تایمر
        timer_label = ttk.Label(frame, text="حالت تایمر:")
        timer_label.pack(anchor='w', pady=(0, 5))
        
        self.timer_mode_var = tk.StringVar(value="free")
        timer_combo = ttk.Combobox(
            frame,
            textvariable=self.timer_mode_var,
            values=["free", "pomodoro"],
            state="readonly",
            width=30
        )
        timer_combo.pack(anchor='w', pady=(0, 15))
        
        # مدت زمان Pause
        pause_label = ttk.Label(frame, text="مدت زمان Pause (دقیقه):")
        pause_label.pack(anchor='w', pady=(0, 5))
        
        self.pause_minutes_var = tk.IntVar(value=self.storage.get_setting("pause_minutes", 10))
        pause_spinbox = ttk.Spinbox(
            frame,
            from_=1,
            to=30,
            textvariable=self.pause_minutes_var,
            width=30
        )
        pause_spinbox.pack(anchor='w', pady=(0, 15))
        
        # حداکثر تغییر پروژه
        switch_label = ttk.Label(frame, text="حداکثر تغییر پروژه در روز:")
        switch_label.pack(anchor='w', pady=(0, 5))
        
        self.max_switches_var = tk.IntVar(value=self.storage.get_setting("max_project_switches_per_day", 2))
        switch_spinbox = ttk.Spinbox(
            frame,
            from_=1,
            to=10,
            textvariable=self.max_switches_var,
            width=30
        )
        switch_spinbox.pack(anchor='w')
        
        # حریم خصوصی
        privacy_text = (
            "این برنامه فقط نام برنامه فعال، عنوان پنجره و مدت‌زمان استفاده را ثبت می‌کند.\n"
            "هیچ متن تایپ‌شده، محتوای صفحه، رمز، اسکرین‌شات یا داده‌ی شخصی حساس ذخیره نمی‌شود.\n"
            "همه داده‌ها به‌صورت محلی روی سیستم شما باقی می‌مانند."
        )
        privacy_label = ttk.Label(
            frame,
            text=privacy_text,
            wraplength=500,
            justify='left',
            foreground='#666'
        )
        privacy_label.pack(pady=(20, 0), anchor='w')
    
    def _setup_whitelist_tab(self, frame):
        """تنظیم تب لیست سفید"""
        info_label = ttk.Label(
            frame,
            text="ابزارهایی که در این لیست قرار می‌گیرند همیشه مجاز هستند:",
            wraplength=500
        )
        info_label.pack(anchor='w', pady=(0, 10))
        
        # لیست‌باکس
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.whitelist_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            width=50,
            height=15
        )
        self.whitelist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.whitelist_listbox.yview)
        
        # پر کردن لیست
        whitelist = self.storage.get_whitelist()
        for item in whitelist:
            self.whitelist_listbox.insert(tk.END, item)
        
        # دکمه‌ها
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        add_btn = ttk.Button(btn_frame, text="افزودن", command=self._add_to_whitelist)
        add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        remove_btn = ttk.Button(btn_frame, text="حذف", command=self._remove_from_whitelist)
        remove_btn.pack(side=tk.LEFT)
    
    def _setup_blacklist_tab(self, frame):
        """تنظیم تب لیست سیاه نرم"""
        info_label = ttk.Label(
            frame,
            text="ابزارهایی که در این لیست قرار می‌گیرند پس از مدتی هشدار نمایش می‌دهند:",
            wraplength=500
        )
        info_label.pack(anchor='w', pady=(0, 10))
        
        # لیست‌باکس
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.blacklist_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            width=50,
            height=15
        )
        self.blacklist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.blacklist_listbox.yview)
        
        # پر کردن لیست
        blacklist = self.storage.get_soft_blacklist()
        for item in blacklist:
            self.blacklist_listbox.insert(tk.END, item)
        
        # دکمه‌ها
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        add_btn = ttk.Button(btn_frame, text="افزودن", command=self._add_to_blacklist)
        add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        remove_btn = ttk.Button(btn_frame, text="حذف", command=self._remove_from_blacklist)
        remove_btn.pack(side=tk.LEFT)
    
    def _setup_thresholds_tab(self, frame):
        """تنظیم تب آستانه‌ها"""
        # آستانه soft blacklist
        soft_label = ttk.Label(frame, text="آستانه زمانی برای ابزارهای مشکوک (ثانیه):")
        soft_label.pack(anchor='w', pady=(0, 5))
        
        self.soft_threshold_var = tk.IntVar(value=self.storage.get_setting("soft_blacklist_threshold_seconds", 20))
        soft_spinbox = ttk.Spinbox(
            frame,
            from_=10,
            to=180,
            textvariable=self.soft_threshold_var,
            width=30
        )
        soft_spinbox.pack(anchor='w', pady=(0, 15))
        
        # آستانه unknown
        unknown_label = ttk.Label(frame, text="آستانه زمانی برای ابزارهای ناشناخته (ثانیه):")
        unknown_label.pack(anchor='w', pady=(0, 5))
        
        self.unknown_threshold_var = tk.IntVar(value=self.storage.get_setting("unknown_threshold_seconds", 90))
        unknown_spinbox = ttk.Spinbox(
            frame,
            from_=10,
            to=300,
            textvariable=self.unknown_threshold_var,
            width=30
        )
        unknown_spinbox.pack(anchor='w', pady=(0, 15))
        
        # حداکثر overlay
        overlay_label = ttk.Label(frame, text="حداکثر تعداد overlay در هر ۳۰ دقیقه:")
        overlay_label.pack(anchor='w', pady=(0, 5))
        
        self.max_overlay_var = tk.IntVar(value=self.storage.get_setting("max_overlays_per_30_minutes", 3))
        overlay_spinbox = ttk.Spinbox(
            frame,
            from_=1,
            to=10,
            textvariable=self.max_overlay_var,
            width=30
        )
        overlay_spinbox.pack(anchor='w')
        
        # راهنما
        hint_text = (
            "نکته: آستانه خیلی کوتاه ممکن است باعث مزاحمت زیاد شود.\n"
            "پیشنهاد می‌شود مقدار بین ۱۵ تا ۶۰ ثانیه برای ابزارهای مشکوک باشد."
        )
        hint_label = ttk.Label(
            frame,
            text=hint_text,
            wraplength=500,
            justify='left',
            foreground='#666'
        )
        hint_label.pack(pady=(20, 0), anchor='w')
    
    def _add_to_whitelist(self):
        """افزودن آیتم به لیست سفید"""
        dialog = tk.Toplevel(self.root)
        dialog.title("افزودن به لیست سفید")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        label = ttk.Label(dialog, text="نام برنامه یا عبارت:")
        label.pack(pady=(10, 5))
        
        entry = ttk.Entry(dialog, width=40)
        entry.pack(pady=(0, 10))
        entry.focus()
        
        def on_ok():
            value = entry.get().strip().lower()
            if value:
                self.storage.add_to_whitelist(value)
                self.whitelist_listbox.insert(tk.END, value)
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack()
        
        ok_btn = ttk.Button(btn_frame, text="افزودن", command=on_ok)
        ok_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_btn = ttk.Button(btn_frame, text="لغو", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT)
    
    def _remove_from_whitelist(self):
        """حذف از لیست سفید"""
        selection = self.whitelist_listbox.curselection()
        if selection:
            index = selection[0]
            item = self.whitelist_listbox.get(index)
            self.storage.remove_from_whitelist(item)
            self.whitelist_listbox.delete(index)
    
    def _add_to_blacklist(self):
        """افزودن آیتم به لیست سیاه"""
        dialog = tk.Toplevel(self.root)
        dialog.title("افزودن به لیست سیاه نرم")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        label = ttk.Label(dialog, text="نام برنامه یا عبارت:")
        label.pack(pady=(10, 5))
        
        entry = ttk.Entry(dialog, width=40)
        entry.pack(pady=(0, 10))
        entry.focus()
        
        def on_ok():
            value = entry.get().strip().lower()
            if value:
                self.storage.add_to_soft_blacklist(value)
                self.blacklist_listbox.insert(tk.END, value)
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack()
        
        ok_btn = ttk.Button(btn_frame, text="افزودن", command=on_ok)
        ok_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_btn = ttk.Button(btn_frame, text="لغو", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT)
    
    def _remove_from_blacklist(self):
        """حذف از لیست سیاه"""
        selection = self.blacklist_listbox.curselection()
        if selection:
            index = selection[0]
            item = self.blacklist_listbox.get(index)
            self.storage.remove_from_soft_blacklist(item)
            self.blacklist_listbox.delete(index)
    
    def _on_save_click(self):
        """ذخیره تنظیمات"""
        # ذخیره تنظیمات عمومی
        self.storage.set_setting("pause_minutes", self.pause_minutes_var.get())
        self.storage.set_setting("max_project_switches_per_day", self.max_switches_var.get())
        self.storage.set_setting("soft_blacklist_threshold_seconds", self.soft_threshold_var.get())
        self.storage.set_setting("unknown_threshold_seconds", self.unknown_threshold_var.get())
        self.storage.set_setting("max_overlays_per_30_minutes", self.max_overlay_var.get())
        
        # ذخیره نهایی
        self.storage.save_settings()
        
        messagebox.showinfo("موفق", "تنظیمات با موفقیت ذخیره شد.")
        self.root.destroy()
        
        if self.on_save:
            self.on_save()

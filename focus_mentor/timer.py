# مدیریت تایمر برای Focus Mentor

import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable
from enum import Enum


class TimerMode(Enum):
    """حالت‌های تایمر"""
    FREE = "free"
    POMODORO = "pomodoro"


class WorkTimer:
    """مدیریت تایمر کاری"""
    
    def __init__(self, storage=None):
        self.storage = storage
        self.mode = TimerMode.FREE
        self.is_running = False
        self.start_time = None
        self.elapsed_seconds = 0.0
        self.pause_start_time = None
        
        # تنظیمات Pomodoro
        self.work_duration_minutes = 25
        self.break_duration_minutes = 5
        self.current_pomodoro_cycle = 0
        self.is_break_time = False
        
        # Callbacks
        self.on_work_end: Optional[Callable] = None
        self.on_break_end: Optional[Callable] = None
        
        # Thread برای تایمر
        self.timer_thread = None
        self.stop_event = threading.Event()
    
    def start(self, mode: TimerMode = TimerMode.FREE):
        """شروع تایمر"""
        self.mode = mode
        self.is_running = True
        self.start_time = datetime.now()
        self.stop_event.clear()
        
        if mode == TimerMode.POMODORO:
            self._start_pomodoro_cycle()
        else:
            self.elapsed_seconds = 0.0
        
        # شروع thread تایمر
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
    
    def _start_pomodoro_cycle(self):
        """شروع یک چرخه Pomodoro"""
        self.is_break_time = False
        self.current_pomodoro_cycle += 1
    
    def _timer_loop(self):
        """حلقه اصلی تایمر"""
        last_update = time.time()
        
        while not self.stop_event.is_set() and self.is_running:
            current_time = time.time()
            delta = current_time - last_update
            last_update = current_time
            
            if not self.pause_start_time:  # اگر در حالت Pause نیستیم
                self.elapsed_seconds += delta
                
                if self.mode == TimerMode.POMODORO:
                    target_seconds = (self.break_duration_minutes if self.is_break_time 
                                     else self.work_duration_minutes) * 60
                    
                    # محاسبه زمان باقی‌مانده در چرخه فعلی
                    cycle_elapsed = self.elapsed_seconds % ((self.work_duration_minutes + self.break_duration_minutes) * 60)
                    
                    if not self.is_break_time and cycle_elapsed >= self.work_duration_minutes * 60:
                        # پایان زمان کار، شروع استراحت
                        self.is_break_time = True
                        if self.on_work_end:
                            self.on_work_end()
                    elif self.is_break_time and cycle_elapsed >= (self.work_duration_minutes + self.break_duration_minutes) * 60:
                        # پایان استراحت، شروع کار جدید
                        self.is_break_time = False
                        self.current_pomodoro_cycle += 1
                        if self.on_break_end:
                            self.on_break_end()
            
            time.sleep(1)
    
    def pause(self):
        """توقف موقت تایمر"""
        if self.is_running and not self.pause_start_time:
            self.pause_start_time = datetime.now()
    
    def resume(self):
        """ادامه تایمر پس از Pause"""
        if self.pause_start_time:
            pause_duration = (datetime.now() - self.pause_start_time).total_seconds()
            # ثبت Pause در storage اگر موجود باشد
            if self.storage:
                from models import PauseEvent
                event = PauseEvent(
                    start_time=self.pause_start_time,
                    end_time=datetime.now(),
                    duration_minutes=int(pause_duration / 60) or 1
                )
                self.storage.save_pause_event(event)
            
            self.pause_start_time = None
    
    def stop(self):
        """توقف کامل تایمر"""
        self.is_running = False
        self.stop_event.set()
        
        if self.timer_thread:
            self.timer_thread.join(timeout=2)
    
    def reset(self):
        """بازنشانی تایمر"""
        self.stop()
        self.elapsed_seconds = 0.0
        self.start_time = None
        self.pause_start_time = None
        self.current_pomodoro_cycle = 0
        self.is_break_time = False
    
    def get_elapsed_time(self) -> float:
        """دریافت زمان سپری‌شده به ثانیه"""
        return self.elapsed_seconds
    
    def get_elapsed_formatted(self) -> str:
        """دریافت زمان سپری‌شده به صورت فرمت‌شده"""
        hours = int(self.elapsed_seconds // 3600)
        minutes = int((self.elapsed_seconds % 3600) // 60)
        seconds = int(self.elapsed_seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def get_pomodoro_status(self) -> dict:
        """دریافت وضعیت Pomodoro"""
        if self.mode != TimerMode.POMODORO:
            return {}
        
        total_cycle_seconds = (self.work_duration_minutes + self.break_duration_minutes) * 60
        cycle_elapsed = self.elapsed_seconds % total_cycle_seconds
        
        if not self.is_break_time:
            remaining = (self.work_duration_minutes * 60) - cycle_elapsed
            status = "work"
        else:
            remaining = (self.break_duration_minutes * 60) - (cycle_elapsed - self.work_duration_minutes * 60)
            status = "break"
        
        return {
            "status": status,
            "remaining_seconds": max(0, remaining),
            "cycle_number": self.current_pomodoro_cycle,
            "is_break": self.is_break_time
        }
    
    def set_pomodoro_durations(self, work_minutes: int, break_minutes: int):
        """تنظیم مدت زمان‌های Pomodoro"""
        self.work_duration_minutes = work_minutes
        self.break_duration_minutes = break_minutes

# مدل‌های داده برای Focus Mentor

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
import json


@dataclass
class DailyProject:
    """پروژه و هدف روز کاری"""
    date: str
    project_name: str
    daily_goal: str
    estimated_duration_minutes: int
    main_tools: List[str] = field(default_factory=list)
    forbidden_activities: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_locked: bool = True
    
    def to_dict(self):
        return {
            "date": self.date,
            "project_name": self.project_name,
            "daily_goal": self.daily_goal,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "main_tools": self.main_tools,
            "forbidden_activities": self.forbidden_activities,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_locked": self.is_locked,
        }
    
    @classmethod
    def from_dict(cls, data):
        start_time = None
        end_time = None
        if data.get("start_time"):
            start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            end_time = datetime.fromisoformat(data["end_time"])
        
        return cls(
            date=data["date"],
            project_name=data["project_name"],
            daily_goal=data["daily_goal"],
            estimated_duration_minutes=data["estimated_duration_minutes"],
            main_tools=data.get("main_tools", []),
            forbidden_activities=data.get("forbidden_activities", []),
            start_time=start_time,
            end_time=end_time,
            is_locked=data.get("is_locked", True),
        )


@dataclass
class WindowEvent:
    """رویداد تغییر پنجره فعال"""
    timestamp: datetime
    process_name: str
    window_title: str
    category: str  # main_work, allowed, soft_blacklist, unknown
    duration_seconds: float = 0.0
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "process_name": self.process_name,
            "window_title": self.window_title,
            "category": self.category,
            "duration_seconds": self.duration_seconds,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            process_name=data["process_name"],
            window_title=data["window_title"],
            category=data["category"],
            duration_seconds=data.get("duration_seconds", 0.0),
        )


@dataclass
class InterventionEvent:
    """رویداد مداخله (نمایش overlay)"""
    timestamp: datetime
    process_name: str
    window_title: str
    user_response: str  # "yes_claim_work", "no_return_to_work"
    user_reason: Optional[str] = None
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "process_name": self.process_name,
            "window_title": self.window_title,
            "user_response": self.user_response,
            "user_reason": self.user_reason,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            process_name=data["process_name"],
            window_title=data["window_title"],
            user_response=data["user_response"],
            user_reason=data.get("user_reason"),
        )


@dataclass
class ProjectSwitch:
    """رویداد تغییر پروژه در میانه روز"""
    timestamp: datetime
    old_project: str
    new_project: str
    reason: str
    switch_number: int
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "old_project": self.old_project,
            "new_project": self.new_project,
            "reason": self.reason,
            "switch_number": self.switch_number,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            old_project=data["old_project"],
            new_project=data["new_project"],
            reason=data["reason"],
            switch_number=data["switch_number"],
        )


@dataclass
class PauseEvent:
    """رویداد Pause"""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int = 10
    
    def to_dict(self):
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
        }
    
    @classmethod
    def from_dict(cls, data):
        start_time = datetime.fromisoformat(data["start_time"])
        end_time = None
        if data.get("end_time"):
            end_time = datetime.fromisoformat(data["end_time"])
        return cls(
            start_time=start_time,
            end_time=end_time,
            duration_minutes=data.get("duration_minutes", 10),
        )


@dataclass
class DailyReport:
    """گزارش پایان روز"""
    date: str
    project_name: str
    daily_goal: str
    total_tracked_seconds: float = 0.0
    main_work_seconds: float = 0.0
    allowed_tool_seconds: float = 0.0
    soft_blacklist_seconds: float = 0.0
    unknown_seconds: float = 0.0
    focus_ratio: float = 0.0
    overlay_count: int = 0
    work_claim_count: int = 0
    project_switch_count: int = 0
    total_pause_minutes: int = 0
    top_distracting_apps: List[str] = field(default_factory=list)
    analytical_warnings: List[str] = field(default_factory=list)
    
    def calculate_focus_ratio(self):
        if self.total_tracked_seconds > 0:
            self.focus_ratio = self.main_work_seconds / self.total_tracked_seconds
        else:
            self.focus_ratio = 0.0
    
    def to_dict(self):
        return {
            "date": self.date,
            "project_name": self.project_name,
            "daily_goal": self.daily_goal,
            "total_tracked_seconds": self.total_tracked_seconds,
            "main_work_seconds": self.main_work_seconds,
            "allowed_tool_seconds": self.allowed_tool_seconds,
            "soft_blacklist_seconds": self.soft_blacklist_seconds,
            "unknown_seconds": self.unknown_seconds,
            "focus_ratio": self.focus_ratio,
            "overlay_count": self.overlay_count,
            "work_claim_count": self.work_claim_count,
            "project_switch_count": self.project_switch_count,
            "total_pause_minutes": self.total_pause_minutes,
            "top_distracting_apps": self.top_distracting_apps,
            "analytical_warnings": self.analytical_warnings,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            date=data["date"],
            project_name=data["project_name"],
            daily_goal=data["daily_goal"],
            total_tracked_seconds=data.get("total_tracked_seconds", 0.0),
            main_work_seconds=data.get("main_work_seconds", 0.0),
            allowed_tool_seconds=data.get("allowed_tool_seconds", 0.0),
            soft_blacklist_seconds=data.get("soft_blacklist_seconds", 0.0),
            unknown_seconds=data.get("unknown_seconds", 0.0),
            focus_ratio=data.get("focus_ratio", 0.0),
            overlay_count=data.get("overlay_count", 0),
            work_claim_count=data.get("work_claim_count", 0),
            project_switch_count=data.get("project_switch_count", 0),
            total_pause_minutes=data.get("total_pause_minutes", 0),
            top_distracting_apps=data.get("top_distracting_apps", []),
            analytical_warnings=data.get("analytical_warnings", []),
        )


@dataclass
class WeeklyReport:
    """گزارش هفتگی"""
    week_start_date: str
    week_end_date: str
    average_focus_ratio: float = 0.0
    total_main_work_seconds: float = 0.0
    total_distraction_seconds: float = 0.0
    most_distracting_apps: List[str] = field(default_factory=list)
    total_overlay_count: int = 0
    total_work_claim_count: int = 0
    total_project_switch_count: int = 0
    best_focus_days: List[str] = field(default_factory=list)
    worst_focus_days: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return {
            "week_start_date": self.week_start_date,
            "week_end_date": self.week_end_date,
            "average_focus_ratio": self.average_focus_ratio,
            "total_main_work_seconds": self.total_main_work_seconds,
            "total_distraction_seconds": self.total_distraction_seconds,
            "most_distracting_apps": self.most_distracting_apps,
            "total_overlay_count": self.total_overlay_count,
            "total_work_claim_count": self.total_work_claim_count,
            "total_project_switch_count": self.total_project_switch_count,
            "best_focus_days": self.best_focus_days,
            "worst_focus_days": self.worst_focus_days,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            week_start_date=data["week_start_date"],
            week_end_date=data["week_end_date"],
            average_focus_ratio=data.get("average_focus_ratio", 0.0),
            total_main_work_seconds=data.get("total_main_work_seconds", 0.0),
            total_distraction_seconds=data.get("total_distraction_seconds", 0.0),
            most_distracting_apps=data.get("most_distracting_apps", []),
            total_overlay_count=data.get("total_overlay_count", 0),
            total_work_claim_count=data.get("total_work_claim_count", 0),
            total_project_switch_count=data.get("total_project_switch_count", 0),
            best_focus_days=data.get("best_focus_days", []),
            worst_focus_days=data.get("worst_focus_days", []),
        )

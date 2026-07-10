# -*- coding: utf-8 -*-
"""
models.py
موجودیت‌های دامنه (Domain Entities) سامانه «شهر پاک»
منطبق بر نمودار کلاس (Class Diagram) فاز ۲ پروژه:
User <|-- Citizen , User <|-- Operator
Report , WasteBin , Vehicle
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    CITIZEN = "citizen"       # شهروند
    OPERATOR = "operator"     # نیروی خدمات شهری
    MANAGER = "manager"       # مدیر شهرداری
    ADMIN = "admin"           # مدیر سیستم


class ReportStatus(str, Enum):
    """
    وضعیت‌های گزارش، دقیقاً منطبق بر نمودار حالت (State Diagram) فاز ۲:
    ارسال شده(جدید) -> در انتظار بررسی -> تأیید شده -> در حال اجرا -> تکمیل شده
                                       -> رد شده
                                                     -> (لغو) -> رد شده
    """
    SUBMITTED = "ارسال شده"
    PENDING_REVIEW = "در انتظار بررسی"
    APPROVED = "تأیید شده"
    IN_PROGRESS = "در حال اجرا"
    COMPLETED = "تکمیل شده"
    REJECTED = "رد شده"


# نگاشت گذارهای مجاز بین وضعیت‌ها (طبق نمودار حالت) - برای اعتبارسنجی در ReportService
ALLOWED_TRANSITIONS = {
    ReportStatus.SUBMITTED: {ReportStatus.PENDING_REVIEW},
    ReportStatus.PENDING_REVIEW: {ReportStatus.APPROVED, ReportStatus.REJECTED},
    ReportStatus.APPROVED: {ReportStatus.IN_PROGRESS, ReportStatus.REJECTED},
    ReportStatus.IN_PROGRESS: {ReportStatus.COMPLETED, ReportStatus.REJECTED},
    ReportStatus.COMPLETED: set(),
    ReportStatus.REJECTED: set(),
}


class BinStatus(str, Enum):
    NORMAL = "normal"                 # عادی
    NEEDS_COLLECTION = "needs_pickup"  # نیازمند جمع‌آوری
    FULL = "full"                     # پر (FR-12 -> نیاز به هشدار)


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    ON_ROUTE = "on_route"
    OFFLINE = "offline"


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------

@dataclass
class User:
    user_id: int
    name: str
    phone: str
    email: str
    password: str
    role: UserRole


@dataclass
class Citizen(User):
    citizen_id: int = None
    address: str = ""

    def __post_init__(self):
        self.role = UserRole.CITIZEN


@dataclass
class Operator(User):
    operator_id: int = None
    department: str = ""

    def __post_init__(self):
        self.role = UserRole.OPERATOR


@dataclass
class Report:
    report_id: int
    title: str
    description: str
    location: str
    lat: float
    lng: float
    status: ReportStatus
    date: str
    image_url: str = ""
    citizen_id: int = None
    reviewed_by: int = None  # operator_id
    bin_id: int = None       # ارتباط اختیاری با یک مخزن (WasteBin <-> Report)

    @staticmethod
    def new(report_id, title, description, location, lat, lng,
            citizen_id, image_url=""):
        return Report(
            report_id=report_id,
            title=title,
            description=description,
            location=location,
            lat=lat,
            lng=lng,
            status=ReportStatus.SUBMITTED,
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            image_url=image_url,
            citizen_id=citizen_id,
        )


@dataclass
class WasteBin:
    bin_id: int
    location: str
    lat: float
    lng: float
    type: str
    status: BinStatus = BinStatus.NORMAL
    fill_level: int = 0  # درصد پر بودن، برای شبیه‌سازی سنسور (طبق محدودیت پروژه: داده‌ی شبیه‌سازی‌شده)


@dataclass
class Vehicle:
    vehicle_id: int
    plate_number: str
    capacity: float
    status: VehicleStatus
    location: str
    assigned_bins: list = field(default_factory=list)

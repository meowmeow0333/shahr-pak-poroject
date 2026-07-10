# -*- coding: utf-8 -*-
"""
models.py
mojoodiyathaye damane (Domain Entities) samane 'shahr pak'
montabegh bar nemoodar class (Class Diagram) faz 2 projeh:
User <|-- Citizen, User <|-- Operator
Report, WasteBin, Vehicle
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, Enum):
    CITIZEN = "citizen"       # shahrvand
    OPERATOR = "operator"     # nirooye khadamat shahri
    MANAGER = "manager"       # modir shahrdari
    ADMIN = "admin"           # modir system


class ReportStatus(str, Enum):
    """
    vaziyathaye gozaresh, daghighan montabegh bar nemoodar halat (State Diagram) faz 2:
    ersal shode(jadid) -> dar entezar barrasi -> taeid shode -> dar hale ejra -> takmil shode
                                       -> rad shode
                                                     -> (laghv) -> rad shode
    """
    SUBMITTED = "ersal shode"
    PENDING_REVIEW = "dar entezar barrasi"
    APPROVED = "taeid shode"
    IN_PROGRESS = "dar hale ejra"
    COMPLETED = "takmil shode"
    REJECTED = "rad shode"


# negasht gozarhaye mojaz beyn vaziyatha (tebghe nemoodar halat) - baraye etebarsanji dr ReportService
ALLOWED_TRANSITIONS = {
    ReportStatus.SUBMITTED: {ReportStatus.PENDING_REVIEW},
    ReportStatus.PENDING_REVIEW: {ReportStatus.APPROVED, ReportStatus.REJECTED},
    ReportStatus.APPROVED: {ReportStatus.IN_PROGRESS, ReportStatus.REJECTED},
    ReportStatus.IN_PROGRESS: {ReportStatus.COMPLETED, ReportStatus.REJECTED},
    ReportStatus.COMPLETED: set(),
    ReportStatus.REJECTED: set(),
}


class BinStatus(str, Enum):
    NORMAL = "normal"                 # adi
    NEEDS_COLLECTION = "needs_pickup"  # niazmand jamavari
    FULL = "full"                     # por (FR-12 -> niaz be hoshdar)


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
    bin_id: int = None       # ertebat ekhtiari ba yek makhzan (WasteBin <-> Report)

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
    fill_level: int = 0  # darsad por boodan, baraye shabihsazi sensor (tbgh mhdvdyt projeh: dadh-y shbyh-sazy-shode)


@dataclass
class Vehicle:
    vehicle_id: int
    plate_number: str
    capacity: float
    status: VehicleStatus
    location: str
    assigned_bins: list = field(default_factory=list)

# -*- coding: utf-8 -*-
"""
services.py
لایه‌ی منطق کسب‌وکار (Business Logic / Service Layer).

پیاده‌سازی سناریوهای اصلی سند نیازمندی‌ها (فاز ۱) و نمودار توالی (فاز ۲):
  سناریو ۱: ثبت گزارش توسط شهروند
  سناریو ۲: بررسی گزارش توسط نیروی خدمات شهری (اپراتور)
  سناریو ۳: مشاهده وضعیت کلی توسط مدیر شهرداری

الگوهای طراحی به‌کاررفته (GoF - الزام فاز ۵):
  - Observer  : برای اعلان (Notification) به شهروند هنگام تغییر وضعیت گزارش
                و هشدار پر شدن مخزن (FR-12) به اپراتور/مدیر.
  - Repository: در repositories.py (جداسازی دسترسی داده از منطق کسب‌وکار).

اصول SOLID رعایت‌شده:
  - SRP: هر سرویس فقط یک مسئولیت دارد (گزارش‌ها / مخازن / اعلان‌ها).
  - DIP: سرویس‌ها به Repository (انتزاع دسترسی داده) وابسته‌اند، نه به SQL خام.
"""

from .models import Report, ReportStatus, ALLOWED_TRANSITIONS, BinStatus
from .repositories import ReportRepository, WasteBinRepository, VehicleRepository, UserRepository


# ---------------------------------------------------------------------------
# Observer Pattern: NotificationService به عنوان Subject و Observerها روی آن ثبت می‌شوند
# ---------------------------------------------------------------------------

class NotificationObserver:
    """رابط پایه‌ی Observer - کلاس‌های فرزند باید notify را پیاده‌سازی کنند."""
    def notify(self, message: str, target_user_id: int = None):
        raise NotImplementedError


class ConsoleNotifier(NotificationObserver):
    """پیاده‌سازی ساده‌ی نمونه اولیه: نمایش اعلان در کنسول (ماژول اعلان و ارتباطات)."""
    def notify(self, message: str, target_user_id: int = None):
        who = f"کاربر #{target_user_id}" if target_user_id else "همه"
        print(f"🔔 [اعلان به {who}]: {message}")


class NotificationService:
    """Subject در الگوی Observer. سرویس‌های دیگر رویداد را اینجا منتشر می‌کنند."""
    def __init__(self):
        self._observers: list[NotificationObserver] = []

    def subscribe(self, observer: NotificationObserver):
        self._observers.append(observer)

    def publish(self, message: str, target_user_id: int = None):
        for obs in self._observers:
            obs.notify(message, target_user_id)


# ---------------------------------------------------------------------------
# سرویس مدیریت گزارش‌ها  (ماژول مدیریت گزارش‌ها - سند فاز ۳)
# ---------------------------------------------------------------------------

class ReportService:
    def __init__(self, report_repo: ReportRepository = None,
                 notifier: NotificationService = None):
        self.report_repo = report_repo or ReportRepository()
        self.notifier = notifier or NotificationService()

    # --- سناریو ۱: ثبت گزارش توسط شهروند (FR-2, FR-3, FR-7) ---
    def submit_report(self, citizen_id: int, title: str, description: str,
                       location: str, lat: float, lng: float, image_url: str = "") -> Report:
        if not title or not description or not location:
            raise ValueError("عنوان، توضیح و موقعیت مکانی الزامی هستند.")

        report = Report.new(
            report_id=None, title=title, description=description, location=location,
            lat=lat, lng=lng, citizen_id=citizen_id, image_url=image_url,
        )
        saved = self.report_repo.add(report)

        self.notifier.publish(
            f"گزارش شما با موفقیت ثبت شد (شناسه #{saved.report_id}).", citizen_id
        )
        return saved

    # --- سناریو ۲: بررسی و تغییر وضعیت گزارش توسط اپراتور (FR-5, FR-8) ---
    def change_status(self, report_id: int, new_status: ReportStatus, operator_id: int) -> Report:
        report = self.report_repo.find_by_id(report_id)
        if report is None:
            raise ValueError("گزارشی با این شناسه یافت نشد.")

        allowed = ALLOWED_TRANSITIONS.get(report.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"گذار از وضعیت «{report.status.value}» به «{new_status.value}» مجاز نیست."
            )

        self.report_repo.update_status(report_id, new_status, reviewed_by=operator_id)
        report.status = new_status
        report.reviewed_by = operator_id

        self.notifier.publish(
            f"وضعیت گزارش #{report_id} شما به «{new_status.value}» تغییر یافت.",
            report.citizen_id,
        )
        return report

    def list_reports(self, status: ReportStatus = None, keyword: str = None):
        """FR-11: جستجو و فیلتر گزارش‌ها."""
        return self.report_repo.find_all(status=status, keyword=keyword)

    def get_report(self, report_id: int):
        return self.report_repo.find_by_id(report_id)


# ---------------------------------------------------------------------------
# سرویس پایش مخازن  (ماژول پایش و نظارت - سند فاز ۳)
# ---------------------------------------------------------------------------

class MonitoringService:
    FULL_THRESHOLD = 80  # درصد پر بودن که مخزن "پر" در نظر گرفته می‌شود (FR-12)

    def __init__(self, bin_repo: WasteBinRepository = None,
                 notifier: NotificationService = None):
        self.bin_repo = bin_repo or WasteBinRepository()
        self.notifier = notifier or NotificationService()

    def list_bins(self):
        """FR-4: نمایش وضعیت مخازن پسماند."""
        return self.bin_repo.find_all()

    def update_fill_level(self, bin_id: int, fill_level: int):
        """
        به‌روزرسانی سطح پرشدگی مخزن (در پروژه‌ی واقعی از سنسور IoT می‌آید،
        طبق محدودیت مصوب پروژه اینجا به صورت شبیه‌سازی‌شده وارد می‌شود).
        در صورت عبور از آستانه، هشدار طبق FR-12 صادر می‌شود.
        """
        status = BinStatus.NORMAL
        if fill_level >= self.FULL_THRESHOLD:
            status = BinStatus.FULL
        elif fill_level >= 50:
            status = BinStatus.NEEDS_COLLECTION

        self.bin_repo.update_status(bin_id, status, fill_level)

        if status == BinStatus.FULL:
            self.notifier.publish(
                f"⚠️ هشدار: مخزن #{bin_id} پر شده و نیازمند جمع‌آوری فوری است."
            )

    def bins_needing_attention(self):
        return [b for b in self.list_bins() if b.status in (BinStatus.FULL, BinStatus.NEEDS_COLLECTION)]


# ---------------------------------------------------------------------------
# سرویس داشبورد مدیر شهرداری (FR-6, FR-9)
# ---------------------------------------------------------------------------

class DashboardService:
    def __init__(self, report_repo: ReportRepository = None,
                 bin_repo: WasteBinRepository = None,
                 vehicle_repo: VehicleRepository = None):
        self.report_repo = report_repo or ReportRepository()
        self.bin_repo = bin_repo or WasteBinRepository()
        self.vehicle_repo = vehicle_repo or VehicleRepository()

    def overview(self) -> dict:
        reports_by_status = self.report_repo.count_by_status()
        bins = self.bin_repo.find_all()
        vehicles = self.vehicle_repo.find_all()

        return {
            "reports_by_status": reports_by_status,
            "total_reports": sum(reports_by_status.values()),
            "total_bins": len(bins),
            "bins_needing_attention": len([b for b in bins if b.status != BinStatus.NORMAL]),
            "total_vehicles": len(vehicles),
            "vehicles_available": len([v for v in vehicles if v.status.value == "available"]),
        }


# ---------------------------------------------------------------------------
# سرویس احراز هویت ساده  (FR-1)
# ---------------------------------------------------------------------------

class AuthService:
    def __init__(self, user_repo: UserRepository = None):
        self.user_repo = user_repo or UserRepository()

    def login(self, email: str, password: str):
        user = self.user_repo.find_by_email(email)
        if user is None or user.password != password:
            raise ValueError("ایمیل یا رمز عبور نادرست است.")
        return user

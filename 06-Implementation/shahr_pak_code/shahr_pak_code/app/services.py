# -*- coding: utf-8 -*-
"""
services.py
layeye mantegh kasbokar (Business Logic / Service Layer).

piadesazi scenariohaye asli sanad niazmandiha (faz 1) v nemoodar tavali (faz 2):
  scenario 1: sabt gozaresh tavasot shahrvand
  scenario 2: barrasi gozaresh tavasot nirooye khadamat shahri (operator)
  scenario 3: moshahede vaziyat kolli tavasot modir shahrdari

algoohaye tarai bekarrafte (GoF - alzam faz 5):
  - Observer: baraye elan (Notification) be shahrvand hengam taghyir vaziyat gozaresh
                va hoshdar por shodan makhzan (FR-12) be operator/modir.
  - Repository: dr repositories.py (jodasazi dastresi dade az mantegh kasbokar).

osool SOLID reayat-shode:
  - SRP: har service faghat yek masooliyat darad (gozareshha / makhzanha / elanha).
  - DIP: serviceha be Repository (antza dstrsy dadh) vabasteand, na be SQL kham.
"""

from.models import Report, ReportStatus, ALLOWED_TRANSITIONS, BinStatus
from.repositories import ReportRepository, WasteBinRepository, VehicleRepository, UserRepository


# ---------------------------------------------------------------------------
# Observer Pattern: NotificationService be onvan Subject va Observerha rooye an sabt mishavand
# ---------------------------------------------------------------------------

class NotificationObserver:
    """rabet payeye Observer - kelashaye farzand bayad notify ra piadesazi konand."""
    def notify(self, message: str, target_user_id: int = None):
        raise NotImplementedError


class ConsoleNotifier(NotificationObserver):
    """piadesazi sadeye nemoone avaliye: namayesh elan dar console (module elan va ertebatat)."""
    def notify(self, message: str, target_user_id: int = None):
        who = f"karbar #{target_user_id}" if target_user_id else "hame"
        print(f"🔔 [elan be {who}]: {message}")


class NotificationService:
    """Subject dr algvy Observer. servicehaye digar rooydad ra inja montasher mikonand."""
    def __init__(self):
        self._observers: list[NotificationObserver] = []

    def subscribe(self, observer: NotificationObserver):
        self._observers.append(observer)

    def publish(self, message: str, target_user_id: int = None):
        for obs in self._observers:
            obs.notify(message, target_user_id)


# ---------------------------------------------------------------------------
# service modiriyat gozareshha  (module modiriyat gozareshha - sanad faz 3)
# ---------------------------------------------------------------------------

class ReportService:
    def __init__(self, report_repo: ReportRepository = None,
                 notifier: NotificationService = None):
        self.report_repo = report_repo or ReportRepository()
        self.notifier = notifier or NotificationService()

    # --- scenario 1: sabt gozaresh tavasot shahrvand (FR-2, FR-3, FR-7) ---
    def submit_report(self, citizen_id: int, title: str, description: str,
                       location: str, lat: float, lng: float, image_url: str = "") -> Report:
        if not title or not description or not location:
            raise ValueError("onvan, tozih va mogheyat makani elzami hastand.")

        report = Report.new(
            report_id=None, title=title, description=description, location=location,
            lat=lat, lng=lng, citizen_id=citizen_id, image_url=image_url,
        )
        saved = self.report_repo.add(report)

        self.notifier.publish(
            f"gozaresh shoma ba movafaghiat sabt shod (shenase #{saved.report_id}).", citizen_id
        )
        return saved

    # --- scenario 2: barrasi va taghyir vaziyat gozaresh tavasot operator (FR-5, FR-8) ---
    def change_status(self, report_id: int, new_status: ReportStatus, operator_id: int) -> Report:
        report = self.report_repo.find_by_id(report_id)
        if report is None:
            raise ValueError("gozareshi ba in shenase yaft nashod.")

        allowed = ALLOWED_TRANSITIONS.get(report.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"gozar az vaziyat '{report.status.value}' be '{new_status.value}' mojaz nist."
            )

        self.report_repo.update_status(report_id, new_status, reviewed_by=operator_id)
        report.status = new_status
        report.reviewed_by = operator_id

        self.notifier.publish(
            f"vaziyat gozaresh #{report_id} shoma be '{new_status.value}' taghyir yaft.",
            report.citizen_id,
        )
        return report

    def list_reports(self, status: ReportStatus = None, keyword: str = None):
        """FR-11: jostojo va filter gozareshha."""
        return self.report_repo.find_all(status=status, keyword=keyword)

    def get_report(self, report_id: int):
        return self.report_repo.find_by_id(report_id)


# ---------------------------------------------------------------------------
# service payesh makhzanha  (module payesh va nezarat - sanad faz 3)
# ---------------------------------------------------------------------------

class MonitoringService:
    FULL_THRESHOLD = 80  # darsad por boodan ke makhzan "por" dar nazar gerefte mishavad (FR-12)

    def __init__(self, bin_repo: WasteBinRepository = None,
                 notifier: NotificationService = None):
        self.bin_repo = bin_repo or WasteBinRepository()
        self.notifier = notifier or NotificationService()

    def list_bins(self):
        """FR-4: namayesh vaziyat makhzan haye pasmand."""
        return self.bin_repo.find_all()

    def update_fill_level(self, bin_id: int, fill_level: int):
        """
        beroozresani sathee porshodegi makhzan (dar projeye vagheyi az sensor IoT miayad,
        tebghe mahdoodiyat mosavab projeh inja be soorat shabihsazi-shode vared mishavad).
        dar soorat oboor az astane, hoshdar tebghe FR-12 sader mishavad.
        """
        status = BinStatus.NORMAL
        if fill_level >= self.FULL_THRESHOLD:
            status = BinStatus.FULL
        elif fill_level >= 50:
            status = BinStatus.NEEDS_COLLECTION

        self.bin_repo.update_status(bin_id, status, fill_level)

        if status == BinStatus.FULL:
            self.notifier.publish(
                f"⚠️ hoshdar: makhzan #{bin_id} por shode va niazmand jamavari fori ast."
            )

    def bins_needing_attention(self):
        return [b for b in self.list_bins() if b.status in (BinStatus.FULL, BinStatus.NEEDS_COLLECTION)]


# ---------------------------------------------------------------------------
# service dashboard modir shahrdari (FR-6, FR-9)
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
            "bins_needing_attention": len([b for b in bins if b.status!= BinStatus.NORMAL]),
            "total_vehicles": len(vehicles),
            "vehicles_available": len([v for v in vehicles if v.status.value == "available"]),
        }


# ---------------------------------------------------------------------------
# service ehraz hoviyat sade  (FR-1)
# ---------------------------------------------------------------------------

class AuthService:
    def __init__(self, user_repo: UserRepository = None):
        self.user_repo = user_repo or UserRepository()

    def login(self, email: str, password: str):
        user = self.user_repo.find_by_email(email)
        if user is None or user.password!= password:
            raise ValueError("email ya ramz oboor nadorost ast.")
        return user

# -*- coding: utf-8 -*-
"""
test_shahr_pak.py
تست‌های واحد (Unit Tests) - پوشش الزام فاز ۷ (حداقل ۱۰ تست خودکار).
اجرا: python3 -m pytest test_shahr_pak.py -v
"""

import os
import pytest

from app import database
from app.models import ReportStatus, BinStatus
from app.repositories import ReportRepository, WasteBinRepository, UserRepository
from app.services import ReportService, MonitoringService, DashboardService, NotificationService


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """هر تست روی یک پایگاه داده‌ی موقت و تمیز اجرا می‌شود."""
    test_db_path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", str(test_db_path))
    database.init_db(reset=True)
    database.seed_demo_data()
    yield


def get_citizen_id():
    user = UserRepository().find_by_email("ali@example.com")
    return user.user_id


def get_operator_id():
    user = UserRepository().find_by_email("op1@example.com")
    return user.user_id


# ---------------------------------------------------------------------------
# تست‌های سناریو ۱: ثبت گزارش
# ---------------------------------------------------------------------------

def test_submit_report_success():
    service = ReportService()
    citizen_id = get_citizen_id()
    report = service.submit_report(
        citizen_id=citizen_id, title="پر شدن مخزن", description="مخزن پر است",
        location="خیابان ولیعصر", lat=35.7, lng=51.4,
    )
    assert report.report_id is not None
    assert report.status == ReportStatus.SUBMITTED


def test_submit_report_missing_fields_raises():
    service = ReportService()
    with pytest.raises(ValueError):
        service.submit_report(
            citizen_id=1, title="", description="", location="", lat=0, lng=0,
        )


def test_submitted_report_is_persisted_and_listed():
    service = ReportService()
    citizen_id = get_citizen_id()
    service.submit_report(citizen_id, "زباله در خیابان", "توضیح", "محل تست", 1.0, 1.0)
    reports = service.list_reports()
    assert any(r.location == "محل تست" for r in reports)


# ---------------------------------------------------------------------------
# تست‌های سناریو ۲: تغییر وضعیت توسط اپراتور
# ---------------------------------------------------------------------------

def test_valid_status_transition():
    service = ReportService()
    citizen_id, operator_id = get_citizen_id(), get_operator_id()
    report = service.submit_report(citizen_id, "t", "d", "loc", 1.0, 1.0)

    updated = service.change_status(report.report_id, ReportStatus.PENDING_REVIEW, operator_id)
    assert updated.status == ReportStatus.PENDING_REVIEW

    updated = service.change_status(report.report_id, ReportStatus.APPROVED, operator_id)
    assert updated.status == ReportStatus.APPROVED


def test_invalid_status_transition_raises():
    service = ReportService()
    citizen_id, operator_id = get_citizen_id(), get_operator_id()
    report = service.submit_report(citizen_id, "t", "d", "loc", 1.0, 1.0)

    # نمی‌توان مستقیم از "ارسال شده" به "تکمیل شده" پرید
    with pytest.raises(ValueError):
        service.change_status(report.report_id, ReportStatus.COMPLETED, operator_id)


def test_completed_report_cannot_change_again():
    service = ReportService()
    citizen_id, operator_id = get_citizen_id(), get_operator_id()
    report = service.submit_report(citizen_id, "t", "d", "loc", 1.0, 1.0)
    service.change_status(report.report_id, ReportStatus.PENDING_REVIEW, operator_id)
    service.change_status(report.report_id, ReportStatus.APPROVED, operator_id)
    service.change_status(report.report_id, ReportStatus.IN_PROGRESS, operator_id)
    service.change_status(report.report_id, ReportStatus.COMPLETED, operator_id)

    with pytest.raises(ValueError):
        service.change_status(report.report_id, ReportStatus.REJECTED, operator_id)


def test_change_status_nonexistent_report_raises():
    service = ReportService()
    with pytest.raises(ValueError):
        service.change_status(99999, ReportStatus.PENDING_REVIEW, operator_id=1)


def test_filter_reports_by_keyword():
    service = ReportService()
    citizen_id = get_citizen_id()
    service.submit_report(citizen_id, "کیس ویژه", "توضیح خاص", "میدان آزادی", 1.0, 1.0)
    result = service.list_reports(keyword="ویژه")
    assert len(result) == 1
    assert result[0].title == "کیس ویژه"


# ---------------------------------------------------------------------------
# تست‌های سرویس پایش مخازن (Monitoring)
# ---------------------------------------------------------------------------

def test_bin_status_updates_to_full_above_threshold():
    service = MonitoringService()
    bins = service.list_bins()
    target = bins[0]
    service.update_fill_level(target.bin_id, 90)
    updated = WasteBinRepository().find_by_id(target.bin_id)
    assert updated.status == BinStatus.FULL
    assert updated.fill_level == 90


def test_bins_needing_attention_excludes_normal():
    service = MonitoringService()
    bins = service.list_bins()
    service.update_fill_level(bins[0].bin_id, 10)   # normal
    service.update_fill_level(bins[1].bin_id, 95)   # full
    needing = service.bins_needing_attention()
    assert all(b.status != BinStatus.NORMAL for b in needing)


def test_notification_published_on_report_submit(capsys):
    from app.services import ConsoleNotifier
    notifier = NotificationService()
    notifier.subscribe(ConsoleNotifier())
    service = ReportService(notifier=notifier)
    service.submit_report(get_citizen_id(), "t", "d", "loc", 1.0, 1.0)
    captured = capsys.readouterr()
    assert "اعلان" in captured.out


# ---------------------------------------------------------------------------
# تست‌های داشبورد مدیر
# ---------------------------------------------------------------------------

def test_dashboard_overview_counts_reports():
    report_service = ReportService()
    citizen_id = get_citizen_id()
    report_service.submit_report(citizen_id, "t1", "d1", "loc1", 1.0, 1.0)
    report_service.submit_report(citizen_id, "t2", "d2", "loc2", 1.0, 1.0)

    dashboard = DashboardService()
    overview = dashboard.overview()
    assert overview["total_reports"] == 2
    assert overview["reports_by_status"][ReportStatus.SUBMITTED.value] == 2


def test_dashboard_reports_bins_and_vehicles_totals():
    dashboard = DashboardService()
    overview = dashboard.overview()
    assert overview["total_bins"] == 3
    assert overview["total_vehicles"] == 2

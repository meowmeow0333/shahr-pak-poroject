# -*- coding: utf-8 -*-
"""
main.py
نمونه اولیه (Prototype) سامانه «شهر پاک» - رابط خط فرمان (CLI)
برای اجرا: python3 main.py

این فایل سه سناریوی اصلی سند نیازمندی‌ها را پیاده‌سازی می‌کند:
  ۱) ثبت گزارش پسماند توسط شهروند
  ۲) بررسی گزارش‌ها و تغییر وضعیت توسط نیروی خدمات شهری (اپراتور)
  ۳) مشاهده وضعیت کلی سامانه توسط مدیر شهرداری
و همچنین مانیتورینگ مخازن (FR-4, FR-12).

کاربران نمونه برای ورود (از داده‌های Seed):
  شهروند   -> ali@example.com   / 1234
  اپراتور  -> op1@example.com   / 1234
  مدیر     -> manager@example.com / 1234
"""

from app.database import init_db, seed_demo_data
from app.models import ReportStatus, UserRole
from app.repositories import UserRepository
from app.services import (
    AuthService, ReportService, MonitoringService,
    DashboardService, NotificationService, ConsoleNotifier,
)


def build_services():
    """Composition Root: ساخت و اتصال سرویس‌ها به هم (Dependency Injection دستی)."""
    notifier = NotificationService()
    notifier.subscribe(ConsoleNotifier())

    return {
        "auth": AuthService(),
        "report": ReportService(notifier=notifier),
        "monitoring": MonitoringService(notifier=notifier),
        "dashboard": DashboardService(),
    }


def pause():
    input("\nبرای ادامه Enter را بزنید...")


# ---------------------------------------------------------------------------
# سناریو ۱: ثبت گزارش توسط شهروند
# ---------------------------------------------------------------------------

def citizen_flow(services, user):
    while True:
        print(f"\n=== پنل شهروند ({user.name}) ===")
        print("1) ثبت گزارش جدید پسماند")
        print("2) مشاهده گزارش‌های من")
        print("3) مشاهده وضعیت مخازن پسماند")
        print("0) خروج به منوی اصلی")
        choice = input("انتخاب شما: ").strip()

        if choice == "1":
            title = input("عنوان مشکل (مثلاً «پر شدن مخزن»): ")
            description = input("توضیح مشکل: ")
            location = input("آدرس/محل: ")
            try:
                lat = float(input("عرض جغرافیایی (lat) [مثلاً 35.70]: ") or 35.70)
                lng = float(input("طول جغرافیایی (lng) [مثلاً 51.33]: ") or 51.33)
            except ValueError:
                lat, lng = 35.70, 51.33
            image_url = input("مسیر عکس (اختیاری): ")

            try:
                report = services["report"].submit_report(
                    citizen_id=user.user_id, title=title, description=description,
                    location=location, lat=lat, lng=lng, image_url=image_url,
                )
                print(f"✅ گزارش شما با شناسه #{report.report_id} با وضعیت "
                      f"«{report.status.value}» ثبت شد.")
            except ValueError as e:
                print(f"❌ خطا: {e}")
            pause()

        elif choice == "2":
            reports = [r for r in services["report"].list_reports()
                       if r.citizen_id == user.user_id]
            if not reports:
                print("هنوز گزارشی ثبت نکرده‌اید.")
            for r in reports:
                print(f"#{r.report_id} | {r.title} | وضعیت: {r.status.value} | تاریخ: {r.date}")
            pause()

        elif choice == "3":
            for b in services["monitoring"].list_bins():
                print(f"#{b.bin_id} | {b.location} | پرشدگی: {b.fill_level}% | وضعیت: {b.status.value}")
            pause()

        elif choice == "0":
            break
        else:
            print("گزینه نامعتبر است.")


# ---------------------------------------------------------------------------
# سناریو ۲: بررسی گزارش توسط اپراتور
# ---------------------------------------------------------------------------

def operator_flow(services, user):
    transitions_hint = {
        ReportStatus.SUBMITTED: [ReportStatus.PENDING_REVIEW],
        ReportStatus.PENDING_REVIEW: [ReportStatus.APPROVED, ReportStatus.REJECTED],
        ReportStatus.APPROVED: [ReportStatus.IN_PROGRESS, ReportStatus.REJECTED],
        ReportStatus.IN_PROGRESS: [ReportStatus.COMPLETED, ReportStatus.REJECTED],
    }

    while True:
        print(f"\n=== پنل اپراتور خدمات شهری ({user.name}) ===")
        print("1) مشاهده لیست گزارش‌ها (فیلتر و جستجو)")
        print("2) تغییر وضعیت یک گزارش")
        print("3) مشاهده مخازن نیازمند رسیدگی")
        print("4) به‌روزرسانی سطح پرشدگی یک مخزن (شبیه‌سازی سنسور)")
        print("0) خروج به منوی اصلی")
        choice = input("انتخاب شما: ").strip()

        if choice == "1":
            keyword = input("عبارت جستجو (خالی برای همه): ").strip() or None
            reports = services["report"].list_reports(keyword=keyword)
            if not reports:
                print("گزارشی یافت نشد.")
            for r in reports:
                print(f"#{r.report_id} | {r.title} | {r.location} | وضعیت: {r.status.value}")
            pause()

        elif choice == "2":
            try:
                rid = int(input("شناسه گزارش: "))
            except ValueError:
                print("شناسه نامعتبر."); continue
            report = services["report"].get_report(rid)
            if report is None:
                print("گزارش یافت نشد."); continue

            options = transitions_hint.get(report.status, [])
            if not options:
                print(f"گزارش در وضعیت نهایی «{report.status.value}» است و قابل تغییر نیست.")
                pause(); continue

            print(f"وضعیت فعلی: {report.status.value}")
            for i, s in enumerate(options, 1):
                print(f"{i}) {s.value}")
            try:
                sel = int(input("وضعیت جدید را انتخاب کنید: "))
                new_status = options[sel - 1]
            except (ValueError, IndexError):
                print("انتخاب نامعتبر."); continue

            try:
                services["report"].change_status(rid, new_status, operator_id=user.user_id)
                print(f"✅ وضعیت گزارش #{rid} به «{new_status.value}» تغییر یافت.")
            except ValueError as e:
                print(f"❌ خطا: {e}")
            pause()

        elif choice == "3":
            bins = services["monitoring"].bins_needing_attention()
            if not bins:
                print("همه‌ی مخازن در وضعیت عادی هستند.")
            for b in bins:
                print(f"#{b.bin_id} | {b.location} | پرشدگی: {b.fill_level}% | وضعیت: {b.status.value}")
            pause()

        elif choice == "4":
            try:
                bid = int(input("شناسه مخزن: "))
                level = int(input("سطح پرشدگی جدید (0-100): "))
            except ValueError:
                print("ورودی نامعتبر."); continue
            services["monitoring"].update_fill_level(bid, level)
            print("✅ سطح پرشدگی به‌روزرسانی شد.")
            pause()

        elif choice == "0":
            break
        else:
            print("گزینه نامعتبر است.")


# ---------------------------------------------------------------------------
# سناریو ۳: داشبورد مدیر شهرداری
# ---------------------------------------------------------------------------

def manager_flow(services, user):
    while True:
        print(f"\n=== داشبورد مدیر شهرداری ({user.name}) ===")
        overview = services["dashboard"].overview()

        print(f"تعداد کل گزارش‌ها: {overview['total_reports']}")
        for status, count in overview["reports_by_status"].items():
            print(f"   - {status}: {count}")
        print(f"تعداد کل مخازن: {overview['total_bins']} "
              f"(نیازمند رسیدگی: {overview['bins_needing_attention']})")
        print(f"تعداد خودروها: {overview['total_vehicles']} "
              f"(در دسترس: {overview['vehicles_available']})")

        print("\n1) بازخوانی داشبورد")
        print("0) خروج به منوی اصلی")
        if input("انتخاب شما: ").strip() == "0":
            break


# ---------------------------------------------------------------------------
# ورود به سیستم و منوی اصلی
# ---------------------------------------------------------------------------

def login_screen(services):
    print("\n--- ورود به سامانه «شهر پاک» ---")
    email = input("ایمیل: ").strip()
    password = input("رمز عبور: ").strip()
    try:
        user = services["auth"].login(email, password)
        print(f"خوش آمدید، {user.name} ({user.role.value})")
        return user
    except ValueError as e:
        print(f"❌ {e}")
        return None


def main():
    init_db()
    seed_demo_data()
    services = build_services()

    print("=" * 60)
    print("  سامانه هوشمند مدیریت یکپارچه و پایش لحظه‌ای پسماند شهری")
    print("                     «شهر پاک»")
    print("=" * 60)
    print("کاربران نمونه:")
    print("  شهروند  : ali@example.com   / 1234")
    print("  اپراتور : op1@example.com   / 1234")
    print("  مدیر    : manager@example.com / 1234")

    while True:
        user = login_screen(services)
        if user is None:
            retry = input("تلاش مجدد؟ (y/n): ").strip().lower()
            if retry != "y":
                break
            continue

        if user.role == UserRole.CITIZEN:
            citizen_flow(services, user)
        elif user.role == UserRole.OPERATOR:
            operator_flow(services, user)
        elif user.role == UserRole.MANAGER:
            manager_flow(services, user)
        else:
            print("این نقش هنوز در نمونه اولیه پیاده‌سازی نشده است.")

        again = input("\nخروج از کل برنامه؟ (y/n): ").strip().lower()
        if again == "y":
            break

    print("\nبرنامه پایان یافت. با تشکر از استفاده شما از «شهر پاک».")


if __name__ == "__main__":
    main()

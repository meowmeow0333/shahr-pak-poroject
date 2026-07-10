# شهر پاک — نمونه اولیه (Prototype)
سامانه هوشمند مدیریت یکپارچه و پایش لحظه‌ای پسماند شهری

این کد، نمونه اولیه‌ی خواسته‌شده در **فاز ۶ (پیاده‌سازی نمونه اولیه)** سند تعریف پروژه است و
۳ سناریوی اصلی سند نیازمندی‌ها (فاز ۱) و نمودار توالی/حالت (فاز ۲) را پیاده می‌کند:

1. ثبت گزارش پسماند توسط شهروند
2. بررسی گزارش و تغییر وضعیت توسط نیروی خدمات شهری (اپراتور)
3. مشاهده داشبورد وضعیت کلی توسط مدیر شهرداری

به‌علاوه پایش وضعیت مخازن (FR-4) و هشدار پر شدن مخزن (FR-12) نیز پیاده‌سازی شده است.

## ساختار پروژه
```
shahr_pak/
├── app/
│   ├── models.py         # موجودیت‌ها: User/Citizen/Operator, Report, WasteBin, Vehicle
│   ├── database.py       # اتصال و ایجاد جداول SQLite + داده‌ی نمونه (Seed)
│   ├── repositories.py   # الگوی Repository (جداسازی SQL از منطق کسب‌وکار)
│   └── services.py       # منطق کسب‌وکار + الگوی Observer برای اعلان‌ها
├── main.py                # رابط خط فرمان (CLI) برای اجرای سناریوها
├── test_shahr_pak.py       # ۱۳ تست خودکار (فاز ۷)
└── README.md
```

## اجرا
```bash
cd shahr_pak
pip install pytest        # فقط برای اجرای تست‌ها لازم است؛ خود برنامه فقط از کتابخانه استاندارد پایتون استفاده می‌کند
python3 main.py
```

### کاربران نمونه برای ورود
| نقش | ایمیل | رمز عبور |
|---|---|---|
| شهروند | ali@example.com | 1234 |
| اپراتور | op1@example.com | 1234 |
| مدیر | manager@example.com | 1234 |

## اجرای تست‌ها
```bash
python3 -m pytest test_shahr_pak.py -v
```

## نگاشت به نیازمندی‌های کارکردی (SRS فاز ۱)
| نیازمندی | محل پیاده‌سازی |
|---|---|
| FR-1 (ثبت‌نام/ورود) | `AuthService.login` |
| FR-2, FR-3 (ثبت گزارش با عکس/موقعیت) | `ReportService.submit_report` |
| FR-4 (نمایش وضعیت مخازن) | `MonitoringService.list_bins` |
| FR-5, FR-8 (بررسی و تغییر وضعیت گزارش) | `ReportService.change_status` |
| FR-6, FR-9 (داشبورد/آمار مدیر) | `DashboardService.overview` |
| FR-7 (ذخیره‌سازی) | `repositories.py` + SQLite |
| FR-11 (جستجو/فیلتر) | `ReportRepository.find_all(keyword=...)` |
| FR-12 (هشدار پر شدن مخزن) | `MonitoringService.update_fill_level` + `NotificationService` |

## الگوهای طراحی (GoF) و اصول SOLID
- **Repository**: `repositories.py` دسترسی به داده را از `services.py` جدا می‌کند (SRP، DIP).
- **Observer**: `NotificationService` (Subject) و `ConsoleNotifier` (Observer) برای اعلان به شهروند
  هنگام تغییر وضعیت گزارش و هشدار پر شدن مخزن. افزودن کانال جدید (مثلاً پیامک) فقط نیازمند
  یک Observer جدید است، بدون تغییر در ReportService/MonitoringService (اصل Open/Closed).
- ماشین‌حالت گذارهای مجاز گزارش (`ALLOWED_TRANSITIONS` در `models.py`) دقیقاً منطبق بر
  نمودار حالت (State Diagram) فاز ۲ است و از تغییر وضعیت نامعتبر جلوگیری می‌کند.

## محدودیت‌های نمونه اولیه (طبق سند فاز ۱)
- داده‌ی سنسور مخازن شبیه‌سازی‌شده است (دسترسی به سخت‌افزار واقعی وجود ندارد).
- رابط کاربری، خط‌فرمان (CLI) ساده است؛ تمرکز پروژه روی تحلیل، طراحی و اثبات صحت معماری است،
  نه ساخت یک محصول تجاری کامل.

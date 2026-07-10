# -*- coding: utf-8 -*-
"""
main.py
nemoone avaliye (Prototype) samane 'shahr pak' - rabet khat farman (CLI)
baraye ejra: python3 main.py

in file se scenario asli sanad niazmandiha ra piadesazi mikonad:
  1) sbt gozaresh pasmand tavasot shahrvand
  2) barrasi gozareshha v taghyir vaziyat tavasot nirooye khadamat shahri (operator)
  3) moshahede vaziyat kolli samane tavasot modir shahrdari
va hamchenin monitoring makhzanha (FR-4, FR-12).

karbaran nemoone baraye vorood (az dadehaye Seed):
  shahrvand   -> ali@example.com   / 1234
  operator  -> op1@example.com   / 1234
  modir     -> manager@example.com / 1234
"""

from app.database import init_db, seed_demo_data
from app.models import ReportStatus, UserRole
from app.repositories import UserRepository
from app.services import (
    AuthService, ReportService, MonitoringService,
    DashboardService, NotificationService, ConsoleNotifier,
)


def build_services():
    """Composition Root: sakht va etesal serviceha be ham (Dependency Injection dasti)."""
    notifier = NotificationService()
    notifier.subscribe(ConsoleNotifier())

    return {
        "auth": AuthService(),
        "report": ReportService(notifier=notifier),
        "monitoring": MonitoringService(notifier=notifier),
        "dashboard": DashboardService(),
    }


def pause():
    input("\nbaraye edame Enter ra bezanid...")


# ---------------------------------------------------------------------------
# scenario 1: sabt gozaresh tavasot shahrvand
# ---------------------------------------------------------------------------

def citizen_flow(services, user):
    while True:
        print(f"\n=== panel shahrvand ({user.name}) ===")
        print("1) sabt gozaresh jadid pasmand")
        print("2) moshahede gozareshhaye man")
        print("3) moshahede vaziyat makhzan haye pasmand")
        print("0) khorooj be menu asli")
        choice = input("entekhab shoma: ").strip()

        if choice == "1":
            title = input("onvan moshkel (mesalan 'por shodan makhzan'): ")
            description = input("tozih moshkel: ")
            location = input("adres/mahal: ")
            try:
                lat = float(input("arz joghrafiyayi (lat) [mesalan 35.70]: ") or 35.70)
                lng = float(input("tool joghrafiyayi (lng) [mesalan 51.33]: ") or 51.33)
            except ValueError:
                lat, lng = 35.70, 51.33
            image_url = input("masir aks (ekhtiari): ")

            try:
                report = services["report"].submit_report(
                    citizen_id=user.user_id, title=title, description=description,
                    location=location, lat=lat, lng=lng, image_url=image_url,
                )
                print(f"✅ gozaresh shoma ba shenase #{report.report_id} ba vaziyat "
                      f"'{report.status.value}' sabt shod.")
            except ValueError as e:
                print(f"❌ khata: {e}")
            pause()

        elif choice == "2":
            reports = [r for r in services["report"].list_reports()
                       if r.citizen_id == user.user_id]
            if not reports:
                print("hanooz gozareshi sabt nakardeid.")
            for r in reports:
                print(f"#{r.report_id} | {r.title} | vaziyat: {r.status.value} | tarikh: {r.date}")
            pause()

        elif choice == "3":
            for b in services["monitoring"].list_bins():
                print(f"#{b.bin_id} | {b.location} | porshodegi: {b.fill_level}% | vaziyat: {b.status.value}")
            pause()

        elif choice == "0":
            break
        else:
            print("gozine namotabar ast.")


# ---------------------------------------------------------------------------
# scenario 2: barrasi gozaresh tavasot operator
# ---------------------------------------------------------------------------

def operator_flow(services, user):
    transitions_hint = {
        ReportStatus.SUBMITTED: [ReportStatus.PENDING_REVIEW],
        ReportStatus.PENDING_REVIEW: [ReportStatus.APPROVED, ReportStatus.REJECTED],
        ReportStatus.APPROVED: [ReportStatus.IN_PROGRESS, ReportStatus.REJECTED],
        ReportStatus.IN_PROGRESS: [ReportStatus.COMPLETED, ReportStatus.REJECTED],
    }

    while True:
        print(f"\n=== panel operator khadamat shahri ({user.name}) ===")
        print("1) moshahede list gozareshha (filter va jostojo)")
        print("2) taghyir vaziyat yek gozaresh")
        print("3) moshahede makhzan haye niazmand residgi")
        print("4) beroozresani sathee porshodegi yek makhzan (shabihsazi sensor)")
        print("0) khorooj be menu asli")
        choice = input("entekhab shoma: ").strip()

        if choice == "1":
            keyword = input("ebarat jostojo (khali baraye hame): ").strip() or None
            reports = services["report"].list_reports(keyword=keyword)
            if not reports:
                print("gozareshi yaft nashod.")
            for r in reports:
                print(f"#{r.report_id} | {r.title} | {r.location} | vaziyat: {r.status.value}")
            pause()

        elif choice == "2":
            try:
                rid = int(input("shenase gozaresh: "))
            except ValueError:
                print("shenase namotabar."); continue
            report = services["report"].get_report(rid)
            if report is None:
                print("gozaresh yaft nashod."); continue

            options = transitions_hint.get(report.status, [])
            if not options:
                print(f"gozaresh dar vaziyat nahayi '{report.status.value}' ast va ghabele taghyir nist.")
                pause(); continue

            print(f"vaziyat feli: {report.status.value}")
            for i, s in enumerate(options, 1):
                print(f"{i}) {s.value}")
            try:
                sel = int(input("vaziyat jadid ra entekhab konid: "))
                new_status = options[sel - 1]
            except (ValueError, IndexError):
                print("entekhab namotabar."); continue

            try:
                services["report"].change_status(rid, new_status, operator_id=user.user_id)
                print(f"✅ vaziyat gozaresh #{rid} be '{new_status.value}' taghyir yaft.")
            except ValueError as e:
                print(f"❌ khata: {e}")
            pause()

        elif choice == "3":
            bins = services["monitoring"].bins_needing_attention()
            if not bins:
                print("hameye makhzanha dar vaziyat adi hastand.")
            for b in bins:
                print(f"#{b.bin_id} | {b.location} | porshodegi: {b.fill_level}% | vaziyat: {b.status.value}")
            pause()

        elif choice == "4":
            try:
                bid = int(input("shenase makhzan: "))
                level = int(input("sathee porshodegi jadid (0-100): "))
            except ValueError:
                print("voroodi namotabar."); continue
            services["monitoring"].update_fill_level(bid, level)
            print("✅ sathee porshodegi beroozresani shod.")
            pause()

        elif choice == "0":
            break
        else:
            print("gozine namotabar ast.")


# ---------------------------------------------------------------------------
# scenario 3: dashboard modir shahrdari
# ---------------------------------------------------------------------------

def manager_flow(services, user):
    while True:
        print(f"\n=== dashboard modir shahrdari ({user.name}) ===")
        overview = services["dashboard"].overview()

        print(f"tedad kol gozareshha: {overview['total_reports']}")
        for status, count in overview["reports_by_status"].items():
            print(f"   - {status}: {count}")
        print(f"tedad kol makhzanha: {overview['total_bins']} "
              f"(niazmand residgi: {overview['bins_needing_attention']})")
        print(f"tedad khodroha: {overview['total_vehicles']} "
              f"(dar dastres: {overview['vehicles_available']})")

        print("\n1) bazkhani dashboard")
        print("0) khorooj be menu asli")
        if input("entekhab shoma: ").strip() == "0":
            break


# ---------------------------------------------------------------------------
# vrvd be systm v mnvy asly
# ---------------------------------------------------------------------------

def login_screen(services):
    print("\n--- vorood be samane 'shahr pak' ---")
    email = input("email: ").strip()
    password = input("ramz oboor: ").strip()
    try:
        user = services["auth"].login(email, password)
        print(f"khosh amadid, {user.name} ({user.role.value})")
        return user
    except ValueError as e:
        print(f"❌ {e}")
        return None


def main():
    init_db()
    seed_demo_data()
    services = build_services()

    print("=" * 60)
    print("  samane hooshmand modiriyat yekparche va payesh lahzeei pasmand shahri")
    print("                     'shahr pak'")
    print("=" * 60)
    print("karbaran nemoone:")
    print("  shahrvand: ali@example.com   / 1234")
    print("  operator: op1@example.com   / 1234")
    print("  modir: manager@example.com / 1234")

    while True:
        user = login_screen(services)
        if user is None:
            retry = input("talash mojaddad? (y/n): ").strip().lower()
            if retry!= "y":
                break
            continue

        if user.role == UserRole.CITIZEN:
            citizen_flow(services, user)
        elif user.role == UserRole.OPERATOR:
            operator_flow(services, user)
        elif user.role == UserRole.MANAGER:
            manager_flow(services, user)
        else:
            print("in naghsh hanooz dar nemoone avaliye piadesazi nashode ast.")

        again = input("\nkhorooj az kol barname? (y/n): ").strip().lower()
        if again == "y":
            break

    print("\nbarname payan yaft. ba tashakkor az estefade shoma az 'shahr pak'.")


if __name__ == "__main__":
    main()

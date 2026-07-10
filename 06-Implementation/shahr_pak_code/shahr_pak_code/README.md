# shahr pak — nemoone avaliye (Prototype)
samane hooshmand modiriyat yekparche va payesh lahzeei pasmand shahri

ayn kd, nemoone avaliye-y khvasth-shode dr **faz 6 (pyadh-sazy nemoone avaliye)** sanad tryf projeh ast v
3 scenarioy asly sanad nyazmndy-ha (faz 1) v nemoodar tavali/halt (faz 2) ra pyadh my-knd:

1. sbt gozaresh pasmand tavasot shahrvand
2. barrasi gozaresh v taghyir vaziyat tavasot nirooye khadamat shahri (operator)
3. moshahede dashbvrd vaziyat kolli tavasot modir shahrdari

be-lavh paysh vaziyat makhzanha (FR-4) va hoshdar por shodan makhzan (FR-12) nyz pyadh-sazy shode ast.

## sakhtar projeh
```
shahr_pak/
├── app/
│   ├── models.py         # mvjvdyt-ha: User/Citizen/Operator, Report, WasteBin, Vehicle
│   ├── database.py       # atsal v ayjad jadavel SQLite + dadh-y nmvnh (Seed)
│   ├── repositories.py   # algvy Repository (jdasazy SQL az mntgh ksb-vkar)
│   └── services.py       # mntgh ksb-vkar + algvy Observer baraye elan-ha
├── main.py                # rabet khat farman (CLI) baraye ejray scenarioha
├── test_shahr_pak.py       # 13 test khodkar (faz 7)
└── README.md
```

## ejra
```bash
cd shahr_pak
pip install pytest        # fght bray ejraye testha lazm ast; khvd brnamh fght az ktabkhanh astandard paytvn estefade my-knd
python3 main.py
```

### karbaran nemoone baraye vorood
| nghsh | aymyl | rmz bvr |
|---|---|---|
| shahrvand | ali@example.com | 1234 |
| operator | op1@example.com | 1234 |
| modir | manager@example.com | 1234 |

## ejraye testha
```bash
python3 -m pytest test_shahr_pak.py -v
```

## negasht be niazmandihaye karkardi (SRS faz 1)
| nyazmndy | mahal piadesazi |
|---|---|
| FR-1 (sabt nam/vorood) | `AuthService.login` |
| FR-2, FR-3 (sabt gozaresh ba aks/mogheyat) | `ReportService.submit_report` |
| FR-4 (namayesh vaziyat makhzanha) | `MonitoringService.list_bins` |
| FR-5, FR-8 (barrasi v taghyir vaziyat gozaresh) | `ReportService.change_status` |
| FR-6, FR-9 (dashboard/amar modir) | `DashboardService.overview` |
| FR-7 (zakhire-sazi) | `repositories.py` + SQLite |
| FR-11 (jostojo/filter) | `ReportRepository.find_all(keyword=...)` |
| FR-12 (hoshdar por shodan makhzan) | `MonitoringService.update_fill_level` + `NotificationService` |

## algoohaye tarai (GoF) v osool SOLID
- **Repository**: `repositories.py` dastresi be dade ra az `services.py` joda mikonad (SRP, DIP).
- **Observer**: `NotificationService` (Subject) v `ConsoleNotifier` (Observer) baraye elan be shahrvand
  hengam taghyir vaziyat gozaresh va hoshdar por shodan makhzan. afzoodan canal jadid (mesalan payamak) faghat niazmand
  yek Observer jadid ast, bedoon taghyir dar ReportService/MonitoringService (asl Open/Closed).
- mashin-halat gozarhaye mojaz gozaresh (`ALLOWED_TRANSITIONS` dr `models.py`) daghighan montabegh bar
  nmvdar halt (State Diagram) faz 2 ast va az taghyir vaziyat namotabar jologiri mikonad.

## mahdoodiyathaye nemoone avaliye (tbgh sanad faz 1)
- dadeye sensor makhzanha shabihsazi-shode ast (dastresi be sakhtafzar vagheyi vojood nadarad).
- rabet karbari, khat-farman (CLI) sade ast; tamarkoz projeh rooye tahlil, tarai va esbat sehat memari ast,
  na sakht yek mahsool tejari kamel.
Jira integration completed.
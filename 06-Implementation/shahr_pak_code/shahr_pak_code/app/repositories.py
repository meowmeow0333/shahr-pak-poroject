# -*- coding: utf-8 -*-
"""
repositories.py
piadesazi algooye tarai Repository (yeki az algoohaye GoF mored niaz faz 5).
har Repository masool tabdil radifhaye paygah dade be Object haye damane (models.py) va baraks ast.
in laye, layeye service (services.py) ra az joziyat SQL joda mikonad (asl SRP az SOLID).
"""

from.database import get_connection
from.models import (
    User, Citizen, Operator, UserRole,
    Report, ReportStatus,
    WasteBin, BinStatus,
    Vehicle, VehicleStatus,
)


class UserRepository:
    def find_by_email(self, email: str):
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE email =?", (email,)).fetchone()
        conn.close()
        return self._row_to_user(row) if row else None

    def find_by_id(self, user_id: int):
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE user_id =?", (user_id,)).fetchone()
        conn.close()
        return self._row_to_user(row) if row else None

    def add(self, name, phone, email, password, role: UserRole, address=None, department=None):
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO users (name, phone, email, password, role, address, department) "
            "VALUES (?,?,?,?,?,?,?)",
            (name, phone, email, password, role.value, address, department),
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return self.find_by_id(new_id)

    @staticmethod
    def _row_to_user(row):
        role = UserRole(row["role"])
        if role == UserRole.CITIZEN:
            return Citizen(
                user_id=row["user_id"], name=row["name"], phone=row["phone"],
                email=row["email"], password=row["password"], role=role,
                citizen_id=row["extra_id"] or row["user_id"], address=row["address"] or "",
            )
        if role == UserRole.OPERATOR:
            return Operator(
                user_id=row["user_id"], name=row["name"], phone=row["phone"],
                email=row["email"], password=row["password"], role=role,
                operator_id=row["extra_id"] or row["user_id"], department=row["department"] or "",
            )
        return User(
            user_id=row["user_id"], name=row["name"], phone=row["phone"],
            email=row["email"], password=row["password"], role=role,
        )


class ReportRepository:
    def add(self, report: Report) -> Report:
        conn = get_connection()
        cur = conn.execute(
            "INSERT INTO reports (title, description, location, lat, lng, status, date, "
            "image_url, citizen_id, reviewed_by, bin_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (report.title, report.description, report.location, report.lat, report.lng,
             report.status.value, report.date, report.image_url, report.citizen_id,
             report.reviewed_by, report.bin_id),
        )
        conn.commit()
        report.report_id = cur.lastrowid
        conn.close()
        return report

    def find_by_id(self, report_id: int):
        conn = get_connection()
        row = conn.execute("SELECT * FROM reports WHERE report_id =?", (report_id,)).fetchone()
        conn.close()
        return self._row_to_report(row) if row else None

    def find_all(self, status: ReportStatus = None, keyword: str = None):
        """poshtibani az filter bar asas vaziyat va jostojooye matni (FR-11)."""
        query = "SELECT * FROM reports WHERE 1=1"
        params = []
        if status is not None:
            query += " AND status =?"
            params.append(status.value)
        if keyword:
            query += " AND (title LIKE? OR description LIKE? OR location LIKE?)"
            like = f"%{keyword}%"
            params += [like, like, like]
        query += " ORDER BY report_id DESC"

        conn = get_connection()
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [self._row_to_report(r) for r in rows]

    def update_status(self, report_id: int, new_status: ReportStatus, reviewed_by: int = None):
        conn = get_connection()
        conn.execute(
            "UPDATE reports SET status =?, reviewed_by = COALESCE(?, reviewed_by) WHERE report_id =?",
            (new_status.value, reviewed_by, report_id),
        )
        conn.commit()
        conn.close()

    def count_by_status(self):
        conn = get_connection()
        rows = conn.execute("SELECT status, COUNT(*) AS c FROM reports GROUP BY status").fetchall()
        conn.close()
        return {r["status"]: r["c"] for r in rows}

    @staticmethod
    def _row_to_report(row):
        return Report(
            report_id=row["report_id"], title=row["title"], description=row["description"],
            location=row["location"], lat=row["lat"], lng=row["lng"],
            status=ReportStatus(row["status"]), date=row["date"], image_url=row["image_url"] or "",
            citizen_id=row["citizen_id"], reviewed_by=row["reviewed_by"], bin_id=row["bin_id"],
        )


class WasteBinRepository:
    def find_all(self):
        conn = get_connection()
        rows = conn.execute("SELECT * FROM waste_bins ORDER BY bin_id").fetchall()
        conn.close()
        return [self._row_to_bin(r) for r in rows]

    def find_by_id(self, bin_id: int):
        conn = get_connection()
        row = conn.execute("SELECT * FROM waste_bins WHERE bin_id =?", (bin_id,)).fetchone()
        conn.close()
        return self._row_to_bin(row) if row else None

    def update_status(self, bin_id: int, status: BinStatus, fill_level: int = None):
        conn = get_connection()
        if fill_level is None:
            conn.execute("UPDATE waste_bins SET status =? WHERE bin_id =?", (status.value, bin_id))
        else:
            conn.execute(
                "UPDATE waste_bins SET status =?, fill_level =? WHERE bin_id =?",
                (status.value, fill_level, bin_id),
            )
        conn.commit()
        conn.close()

    @staticmethod
    def _row_to_bin(row):
        return WasteBin(
            bin_id=row["bin_id"], location=row["location"], lat=row["lat"], lng=row["lng"],
            type=row["type"], status=BinStatus(row["status"]), fill_level=row["fill_level"],
        )


class VehicleRepository:
    def find_all(self):
        conn = get_connection()
        rows = conn.execute("SELECT * FROM vehicles ORDER BY vehicle_id").fetchall()
        conn.close()
        return [self._row_to_vehicle(r) for r in rows]

    def find_available(self):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM vehicles WHERE status =?", (VehicleStatus.AVAILABLE.value,)
        ).fetchall()
        conn.close()
        return [self._row_to_vehicle(r) for r in rows]

    def update_status(self, vehicle_id: int, status: VehicleStatus):
        conn = get_connection()
        conn.execute("UPDATE vehicles SET status =? WHERE vehicle_id =?", (status.value, vehicle_id))
        conn.commit()
        conn.close()

    @staticmethod
    def _row_to_vehicle(row):
        return Vehicle(
            vehicle_id=row["vehicle_id"], plate_number=row["plate_number"], capacity=row["capacity"],
            status=VehicleStatus(row["status"]), location=row["location"],
        )

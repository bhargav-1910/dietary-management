from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from clinic_app.database import DatabaseManager


class ClinicService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.current_user_id: int | None = None

    def set_current_user(self, user_id: int | None) -> None:
        self.current_user_id = user_id

    def _require_user_id(self) -> int:
        if self.current_user_id is None:
            raise ValueError("No active user context. Please login again.")
        return self.current_user_id

    def list_patients(self, search: str = "", include_deleted: bool = False) -> list[dict[str, Any]]:
        user_id = self._require_user_id()
        query = "SELECT * FROM Patients"
        params: list[Any] = [user_id]

        filters: list[str] = []
        filters.append("owner_user_id = ?")
        if not include_deleted:
            filters.append("deleted_at IS NULL")

        if search.strip():
            filters.append("(name LIKE ? OR phone LIKE ?)")
            wildcard = f"%{search.strip()}%"
            params.extend([wildcard, wildcard])

        if filters:
            query += " WHERE " + " AND ".join(filters)
        query += " ORDER BY id DESC"

        with self.db._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return self.db.rows_to_dict(rows)

    def _validate_patient_payload(
        self,
        name: str,
        age: int | None,
        phone: str,
        exclude_patient_id: int | None = None,
    ) -> None:
        user_id = self._require_user_id()
        cleaned_name = name.strip()
        cleaned_phone = phone.strip()

        if len(cleaned_name) < 2:
            raise ValueError("Patient name must be at least 2 characters.")

        if age is not None and (age < 0 or age > 120):
            raise ValueError("Age must be between 0 and 120.")

        if cleaned_phone:
            if not re.fullmatch(r"\d{10,15}", cleaned_phone):
                raise ValueError("Phone must contain only digits and be 10 to 15 digits long.")

        with self.db._connect() as conn:
            if exclude_patient_id is None:
                row = conn.execute(
                    """
                    SELECT id FROM Patients
                    WHERE deleted_at IS NULL
                                            AND owner_user_id = ?
                      AND LOWER(name)=LOWER(?)
                      AND COALESCE(phone, '')=COALESCE(?, '')
                    """,
                                        (user_id, cleaned_name, cleaned_phone),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT id FROM Patients
                    WHERE deleted_at IS NULL
                                            AND owner_user_id = ?
                      AND LOWER(name)=LOWER(?)
                      AND COALESCE(phone, '')=COALESCE(?, '')
                      AND id <> ?
                    """,
                                        (user_id, cleaned_name, cleaned_phone, exclude_patient_id),
                ).fetchone()

        if row:
            raise ValueError("An active patient with the same name and phone already exists.")

    def add_patient(self, name: str, age: int | None, gender: str, phone: str, notes: str) -> None:
        user_id = self._require_user_id()
        self._validate_patient_payload(name, age, phone)
        with self.db._connect() as conn:
            conn.execute(
                "INSERT INTO Patients(owner_user_id, name, age, gender, phone, notes, deleted_at) VALUES (?, ?, ?, ?, ?, ?, NULL)",
                (user_id, name.strip(), age, gender.strip(), phone.strip(), notes.strip()),
            )

    def update_patient(self, patient_id: int, name: str, age: int | None, gender: str, phone: str, notes: str) -> None:
        user_id = self._require_user_id()
        self._validate_patient_payload(name, age, phone, exclude_patient_id=patient_id)
        with self.db._connect() as conn:
            conn.execute(
                "UPDATE Patients SET name=?, age=?, gender=?, phone=?, notes=? WHERE id=? AND owner_user_id=? AND deleted_at IS NULL",
                (name.strip(), age, gender.strip(), phone.strip(), notes.strip(), patient_id, user_id),
            )

    def delete_patient(self, patient_id: int, force: bool = False) -> tuple[bool, str]:
        user_id = self._require_user_id()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.db._connect() as conn:
            row = conn.execute(
                "SELECT id FROM Patients WHERE id=? AND owner_user_id=? AND deleted_at IS NULL",
                (patient_id, user_id),
            ).fetchone()
            if not row:
                return False, "Patient not found."

            history_count = conn.execute(
                "SELECT COUNT(*) AS count FROM Quotations WHERE patient_id=? AND owner_user_id=? AND deleted_at IS NULL",
                (patient_id, user_id),
            ).fetchone()["count"]

            if history_count > 0 and not force:
                return False, f"Patient has {history_count} quotation record(s)."

            if history_count > 0 and force:
                conn.execute(
                    "UPDATE Quotations SET deleted_at=? WHERE patient_id=? AND owner_user_id=? AND deleted_at IS NULL",
                    (timestamp, patient_id, user_id),
                )

            conn.execute("UPDATE Patients SET deleted_at=? WHERE id=? AND owner_user_id=?", (timestamp, patient_id, user_id))

        return True, "Patient archived successfully."

    def list_archived_patients(self, search: str = "") -> list[dict[str, Any]]:
        user_id = self._require_user_id()
        query = "SELECT * FROM Patients WHERE deleted_at IS NOT NULL AND owner_user_id = ?"
        params: list[Any] = [user_id]
        if search.strip():
            wildcard = f"%{search.strip()}%"
            query += " AND (name LIKE ? OR phone LIKE ?)"
            params.extend([wildcard, wildcard])

        query += " ORDER BY deleted_at DESC, id DESC"
        with self.db._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return self.db.rows_to_dict(rows)

    def restore_patient(self, patient_id: int, restore_quotations: bool = True) -> tuple[bool, str]:
        user_id = self._require_user_id()
        with self.db._connect() as conn:
            row = conn.execute(
                "SELECT id FROM Patients WHERE id=? AND owner_user_id=? AND deleted_at IS NOT NULL",
                (patient_id, user_id),
            ).fetchone()
            if not row:
                return False, "Archived patient not found."

            conn.execute("UPDATE Patients SET deleted_at=NULL WHERE id=? AND owner_user_id=?", (patient_id, user_id))
            if restore_quotations:
                conn.execute(
                    "UPDATE Quotations SET deleted_at=NULL WHERE patient_id=? AND owner_user_id=?",
                    (patient_id, user_id),
                )

        return True, "Patient restored successfully."

    def list_products(self) -> list[dict[str, Any]]:
        with self.db._connect() as conn:
            rows = conn.execute("SELECT * FROM Products ORDER BY category, name").fetchall()
        return self.db.rows_to_dict(rows)

    def add_product(self, name: str, category: str, mrp: float, base_price: float, tax_percent: float) -> None:
        self._validate_product_payload(name, category, mrp, base_price, tax_percent)
        with self.db._connect() as conn:
            conn.execute(
                "INSERT INTO Products(name, category, mrp, base_price, tax_percent) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), category.strip(), mrp, base_price, tax_percent),
            )

    def update_product(
        self,
        product_id: int,
        name: str,
        category: str,
        mrp: float,
        base_price: float,
        tax_percent: float,
    ) -> None:
        self._validate_product_payload(name, category, mrp, base_price, tax_percent)
        with self.db._connect() as conn:
            conn.execute(
                "UPDATE Products SET name=?, category=?, mrp=?, base_price=?, tax_percent=? WHERE id=?",
                (name.strip(), category.strip(), mrp, base_price, tax_percent, product_id),
            )

    @staticmethod
    def _validate_product_payload(name: str, category: str, mrp: float, base_price: float, tax_percent: float) -> None:
        if len(name.strip()) < 2:
            raise ValueError("Product name must be at least 2 characters.")
        if len(category.strip()) < 2:
            raise ValueError("Category is required.")
        if mrp <= 0 or base_price <= 0:
            raise ValueError("MRP and Base Price must be greater than zero.")
        if mrp < base_price:
            raise ValueError("MRP must be greater than or equal to Base Price.")
        if tax_percent < 0 or tax_percent > 50:
            raise ValueError("Tax percentage must be between 0 and 50.")

    def delete_product(self, product_id: int) -> None:
        with self.db._connect() as conn:
            conn.execute("DELETE FROM Products WHERE id=?", (product_id,))

    def create_quotation(self, patient_id: int, selected_items: list[dict[str, Any]]) -> dict[str, Any]:
        user_id = self._require_user_id()
        if not selected_items:
            raise ValueError("At least one item is required to create a quotation.")

        patient = self.get_patient(patient_id)
        if not patient:
            raise ValueError("Cannot create quotation for an archived or unknown patient.")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        subtotal = 0.0
        total_tax = 0.0
        for item in selected_items:
            qty = int(item["quantity"])
            if qty <= 0:
                raise ValueError("Quantity must be greater than zero.")
            base = float(item["base_price"])
            tax_percent = float(item["tax_percent"])
            subtotal += base * qty
            total_tax += (base * tax_percent / 100.0) * qty

        grand_total = subtotal + total_tax

        with self.db._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO Quotations(owner_user_id, patient_id, date, subtotal, total_tax, grand_total) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, patient_id, now, subtotal, total_tax, grand_total),
            )
            quotation_id = cursor.lastrowid
            for item in selected_items:
                qty = int(item["quantity"])
                if qty <= 0:
                    raise ValueError("Quantity must be greater than zero.")
                base = float(item["base_price"])
                tax_percent = float(item["tax_percent"])
                tax_amount = (base * tax_percent / 100.0) * qty
                line_final = (base * qty) + tax_amount
                conn.execute(
                    """
                    INSERT INTO Quotation_Items(
                        quotation_id,
                        product_id,
                        quantity,
                        base_price,
                        tax_amount,
                        final_price
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (quotation_id, item["id"], qty, base, tax_amount, line_final),
                )

        return {
            "quotation_id": quotation_id,
            "invoice_number": self.invoice_number(quotation_id),
            "date": now,
            "subtotal": subtotal,
            "total_tax": total_tax,
            "grand_total": grand_total,
        }

    @staticmethod
    def invoice_number(quotation_id: int) -> str:
        return f"INV-{quotation_id:04d}"

    def list_patient_quotations(self, patient_id: int) -> list[dict[str, Any]]:
        user_id = self._require_user_id()
        with self.db._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, date, subtotal, total_tax, grand_total
                FROM Quotations
                WHERE patient_id = ?
                  AND owner_user_id = ?
                  AND deleted_at IS NULL
                ORDER BY id DESC
                """,
                (patient_id, user_id),
            ).fetchall()

        history = self.db.rows_to_dict(rows)
        for row in history:
            row["invoice_number"] = self.invoice_number(int(row["id"]))
        return history

    def get_quotation_detail(self, quotation_id: int) -> dict[str, Any] | None:
        user_id = self._require_user_id()
        with self.db._connect() as conn:
            quotation = conn.execute(
                """
                SELECT q.id, q.patient_id, q.date, q.subtotal, q.total_tax, q.grand_total,
                       p.name AS patient_name, p.age, p.gender, p.phone, p.notes
                FROM Quotations q
                INNER JOIN Patients p ON p.id = q.patient_id
                WHERE q.id = ?
                  AND q.owner_user_id = ?
                  AND q.deleted_at IS NULL
                """,
                (quotation_id, user_id),
            ).fetchone()
            if not quotation:
                return None

            items = conn.execute(
                """
                SELECT qi.product_id, pr.name, qi.quantity, qi.base_price, qi.tax_amount, qi.final_price, pr.tax_percent
                FROM Quotation_Items qi
                INNER JOIN Products pr ON pr.id = qi.product_id
                WHERE qi.quotation_id = ?
                ORDER BY qi.id ASC
                """,
                (quotation_id,),
            ).fetchall()

        quotation_dict = dict(quotation)
        quotation_dict["invoice_number"] = self.invoice_number(int(quotation_dict["id"]))
        quotation_dict["patient"] = {
            "id": quotation_dict["patient_id"],
            "name": quotation_dict["patient_name"],
            "age": quotation_dict.get("age"),
            "gender": quotation_dict.get("gender"),
            "phone": quotation_dict.get("phone"),
            "notes": quotation_dict.get("notes"),
        }
        quotation_dict["items"] = [dict(item) for item in items]
        return quotation_dict

    def backup_database(self, target_path: str | Path) -> Path:
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db.db_path, target)
        return target

    def restore_database(self, source_path: str | Path) -> Path:
        source = Path(source_path)
        self.db.db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, self.db.db_path)
        return self.db.db_path

    def get_patient(self, patient_id: int, include_deleted: bool = False) -> dict[str, Any] | None:
        user_id = self._require_user_id()
        with self.db._connect() as conn:
            if include_deleted:
                row = conn.execute("SELECT * FROM Patients WHERE id=? AND owner_user_id=?", (patient_id, user_id)).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM Patients WHERE id=? AND owner_user_id=? AND deleted_at IS NULL",
                    (patient_id, user_id),
                ).fetchone()
        return dict(row) if row else None

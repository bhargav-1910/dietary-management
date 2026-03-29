from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from clinic_app.database import DatabaseManager


class ClinicService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    def list_patients(self, search: str = "") -> list[dict[str, Any]]:
        query = "SELECT * FROM Patients"
        params: tuple[Any, ...] = ()
        if search.strip():
            query += " WHERE name LIKE ? OR phone LIKE ?"
            wildcard = f"%{search.strip()}%"
            params = (wildcard, wildcard)
        query += " ORDER BY id DESC"

        with self.db._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return self.db.rows_to_dict(rows)

    def add_patient(self, name: str, age: int | None, gender: str, phone: str, notes: str) -> None:
        with self.db._connect() as conn:
            conn.execute(
                "INSERT INTO Patients(name, age, gender, phone, notes) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), age, gender.strip(), phone.strip(), notes.strip()),
            )

    def update_patient(self, patient_id: int, name: str, age: int | None, gender: str, phone: str, notes: str) -> None:
        with self.db._connect() as conn:
            conn.execute(
                "UPDATE Patients SET name=?, age=?, gender=?, phone=?, notes=? WHERE id=?",
                (name.strip(), age, gender.strip(), phone.strip(), notes.strip(), patient_id),
            )

    def delete_patient(self, patient_id: int) -> None:
        with self.db._connect() as conn:
            conn.execute("DELETE FROM Patients WHERE id=?", (patient_id,))

    def list_products(self) -> list[dict[str, Any]]:
        with self.db._connect() as conn:
            rows = conn.execute("SELECT * FROM Products ORDER BY category, name").fetchall()
        return self.db.rows_to_dict(rows)

    def add_product(self, name: str, category: str, mrp: float, base_price: float, tax_percent: float) -> None:
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
        with self.db._connect() as conn:
            conn.execute(
                "UPDATE Products SET name=?, category=?, mrp=?, base_price=?, tax_percent=? WHERE id=?",
                (name.strip(), category.strip(), mrp, base_price, tax_percent, product_id),
            )

    def delete_product(self, product_id: int) -> None:
        with self.db._connect() as conn:
            conn.execute("DELETE FROM Products WHERE id=?", (product_id,))

    def create_quotation(self, patient_id: int, selected_items: list[dict[str, Any]]) -> dict[str, Any]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        subtotal = 0.0
        total_tax = 0.0
        for item in selected_items:
            qty = int(item["quantity"])
            base = float(item["base_price"])
            tax_percent = float(item["tax_percent"])
            subtotal += base * qty
            total_tax += (base * tax_percent / 100.0) * qty

        grand_total = subtotal + total_tax

        with self.db._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO Quotations(patient_id, date, subtotal, total_tax, grand_total) VALUES (?, ?, ?, ?, ?)",
                (patient_id, now, subtotal, total_tax, grand_total),
            )
            quotation_id = cursor.lastrowid
            for item in selected_items:
                qty = int(item["quantity"])
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
        with self.db._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, date, subtotal, total_tax, grand_total
                FROM Quotations
                WHERE patient_id = ?
                ORDER BY id DESC
                """,
                (patient_id,),
            ).fetchall()

        history = self.db.rows_to_dict(rows)
        for row in history:
            row["invoice_number"] = self.invoice_number(int(row["id"]))
        return history

    def get_quotation_detail(self, quotation_id: int) -> dict[str, Any] | None:
        with self.db._connect() as conn:
            quotation = conn.execute(
                """
                SELECT q.id, q.patient_id, q.date, q.subtotal, q.total_tax, q.grand_total,
                       p.name AS patient_name, p.age, p.gender, p.phone, p.notes
                FROM Quotations q
                INNER JOIN Patients p ON p.id = q.patient_id
                WHERE q.id = ?
                """,
                (quotation_id,),
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

    def get_patient(self, patient_id: int) -> dict[str, Any] | None:
        with self.db._connect() as conn:
            row = conn.execute("SELECT * FROM Patients WHERE id=?", (patient_id,)).fetchone()
        return dict(row) if row else None

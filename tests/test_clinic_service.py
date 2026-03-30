from __future__ import annotations

import os
import tempfile
import unittest
from uuid import uuid4
from pathlib import Path

from clinic_app.database import DatabaseManager
from clinic_app.services import ClinicService


class ClinicServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = Path(tempfile.gettempdir()) / f"clinic_test_{uuid4().hex}.db"
        self.db = DatabaseManager(db_path=self.db_path)
        self.service = ClinicService(self.db)
        with self.db._connect() as conn:
            admin_row = conn.execute("SELECT id FROM Users WHERE username = ?", ("admin",)).fetchone()
        self.assertIsNotNone(admin_row)
        self.service.set_current_user(int(admin_row["id"]))

    def tearDown(self) -> None:
        try:
            if self.db_path.exists():
                os.remove(self.db_path)
        except PermissionError:
            # Ignore occasional Windows file lock release delay during test shutdown.
            pass

    def _add_sample_patient(self) -> int:
        self.service.add_patient("Test Patient", 35, "Female", "9876543210", "Test notes")
        patients = self.service.list_patients(search="Test Patient")
        self.assertTrue(patients)
        return int(patients[0]["id"])

    def _sample_selected_item(self) -> list[dict]:
        product = self.service.list_products()[0]
        return [
            {
                "id": int(product["id"]),
                "name": product["name"],
                "base_price": float(product["base_price"]),
                "tax_percent": float(product["tax_percent"]),
                "quantity": 2,
            }
        ]

    def test_soft_delete_and_restore_patient_with_quotations(self) -> None:
        patient_id = self._add_sample_patient()
        quotation = self.service.create_quotation(patient_id, self._sample_selected_item())
        self.assertIsNotNone(quotation["quotation_id"])

        ok, message = self.service.delete_patient(patient_id)
        self.assertFalse(ok)
        self.assertIn("quotation record", message)

        ok, message = self.service.delete_patient(patient_id, force=True)
        self.assertTrue(ok)
        self.assertIn("archived", message.lower())

        self.assertIsNone(self.service.get_patient(patient_id))
        archived = self.service.get_patient(patient_id, include_deleted=True)
        self.assertIsNotNone(archived)
        self.assertIsNotNone(archived["deleted_at"])

        self.assertEqual(self.service.list_patient_quotations(patient_id), [])

        ok, message = self.service.restore_patient(patient_id, restore_quotations=True)
        self.assertTrue(ok)
        self.assertIn("restored", message.lower())

        self.assertIsNotNone(self.service.get_patient(patient_id))
        history = self.service.list_patient_quotations(patient_id)
        self.assertEqual(len(history), 1)

    def test_patient_validation_phone_and_duplicate(self) -> None:
        with self.assertRaises(ValueError):
            self.service.add_patient("Invalid Phone", 20, "Male", "98A765", "")

        self.service.add_patient("Unique Name", 29, "Male", "9998887776", "")
        with self.assertRaises(ValueError):
            self.service.add_patient("Unique Name", 29, "Male", "9998887776", "")

    def test_product_validation_rules(self) -> None:
        with self.assertRaises(ValueError):
            self.service.add_product("X", "Cat", 100.0, 90.0, 5.0)

        with self.assertRaises(ValueError):
            self.service.add_product("Valid Name", "Category", 80.0, 90.0, 5.0)

        with self.assertRaises(ValueError):
            self.service.add_product("Valid Name", "Category", 120.0, 100.0, 70.0)

    def test_create_quotation_requires_positive_quantity(self) -> None:
        patient_id = self._add_sample_patient()
        product = self.service.list_products()[0]

        with self.assertRaises(ValueError):
            self.service.create_quotation(
                patient_id,
                [
                    {
                        "id": int(product["id"]),
                        "name": product["name"],
                        "base_price": float(product["base_price"]),
                        "tax_percent": float(product["tax_percent"]),
                        "quantity": 0,
                    }
                ],
            )

    def test_patients_are_isolated_per_account(self) -> None:
        with self.db._connect() as conn:
            conn.execute(
                """
                INSERT INTO Users(username, password_hash, recovery_question, recovery_answer_hash)
                VALUES('userb', X'00', 'q', X'00')
                """
            )
            user_b_id = conn.execute("SELECT id FROM Users WHERE username='userb'").fetchone()["id"]
            admin_id = conn.execute("SELECT id FROM Users WHERE username='admin'").fetchone()["id"]

        self.service.set_current_user(int(admin_id))
        self.service.add_patient("Admin Scoped", 33, "Male", "9991112223", "admin data")
        admin_rows = self.service.list_patients(search="Admin Scoped")
        self.assertEqual(len(admin_rows), 1)

        self.service.set_current_user(int(user_b_id))
        user_b_rows = self.service.list_patients(search="Admin Scoped")
        self.assertEqual(len(user_b_rows), 0)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import bcrypt

LOCAL_DB_DIR = Path.home() / "AppData" / "Local" / "ClinicApp"
DB_PATH = LOCAL_DB_DIR / "clinic.db"


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS Users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash BLOB NOT NULL,
                    recovery_question TEXT,
                    recovery_answer_hash BLOB
                );

                CREATE TABLE IF NOT EXISTS Patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_user_id INTEGER,
                    name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    phone TEXT,
                    notes TEXT,
                    deleted_at TEXT,
                    FOREIGN KEY (owner_user_id) REFERENCES Users(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS Products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    mrp REAL NOT NULL,
                    base_price REAL NOT NULL,
                    tax_percent REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Quotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_user_id INTEGER,
                    patient_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    subtotal REAL NOT NULL DEFAULT 0,
                    total_tax REAL NOT NULL DEFAULT 0,
                    grand_total REAL NOT NULL DEFAULT 0,
                    deleted_at TEXT,
                    FOREIGN KEY (patient_id) REFERENCES Patients(id) ON DELETE RESTRICT,
                    FOREIGN KEY (owner_user_id) REFERENCES Users(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS Quotation_Items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quotation_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    base_price REAL NOT NULL DEFAULT 0,
                    tax_amount REAL NOT NULL DEFAULT 0,
                    final_price REAL NOT NULL,
                    FOREIGN KEY (quotation_id) REFERENCES Quotations(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE RESTRICT
                );

                CREATE TABLE IF NOT EXISTS Settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            self._run_migrations(conn)
        self.seed_defaults()

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        self._ensure_column(conn, "Quotations", "subtotal", "REAL NOT NULL DEFAULT 0")
        self._ensure_column(conn, "Quotations", "total_tax", "REAL NOT NULL DEFAULT 0")
        self._ensure_column(conn, "Quotations", "grand_total", "REAL NOT NULL DEFAULT 0")
        self._ensure_column(conn, "Quotations", "deleted_at", "TEXT")
        self._ensure_column(conn, "Quotations", "owner_user_id", "INTEGER")

        self._ensure_column(conn, "Quotation_Items", "base_price", "REAL NOT NULL DEFAULT 0")
        self._ensure_column(conn, "Quotation_Items", "tax_amount", "REAL NOT NULL DEFAULT 0")
        self._ensure_column(conn, "Patients", "owner_user_id", "INTEGER")
        self._ensure_column(conn, "Patients", "deleted_at", "TEXT")
        self._ensure_column(conn, "Users", "recovery_question", "TEXT")
        self._ensure_column(conn, "Users", "recovery_answer_hash", "BLOB")

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
        columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing_names = {row["name"] for row in columns}
        if column in existing_names:
            return
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

    def seed_defaults(self) -> None:
        with self._connect() as conn:
            admin_exists = conn.execute("SELECT id FROM Users WHERE username = ?", ("admin",)).fetchone()
            if not admin_exists:
                password_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt())
                answer_hash = bcrypt.hashpw("admin1234".encode("utf-8"), bcrypt.gensalt())
                conn.execute(
                    """
                    INSERT INTO Users(username, password_hash, recovery_question, recovery_answer_hash)
                    VALUES(?, ?, ?, ?)
                    """,
                    ("admin", password_hash, "What is the clinic admin recovery code?", answer_hash),
                )

            doctor_exists = conn.execute("SELECT id FROM Users WHERE username = ?", ("doctor",)).fetchone()
            if not doctor_exists:
                doctor_hash = bcrypt.hashpw("doctor123".encode("utf-8"), bcrypt.gensalt())
                doctor_answer_hash = bcrypt.hashpw("doctor1234".encode("utf-8"), bcrypt.gensalt())
                conn.execute(
                    """
                    INSERT INTO Users(username, password_hash, recovery_question, recovery_answer_hash)
                    VALUES(?, ?, ?, ?)
                    """,
                    ("doctor", doctor_hash, "What is the doctor recovery code?", doctor_answer_hash),
                )

            conn.execute(
                """
                UPDATE Users
                SET recovery_question = ?
                WHERE username = ? AND (recovery_question IS NULL OR TRIM(recovery_question) = '')
                """,
                ("What is the clinic admin recovery code?", "admin"),
            )
            conn.execute(
                """
                UPDATE Users
                SET recovery_question = ?
                WHERE username = ? AND (recovery_question IS NULL OR TRIM(recovery_question) = '')
                """,
                ("What is the doctor recovery code?", "doctor"),
            )

            admin_recovery_row = conn.execute(
                "SELECT recovery_answer_hash FROM Users WHERE username = ?",
                ("admin",),
            ).fetchone()
            if admin_recovery_row and not admin_recovery_row["recovery_answer_hash"]:
                conn.execute(
                    "UPDATE Users SET recovery_answer_hash = ? WHERE username = ?",
                    (bcrypt.hashpw("admin1234".encode("utf-8"), bcrypt.gensalt()), "admin"),
                )

            doctor_recovery_row = conn.execute(
                "SELECT recovery_answer_hash FROM Users WHERE username = ?",
                ("doctor",),
            ).fetchone()
            if doctor_recovery_row and not doctor_recovery_row["recovery_answer_hash"]:
                conn.execute(
                    "UPDATE Users SET recovery_answer_hash = ? WHERE username = ?",
                    (bcrypt.hashpw("doctor1234".encode("utf-8"), bcrypt.gensalt()), "doctor"),
                )

            admin_user_row = conn.execute("SELECT id FROM Users WHERE username = ?", ("admin",)).fetchone()
            admin_user_id = admin_user_row["id"] if admin_user_row else None
            if admin_user_id is not None:
                conn.execute(
                    "UPDATE Patients SET owner_user_id = ? WHERE owner_user_id IS NULL",
                    (admin_user_id,),
                )
                conn.execute(
                    """
                    UPDATE Quotations
                    SET owner_user_id = (
                        SELECT p.owner_user_id
                        FROM Patients p
                        WHERE p.id = Quotations.patient_id
                    )
                    WHERE owner_user_id IS NULL
                    """,
                )
                conn.execute(
                    "UPDATE Quotations SET owner_user_id = ? WHERE owner_user_id IS NULL",
                    (admin_user_id,),
                )

            pin_row = conn.execute("SELECT value FROM Settings WHERE key = ?", ("admin_pin_hash",)).fetchone()
            if not pin_row:
                default_pin_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                conn.execute(
                    "INSERT INTO Settings(key, value) VALUES(?, ?)",
                    ("admin_pin_hash", default_pin_hash),
                )

            default_products = [
                ("Cap CH95 (30Cap)", "Nutrition Kit", 590, 561.90, 5),
                ("C3M Powder", "Nutrition Kit", 2599, 2475.24, 5),
                ("CUP Powder", "Nutrition Kit", 2213, 2107.62, 5),
                ("Cap Withangen (30Cap)", "Nutrition Kit", 799, 760.95, 5),
                ("Cap AC95 (30Cap)", "Nutrition Kit", 2950, 2809.52, 5),
                ("Cap Livocin (30Cap)", "Nutrition Kit", 2124, 2022.86, 5),
                ("Cap Fulvican (30Cap)", "Nutrition Kit", 738, 702.86, 5),
                ("Frank Oil", "Nutrition Kit", 2056, 1958.10, 5),
                ("Tab Cyanolina (60Tab)", "Nutrition Kit", 516, 491.43, 5),
                ("Tab Phytox (60Tab)", "Nutrition Kit", 1270, 1209.52, 5),
                ("Quinoil", "Nutrition Kit", 1180, 1123.81, 5),
                ("Anacose Powder", "Nutrition Kit", 2124, 2022.86, 5),
                ("Methicon", "Nutrition Kit", 900, 857.14, 5),
                ("Cap K27 (30Cap)", "Nutrition Kit", 2700, 2571.43, 5),
                ("Cap Oxy95 (30Cap)", "Nutrition Kit", 3257, 3101.90, 5),
                ("Cap OxyForte (30Cap)", "Nutrition Kit", 3983, 3793.33, 5),
                ("Cap PSP (30Cap)", "Nutrition Kit", 1770, 1685.71, 5),
                ("OMG Oil", "Nutrition Kit", 8250, 7857.14, 5),
                ("3C (30Cap)", "Nutrition Kit", 1918, 1826.67, 5),
                ("Drops (G)", "Nutrition Kit", 1000, 1000.00, 0),
                ("Probiotics", "Enzyme Kit", 1150, 1150.00, 0),
                ("Limcee Chewable Tab (15's)", "Enzyme Kit", 25, 25.00, 0),
                ("Serratiopeptidase 10mg (10's)", "Enzyme Kit", 70, 70.00, 0),
                ("Ivermectin (10's)", "Enzyme Kit", 250, 250.00, 0),
                ("Supradyn Tab (15's)", "Enzyme Kit", 40, 40.00, 0),
                ("Folic Tab (45's)", "Enzyme Kit", 77, 77.00, 0),
                ("Hemofix (15's)", "Enzyme Kit", 300, 300.00, 0),
                ("Gisse3 (10's)", "Enzyme Kit", 190, 190.00, 0),
                ("Albendazole & Ivermectine", "Enzyme Kit", 30, 30.00, 0),
                ("N-Acetyl Cysteine (Mucyst) (10's)", "Enzyme Kit", 286, 286.00, 0),
                ("Vitamin D3 60k Sachet (10's)", "Enzyme Kit", 364, 364.00, 0),
                ("Coconut Oil", "Dietary Kit", 1071, 1020.00, 5),
                ("Juice Powder", "Dietary Kit", 354, 316.07, 12),
                ("Himalayan Pink Salt", "Dietary Kit", 180, 180.00, 0),
                ("Vedic A2 Cow Ghee", "Dietary Kit", 1008, 960.00, 5),
                ("Natural & Unrefined Honey", "Dietary Kit", 630, 600.00, 5),
                ("Sodium Bicarbonate", "Dietary Kit", 135, 120.54, 12),
                ("MCT Powder", "Dietary Kit", 850, 720.34, 18),
                ("Green Tea Leaves", "Dietary Kit", 100, 100.00, 0),
                ("MCT Oil (250ml)", "Dietary Kit", 1125, 953.39, 18),
                ("MCT Oil (500ml)", "Dietary Kit", 2124, 1800.00, 18),
                ("Wheat (1kg)", "Dietary Kit", 150, 150.00, 0),
                ("Red Rice", "Dietary Kit", 350, 350.00, 0),
            ]
            conn.executemany(
                """
                INSERT INTO Products(name, category, mrp, base_price, tax_percent)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    category=excluded.category,
                    mrp=excluded.mrp,
                    base_price=excluded.base_price,
                    tax_percent=excluded.tax_percent
                """,
                default_products,
            )

            patients_count = conn.execute("SELECT COUNT(*) AS count FROM Patients").fetchone()["count"]
            if patients_count == 0:
                conn.executemany(
                    "INSERT INTO Patients(name, age, gender, phone, notes) VALUES(?, ?, ?, ?, ?)",
                    [
                        ("Riya Sharma", 34, "Female", "9876543210", "Thyroid support plan"),
                        ("Amit Verma", 41, "Male", "9898989898", "Weight management"),
                    ],
                )

    @staticmethod
    def rows_to_dict(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows]

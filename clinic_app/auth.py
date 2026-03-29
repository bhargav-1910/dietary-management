from __future__ import annotations

import bcrypt

from clinic_app.database import DatabaseManager


class AuthService:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db

    @staticmethod
    def _normalize_hash(stored_hash) -> bytes:
        if isinstance(stored_hash, memoryview):
            stored_hash = stored_hash.tobytes()
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")
        return stored_hash

    def login(self, username: str, password: str) -> bool:
        with self.db._connect() as conn:
            row = conn.execute(
                "SELECT password_hash FROM Users WHERE username = ?",
                (username.strip(),),
            ).fetchone()

        if not row:
            return False

        stored_hash = self._normalize_hash(row["password_hash"])

        return bcrypt.checkpw(password.encode("utf-8"), stored_hash)

    def reset_password_with_pin(self, username: str, new_password: str, admin_pin: str) -> bool:
        with self.db._connect() as conn:
            pin_row = conn.execute("SELECT value FROM Settings WHERE key = ?", ("admin_pin_hash",)).fetchone()
            if not pin_row:
                return False

            pin_hash = self._normalize_hash(pin_row["value"])
            if not bcrypt.checkpw(admin_pin.encode("utf-8"), pin_hash):
                return False

            user_row = conn.execute("SELECT id FROM Users WHERE username = ?", (username.strip(),)).fetchone()
            if not user_row:
                return False

            new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
            conn.execute("UPDATE Users SET password_hash = ? WHERE id = ?", (new_hash, user_row["id"]))

        return True

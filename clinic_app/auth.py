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

    def get_user_id(self, username: str) -> int | None:
        with self.db._connect() as conn:
            row = conn.execute("SELECT id FROM Users WHERE username = ?", (username.strip(),)).fetchone()
        return int(row["id"]) if row else None

    def create_account(
        self,
        username: str,
        password: str,
        recovery_question: str,
        recovery_answer: str,
    ) -> tuple[bool, str]:
        username = username.strip()
        recovery_question = recovery_question.strip()
        recovery_answer = recovery_answer.strip()

        if len(username) < 3:
            return False, "Username must be at least 3 characters."
        if len(password) < 6:
            return False, "Password must be at least 6 characters."
        if len(recovery_question) < 6:
            return False, "Recovery question is too short."
        if len(recovery_answer) < 3:
            return False, "Recovery answer must be at least 3 characters."

        with self.db._connect() as conn:
            exists = conn.execute("SELECT id FROM Users WHERE username = ?", (username,)).fetchone()
            if exists:
                return False, "Username already exists."

            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            answer_hash = bcrypt.hashpw(recovery_answer.lower().encode("utf-8"), bcrypt.gensalt())
            conn.execute(
                """
                INSERT INTO Users(username, password_hash, recovery_question, recovery_answer_hash)
                VALUES(?, ?, ?, ?)
                """,
                (username, password_hash, recovery_question, answer_hash),
            )

        return True, "Account created."

    def get_recovery_question(self, username: str) -> str | None:
        with self.db._connect() as conn:
            row = conn.execute(
                "SELECT recovery_question FROM Users WHERE username = ?",
                (username.strip(),),
            ).fetchone()
        if not row:
            return None
        return row["recovery_question"]

    def reset_password_with_recovery_answer(self, username: str, new_password: str, recovery_answer: str) -> bool:
        username = username.strip()
        recovery_answer = recovery_answer.strip()
        if len(new_password) < 6 or not recovery_answer:
            return False

        with self.db._connect() as conn:
            user_row = conn.execute(
                "SELECT id, recovery_answer_hash FROM Users WHERE username = ?",
                (username,),
            ).fetchone()
            if not user_row:
                return False

            answer_hash = user_row["recovery_answer_hash"]
            if not answer_hash:
                return False

            answer_hash_normalized = self._normalize_hash(answer_hash)
            if not bcrypt.checkpw(recovery_answer.lower().encode("utf-8"), answer_hash_normalized):
                return False

            new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
            conn.execute("UPDATE Users SET password_hash = ? WHERE id = ?", (new_hash, user_row["id"]))

        return True

    def reset_password_with_pin(self, username: str, new_password: str, admin_pin: str) -> bool:
        return self.reset_password_with_recovery_answer(username, new_password, admin_pin)

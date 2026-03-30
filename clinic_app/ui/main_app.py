from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from clinic_app.auth import AuthService
from clinic_app.database import DatabaseManager
from clinic_app.pdf_service import PDFService
from clinic_app.services import ClinicService
from clinic_app.ui.login_frame import LoginFrame
from clinic_app.ui.main_frame import MainFrame


class ClinicApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Dietary Clinic Quotation System")
        self.geometry("1200x760")
        self.minsize(1080, 680)

        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color="#f8f9fa")

        self.db = DatabaseManager()
        self.auth_service = AuthService(self.db)
        self.clinic_service = ClinicService(self.db)
        self.pdf_service = PDFService(Path(__file__).resolve().parent.parent.parent / "output")

        self.current_user: str | None = None
        self.current_frame: ctk.CTkFrame | None = None

        self.show_login()

    def _swap_frame(self, frame: ctk.CTkFrame) -> None:
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = frame
        self.current_frame.pack(fill="both", expand=True)

    def show_login(self) -> None:
        self.current_user = None
        self.clinic_service.set_current_user(None)
        frame = LoginFrame(self, on_login_success=self.on_login_success)
        self._swap_frame(frame)

    def on_login_success(self, username: str) -> None:
        user_id = self.auth_service.get_user_id(username)
        if user_id is None:
            self.show_login()
            return

        self.clinic_service.set_current_user(user_id)
        self.current_user = username
        frame = MainFrame(
            self,
            clinic_service=self.clinic_service,
            pdf_service=self.pdf_service,
            username=username,
            on_logout=self.show_login,
        )
        self._swap_frame(frame)

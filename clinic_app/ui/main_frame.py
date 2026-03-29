from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox

from clinic_app.pdf_service import PDFService
from clinic_app.services import ClinicService
from clinic_app.ui.patients_frame import PatientsFrame
from clinic_app.ui.products_frame import ProductsFrame
from clinic_app.ui.history_preview_window import HistoryPreviewWindow
from clinic_app.ui.quotation_popup import QuotationPopup


class MainFrame(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk,
        clinic_service: ClinicService,
        pdf_service: PDFService,
        username: str,
        on_logout,
    ) -> None:
        super().__init__(master)
        self.master = master
        self.clinic_service = clinic_service
        self.pdf_service = pdf_service
        self.username = username
        self.on_logout = on_logout

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(sidebar, text="Dietary Clinic", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(24, 8), sticky="w"
        )
        ctk.CTkLabel(sidebar, text=f"Doctor: {username}", text_color="gray").grid(
            row=1, column=0, padx=20, pady=(0, 20), sticky="w"
        )

        ctk.CTkButton(sidebar, text="Dashboard", command=lambda: self.show_screen("dashboard")).grid(
            row=2, column=0, padx=16, pady=8, sticky="ew"
        )
        ctk.CTkButton(sidebar, text="Patients", command=lambda: self.show_screen("patients")).grid(
            row=3, column=0, padx=16, pady=8, sticky="ew"
        )
        ctk.CTkButton(sidebar, text="Products", command=lambda: self.show_screen("products")).grid(
            row=4, column=0, padx=16, pady=8, sticky="ew"
        )

        ctk.CTkButton(sidebar, text="Logout", fg_color="#b91c1c", hover_color="#991b1b", command=self._logout).grid(
            row=8, column=0, padx=16, pady=8, sticky="sew"
        )
        sidebar.grid_rowconfigure(7, weight=1)

        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=0)
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.screens: dict[str, ctk.CTkFrame] = {
            "dashboard": self._build_dashboard(),
            "patients": PatientsFrame(
                self.content,
                clinic_service=self.clinic_service,
                on_generate_quotation=self._open_quotation_popup,
                on_view_quotation=self._open_history_preview,
            ),
            "products": ProductsFrame(self.content, clinic_service=self.clinic_service),
        }

        self.current_screen: ctk.CTkFrame | None = None
        self.show_screen("dashboard")

    def _build_dashboard(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.content)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Quotation Dashboard", font=ctk.CTkFont(size=28, weight="bold")).grid(
            row=0, column=0, padx=26, pady=(28, 10), sticky="w"
        )
        ctk.CTkLabel(
            frame,
            justify="left",
            text=(
                "Workflow:\n"
                "1. Login\n"
                "2. Open Patients\n"
                "3. Select patient\n"
                "4. Click Generate Quotation\n"
                "5. Select checklist items in popup"
            ),
            font=ctk.CTkFont(size=16),
        ).grid(row=1, column=0, padx=26, pady=8, sticky="w")

        ctk.CTkButton(frame, text="Backup Database", width=220, command=self._backup_database).grid(
            row=2, column=0, padx=26, pady=(20, 8), sticky="w"
        )
        ctk.CTkButton(frame, text="Restore Database", width=220, command=self._restore_database).grid(
            row=3, column=0, padx=26, pady=8, sticky="w"
        )
        ctk.CTkLabel(
            frame,
            text=f"Local DB: {self.master.db.db_path}",
            text_color="gray",
            justify="left",
        ).grid(row=4, column=0, padx=26, pady=(10, 8), sticky="w")

        return frame

    def show_screen(self, key: str) -> None:
        if self.current_screen is not None:
            self.current_screen.grid_forget()
        screen = self.screens[key]
        screen.grid(row=0, column=0, sticky="nsew")
        self.current_screen = screen

    def _open_quotation_popup(self, patient: dict, on_saved_callback=None) -> None:
        products = self.clinic_service.list_products()
        QuotationPopup(
            self,
            clinic_service=self.clinic_service,
            pdf_service=self.pdf_service,
            patient=patient,
            products=products,
            on_saved_callback=on_saved_callback,
        )

    def _open_history_preview(self, quotation: dict, mode: str) -> None:
        HistoryPreviewWindow(self, self.pdf_service, quotation, mode=mode)

    def _backup_database(self) -> None:
        suggested = Path.home() / "Desktop" / "clinic_backup.db"
        selected = filedialog.asksaveasfilename(
            parent=self,
            title="Backup Database",
            initialfile=suggested.name,
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db")],
        )
        if not selected:
            return

        backup_path = self.clinic_service.backup_database(selected)
        messagebox.showinfo("Backup complete", f"Backup saved to:\n{backup_path}")

    def _restore_database(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self,
            title="Restore Database",
            filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")],
        )
        if not selected:
            return

        if not messagebox.askyesno("Confirm restore", "This will overwrite current data. Continue?"):
            return

        db_path = self.clinic_service.restore_database(selected)
        patients_screen = self.screens.get("patients")
        if hasattr(patients_screen, "refresh_table"):
            patients_screen.refresh_table()

        products_screen = self.screens.get("products")
        if hasattr(products_screen, "refresh_table"):
            products_screen.refresh_table()

        messagebox.showinfo("Restore complete", f"Database restored from file.\nActive DB:\n{db_path}")

    def _logout(self) -> None:
        if messagebox.askyesno("Confirm logout", "Do you want to logout?"):
            self.on_logout()

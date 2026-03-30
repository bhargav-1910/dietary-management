from __future__ import annotations

import json
import tempfile
import zipfile
from datetime import datetime
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

        self.palette = {
            "surface": "#f8f9fa",
            "sidebar": "#f3f4f5",
            "card": "#ffffff",
            "text": "#191c1d",
            "muted": "#414751",
            "primary": "#005da7",
            "primary_hover": "#004883",
            "danger": "#ba1a1a",
            "danger_hover": "#93000a",
        }
        self.configure(fg_color=self.palette["surface"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=self.palette["sidebar"])
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="Clinical\nSanctuary",
            text_color=self.palette["text"],
            font=ctk.CTkFont(size=20, weight="bold"),
            justify="left",
        ).grid(
            row=0, column=0, padx=20, pady=(24, 8), sticky="w"
        )
        ctk.CTkLabel(sidebar, text=f"Account: {username}", text_color=self.palette["muted"]).grid(
            row=1, column=0, padx=20, pady=(0, 20), sticky="w"
        )

        ctk.CTkButton(
            sidebar,
            text="Dashboard",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=lambda: self.show_screen("dashboard"),
        ).grid(
            row=2, column=0, padx=16, pady=8, sticky="ew"
        )
        ctk.CTkButton(
            sidebar,
            text="Patients",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=lambda: self.show_screen("patients"),
        ).grid(
            row=3, column=0, padx=16, pady=8, sticky="ew"
        )
        ctk.CTkButton(
            sidebar,
            text="Products",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=lambda: self.show_screen("products"),
        ).grid(
            row=4, column=0, padx=16, pady=8, sticky="ew"
        )

        ctk.CTkButton(
            sidebar,
            text="Logout",
            fg_color=self.palette["danger"],
            hover_color=self.palette["danger_hover"],
            command=self._logout,
        ).grid(
            row=8, column=0, padx=16, pady=8, sticky="sew"
        )
        sidebar.grid_rowconfigure(7, weight=1)

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=self.palette["surface"])
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
        frame = ctk.CTkFrame(self.content, fg_color=self.palette["surface"])
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        patients = self.clinic_service.list_patients()
        patient_count = len(patients)
        quotation_count = 0
        revenue_total = 0.0
        for patient in patients:
            rows = self.clinic_service.list_patient_quotations(int(patient["id"]))
            quotation_count += len(rows)
            revenue_total += sum(float(row["grand_total"]) for row in rows)

        ctk.CTkLabel(
            frame,
            text="Clinic Command Center",
            text_color=self.palette["text"],
            font=ctk.CTkFont(size=32, weight="bold"),
        ).grid(
            row=0, column=0, columnspan=3, padx=26, pady=(28, 4), sticky="w"
        )
        ctk.CTkLabel(
            frame,
            text=f"Signed in as {self.username}. Data shown is account-scoped.",
            text_color=self.palette["muted"],
            font=ctk.CTkFont(size=14),
        ).grid(row=1, column=0, columnspan=3, padx=26, pady=(0, 12), sticky="w")

        stats = [
            ("Patients", str(patient_count)),
            ("Quotations", str(quotation_count)),
            ("Revenue", f"{revenue_total:.2f}"),
        ]
        for idx, (label, value) in enumerate(stats):
            card = ctk.CTkFrame(
                frame,
                fg_color=self.palette["card"],
                corner_radius=14,
                border_width=1,
                border_color="#dfe3eb",
            )
            card.grid(row=2, column=idx, padx=(26 if idx == 0 else 8, 26 if idx == 2 else 8), pady=(0, 10), sticky="ew")
            ctk.CTkLabel(card, text=label, text_color=self.palette["muted"], font=ctk.CTkFont(size=14)).grid(
                row=0, column=0, padx=16, pady=(14, 4), sticky="w"
            )
            ctk.CTkLabel(card, text=value, text_color=self.palette["text"], font=ctk.CTkFont(size=24, weight="bold")).grid(
                row=1, column=0, padx=16, pady=(0, 14), sticky="w"
            )

        workflow_card = ctk.CTkFrame(frame, fg_color=self.palette["card"], corner_radius=14, border_width=1, border_color="#dfe3eb")
        workflow_card.grid(row=3, column=0, columnspan=3, padx=26, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(
            workflow_card,
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
            text_color=self.palette["muted"],
        ).grid(row=0, column=0, padx=20, pady=16, sticky="w")

        actions = ctk.CTkFrame(frame, fg_color="transparent")
        actions.grid(row=4, column=0, columnspan=3, padx=26, pady=(8, 8), sticky="ew")
        actions.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkButton(
            actions,
            text="Open Patients",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=lambda: self.show_screen("patients"),
        ).grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        ctk.CTkButton(
            actions,
            text="Open Products",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=lambda: self.show_screen("products"),
        ).grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        ctk.CTkButton(
            actions,
            text="Backup Database",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=self._backup_database,
        ).grid(row=0, column=2, padx=6, pady=6, sticky="ew")
        ctk.CTkButton(
            actions,
            text="Restore Database",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=self._restore_database,
        ).grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        ctk.CTkButton(
            frame,
            text="Export This Account Bundle (JSON + PDFs)",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=self._export_account_bundle,
        ).grid(row=5, column=0, columnspan=3, padx=26, pady=(6, 8), sticky="ew")
        ctk.CTkLabel(
            frame,
            text=f"Local DB: {self.master.db.db_path}",
            text_color=self.palette["muted"],
            justify="left",
        ).grid(row=6, column=0, columnspan=3, padx=26, pady=(6, 4), sticky="w")

        ctk.CTkLabel(
            frame,
            text=(
                "Backup/Restore note: This operation applies to the full application database "
                "(all accounts in this app instance)."
            ),
            text_color=self.palette["muted"],
            justify="left",
            wraplength=760,
        ).grid(row=7, column=0, columnspan=3, padx=26, pady=(0, 8), sticky="w")

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

    def _export_account_bundle(self) -> None:
        suggested = Path.home() / "Desktop" / f"{self.username}_bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        selected = filedialog.asksaveasfilename(
            parent=self,
            title="Export Account Bundle",
            initialfile=suggested.name,
            defaultextension=".zip",
            filetypes=[("ZIP archive", "*.zip")],
        )
        if not selected:
            return

        patients = self.clinic_service.list_patients()
        patient_records: list[dict] = []
        quotations: list[dict] = []
        for patient in patients:
            history = self.clinic_service.list_patient_quotations(int(patient["id"]))
            details = []
            for row in history:
                detail = self.clinic_service.get_quotation_detail(int(row["id"]))
                if detail:
                    details.append(detail)
                    quotations.append(detail)

            patient_copy = dict(patient)
            patient_copy["quotations"] = details
            patient_records.append(patient_copy)

        payload = {
            "account": self.username,
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "patient_count": len(patient_records),
            "quotation_count": len(quotations),
            "patients": patient_records,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            json_path = root / "account_data.json"
            pdf_dir = root / "pdf"
            pdf_dir.mkdir(parents=True, exist_ok=True)

            json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

            for quotation in quotations:
                invoice_items = [
                    {
                        "name": item["name"],
                        "quantity": int(item["quantity"]),
                        "base_price": float(item["base_price"]),
                        "tax_percent": float(item["tax_percent"]),
                    }
                    for item in quotation["items"]
                ]
                totals = {
                    "subtotal": float(quotation["subtotal"]),
                    "total_tax": float(quotation["total_tax"]),
                    "grand_total": float(quotation["grand_total"]),
                }

                invoice_path = pdf_dir / f"{quotation['invoice_number']}.pdf"
                package_path = pdf_dir / f"package_{quotation['invoice_number']}.pdf"

                self.pdf_service.generate_invoice_pdf(
                    int(quotation["id"]),
                    quotation["patient"],
                    invoice_items,
                    totals,
                    str(quotation["date"]),
                    output_path=invoice_path,
                    invoice_number=quotation["invoice_number"],
                    document_title="Invoice",
                    document_number_label="Invoice Number",
                )

                self.pdf_service.generate_package_sheet(
                    quotation["patient"],
                    [{"name": item["name"]} for item in quotation["items"]],
                    output_path=package_path,
                )

            with zipfile.ZipFile(selected, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for file_path in root.rglob("*"):
                    if file_path.is_file():
                        archive.write(file_path, file_path.relative_to(root))

        messagebox.showinfo(
            "Export complete",
            (
                f"Account bundle saved to:\n{selected}\n\n"
                f"Patients: {len(patient_records)}\n"
                f"Quotations: {len(quotations)}"
            ),
        )

    def _logout(self) -> None:
        if messagebox.askyesno("Confirm logout", "Do you want to logout?"):
            self.on_logout()

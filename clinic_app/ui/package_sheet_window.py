from __future__ import annotations

import os
import tempfile

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from clinic_app.pdf_service import PDFService


class PackageSheetWindow(ctk.CTkToplevel):
    def __init__(self, master, pdf_service: PDFService, patient: dict, selected_items: list[dict]) -> None:
        super().__init__(master)
        self.pdf_service = pdf_service
        self.patient = patient
        self.selected_items = selected_items

        self.title("Package Sheet")
        self.geometry("760x560")
        self.minsize(680, 500)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Package Sheet", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=18, pady=(16, 4), sticky="w"
        )
        ctk.CTkLabel(self, text=f"Patient: {patient['name']}", font=ctk.CTkFont(size=15)).grid(
            row=1, column=0, padx=18, pady=(0, 10), sticky="w"
        )

        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        tree = ttk.Treeview(table_frame, columns=("product",), show="headings")
        tree.heading("product", text="Selected Products")
        tree.column("product", width=560)

        for item in selected_items:
            tree.insert("", "end", values=(item["name"],))

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        actions = ctk.CTkFrame(self)
        actions.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 16))
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(actions, text="Download PDF", command=self.download_pdf).grid(
            row=0, column=0, padx=6, pady=8, sticky="ew"
        )
        ctk.CTkButton(actions, text="Print", command=self.print_pdf).grid(
            row=0, column=1, padx=6, pady=8, sticky="ew"
        )

    def _render_pdf(self, output_path: str) -> str:
        file_path = self.pdf_service.generate_package_sheet(
            self.patient,
            self.selected_items,
            output_path=output_path,
        )
        return str(file_path)

    def download_pdf(self) -> None:
        default_name = f"package_sheet_{self.patient['id']}.pdf"
        selected_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Package Sheet PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")],
        )
        if not selected_path:
            return

        final_path = self._render_pdf(selected_path)
        messagebox.showinfo("Saved", f"Package sheet saved to:\n{final_path}")

    def print_pdf(self) -> None:
        temp_file = os.path.join(tempfile.gettempdir(), f"package_sheet_{self.patient['id']}.pdf")
        final_path = self._render_pdf(temp_file)

        try:
            os.startfile(final_path, "print")  # type: ignore[attr-defined]
        except Exception as exc:
            messagebox.showerror("Print failed", f"Could not send file to printer.\n{exc}")

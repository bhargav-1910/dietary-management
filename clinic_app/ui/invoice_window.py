from __future__ import annotations

import os
import tempfile

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from clinic_app.pdf_service import PDFService


class InvoiceWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        pdf_service: PDFService,
        patient: dict,
        selected_items: list[dict],
        totals: dict,
        quotation_info: dict,
    ) -> None:
        super().__init__(master)
        self.pdf_service = pdf_service
        self.patient = patient
        self.selected_items = selected_items
        self.totals = totals
        self.quotation_info = quotation_info

        self.title(f"Invoice #{quotation_info['quotation_id']}")
        self.geometry("900x620")
        self.minsize(840, 560)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(self, text=f"Invoice #{quotation_info['quotation_id']}", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(18, 4), sticky="w"
        )
        ctk.CTkLabel(self, text=f"Date: {quotation_info['date']}").grid(row=1, column=0, padx=20, pady=2, sticky="w")
        ctk.CTkLabel(
            self,
            text=(
                f"Patient: {patient['name']} | Age: {patient.get('age', '-')} | "
                f"Gender: {patient.get('gender', '-')} | Phone: {patient.get('phone', '-')}"
            ),
        ).grid(row=2, column=0, padx=20, pady=(2, 10), sticky="w")

        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("product", "qty", "base", "tax", "line_total")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        tree.heading("product", text="Product")
        tree.heading("qty", text="Qty")
        tree.heading("base", text="Base")
        tree.heading("tax", text="Tax %")
        tree.heading("line_total", text="Line Total")

        tree.column("product", width=320)
        tree.column("qty", width=60, anchor="center")
        tree.column("base", width=100, anchor="e")
        tree.column("tax", width=80, anchor="e")
        tree.column("line_total", width=120, anchor="e")

        for item in selected_items:
            qty = int(item["quantity"])
            base = float(item["base_price"])
            tax = float(item["tax_percent"])
            line_total = (base + (base * tax / 100.0)) * qty
            tree.insert("", "end", values=(item["name"], qty, f"{base:.2f}", f"{tax:.0f}%", f"{line_total:.2f}"))

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        footer = ctk.CTkFrame(self)
        footer.grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 16))
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(footer, text=f"Subtotal: {totals['subtotal']:.2f}", font=ctk.CTkFont(size=14)).grid(
            row=0, column=0, padx=12, pady=4, sticky="e"
        )
        ctk.CTkLabel(footer, text=f"Tax: {totals['total_tax']:.2f}", font=ctk.CTkFont(size=14)).grid(
            row=1, column=0, padx=12, pady=4, sticky="e"
        )
        ctk.CTkLabel(footer, text=f"Grand Total: {totals['grand_total']:.2f}", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=2, column=0, padx=12, pady=(4, 8), sticky="e"
        )

        actions = ctk.CTkFrame(self)
        actions.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 16))
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(actions, text="Download PDF", command=self.download_pdf).grid(
            row=0, column=0, padx=6, pady=8, sticky="ew"
        )
        ctk.CTkButton(actions, text="Print", command=self.print_pdf).grid(
            row=0, column=1, padx=6, pady=8, sticky="ew"
        )

    def _render_pdf(self, output_path: str) -> str:
        file_path = self.pdf_service.generate_invoice_pdf(
            self.quotation_info["quotation_id"],
            self.patient,
            self.selected_items,
            self.totals,
            self.quotation_info["date"],
            output_path=output_path,
        )
        return str(file_path)

    def download_pdf(self) -> None:
        default_name = f"invoice_{self.quotation_info['quotation_id']}.pdf"
        selected_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Invoice PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")],
        )
        if not selected_path:
            return

        final_path = self._render_pdf(selected_path)
        messagebox.showinfo("Saved", f"Invoice saved to:\n{final_path}")

    def print_pdf(self) -> None:
        temp_file = os.path.join(tempfile.gettempdir(), f"invoice_{self.quotation_info['quotation_id']}.pdf")
        final_path = self._render_pdf(temp_file)

        try:
            os.startfile(final_path, "print")  # type: ignore[attr-defined]
        except Exception as exc:
            messagebox.showerror("Print failed", f"Could not send file to printer.\n{exc}")

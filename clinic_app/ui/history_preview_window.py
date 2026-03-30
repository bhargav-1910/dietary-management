from __future__ import annotations

import tempfile
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from clinic_app.pdf_service import PDFService
from clinic_app.print_utils import has_connected_printer, print_pdf


class HistoryPreviewWindow(ctk.CTkToplevel):
    def __init__(self, master, pdf_service: PDFService, quotation: dict, mode: str = "invoice") -> None:
        super().__init__(master)
        self.pdf_service = pdf_service
        self.quotation = quotation
        self.mode = mode

        if mode == "invoice":
            title = "Bill Preview"
        elif mode == "quotation":
            title = "Quotation Preview"
        else:
            title = "Package Sheet Preview"
        self.title(title)
        self.geometry("920x640")
        self.minsize(840, 560)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=18, pady=(16, 4), sticky="w"
        )
        ctk.CTkLabel(
            self,
            text=f"{quotation['invoice_number']} | Date: {quotation['date']} | Patient: {quotation['patient']['name']}",
        ).grid(row=1, column=0, padx=18, pady=(0, 8), sticky="w")

        body = ctk.CTkFrame(self)
        body.grid(row=2, column=0, padx=18, pady=(0, 10), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        if mode in ("invoice", "quotation"):
            cols = ("product", "qty", "base", "tax", "final")
            tree = ttk.Treeview(body, columns=cols, show="headings")
            tree.heading("product", text="Product")
            tree.heading("qty", text="Qty")
            tree.heading("base", text="Base Price")
            tree.heading("tax", text="Tax %")
            tree.heading("final", text="Final Price")
            tree.column("product", width=340)
            tree.column("qty", width=70, anchor="center")
            tree.column("base", width=120, anchor="e")
            tree.column("tax", width=90, anchor="e")
            tree.column("final", width=120, anchor="e")

            for item in quotation["items"]:
                tree.insert(
                    "",
                    "end",
                    values=(
                        item["name"],
                        item["quantity"],
                        f"{float(item['base_price']):.2f}",
                        f"{float(item['tax_percent']):.0f}%",
                        f"{float(item['final_price']):.2f}",
                    ),
                )
        else:
            tree = ttk.Treeview(body, columns=("product",), show="headings")
            tree.heading("product", text="Selected Products")
            tree.column("product", width=620)
            for item in quotation["items"]:
                tree.insert("", "end", values=(item["name"],))

        scroll = ttk.Scrollbar(body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        if mode in ("invoice", "quotation"):
            totals_frame = ctk.CTkFrame(self)
            totals_frame.grid(row=3, column=0, padx=18, pady=(0, 10), sticky="ew")
            totals_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(totals_frame, text=f"Subtotal: {float(quotation['subtotal']):.2f}").grid(
                row=0, column=0, padx=10, pady=4, sticky="e"
            )
            ctk.CTkLabel(totals_frame, text=f"Tax: {float(quotation['total_tax']):.2f}").grid(
                row=1, column=0, padx=10, pady=4, sticky="e"
            )
            ctk.CTkLabel(
                totals_frame,
                text=f"Grand Total: {float(quotation['grand_total']):.2f}",
                font=ctk.CTkFont(size=18, weight="bold"),
            ).grid(row=2, column=0, padx=10, pady=(4, 8), sticky="e")

        actions = ctk.CTkFrame(self)
        actions.grid(row=4, column=0, padx=18, pady=(0, 16), sticky="ew")
        actions.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(actions, text="Print", command=self.print_current).grid(row=0, column=0, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(actions, text="Save as PDF", command=self.save_pdf).grid(row=0, column=1, padx=6, pady=8, sticky="ew")
        ctk.CTkButton(actions, text="Close", fg_color="gray", command=self.destroy).grid(row=0, column=2, padx=6, pady=8, sticky="ew")

    def _invoice_items_for_pdf(self) -> list[dict]:
        return [
            {
                "name": item["name"],
                "quantity": int(item["quantity"]),
                "base_price": float(item["base_price"]),
                "tax_percent": float(item["tax_percent"]),
            }
            for item in self.quotation["items"]
        ]

    def _write_pdf(self, target_path: str | Path) -> Path:
        if self.mode in ("invoice", "quotation"):
            if self.mode == "invoice":
                document_title = "Invoice"
                document_number_label = "Invoice Number"
                document_number = self.quotation["invoice_number"]
            else:
                document_title = "Quotation"
                document_number_label = "Quotation Number"
                document_number = f"QTN-{int(self.quotation['id']):04d}"

            return self.pdf_service.generate_invoice_pdf(
                int(self.quotation["id"]),
                self.quotation["patient"],
                self._invoice_items_for_pdf(),
                {
                    "subtotal": float(self.quotation["subtotal"]),
                    "total_tax": float(self.quotation["total_tax"]),
                    "grand_total": float(self.quotation["grand_total"]),
                },
                self.quotation["date"],
                output_path=target_path,
                invoice_number=document_number,
                document_title=document_title,
                document_number_label=document_number_label,
            )

        return self.pdf_service.generate_package_sheet(
            self.quotation["patient"],
            [{"name": item["name"]} for item in self.quotation["items"]],
            output_path=target_path,
        )

    def print_current(self) -> None:
        if not has_connected_printer():
            messagebox.showerror("No printer connected", "No printer connected")
            return

        temp_name = f"{self.mode}_{self.quotation['id']}.pdf"
        temp_path = Path(tempfile.gettempdir()) / temp_name
        pdf_path = self._write_pdf(temp_path)
        try:
            print_pdf(pdf_path)
        except Exception as exc:
            messagebox.showerror("Print failed", f"Could not send file to printer.\n{exc}")

    def save_pdf(self) -> None:
        default_name = f"{self.mode}_{self.quotation['id']}.pdf"
        selected_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")],
        )
        if not selected_path:
            return

        path = self._write_pdf(selected_path)
        messagebox.showinfo("Saved", f"PDF saved to:\n{path}")

from __future__ import annotations

import os
import tempfile
from collections import defaultdict
from typing import Any

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from clinic_app.pdf_service import PDFService
from clinic_app.print_utils import has_connected_printer, print_pdf
from clinic_app.services import ClinicService


class QuotationPopup(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        clinic_service: ClinicService,
        pdf_service: PDFService,
        patient: dict[str, Any],
        products: list[dict[str, Any]],
        on_saved_callback=None,
    ) -> None:
        super().__init__(master)
        self.title("Generate Quotation")
        self.geometry("1080x700")
        self.minsize(980, 620)

        self.clinic_service = clinic_service
        self.pdf_service = pdf_service
        self.patient = patient
        self.products = products
        self.on_saved_callback = on_saved_callback

        self.saved_quotation_info: dict[str, Any] | None = None
        self.current_preview: dict[str, Any] | None = None

        self.product_vars: dict[int, dict[str, Any]] = {}
        self.subtotal_var = ctk.StringVar(value="0.00")
        self.tax_var = ctk.StringVar(value="0.00")
        self.grand_var = ctk.StringVar(value="0.00")
        self.preview_mode_var = ctk.StringVar(value="Quotation")
        self.zoom_var = ctk.DoubleVar(value=1.0)
        self.print_copies_var = ctk.StringVar(value="1")

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text=f"Quotation for {patient['name']}",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(14, 8), sticky="w")

        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, padx=(18, 10), pady=10, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        right = ctk.CTkFrame(self)
        right.grid(row=1, column=1, padx=(10, 18), pady=10, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Live Totals", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=14, pady=(14, 10), sticky="w"
        )

        self._total_row(right, 1, "Subtotal", self.subtotal_var)
        self._total_row(right, 2, "Tax", self.tax_var)
        self._total_row(right, 3, "Grand Total", self.grand_var, bold=True)

        ctk.CTkLabel(right, text="Preview Mode", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=4, column=0, padx=14, pady=(14, 4), sticky="w"
        )
        ctk.CTkSegmentedButton(right, values=["Quotation", "Bill", "Package"], variable=self.preview_mode_var).grid(
            row=5, column=0, padx=14, pady=(0, 8), sticky="ew"
        )
        ctk.CTkButton(right, text="Preview Selected", height=40, command=self.preview_selected).grid(
            row=6, column=0, padx=14, pady=(0, 8), sticky="ew"
        )

        ctk.CTkButton(right, text="Preview Quotation", height=36, command=self.generate).grid(
            row=7, column=0, padx=14, pady=(4, 4), sticky="ew"
        )
        ctk.CTkButton(right, text="Preview Bill", height=36, command=self.preview_bill).grid(
            row=8, column=0, padx=14, pady=4, sticky="ew"
        )
        ctk.CTkButton(right, text="Preview Package Sheet", height=36, command=self.preview_package_sheet).grid(
            row=9, column=0, padx=14, pady=4, sticky="ew"
        )

        ctk.CTkLabel(right, text="Preview Zoom", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=10, column=0, padx=14, pady=(8, 2), sticky="w"
        )
        ctk.CTkSlider(
            right,
            from_=0.9,
            to=1.4,
            number_of_steps=10,
            variable=self.zoom_var,
            command=lambda _value: self._refresh_current_preview(),
        ).grid(row=11, column=0, padx=14, pady=(0, 8), sticky="ew")

        print_settings = ctk.CTkFrame(right, fg_color="transparent")
        print_settings.grid(row=12, column=0, padx=14, pady=(0, 8), sticky="ew")
        print_settings.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(print_settings, text="Copies").grid(row=0, column=0, padx=(0, 8), pady=2, sticky="w")
        ctk.CTkOptionMenu(print_settings, values=["1", "2", "3", "4", "5"], variable=self.print_copies_var).grid(
            row=0, column=1, pady=2, sticky="ew"
        )

        self.print_button = ctk.CTkButton(right, text="Print", height=40, command=self.print_bill)
        self.print_button.grid(row=13, column=0, padx=14, pady=8, sticky="ew")
        self.download_button = ctk.CTkButton(right, text="Save as PDF", height=40, command=self.download_pdf)
        self.download_button.grid(row=14, column=0, padx=14, pady=8, sticky="ew")
        self.back_button = ctk.CTkButton(right, text="Close Preview", height=40, fg_color="gray", command=self.show_checklist)
        self.back_button.grid(row=15, column=0, padx=14, pady=8, sticky="ew")
        ctk.CTkButton(right, text="Cancel", height=40, fg_color="#b91c1c", hover_color="#991b1b", command=self.destroy).grid(
            row=16, column=0, padx=14, pady=(8, 14), sticky="ew"
        )

        self._build_checklist_table()
        self._toggle_preview_actions(False)
        self.update_totals()
        self.transient(master)
        self.grab_set()

    def _clear_content(self) -> None:
        for child in self.content_frame.winfo_children():
            child.destroy()

    def _build_checklist_table(self) -> None:
        self._clear_content()

        frame = ctk.CTkScrollableFrame(self.content_frame, label_text="Category-wise Product Checklist")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.grid_columnconfigure(1, weight=1)

        header_font = ctk.CTkFont(size=14, weight="bold")
        ctk.CTkLabel(frame, text="Select", font=header_font).grid(row=0, column=0, padx=8, pady=(8, 6), sticky="w")
        ctk.CTkLabel(frame, text="Product", font=header_font).grid(row=0, column=1, padx=8, pady=(8, 6), sticky="w")
        ctk.CTkLabel(frame, text="Base", font=header_font).grid(row=0, column=2, padx=8, pady=(8, 6), sticky="e")
        ctk.CTkLabel(frame, text="Tax %", font=header_font).grid(row=0, column=3, padx=8, pady=(8, 6), sticky="e")
        ctk.CTkLabel(frame, text="Qty", font=header_font).grid(row=0, column=4, padx=8, pady=(8, 6), sticky="e")

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for p in self.products:
            grouped[p["category"]].append(p)

        category_order = ["Nutrition Kit", "Enzyme Kit", "Dietary Kit"]
        display_categories = category_order + sorted([c for c in grouped.keys() if c not in category_order])

        row_index = 1
        for category in display_categories:
            if category not in grouped:
                continue

            cat_label = ctk.CTkLabel(
                frame,
                text=category,
                font=ctk.CTkFont(size=15, weight="bold"),
                fg_color=("#e5e7eb", "#374151"),
                corner_radius=6,
                anchor="w",
            )
            cat_label.grid(row=row_index, column=0, columnspan=5, sticky="ew", padx=6, pady=(8, 4), ipadx=8, ipady=4)
            row_index += 1

            for product in grouped[category]:
                selected_var = self.product_vars.get(product["id"], {}).get("selected_var", ctk.IntVar(value=0))
                qty_var = self.product_vars.get(product["id"], {}).get("qty_var", ctk.StringVar(value="1"))
                if product["id"] not in self.product_vars:
                    qty_var.trace_add("write", lambda *_args: self.update_totals())

                self.product_vars[product["id"]] = {
                    "product": product,
                    "selected_var": selected_var,
                    "qty_var": qty_var,
                }

                ctk.CTkCheckBox(frame, text="", variable=selected_var, width=20, command=self.update_totals).grid(
                    row=row_index, column=0, padx=8, pady=4, sticky="w"
                )
                ctk.CTkLabel(frame, text=product["name"], anchor="w").grid(
                    row=row_index, column=1, padx=8, pady=4, sticky="w"
                )
                ctk.CTkLabel(frame, text=f"{float(product['base_price']):.2f}").grid(
                    row=row_index, column=2, padx=8, pady=4, sticky="e"
                )
                ctk.CTkLabel(frame, text=f"{float(product['tax_percent']):.0f}%").grid(
                    row=row_index, column=3, padx=8, pady=4, sticky="e"
                )

                qty_entry = ctk.CTkEntry(frame, width=64, textvariable=qty_var)
                qty_entry.grid(row=row_index, column=4, padx=8, pady=4, sticky="e")
                qty_entry.bind("<KeyRelease>", lambda _event: self.update_totals())

                row_index += 1

    def _total_row(self, frame: ctk.CTkFrame, row: int, label: str, value_var: ctk.StringVar, bold: bool = False) -> None:
        ctk.CTkLabel(frame, text=label).grid(row=row, column=0, padx=14, pady=(6, 0), sticky="w")
        font = ctk.CTkFont(size=18 if bold else 16, weight="bold" if bold else "normal")
        ctk.CTkLabel(frame, textvariable=value_var, font=font).grid(row=row, column=0, padx=14, pady=(6, 0), sticky="e")

    def _selected_items_and_totals(self) -> tuple[list[dict[str, Any]], dict[str, float]]:
        selected_items: list[dict[str, Any]] = []
        subtotal = 0.0
        total_tax = 0.0

        for config in self.product_vars.values():
            product = config["product"]
            if config["selected_var"].get() != 1:
                continue

            qty_text = str(config["qty_var"].get()).strip()
            if not qty_text.isdigit() or int(qty_text) <= 0:
                raise ValueError(f"Quantity for '{product['name']}' must be a positive whole number.")
            qty = int(qty_text)
            if qty > 999:
                raise ValueError(f"Quantity for '{product['name']}' cannot exceed 999.")

            base = float(product["base_price"])
            tax_percent = float(product["tax_percent"])
            tax_amount = base * (tax_percent / 100.0)

            subtotal += base * qty
            total_tax += tax_amount * qty

            selected_items.append(
                {
                    "id": product["id"],
                    "name": product["name"],
                    "category": product["category"],
                    "base_price": base,
                    "tax_percent": tax_percent,
                    "quantity": qty,
                }
            )

        totals = {
            "subtotal": subtotal,
            "total_tax": total_tax,
            "grand_total": subtotal + total_tax,
        }
        return selected_items, totals

    def update_totals(self) -> None:
        try:
            _, totals = self._selected_items_and_totals()
        except ValueError:
            return
        self.subtotal_var.set(f"{totals['subtotal']:.2f}")
        self.tax_var.set(f"{totals['total_tax']:.2f}")
        self.grand_var.set(f"{totals['grand_total']:.2f}")

    def _toggle_preview_actions(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.download_button.configure(state=state)
        self.back_button.configure(state=state)
        self.print_button.configure(state=state)

    def show_checklist(self) -> None:
        self.current_preview = None
        self._build_checklist_table()
        self._toggle_preview_actions(False)

    def _show_invoice_preview(
        self,
        selected_items: list[dict[str, Any]],
        totals: dict[str, float],
        quotation_info: dict[str, Any],
    ) -> None:
        self._clear_content()
        scale = float(self.zoom_var.get())

        self.current_preview = {
            "type": "invoice",
            "selected_items": selected_items,
            "totals": totals,
            "quotation_info": quotation_info,
        }

        wrap = ctk.CTkFrame(self.content_frame)
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(wrap, text=f"Invoice {quotation_info['invoice_number']}", font=ctk.CTkFont(size=max(14, int(22 * scale)), weight="bold")).grid(
            row=0, column=0, padx=16, pady=(14, 4), sticky="w"
        )
        ctk.CTkLabel(wrap, text=f"Date: {quotation_info['date']}").grid(row=1, column=0, padx=16, pady=2, sticky="w")
        ctk.CTkLabel(
            wrap,
            text=(
                f"Patient: {self.patient['name']} | Age: {self.patient.get('age', '-')} | "
                f"Gender: {self.patient.get('gender', '-')} | Phone: {self.patient.get('phone', '-')}"
            ),
        ).grid(row=2, column=0, padx=16, pady=(2, 8), sticky="w")

        table_frame = ctk.CTkFrame(wrap)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("product", "qty", "base", "tax", "line_total")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        style_name = f"PreviewInvoice{int(scale * 100)}.Treeview"
        style = ttk.Style(self)
        style.configure(style_name, rowheight=max(20, int(24 * scale)))
        tree.configure(style=style_name)
        tree.heading("product", text="Product")
        tree.heading("qty", text="Qty")
        tree.heading("base", text="Base")
        tree.heading("tax", text="Tax %")
        tree.heading("line_total", text="Line Total")
        tree.column("product", width=350)
        tree.column("qty", width=70, anchor="center")
        tree.column("base", width=120, anchor="e")
        tree.column("tax", width=90, anchor="e")
        tree.column("line_total", width=130, anchor="e")

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

        self._toggle_preview_actions(True)

    def _show_quotation_preview(
        self,
        selected_items: list[dict[str, Any]],
        totals: dict[str, float],
        quotation_info: dict[str, Any],
    ) -> None:
        self._clear_content()
        scale = float(self.zoom_var.get())

        self.current_preview = {
            "type": "quotation",
            "selected_items": selected_items,
            "totals": totals,
            "quotation_info": quotation_info,
        }

        wrap = ctk.CTkFrame(self.content_frame)
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(3, weight=1)

        quotation_number = f"QTN-{int(quotation_info['quotation_id']):04d}"
        ctk.CTkLabel(wrap, text=f"Quotation {quotation_number}", font=ctk.CTkFont(size=max(14, int(22 * scale)), weight="bold")).grid(
            row=0, column=0, padx=16, pady=(14, 4), sticky="w"
        )
        ctk.CTkLabel(wrap, text=f"Date: {quotation_info['date']}").grid(row=1, column=0, padx=16, pady=2, sticky="w")
        ctk.CTkLabel(
            wrap,
            text=(
                f"Patient: {self.patient['name']} | Age: {self.patient.get('age', '-')} | "
                f"Gender: {self.patient.get('gender', '-')} | Phone: {self.patient.get('phone', '-')}"
            ),
        ).grid(row=2, column=0, padx=16, pady=(2, 8), sticky="w")

        table_frame = ctk.CTkFrame(wrap)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("product", "qty", "base", "tax", "line_total")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        style_name = f"PreviewQuotation{int(scale * 100)}.Treeview"
        style = ttk.Style(self)
        style.configure(style_name, rowheight=max(20, int(24 * scale)))
        tree.configure(style=style_name)
        tree.heading("product", text="Product")
        tree.heading("qty", text="Qty")
        tree.heading("base", text="Base")
        tree.heading("tax", text="Tax %")
        tree.heading("line_total", text="Line Total")
        tree.column("product", width=350)
        tree.column("qty", width=70, anchor="center")
        tree.column("base", width=120, anchor="e")
        tree.column("tax", width=90, anchor="e")
        tree.column("line_total", width=130, anchor="e")

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

        self._toggle_preview_actions(True)

    def _show_package_preview(self, selected_items: list[dict[str, Any]]) -> None:
        self._clear_content()
        scale = float(self.zoom_var.get())

        self.current_preview = {
            "type": "package",
            "selected_items": selected_items,
        }

        wrap = ctk.CTkFrame(self.content_frame)
        wrap.grid(row=0, column=0, sticky="nsew")
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(wrap, text="Package Sheet", font=ctk.CTkFont(size=max(14, int(22 * scale)), weight="bold")).grid(
            row=0, column=0, padx=16, pady=(14, 4), sticky="w"
        )
        ctk.CTkLabel(wrap, text=f"Patient: {self.patient['name']}").grid(row=1, column=0, padx=16, pady=(0, 8), sticky="w")

        table_frame = ctk.CTkFrame(wrap)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        tree = ttk.Treeview(table_frame, columns=("product",), show="headings")
        style_name = f"PreviewPackage{int(scale * 100)}.Treeview"
        style = ttk.Style(self)
        style.configure(style_name, rowheight=max(20, int(24 * scale)))
        tree.configure(style=style_name)
        tree.heading("product", text="Selected Products")
        tree.column("product", width=580)

        for item in selected_items:
            tree.insert("", "end", values=(item["name"],))

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

        self._toggle_preview_actions(True)

    def _ensure_items(self) -> tuple[list[dict[str, Any]], dict[str, float]] | None:
        try:
            selected_items, totals = self._selected_items_and_totals()
        except ValueError as exc:
            messagebox.showerror("Invalid quantity", str(exc))
            return None

        if not selected_items:
            messagebox.showwarning("No items selected", "Please select at least one product.")
            return None
        return selected_items, totals

    def preview_selected(self) -> None:
        mode = self.preview_mode_var.get()
        if mode == "Quotation":
            self.preview_quotation()
            return
        if mode == "Bill":
            self.preview_bill()
            return
        self.preview_package_sheet()

    def _refresh_current_preview(self) -> None:
        if not self.current_preview:
            return

        preview_type = self.current_preview["type"]
        if preview_type == "quotation":
            self._show_quotation_preview(
                self.current_preview["selected_items"],
                self.current_preview["totals"],
                self.current_preview["quotation_info"],
            )
            return

        if preview_type == "invoice":
            self._show_invoice_preview(
                self.current_preview["selected_items"],
                self.current_preview["totals"],
                self.current_preview["quotation_info"],
            )
            return

        self._show_package_preview(self.current_preview["selected_items"])

    def _ensure_saved_quotation(self, selected_items: list[dict[str, Any]]) -> dict[str, Any]:
        if self.saved_quotation_info:
            return self.saved_quotation_info

        quotation_info = self.clinic_service.create_quotation(self.patient["id"], selected_items)
        self.saved_quotation_info = quotation_info
        return quotation_info

    def generate(self) -> None:
        self.preview_quotation()

    def preview_quotation(self) -> None:
        payload = self._ensure_items()
        if not payload:
            return
        selected_items, totals = payload

        quotation_info = self._ensure_saved_quotation(selected_items)
        if self.on_saved_callback:
            self.on_saved_callback()
        self._show_quotation_preview(selected_items, totals, quotation_info)

    def preview_bill(self) -> None:
        payload = self._ensure_items()
        if not payload:
            return

        selected_items, totals = payload
        quotation_info = self._ensure_saved_quotation(selected_items)
        if self.on_saved_callback:
            self.on_saved_callback()
        self._show_invoice_preview(selected_items, totals, quotation_info)

    def print_bill(self) -> None:
        if not self.current_preview:
            messagebox.showwarning("Preview required", "Preview quotation, bill, or package sheet before printing.")
            return

        preview_type = self.current_preview["type"]
        if preview_type in ("invoice", "quotation"):
            quotation_info = self.current_preview["quotation_info"]
            selected_items = self.current_preview["selected_items"]
            totals = self.current_preview["totals"]
            temp_prefix = "invoice" if preview_type == "invoice" else "quotation"
            temp_file = os.path.join(tempfile.gettempdir(), f"{temp_prefix}_{quotation_info['quotation_id']}.pdf")

            if preview_type == "invoice":
                document_title = "Invoice"
                document_number_label = "Invoice Number"
                doc_number = quotation_info["invoice_number"]
            else:
                document_title = "Quotation"
                document_number_label = "Quotation Number"
                doc_number = f"QTN-{int(quotation_info['quotation_id']):04d}"

            file_path = self.pdf_service.generate_invoice_pdf(
                quotation_info["quotation_id"],
                self.patient,
                selected_items,
                totals,
                quotation_info["date"],
                output_path=temp_file,
                invoice_number=doc_number,
                document_title=document_title,
                document_number_label=document_number_label,
            )
        else:
            selected_items = self.current_preview["selected_items"]
            temp_file = os.path.join(tempfile.gettempdir(), f"package_sheet_{self.patient['id']}.pdf")
            file_path = self.pdf_service.generate_package_sheet(
                self.patient,
                selected_items,
                output_path=temp_file,
            )

        if not has_connected_printer():
            messagebox.showerror("No printer connected", "No printer connected")
            return

        try:
            copies = int(self.print_copies_var.get()) if self.print_copies_var.get().isdigit() else 1
            copies = max(1, min(copies, 5))
            for _idx in range(copies):
                print_pdf(file_path)
        except Exception as exc:
            messagebox.showerror("Print failed", f"Could not send file to printer.\n{exc}")

    def preview_package_sheet(self) -> None:
        payload = self._ensure_items()
        if not payload:
            return
        selected_items, _totals = payload

        # Ensure previewed data is always tied to patient history quotation.
        self._ensure_saved_quotation(selected_items)
        if self.on_saved_callback:
            self.on_saved_callback()

        self._show_package_preview(selected_items)

    def download_pdf(self) -> None:
        if not self.current_preview:
            messagebox.showwarning("No preview", "Preview quotation, bill, or package sheet first.")
            return

        preview_type = self.current_preview["type"]
        if preview_type in ("invoice", "quotation"):
            quotation_info = self.current_preview["quotation_info"]
            selected_items = self.current_preview["selected_items"]
            totals = self.current_preview["totals"]
            default_name = (
                f"invoice_{quotation_info['quotation_id']}.pdf"
                if preview_type == "invoice"
                else f"quotation_{quotation_info['quotation_id']}.pdf"
            )
        else:
            selected_items = self.current_preview["selected_items"]
            default_name = f"package_sheet_{self.patient['id']}.pdf"

        selected_path = filedialog.asksaveasfilename(
            parent=self,
            title="Save PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")],
        )
        if not selected_path:
            return

        if preview_type in ("invoice", "quotation"):
            if preview_type == "invoice":
                document_title = "Invoice"
                document_number_label = "Invoice Number"
                doc_number = quotation_info["invoice_number"]
            else:
                document_title = "Quotation"
                document_number_label = "Quotation Number"
                doc_number = f"QTN-{int(quotation_info['quotation_id']):04d}"

            file_path = self.pdf_service.generate_invoice_pdf(
                quotation_info["quotation_id"],
                self.patient,
                selected_items,
                totals,
                quotation_info["date"],
                output_path=selected_path,
                invoice_number=doc_number,
                document_title=document_title,
                document_number_label=document_number_label,
            )
        else:
            file_path = self.pdf_service.generate_package_sheet(
                self.patient,
                selected_items,
                output_path=selected_path,
            )

        messagebox.showinfo("Saved", f"PDF saved to:\n{file_path}")

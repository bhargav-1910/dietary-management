from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from clinic_app.services import ClinicService


class ProductsFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, clinic_service: ClinicService) -> None:
        super().__init__(master)
        self.clinic_service = clinic_service
        self.selected_product_id: int | None = None

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Products", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(16, 8), sticky="w"
        )

        table_wrap = ctk.CTkFrame(self)
        table_wrap.grid(row=1, column=0, padx=(20, 10), pady=(0, 18), sticky="nsew")
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        columns = ("id", "name", "category", "mrp", "base_price", "tax_percent")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=180)
        self.tree.column("category", width=120)
        self.tree.column("mrp", width=90, anchor=tk.E)
        self.tree.column("base_price", width=100, anchor=tk.E)
        self.tree.column("tax_percent", width=80, anchor=tk.E)

        yscroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=1, padx=(10, 20), pady=(0, 18), sticky="nsew")
        form.grid_columnconfigure(1, weight=1)

        self.name_var = ctk.StringVar()
        self.category_var = ctk.StringVar()
        self.mrp_var = ctk.StringVar()
        self.base_var = ctk.StringVar()
        self.tax_var = ctk.StringVar()

        self._row(form, 0, "Name", self.name_var)
        self._row(form, 1, "Category", self.category_var)
        self._row(form, 2, "MRP", self.mrp_var)
        self._row(form, 3, "Base Price", self.base_var)
        self._row(form, 4, "Tax %", self.tax_var)

        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        for i in range(3):
            buttons.grid_columnconfigure(i, weight=1)

        ctk.CTkButton(buttons, text="Add", command=self.add_product).grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkButton(buttons, text="Update", command=self.update_product).grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkButton(buttons, text="Delete", fg_color="#b91c1c", hover_color="#991b1b", command=self.delete_product).grid(
            row=0, column=2, padx=4, sticky="ew"
        )
        ctk.CTkButton(form, text="Clear Form", fg_color="gray", command=self.clear_form).grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=8
        )

        self.refresh_table()

    def _row(self, frame: ctk.CTkFrame, row: int, label: str, var: ctk.StringVar) -> None:
        ctk.CTkLabel(frame, text=label).grid(row=row, column=0, padx=8, pady=6, sticky="w")
        ctk.CTkEntry(frame, textvariable=var).grid(row=row, column=1, padx=8, pady=6, sticky="ew")

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for p in self.clinic_service.list_products():
            self.tree.insert(
                "",
                "end",
                values=(p["id"], p["name"], p["category"], p["mrp"], p["base_price"], p["tax_percent"]),
            )

    def _on_select(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        row = self.tree.item(selected[0], "values")
        self.selected_product_id = int(row[0])
        self.name_var.set(str(row[1]))
        self.category_var.set(str(row[2]))
        self.mrp_var.set(str(row[3]))
        self.base_var.set(str(row[4]))
        self.tax_var.set(str(row[5]))

    def _payload(self):
        name = self.name_var.get().strip()
        category = self.category_var.get().strip()
        if not name or not category:
            messagebox.showwarning("Missing fields", "Name and category are required.")
            return None

        try:
            mrp = float(self.mrp_var.get())
            base_price = float(self.base_var.get())
            tax_percent = float(self.tax_var.get())
        except ValueError:
            messagebox.showwarning("Invalid values", "MRP, Base Price and Tax must be numbers.")
            return None

        return name, category, mrp, base_price, tax_percent

    def add_product(self) -> None:
        payload = self._payload()
        if not payload:
            return

        self.clinic_service.add_product(*payload)
        self.refresh_table()
        self.clear_form()

    def update_product(self) -> None:
        if not self.selected_product_id:
            messagebox.showwarning("No product", "Select a product to update.")
            return

        payload = self._payload()
        if not payload:
            return

        self.clinic_service.update_product(self.selected_product_id, *payload)
        self.refresh_table()

    def delete_product(self) -> None:
        if not self.selected_product_id:
            messagebox.showwarning("No product", "Select a product to delete.")
            return

        if not messagebox.askyesno("Confirm", "Delete selected product?"):
            return

        self.clinic_service.delete_product(self.selected_product_id)
        self.refresh_table()
        self.clear_form()

    def clear_form(self) -> None:
        self.selected_product_id = None
        self.name_var.set("")
        self.category_var.set("")
        self.mrp_var.set("")
        self.base_var.set("")
        self.tax_var.set("")

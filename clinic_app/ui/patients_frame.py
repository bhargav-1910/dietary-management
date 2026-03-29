from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from clinic_app.services import ClinicService


class PatientsFrame(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTkFrame,
        clinic_service: ClinicService,
        on_generate_quotation,
        on_view_quotation,
    ) -> None:
        super().__init__(master)
        self.clinic_service = clinic_service
        self.on_generate_quotation = on_generate_quotation
        self.on_view_quotation = on_view_quotation

        self.selected_patient: dict | None = None
        self.patient_dropdown_map: dict[str, dict] = {}

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Patients", font=ctk.CTkFont(size=24, weight="bold")).grid(
            row=0, column=0, padx=20, pady=(16, 8), sticky="w"
        )

        top_bar = ctk.CTkFrame(self)
        top_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        top_bar.grid_columnconfigure(3, weight=1)

        self.search_var = ctk.StringVar()
        ctk.CTkEntry(top_bar, width=220, textvariable=self.search_var, placeholder_text="Search name or phone").grid(
            row=0, column=0, padx=8, pady=8
        )
        ctk.CTkButton(top_bar, text="Search", command=self.refresh_table).grid(row=0, column=1, padx=8, pady=8)
        ctk.CTkButton(top_bar, text="Clear", command=self.clear_search).grid(row=0, column=2, padx=8, pady=8)

        self.patient_combo = ctk.CTkComboBox(top_bar, width=360, values=[], command=self._select_from_dropdown)
        self.patient_combo.grid(row=0, column=3, padx=8, pady=8, sticky="e")

        table_wrap = ctk.CTkFrame(self)
        table_wrap.grid(row=2, column=0, padx=(20, 10), pady=(0, 18), sticky="nsew")
        table_wrap.grid_columnconfigure(0, weight=1)
        table_wrap.grid_rowconfigure(0, weight=1)

        columns = ("id", "name", "age", "gender", "phone", "notes")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=14)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("name", width=150)
        self.tree.column("age", width=50, anchor=tk.CENTER)
        self.tree.column("gender", width=80, anchor=tk.CENTER)
        self.tree.column("phone", width=120)
        self.tree.column("notes", width=220)

        yscroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        form = ctk.CTkFrame(self)
        form.grid(row=2, column=1, padx=(10, 20), pady=(0, 18), sticky="nsew")
        form.grid_columnconfigure(1, weight=1)
        form.grid_rowconfigure(9, weight=1)

        self.name_var = ctk.StringVar()
        self.age_var = ctk.StringVar()
        self.gender_var = ctk.StringVar()
        self.phone_var = ctk.StringVar()
        self.notes_var = ctk.StringVar()

        self._form_row(form, 0, "Name", self.name_var)
        self._form_row(form, 1, "Age", self.age_var)
        self._form_row(form, 2, "Gender", self.gender_var)
        self._form_row(form, 3, "Phone", self.phone_var)
        self._form_row(form, 4, "Notes", self.notes_var)

        button_bar = ctk.CTkFrame(form, fg_color="transparent")
        button_bar.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 4))
        for idx in range(3):
            button_bar.grid_columnconfigure(idx, weight=1)

        ctk.CTkButton(button_bar, text="Add", command=self.add_patient).grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkButton(button_bar, text="Update", command=self.update_patient).grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkButton(button_bar, text="Delete", fg_color="#b91c1c", hover_color="#991b1b", command=self.delete_patient).grid(
            row=0, column=2, padx=4, sticky="ew"
        )

        ctk.CTkButton(
            form,
            text="Generate Quotation",
            height=40,
            command=self.generate_quotation,
        ).grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=(12, 8))

        ctk.CTkButton(form, text="Clear Form", fg_color="gray", command=self.clear_form).grid(
            row=7, column=0, columnspan=2, sticky="ew", padx=8
        )

        ctk.CTkLabel(form, text="Quotation History", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=8, column=0, columnspan=2, padx=8, pady=(12, 4), sticky="w"
        )

        history_wrap = ctk.CTkFrame(form)
        history_wrap.grid(row=9, column=0, columnspan=2, padx=8, pady=(0, 6), sticky="nsew")
        history_wrap.grid_columnconfigure(0, weight=1)
        history_wrap.grid_rowconfigure(0, weight=1)

        h_columns = ("id", "invoice", "date", "total")
        self.history_tree = ttk.Treeview(history_wrap, columns=h_columns, show="headings", height=7)
        self.history_tree.heading("id", text="ID")
        self.history_tree.heading("invoice", text="Invoice")
        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("total", text="Grand Total")
        self.history_tree.column("id", width=45, anchor=tk.CENTER)
        self.history_tree.column("invoice", width=90, anchor=tk.CENTER)
        self.history_tree.column("date", width=140)
        self.history_tree.column("total", width=95, anchor=tk.E)
        self.history_tree.grid(row=0, column=0, sticky="nsew")

        h_scroll = ttk.Scrollbar(history_wrap, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=h_scroll.set)
        h_scroll.grid(row=0, column=1, sticky="ns")

        history_actions = ctk.CTkFrame(form, fg_color="transparent")
        history_actions.grid(row=10, column=0, columnspan=2, padx=8, pady=(4, 0), sticky="ew")
        for idx in range(3):
            history_actions.grid_columnconfigure(idx, weight=1)

        ctk.CTkButton(history_actions, text="View", command=self.view_selected_history).grid(
            row=0, column=0, padx=4, sticky="ew"
        )
        ctk.CTkButton(history_actions, text="Reprint Bill", command=lambda: self.view_selected_history("invoice")).grid(
            row=0, column=1, padx=4, sticky="ew"
        )
        ctk.CTkButton(history_actions, text="Reprint Package", command=lambda: self.view_selected_history("package")).grid(
            row=0, column=2, padx=4, sticky="ew"
        )

        self.refresh_table()

    def _form_row(self, frame: ctk.CTkFrame, row: int, label: str, var: ctk.StringVar) -> None:
        ctk.CTkLabel(frame, text=label).grid(row=row, column=0, padx=8, pady=6, sticky="w")
        ctk.CTkEntry(frame, textvariable=var).grid(row=row, column=1, padx=8, pady=6, sticky="ew")

    def clear_search(self) -> None:
        self.search_var.set("")
        self.refresh_table()

    def refresh_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = self.clinic_service.list_patients(self.search_var.get())
        self.patient_dropdown_map.clear()

        combo_values: list[str] = []
        for patient in rows:
            values = (
                patient["id"],
                patient["name"],
                patient.get("age") or "",
                patient.get("gender") or "",
                patient.get("phone") or "",
                patient.get("notes") or "",
            )
            self.tree.insert("", "end", values=values)
            label = f"{patient['id']} - {patient['name']} ({patient.get('phone') or '-'})"
            combo_values.append(label)
            self.patient_dropdown_map[label] = patient

        self.patient_combo.configure(values=combo_values)
        if combo_values:
            self.patient_combo.set(combo_values[0])
            self._select_from_dropdown(combo_values[0])
        else:
            self.patient_combo.set("")
            self.selected_patient = None

    def _on_tree_select(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        row_values = self.tree.item(selected[0], "values")
        patient = {
            "id": int(row_values[0]),
            "name": row_values[1],
            "age": row_values[2],
            "gender": row_values[3],
            "phone": row_values[4],
            "notes": row_values[5],
        }
        self.selected_patient = patient
        self.fill_form(patient)
        self.refresh_history()

    def _select_from_dropdown(self, selected_value: str) -> None:
        patient = self.patient_dropdown_map.get(selected_value)
        if not patient:
            return
        self.selected_patient = patient
        self.fill_form(patient)
        self.refresh_history()

    def fill_form(self, patient: dict) -> None:
        self.name_var.set(str(patient.get("name", "")))
        self.age_var.set(str(patient.get("age", "")))
        self.gender_var.set(str(patient.get("gender", "")))
        self.phone_var.set(str(patient.get("phone", "")))
        self.notes_var.set(str(patient.get("notes", "")))

    def clear_form(self) -> None:
        self.selected_patient = None
        self.name_var.set("")
        self.age_var.set("")
        self.gender_var.set("")
        self.phone_var.set("")
        self.notes_var.set("")
        self.refresh_history()

    def _validated_payload(self) -> tuple[str, int | None, str, str, str] | None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing name", "Patient name is required.")
            return None

        age_text = self.age_var.get().strip()
        age: int | None = None
        if age_text:
            if not age_text.isdigit():
                messagebox.showwarning("Invalid age", "Age must be a valid number.")
                return None
            age = int(age_text)

        return (
            name,
            age,
            self.gender_var.get().strip(),
            self.phone_var.get().strip(),
            self.notes_var.get().strip(),
        )

    def add_patient(self) -> None:
        payload = self._validated_payload()
        if not payload:
            return

        self.clinic_service.add_patient(*payload)
        self.refresh_table()
        self.clear_form()

    def update_patient(self) -> None:
        if not self.selected_patient:
            messagebox.showwarning("No patient", "Select a patient to update.")
            return

        payload = self._validated_payload()
        if not payload:
            return

        self.clinic_service.update_patient(self.selected_patient["id"], *payload)
        self.refresh_table()
        self.refresh_history()

    def delete_patient(self) -> None:
        if not self.selected_patient:
            messagebox.showwarning("No patient", "Select a patient to delete.")
            return

        if not messagebox.askyesno("Confirm delete", "Delete selected patient?"):
            return

        self.clinic_service.delete_patient(self.selected_patient["id"])
        self.refresh_table()
        self.clear_form()

    def generate_quotation(self) -> None:
        if not self.selected_patient:
            messagebox.showwarning("Select patient", "Please select a patient before generating quotation.")
            return

        patient_id = int(self.selected_patient["id"])
        patient = self.clinic_service.get_patient(patient_id)
        if not patient:
            messagebox.showerror("Not found", "Selected patient does not exist.")
            return

        self.on_generate_quotation(patient, self.refresh_history)

    def refresh_history(self) -> None:
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        if not self.selected_patient:
            return

        rows = self.clinic_service.list_patient_quotations(int(self.selected_patient["id"]))
        for row in rows:
            self.history_tree.insert(
                "",
                "end",
                values=(row["id"], row["invoice_number"], row["date"], f"{float(row['grand_total']):.2f}"),
            )

    def view_selected_history(self, mode: str = "invoice") -> None:
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select a quotation from history.")
            return

        quotation_id = int(self.history_tree.item(selected[0], "values")[0])
        quotation = self.clinic_service.get_quotation_detail(quotation_id)
        if not quotation:
            messagebox.showerror("Not found", "Quotation not found.")
            return

        self.on_view_quotation(quotation, mode)

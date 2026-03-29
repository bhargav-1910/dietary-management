from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, on_login_success) -> None:
        super().__init__(master)
        self.master = master
        self.on_login_success = on_login_success

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self, width=420, height=390, corner_radius=14)
        card.grid(row=0, column=0, padx=24, pady=24)
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Clinic Login", font=ctk.CTkFont(size=28, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(32, 8)
        )
        ctk.CTkLabel(card, text="Enter credentials to continue", text_color="gray").grid(
            row=1, column=0, padx=24, pady=(0, 18)
        )

        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()

        ctk.CTkLabel(card, text="Username").grid(row=2, column=0, sticky="w", padx=24)
        username_entry = ctk.CTkEntry(card, textvariable=self.username_var, width=320)
        username_entry.grid(row=3, column=0, padx=24, pady=(4, 12))

        ctk.CTkLabel(card, text="Password").grid(row=4, column=0, sticky="w", padx=24)
        password_entry = ctk.CTkEntry(card, textvariable=self.password_var, show="*", width=320)
        password_entry.grid(row=5, column=0, padx=24, pady=(4, 18))

        ctk.CTkButton(card, text="Login", width=320, command=self._login).grid(row=6, column=0, padx=24, pady=(0, 10))
        ctk.CTkButton(card, text="Forgot Password", width=320, fg_color="gray", command=self._open_forgot_password).grid(
            row=7, column=0, padx=24, pady=(0, 8)
        )
        ctk.CTkLabel(card, text="Default logins: admin/admin123 or doctor/doctor123", text_color="gray").grid(
            row=8, column=0, padx=24, pady=(0, 16)
        )

        username_entry.focus_set()
        username_entry.bind("<Return>", lambda _event: self._login())
        password_entry.bind("<Return>", lambda _event: self._login())

    def _login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Missing details", "Please enter both username and password.")
            return

        if self.master.auth_service.login(username, password):
            self.on_login_success(username)
            return

        messagebox.showerror("Login failed", "Invalid username or password.")

    def _open_forgot_password(self) -> None:
        window = ctk.CTkToplevel(self)
        window.title("Reset Password")
        window.geometry("420x300")
        window.resizable(False, False)
        window.transient(self)
        window.grab_set()

        window.grid_columnconfigure(1, weight=1)

        username_var = ctk.StringVar(value=self.username_var.get().strip())
        new_password_var = ctk.StringVar()
        pin_var = ctk.StringVar()

        ctk.CTkLabel(window, text="Username").grid(row=0, column=0, padx=16, pady=(20, 8), sticky="w")
        ctk.CTkEntry(window, textvariable=username_var).grid(row=0, column=1, padx=16, pady=(20, 8), sticky="ew")

        ctk.CTkLabel(window, text="New Password").grid(row=1, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkEntry(window, textvariable=new_password_var, show="*").grid(row=1, column=1, padx=16, pady=8, sticky="ew")

        ctk.CTkLabel(window, text="Admin PIN").grid(row=2, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkEntry(window, textvariable=pin_var, show="*").grid(row=2, column=1, padx=16, pady=8, sticky="ew")

        ctk.CTkLabel(window, text="Default Admin PIN: 1234", text_color="gray").grid(
            row=3, column=0, columnspan=2, padx=16, pady=(4, 16), sticky="w"
        )

        def reset_action() -> None:
            username = username_var.get().strip()
            new_password = new_password_var.get().strip()
            admin_pin = pin_var.get().strip()
            if not username or not new_password or not admin_pin:
                messagebox.showwarning("Missing values", "Please fill username, new password, and admin PIN.")
                return

            ok = self.master.auth_service.reset_password_with_pin(username, new_password, admin_pin)
            if not ok:
                messagebox.showerror("Reset failed", "Invalid Admin PIN or username not found.")
                return

            messagebox.showinfo("Reset successful", "Password updated. Please login with new password.")
            window.destroy()

        ctk.CTkButton(window, text="Reset Password", command=reset_action).grid(
            row=4, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="ew"
        )
        ctk.CTkButton(window, text="Close", fg_color="gray", command=window.destroy).grid(
            row=5, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew"
        )

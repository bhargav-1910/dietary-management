from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, on_login_success) -> None:
        super().__init__(master)
        self.master = master
        self.on_login_success = on_login_success

        self.palette = {
            "surface": "#f8f9fa",
            "surface_low": "#f3f4f5",
            "surface_card": "#ffffff",
            "text": "#191c1d",
            "muted": "#414751",
            "primary": "#005da7",
            "primary_hover": "#004883",
            "secondary": "#e7e8e9",
            "secondary_hover": "#d9dadb",
        }

        self.configure(fg_color=self.palette["surface"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self,
            width=460,
            height=560,
            corner_radius=18,
            fg_color=self.palette["surface_card"],
            border_width=1,
            border_color="#dfe3eb",
        )
        card.grid(row=0, column=0, padx=24, pady=24)
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="Clinical Sanctuary",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.palette["text"],
        ).grid(row=0, column=0, padx=24, pady=(32, 6))
        ctk.CTkLabel(
            card,
            text="Dietary Management Portal",
            text_color=self.palette["muted"],
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=1, column=0, padx=24, pady=(0, 16))
        ctk.CTkLabel(
            card,
            text="Welcome back",
            text_color=self.palette["text"],
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=2, column=0, padx=24, pady=(4, 4))
        ctk.CTkLabel(
            card,
            text="Enter your credentials to continue",
            text_color=self.palette["muted"],
        ).grid(row=3, column=0, padx=24, pady=(0, 18))

        self.username_var = ctk.StringVar()
        self.password_var = ctk.StringVar()

        ctk.CTkLabel(card, text="Username", text_color=self.palette["muted"]).grid(row=4, column=0, sticky="w", padx=24)
        username_entry = ctk.CTkEntry(
            card,
            textvariable=self.username_var,
            width=360,
            height=42,
            corner_radius=12,
            fg_color=self.palette["surface_low"],
            border_width=0,
        )
        username_entry.grid(row=5, column=0, padx=24, pady=(4, 12))

        ctk.CTkLabel(card, text="Password", text_color=self.palette["muted"]).grid(row=6, column=0, sticky="w", padx=24)
        password_entry = ctk.CTkEntry(
            card,
            textvariable=self.password_var,
            show="*",
            width=360,
            height=42,
            corner_radius=12,
            fg_color=self.palette["surface_low"],
            border_width=0,
        )
        password_entry.grid(row=7, column=0, padx=24, pady=(4, 16))

        ctk.CTkButton(
            card,
            text="Login",
            width=360,
            height=46,
            corner_radius=999,
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=self._login,
        ).grid(row=8, column=0, padx=24, pady=(0, 10))

        action_bar = ctk.CTkFrame(card, fg_color="transparent")
        action_bar.grid(row=9, column=0, padx=24, pady=(0, 8), sticky="ew")
        action_bar.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            action_bar,
            text="Create Account",
            height=38,
            corner_radius=999,
            fg_color=self.palette["secondary"],
            hover_color=self.palette["secondary_hover"],
            text_color=self.palette["text"],
            command=self._open_create_account,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(
            action_bar,
            text="Forgot Password",
            height=38,
            corner_radius=999,
            fg_color=self.palette["secondary"],
            hover_color=self.palette["secondary_hover"],
            text_color=self.palette["text"],
            command=self._open_forgot_password,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ctk.CTkLabel(
            card,
            text="Default accounts:\nadmin / admin123\ndoctor / doctor123",
            text_color=self.palette["muted"],
            font=ctk.CTkFont(size=12),
            justify="center",
        ).grid(row=10, column=0, padx=24, pady=(6, 2))
        ctk.CTkLabel(
            card,
            text="Recovery codes:\nadmin1234 | doctor1234",
            text_color=self.palette["muted"],
            font=ctk.CTkFont(size=12),
            justify="center",
        ).grid(row=11, column=0, padx=24, pady=(0, 16))

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

    def _open_create_account(self) -> None:
        window = ctk.CTkToplevel(self)
        window.title("Create Account")
        window.geometry("500x460")
        window.resizable(False, False)
        window.transient(self)
        window.grab_set()
        window.configure(fg_color=self.palette["surface"])
        window.grid_columnconfigure(1, weight=1)

        username_var = ctk.StringVar()
        password_var = ctk.StringVar()
        confirm_var = ctk.StringVar()
        question_var = ctk.StringVar(value="What is your recovery keyword?")
        answer_var = ctk.StringVar()

        ctk.CTkLabel(window, text="Username", text_color=self.palette["muted"]).grid(row=0, column=0, padx=16, pady=(20, 8), sticky="w")
        ctk.CTkEntry(window, textvariable=username_var, height=40, fg_color=self.palette["surface_card"]).grid(
            row=0, column=1, padx=16, pady=(20, 8), sticky="ew"
        )

        ctk.CTkLabel(window, text="Password", text_color=self.palette["muted"]).grid(row=1, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkEntry(window, textvariable=password_var, show="*", height=40, fg_color=self.palette["surface_card"]).grid(
            row=1, column=1, padx=16, pady=8, sticky="ew"
        )

        ctk.CTkLabel(window, text="Confirm Password", text_color=self.palette["muted"]).grid(row=2, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkEntry(window, textvariable=confirm_var, show="*", height=40, fg_color=self.palette["surface_card"]).grid(
            row=2, column=1, padx=16, pady=8, sticky="ew"
        )

        ctk.CTkLabel(window, text="Recovery Question", text_color=self.palette["muted"]).grid(row=3, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkEntry(window, textvariable=question_var, height=40, fg_color=self.palette["surface_card"]).grid(
            row=3, column=1, padx=16, pady=8, sticky="ew"
        )

        ctk.CTkLabel(window, text="Recovery Answer", text_color=self.palette["muted"]).grid(row=4, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkEntry(window, textvariable=answer_var, show="*", height=40, fg_color=self.palette["surface_card"]).grid(
            row=4, column=1, padx=16, pady=8, sticky="ew"
        )

        def create_action() -> None:
            username = username_var.get().strip()
            password = password_var.get().strip()
            confirm = confirm_var.get().strip()
            question = question_var.get().strip()
            answer = answer_var.get().strip()

            if not username or not password or not confirm or not question or not answer:
                messagebox.showwarning("Missing values", "Please complete all fields.")
                return

            if password != confirm:
                messagebox.showwarning("Password mismatch", "Password and confirm password must match.")
                return

            ok, msg = self.master.auth_service.create_account(username, password, question, answer)
            if not ok:
                messagebox.showerror("Create account failed", msg)
                return

            self.username_var.set(username)
            self.password_var.set(password)
            messagebox.showinfo("Account created", "Account created successfully. You can login now.")
            window.destroy()

        ctk.CTkButton(
            window,
            text="Create Account",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=create_action,
        ).grid(row=5, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="ew")
        ctk.CTkButton(
            window,
            text="Close",
            fg_color=self.palette["secondary"],
            hover_color=self.palette["secondary_hover"],
            text_color=self.palette["text"],
            command=window.destroy,
        ).grid(row=6, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")

    def _open_forgot_password(self) -> None:
        window = ctk.CTkToplevel(self)
        window.title("Recover Password")
        window.geometry("500x390")
        window.resizable(False, False)
        window.transient(self)
        window.grab_set()
        window.configure(fg_color=self.palette["surface"])

        window.grid_columnconfigure(1, weight=1)

        username_var = ctk.StringVar(value=self.username_var.get().strip())
        question_var = ctk.StringVar(value="")
        answer_var = ctk.StringVar()
        new_password_var = ctk.StringVar()

        ctk.CTkLabel(window, text="Username", text_color=self.palette["muted"]).grid(row=0, column=0, padx=16, pady=(20, 8), sticky="w")
        ctk.CTkEntry(window, textvariable=username_var, height=40, fg_color=self.palette["surface_card"]).grid(
            row=0, column=1, padx=16, pady=(20, 8), sticky="ew"
        )

        def load_question() -> None:
            question = self.master.auth_service.get_recovery_question(username_var.get().strip())
            if not question:
                messagebox.showerror("User not found", "No recovery question found for this username.")
                question_var.set("")
                return
            question_var.set(question)

        ctk.CTkButton(
            window,
            text="Load Recovery Question",
            fg_color=self.palette["secondary"],
            hover_color=self.palette["secondary_hover"],
            text_color=self.palette["text"],
            command=load_question,
        ).grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky="ew")

        ctk.CTkLabel(window, text="Recovery Question", text_color=self.palette["muted"]).grid(row=2, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkEntry(window, textvariable=question_var, state="readonly", height=40, fg_color=self.palette["surface_low"]).grid(
            row=2, column=1, padx=16, pady=8, sticky="ew"
        )

        ctk.CTkLabel(window, text="Recovery Answer", text_color=self.palette["muted"]).grid(row=3, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkEntry(window, textvariable=answer_var, show="*", height=40, fg_color=self.palette["surface_card"]).grid(
            row=3, column=1, padx=16, pady=8, sticky="ew"
        )

        ctk.CTkLabel(window, text="New Password", text_color=self.palette["muted"]).grid(row=4, column=0, padx=16, pady=8, sticky="w")
        ctk.CTkEntry(window, textvariable=new_password_var, show="*", height=40, fg_color=self.palette["surface_card"]).grid(
            row=4, column=1, padx=16, pady=8, sticky="ew"
        )

        def reset_action() -> None:
            username = username_var.get().strip()
            answer = answer_var.get().strip()
            new_password = new_password_var.get().strip()
            if not username or not answer or not new_password:
                messagebox.showwarning("Missing values", "Please fill username, recovery answer, and new password.")
                return

            ok = self.master.auth_service.reset_password_with_recovery_answer(username, new_password, answer)
            if not ok:
                messagebox.showerror("Reset failed", "Recovery answer is invalid or user does not exist.")
                return

            messagebox.showinfo("Reset successful", "Password updated. Please login with new password.")
            self.username_var.set(username)
            self.password_var.set("")
            window.destroy()

        ctk.CTkButton(
            window,
            text="Reset Password",
            fg_color=self.palette["primary"],
            hover_color=self.palette["primary_hover"],
            command=reset_action,
        ).grid(row=5, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="ew")
        ctk.CTkButton(
            window,
            text="Close",
            fg_color=self.palette["secondary"],
            hover_color=self.palette["secondary_hover"],
            text_color=self.palette["text"],
            command=window.destroy,
        ).grid(row=6, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")

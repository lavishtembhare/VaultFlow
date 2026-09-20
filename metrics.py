import customtkinter as ctk
import pandas as pd
from database import format_currency_amount

class MetricCardsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.income_card = self.make_card("Total Income", "$0.00", 0, text_color="#10b981")
        self.expense_card = self.make_card("Total Expenses", "$0.00", 1, text_color="#ef4444")
        self.savings_card = self.make_card("Net Balance", "$0.00", 2, text_color="#38bdf8")
        self.count_card = self.make_card("Transactions", "0", 3, text_color="#facc15")

        # Internal state for smooth counting animations
        self._current_income = 0.0
        self._current_expense = 0.0
        self._current_balance = 0.0
        self._current_count = 0
        self._anim_job = None

    def make_card(self, title, val, col, text_color="white"):
        frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#1f2937")
        frame.grid(row=0, column=col, sticky="ew", padx=6, pady=2)
        
        lbl_title = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12), text_color="#9ca3af")
        lbl_title.pack(anchor="w", padx=16, pady=(12, 2))
        
        lbl_val = ctk.CTkLabel(frame, text=val, font=ctk.CTkFont(size=20, weight="bold"), text_color=text_color)
        lbl_val.pack(anchor="w", padx=16, pady=(0, 12))
        return lbl_val

    def update_metrics(self, df: pd.DataFrame, currency: str, db, animate=True):
        if self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None

        compact_enabled = db.get_setting("compact_numbers", "False") == "True"
        format_style = db.get_setting("number_format", "Millions / Billions")

        target_income = df[df["type"] == "Income"]["amount"].sum() if not df.empty else 0.0
        target_expense = df[df["type"] == "Expense"]["amount"].sum() if not df.empty else 0.0
        target_balance = target_income - target_expense
        target_count = len(df)

        start_income = self._current_income
        start_expense = self._current_expense
        start_balance = self._current_balance
        start_count = self._current_count

        total_steps = 12 if animate else 1

        def step_count(step):
            p = 1.0 if not animate else 1.0 - (1.0 - (step / total_steps)) ** 2
            curr_inc = start_income + (target_income - start_income) * p
            curr_exp = start_expense + (target_expense - start_expense) * p
            curr_bal = start_balance + (target_balance - start_balance) * p
            curr_cnt = int(start_count + (target_count - start_count) * p)

            self.income_card.configure(text=format_currency_amount(curr_inc, currency, format_style, compact_enabled))
            self.expense_card.configure(text=format_currency_amount(curr_exp, currency, format_style, compact_enabled))
            self.savings_card.configure(text=format_currency_amount(curr_bal, currency, format_style, compact_enabled))
            self.count_card.configure(text=str(curr_cnt))

            if step < total_steps and animate:
                self._anim_job = self.after(16, lambda: step_count(step + 1))
            else:
                self._current_income = target_income
                self._current_expense = target_expense
                self._current_balance = target_balance
                self._current_count = target_count
                self._anim_job = None

        step_count(1)
import customtkinter as ctk
import pandas as pd

class MetricCardsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.income_card = self.make_card("Total Income", "$0.00", 0, text_color="#10b981")
        self.expense_card = self.make_card("Total Expenses", "$0.00", 1, text_color="#ef4444")
        self.savings_card = self.make_card("Net Balance", "$0.00", 2, text_color="#38bdf8")
        self.count_card = self.make_card("Transactions", "0", 3, text_color="#facc15")

    def make_card(self, title, val, col, text_color="white"):
        frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#1f2937")
        frame.grid(row=0, column=col, sticky="ew", padx=6, pady=2)
        
        lbl_title = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12), text_color="#9ca3af")
        lbl_title.pack(anchor="w", padx=16, pady=(12, 2))
        
        lbl_val = ctk.CTkLabel(frame, text=val, font=ctk.CTkFont(size=20, weight="bold"), text_color=text_color)
        lbl_val.pack(anchor="w", padx=16, pady=(0, 12))
        return lbl_val

    def update_metrics(self, df: pd.DataFrame, currency: str):
        if df.empty:
            self.income_card.configure(text=f"{currency}0.00")
            self.expense_card.configure(text=f"{currency}0.00")
            self.savings_card.configure(text=f"{currency}0.00")
            self.count_card.configure(text="0")
            return

        total_income = df[df["type"] == "Income"]["amount"].sum()
        total_expense = df[df["type"] == "Expense"]["amount"].sum()
        balance = total_income - total_expense

        self.income_card.configure(text=f"{currency}{total_income:,.2f}")
        self.expense_card.configure(text=f"{currency}{total_expense:,.2f}")
        self.savings_card.configure(text=f"{currency}{balance:,.2f}")
        self.count_card.configure(text=str(len(df)))

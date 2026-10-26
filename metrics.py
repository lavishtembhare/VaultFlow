import customtkinter as ctk
import pandas as pd
from database import format_currency_amount

class MetricCardsView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.income_card = self.make_card(
            tag="INFLOW", title="Total Income", val="$0.00", col=0, text_color="#10b981"
        )
        self.expense_card = self.make_card(
            tag="OUTFLOW", title="Total Expenses", val="$0.00", col=1, text_color="#f43f5e"
        )
        self.savings_card = self.make_card(
            tag="NET RESERVE", title="Vault Balance", val="$0.00", col=2, text_color="#f59e0b"
        )
        self.count_card = self.make_card(
            tag="ACTIVITY", title="Total Records", val="0", col=3, text_color="#38bdf8"
        )

    def make_card(self, tag, title, val, col, text_color):
        frame = ctk.CTkFrame(
            self, corner_radius=12, fg_color="#111625",
            border_width=1, border_color="#1e293b"
        )
        frame.grid(row=0, column=col, sticky="ew", padx=6, pady=2)

        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(12, 2))

        ctk.CTkLabel(
            top_row, text=tag,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748b"
        ).pack(side="left")

        ctk.CTkLabel(
            frame, text=title,
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8"
        ).pack(anchor="w", padx=16, pady=(0, 2))

        lbl_val = ctk.CTkLabel(
            frame, text=val,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=text_color
        )
        lbl_val.pack(anchor="w", padx=16, pady=(2, 14))

        return lbl_val

    def update_metrics(self, df: pd.DataFrame, currency: str, db):
        compact_enabled = db.get_setting("compact_numbers", "False") == "True"
        format_style = db.get_setting("number_format", "Millions / Billions")

        if df is None or df.empty:
            zero_str = format_currency_amount(0.0, currency, format_style, compact_enabled)
            self.income_card.configure(text=zero_str)
            self.expense_card.configure(text=zero_str)
            self.savings_card.configure(text=zero_str)
            self.count_card.configure(text="0")
            return

        # Single O(n) pass over types and amounts
        total_income = 0.0
        total_expense = 0.0
        count = 0

        for tx_type, amt in zip(df["type"], df["amount"]):
            val = float(amt) if pd.notna(amt) else 0.0
            if tx_type == "Income":
                total_income += val
            else:
                total_expense += val
            count += 1

        balance = total_income - total_expense

        self.income_card.configure(text=format_currency_amount(total_income, currency, format_style, compact_enabled))
        self.expense_card.configure(text=format_currency_amount(total_expense, currency, format_style, compact_enabled))
        self.savings_card.configure(text=format_currency_amount(balance, currency, format_style, compact_enabled))
        self.count_card.configure(text=f"{count:,}")
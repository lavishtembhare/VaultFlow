import customtkinter as ctk
import pandas as pd
from database import format_currency_amount

class TransactionHistoryView(ctk.CTkScrollableFrame):
    def __init__(self, parent, on_delete_callback):
        super().__init__(parent, label_text="Transaction Records", corner_radius=12, fg_color="#1f2937")
        self.on_delete_callback = on_delete_callback

    def render_list(self, df: pd.DataFrame, currency: str, db, highlight_new=False):
        for widget in self.winfo_children():
            widget.destroy()

        if df.empty:
            ctk.CTkLabel(self, text="No transactions recorded yet.", text_color="#6b7280").pack(pady=30)
            return

        compact_enabled = db.get_setting("compact_numbers", "False") == "True"
        format_style = db.get_setting("number_format", "Millions / Billions")

        for idx, row in df.iterrows():
            is_newest = (idx == 0 and highlight_new)
            is_income = row["type"] == "Income"
            accent_color = "#10b981" if is_income else "#ef4444"
            sign = "+" if is_income else "-"
            pm = row.get("payment_mode", "UPI") if pd.notna(row.get("payment_mode")) else "UPI"

            # If newest item: give it a glowing reaction color
            card_bg = "#064e3b" if (is_newest and is_income) else ("#7f1d1d" if (is_newest and not is_income) else "#111827")

            row_card = ctk.CTkFrame(
                self, 
                fg_color=card_bg, 
                border_width=2 if is_newest else 0,
                border_color="#34d399" if (is_newest and is_income) else "#f87171",
                corner_radius=8
            )
            row_card.pack(fill="x", pady=4, padx=5)

            # Left Info
            left_col = ctk.CTkFrame(row_card, fg_color="transparent")
            left_col.pack(side="left", padx=12, pady=8)

            title_text = row["description"] if row["description"] else row["category"]
            if is_newest:
                title_text = f"✨ Just Added  •  {title_text}"

            ctk.CTkLabel(
                left_col, text=title_text, 
                font=ctk.CTkFont(size=13, weight="bold"), 
                text_color="#f3f4f6"
            ).pack(anchor="w")

            ctk.CTkLabel(
                left_col, 
                text=f"{row['date']}  •  {row['category']}  •  💳 {pm}", 
                font=ctk.CTkFont(size=11), 
                text_color="#9ca3af"
            ).pack(anchor="w")

            # Right Info
            right_col = ctk.CTkFrame(row_card, fg_color="transparent")
            right_col.pack(side="right", padx=12, pady=8)

            amt_formatted = format_currency_amount(row['amount'], currency, format_style, compact_enabled)
            ctk.CTkLabel(
                right_col, 
                text=f"{sign}{amt_formatted}", 
                font=ctk.CTkFont(size=14, weight="bold"), 
                text_color=accent_color
            ).pack(side="left", padx=10)

            del_btn = ctk.CTkButton(
                right_col, text="✕", width=26, height=26, 
                fg_color="#374151", hover_color="#ef4444", 
                command=lambda tid=row["id"]: self.on_delete_callback(tid)
            )
            del_btn.pack(side="left")

            # Fade newly added row to standard background after 1.5 seconds
            if is_newest:
                self.after(1500, lambda card=row_card: card.configure(fg_color="#111827", border_width=0))
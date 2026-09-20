import customtkinter as ctk
import pandas as pd

class TransactionHistoryView(ctk.CTkScrollableFrame):
    def __init__(self, parent, on_delete_callback):
        super().__init__(parent, label_text="Transaction Records", corner_radius=12, fg_color="#1f2937")
        self.on_delete_callback = on_delete_callback

    def render_list(self, df: pd.DataFrame, currency: str):
        for widget in self.winfo_children():
            widget.destroy()

        if df.empty:
            ctk.CTkLabel(self, text="No transactions recorded yet.", text_color="#6b7280").pack(pady=30)
            return

        for _, row in df.iterrows():
            is_income = row["type"] == "Income"
            accent_color = "#10b981" if is_income else "#ef4444"
            sign = "+" if is_income else "-"
            pm = row.get("payment_mode", "UPI") if pd.notna(row.get("payment_mode")) else "UPI"

            row_card = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
            row_card.pack(fill="x", pady=4, padx=5)

            # Left side: description and metadata
            left_col = ctk.CTkFrame(row_card, fg_color="transparent")
            left_col.pack(side="left", padx=12, pady=8)

            title_text = row["description"] if row["description"] else row["category"]
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

            # Right side: amount and delete button
            right_col = ctk.CTkFrame(row_card, fg_color="transparent")
            right_col.pack(side="right", padx=12, pady=8)

            ctk.CTkLabel(
                right_col, 
                text=f"{sign}{currency}{row['amount']:,.2f}", 
                font=ctk.CTkFont(size=14, weight="bold"), 
                text_color=accent_color
            ).pack(side="left", padx=10)

            del_btn = ctk.CTkButton(
                right_col, text="✕", width=26, height=26, 
                fg_color="#374151", hover_color="#ef4444", 
                command=lambda tid=row["id"]: self.on_delete_callback(tid)
            )
            del_btn.pack(side="left")
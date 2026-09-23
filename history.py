import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
from database import format_currency_amount

class TransactionHistoryView(ctk.CTkFrame):
    def __init__(self, parent, on_delete_callback, on_clear_all_callback=None):
        super().__init__(parent, corner_radius=12, fg_color="#111625", border_width=1, border_color="#1e263b")
        self.on_delete_callback = on_delete_callback
        self.on_clear_all_callback = on_clear_all_callback
        self.row_cards = []
        self.empty_lbl = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header_bar = ctk.CTkFrame(self, fg_color="transparent")
        header_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        header_bar.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header_bar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box, text="⚡ AUDITED TRANSACTION LEDGER", 
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), 
            text_color="#f8fafc"
        ).pack(side="left")

        self.count_badge = ctk.CTkLabel(
            title_box, text="[00]", 
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), 
            text_color="#f59e0b"
        )
        self.count_badge.pack(side="left", padx=8)

        self.clear_all_btn = ctk.CTkButton(
            header_bar, text="Purge Ledger", width=88, height=26,
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            fg_color="#3b0d18", hover_color="#540f22", text_color="#f43f5e",
            border_width=1, border_color="#540f22",
            command=self._handle_clear_all
        )
        self.clear_all_btn.pack(side="right")

        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_area.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    def _handle_clear_all(self):
        if not self.row_cards:
            messagebox.showinfo("Purge", "Ledger is currently empty.")
            return

        confirm = messagebox.askyesno(
            "Purge Ledger Records",
            f"⚠️ Confirm permanent wipe of ALL {len(self.row_cards)} ledger records?\n\nThis permanently resets asset telemetry to zero."
        )
        if confirm and self.on_clear_all_callback:
            self.on_clear_all_callback()

    def render_list(self, df: pd.DataFrame, currency: str, db, highlight_new=False):
        for card in self.row_cards:
            try: card.destroy()
            except Exception: pass
        self.row_cards.clear()

        if self.empty_lbl:
            try: self.empty_lbl.destroy()
            except Exception: pass
            self.empty_lbl = None

        total_count = len(df) if df is not None else 0
        self.count_badge.configure(text=f"[{total_count:02d}]")

        if df is None or df.empty:
            self.empty_lbl = ctk.CTkLabel(self.scroll_area, text="// NO TRANSACTION TELEMETRY REGISTERED", font=ctk.CTkFont(family="Consolas", size=11), text_color="#475569")
            self.empty_lbl.pack(pady=35)
            return

        compact_enabled = db.get_setting("compact_numbers", "False") == "True"
        format_style = db.get_setting("number_format", "Millions / Billions")

        for idx, row in df.iterrows():
            is_newest = (idx == 0 and highlight_new)
            is_income = row["type"] == "Income"
            accent_color = "#10b981" if is_income else "#f43f5e"
            sign = "+" if is_income else "-"
            pm = row.get("payment_mode", "UPI") if pd.notna(row.get("payment_mode")) else "UPI"
            acc = row.get("account", "Bank") if pd.notna(row.get("account")) else "Bank"

            card_bg = "#182033" if is_newest else "#0c0f18"

            row_card = ctk.CTkFrame(
                self.scroll_area, 
                fg_color=card_bg, 
                border_width=1,
                border_color="#f59e0b" if is_newest else "#1a2233",
                corner_radius=8
            )
            row_card.pack(fill="x", pady=3, padx=4)
            self.row_cards.append(row_card)

            left_col = ctk.CTkFrame(row_card, fg_color="transparent")
            left_col.pack(side="left", padx=12, pady=8)

            title_text = row["description"] if row["description"] else row["category"]
            if is_newest:
                title_text = f"⚡ JUST REGISTERED  •  {title_text}"

            ctk.CTkLabel(
                left_col, text=title_text, 
                font=ctk.CTkFont(size=12, weight="bold"), 
                text_color="#f8fafc"
            ).pack(anchor="w")

            meta_tag = f"INTO: {acc}" if is_income else f"FROM: {acc}"
            ctk.CTkLabel(
                left_col, 
                text=f"{row['date']}   •   CAT: {row['category']}   •   {meta_tag}   •   CH: {pm}", 
                font=ctk.CTkFont(family="Consolas", size=10), 
                text_color="#64748b"
            ).pack(anchor="w")

            right_col = ctk.CTkFrame(row_card, fg_color="transparent")
            right_col.pack(side="right", padx=12, pady=8)

            amt_formatted = format_currency_amount(row['amount'], currency, format_style, compact_enabled)
            ctk.CTkLabel(
                right_col, 
                text=f"{sign}{amt_formatted}", 
                font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), 
                text_color=accent_color
            ).pack(side="left", padx=10)

            del_btn = ctk.CTkButton(
                right_col, text="✕", width=26, height=26, 
                fg_color="#181e2e", hover_color="#ef4444", text_color="#94a3b8",
                command=lambda tid=row["id"]: self.on_delete_callback(tid)
            )
            del_btn.pack(side="left")
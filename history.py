import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
from database import format_currency_amount

class TransactionHistoryView(ctk.CTkFrame):
    def __init__(self, parent, on_delete_callback, on_clear_all_callback=None):
        super().__init__(parent, corner_radius=12, fg_color="#1f2937")
        self.on_delete_callback = on_delete_callback
        self.on_clear_all_callback = on_clear_all_callback
        self.row_cards = []
        self.empty_lbl = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # --- Top Header Bar of Transaction Section ---
        header_bar = ctk.CTkFrame(self, fg_color="transparent")
        header_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=(10, 4))
        header_bar.grid_columnconfigure(0, weight=1)

        # Left: Title + Dynamic Count Badge
        title_box = ctk.CTkFrame(header_bar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box, text="Transaction Records", 
            font=ctk.CTkFont(size=14, weight="bold"), 
            text_color="#f3f4f6"
        ).pack(side="left")

        self.count_badge = ctk.CTkLabel(
            title_box, text="(0)", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#9ca3af"
        )
        self.count_badge.pack(side="left", padx=8)

        # Right: Clear All Button in the Transaction Section
        self.clear_all_btn = ctk.CTkButton(
            header_bar,
            text="🗑️ Clear All",
            width=92,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#991b1b",
            hover_color="#dc2626",
            command=self._handle_clear_all
        )
        self.clear_all_btn.pack(side="right")

        # --- Scrollable Area for Records ---
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll_area.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))

    def _handle_clear_all(self):
        """Prompts confirmation before deleting all transactions."""
        if not self.row_cards:
            messagebox.showinfo("Clear All", "There are no transactions to clear.")
            return

        confirm = messagebox.askyesno(
            "Confirm Clear All",
            f"⚠️ Are you sure you want to delete ALL {len(self.row_cards)} transactions?\n\nThis will permanently reset your balance and records. This action cannot be undone."
        )
        if confirm and self.on_clear_all_callback:
            self.on_clear_all_callback()

    def render_list(self, df: pd.DataFrame, currency: str, db, highlight_new=False):
        # Safely remove old transaction cards without touching scrollbars
        for card in self.row_cards:
            try:
                card.destroy()
            except Exception:
                pass
        self.row_cards.clear()

        if self.empty_lbl:
            try:
                self.empty_lbl.destroy()
            except Exception:
                pass
            self.empty_lbl = None

        total_count = len(df) if df is not None else 0
        self.count_badge.configure(text=f"({total_count})")

        if df is None or df.empty:
            self.empty_lbl = ctk.CTkLabel(self.scroll_area, text="No transactions recorded yet.", text_color="#6b7280")
            self.empty_lbl.pack(pady=30)
            return

        compact_enabled = db.get_setting("compact_numbers", "False") == "True"
        format_style = db.get_setting("number_format", "Millions / Billions")

        for idx, row in df.iterrows():
            is_newest = (idx == 0 and highlight_new)
            is_income = row["type"] == "Income"
            accent_color = "#10b981" if is_income else "#ef4444"
            sign = "+" if is_income else "-"
            pm = row.get("payment_mode", "UPI") if pd.notna(row.get("payment_mode")) else "UPI"
            acc = row.get("account", "Bank") if pd.notna(row.get("account")) else "Bank"

            acc_tag = f"📥 In: {acc}" if is_income else f"📤 From: {acc}"

            card_bg = "#064e3b" if (is_newest and is_income) else ("#7f1d1d" if (is_newest and not is_income) else "#111827")

            row_card = ctk.CTkFrame(
                self.scroll_area, 
                fg_color=card_bg, 
                border_width=2 if is_newest else 0,
                border_color="#34d399" if (is_newest and is_income) else "#f87171",
                corner_radius=8
            )
            row_card.pack(fill="x", pady=4, padx=5)
            self.row_cards.append(row_card)

            # Left Column (Description, Date, Category, Account, Mode)
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
                text=f"{row['date']}  •  {row['category']}  •  {acc_tag}  •  💳 {pm}", 
                font=ctk.CTkFont(size=11), 
                text_color="#9ca3af"
            ).pack(anchor="w")

            # Right Column (Amount + Single Delete Button)
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

            if is_newest:
                def fade_back(c=row_card):
                    try:
                        if c.winfo_exists():
                            c.configure(fg_color="#111827", border_width=0)
                    except Exception:
                        pass
                self.after(1400, fade_back)
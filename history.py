import customtkinter as ctk
import pandas as pd
from tkinter import messagebox
from database import format_currency_amount

class TransactionHistoryView(ctk.CTkFrame):
    def __init__(self, parent, on_delete_callback, on_clear_all_callback=None, on_import_excel_callback=None):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.on_delete_callback = on_delete_callback
        self.on_clear_all_callback = on_clear_all_callback
        self.on_import_excel_callback = on_import_excel_callback
        self.row_cards = []
        self.empty_lbl = None
        self._cached_df = None
        self._cached_currency = "$"
        self._cached_db = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Page Header
        top_section = ctk.CTkFrame(self, fg_color="transparent")
        top_section.grid(row=0, column=0, sticky="ew", padx=32, pady=(26, 14))
        top_section.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(top_section, fg_color="transparent")
        title_row.pack(fill="x", pady=(0, 12))

        title_left = ctk.CTkFrame(title_row, fg_color="transparent")
        title_left.pack(side="left")

        ctk.CTkLabel(
            title_left, text="Transaction Logs",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f8fafc"
        ).pack(side="left")

        self.count_badge = ctk.CTkLabel(
            title_left, text="0 records",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#162035",
            text_color="#38bdf8",
            corner_radius=8,
            padx=10, pady=3
        )
        self.count_badge.pack(side="left", padx=12)

        # Action Buttons (Import Excel + Purge Ledger)
        actions_right = ctk.CTkFrame(title_row, fg_color="transparent")
        actions_right.pack(side="right")

        if self.on_import_excel_callback:
            self.import_btn = ctk.CTkButton(
                actions_right, text="📥  Import Excel / CSV", height=34,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#162035", hover_color="#1e2d4a", text_color="#38bdf8",
                border_width=1, border_color="#28385c", corner_radius=8,
                command=self.on_import_excel_callback
            )
            self.import_btn.pack(side="left", padx=(0, 10))

        self.clear_all_btn = ctk.CTkButton(
            actions_right, text="Clear All", width=95, height=34,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2c0b14", hover_color="#45101f", text_color="#f43f5e",
            border_width=1, border_color="#45101f", corner_radius=8,
            command=self._handle_clear_all
        )
        self.clear_all_btn.pack(side="left")

        # Search Filter Bar
        search_bar = ctk.CTkFrame(top_section, fg_color="transparent")
        search_bar.pack(fill="x")

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_bar,
            textvariable=self.search_var,
            placeholder_text="Search logs by description, category, account, or payment mode...",
            height=36,
            fg_color="#111625",
            border_color="#1e293b",
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_var.trace_add("write", lambda *_: self._apply_search_filter())

        # Logs Card Container
        self.list_container = ctk.CTkFrame(
            self, corner_radius=12, fg_color="#111625",
            border_width=1, border_color="#1e293b"
        )
        self.list_container.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 26))
        self.list_container.grid_rowconfigure(0, weight=1)
        self.list_container.grid_columnconfigure(0, weight=1)

        self.scroll_area = ctk.CTkScrollableFrame(self.list_container, fg_color="transparent", corner_radius=0)
        self.scroll_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _handle_clear_all(self):
        if not self.row_cards:
            messagebox.showinfo("Clear Logs", "The transaction log is already empty.")
            return

        confirm = messagebox.askyesno(
            "Clear All Transactions",
            f"Are you sure you want to permanently delete all {len(self.row_cards)} records?"
        )
        if confirm and self.on_clear_all_callback:
            self.on_clear_all_callback()

    def _apply_search_filter(self):
        if self._cached_df is not None and self._cached_db is not None:
            self._render_rows(self._cached_df, self._cached_currency, self._cached_db, highlight_new=False)

    def render_list(self, df: pd.DataFrame, currency: str, db, highlight_new=False):
        self._cached_df = df
        self._cached_currency = currency
        self._cached_db = db
        self._render_rows(df, currency, db, highlight_new=highlight_new)

    def _render_rows(self, df: pd.DataFrame, currency: str, db, highlight_new=False):
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

        if df is None or df.empty:
            self.count_badge.configure(text="0 records")
            self.empty_lbl = ctk.CTkLabel(
                self.scroll_area,
                text="No transaction records found.",
                font=ctk.CTkFont(size=13),
                text_color="#64748b"
            )
            self.empty_lbl.pack(pady=45)
            return

        query = self.search_var.get().strip().lower()
        compact_enabled = db.get_setting("compact_numbers", "False") == "True"
        format_style = db.get_setting("number_format", "Millions / Billions")

        # Single O(n) pass over rows using itertuples
        matched_rows = 0
        for idx, row in enumerate(df.itertuples(index=False)):
            tx_id = getattr(row, "id", idx)
            tx_type = getattr(row, "type", "Expense")
            date_str = getattr(row, "date", "")
            category = getattr(row, "category", "Other")
            pm = getattr(row, "payment_mode", "UPI") or "UPI"
            acc = getattr(row, "account", "Bank") or "Bank"
            amount = float(getattr(row, "amount", 0.0) or 0.0)
            desc = getattr(row, "description", "") or ""

            if query:
                searchable = f"{desc} {category} {acc} {pm} {date_str} {tx_type}".lower()
                if query not in searchable:
                    continue

            matched_rows += 1
            is_newest = (idx == 0 and highlight_new)
            is_income = (tx_type == "Income")
            accent_color = "#10b981" if is_income else "#f43f5e"
            sign = "+" if is_income else "-"

            card_bg = "#17223b" if is_newest else "#0c101b"

            row_card = ctk.CTkFrame(
                self.scroll_area,
                fg_color=card_bg,
                border_width=1,
                border_color="#38bdf8" if is_newest else "#1c2539",
                corner_radius=10
            )
            row_card.pack(fill="x", pady=4, padx=4)
            self.row_cards.append(row_card)

            left_col = ctk.CTkFrame(row_card, fg_color="transparent")
            left_col.pack(side="left", padx=14, pady=10)

            title_text = desc if desc else category
            if is_newest:
                title_text = f"New  •  {title_text}"

            ctk.CTkLabel(
                left_col, text=title_text,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#f8fafc"
            ).pack(anchor="w")

            meta_tag = f"Account: {acc}"
            ctk.CTkLabel(
                left_col,
                text=f"{date_str}   •   {category}   •   {meta_tag}   •   {pm}",
                font=ctk.CTkFont(size=11),
                text_color="#64748b"
            ).pack(anchor="w", pady=(2, 0))

            right_col = ctk.CTkFrame(row_card, fg_color="transparent")
            right_col.pack(side="right", padx=14, pady=10)

            amt_formatted = format_currency_amount(amount, currency, format_style, compact_enabled)
            ctk.CTkLabel(
                right_col,
                text=f"{sign}{amt_formatted}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=accent_color
            ).pack(side="left", padx=12)

            del_btn = ctk.CTkButton(
                right_col, text="✕", width=28, height=28,
                corner_radius=6,
                fg_color="#182032", hover_color="#ef4444", text_color="#94a3b8",
                command=lambda tid=tx_id: self.on_delete_callback(tid)
            )
            del_btn.pack(side="left")

        self.count_badge.configure(text=f"{matched_rows} record{'s' if matched_rows != 1 else ''}")

        if matched_rows == 0:
            self.empty_lbl = ctk.CTkLabel(
                self.scroll_area,
                text="No matching transactions found.",
                font=ctk.CTkFont(size=13),
                text_color="#64748b"
            )
            self.empty_lbl.pack(pady=45)
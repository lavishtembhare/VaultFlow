import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
from dialogs import ExportFilterDialog

class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db, on_settings_changed):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_settings_changed = on_settings_changed
        self.cat_row_widgets = []

        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=40, pady=(30, 20))

        ctk.CTkLabel(
            title_box, text="// VAULT PARAMETERS & CONTROL",
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
            text_color="#f8fafc"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, text="Configure currency notations, classification tags, and encrypted exports.",
            font=ctk.CTkFont(size=12),
            text_color="#64748b"
        ).pack(anchor="w")

        cards_grid = ctk.CTkFrame(self, fg_color="transparent")
        cards_grid.pack(fill="x", padx=40, pady=(0, 20))
        cards_grid.grid_columnconfigure((0, 1), weight=1)

        # Left Card: Preferences
        pref_card = ctk.CTkFrame(cards_grid, fg_color="#111625", corner_radius=14, border_width=1, border_color="#1e263b")
        pref_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(pref_card, text="CURRENCY & NOTATION RULES", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#f59e0b").pack(anchor="w", padx=20, pady=(20, 2))
        ctk.CTkLabel(pref_card, text="Financial display formatting and terminal input rules.", font=ctk.CTkFont(size=11), text_color="#64748b").pack(anchor="w", padx=20, pady=(0, 14))

        ctk.CTkLabel(pref_card, text="Sovereign Currency Symbol:", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#cbd5e1").pack(anchor="w", padx=20, pady=(0, 2))
        saved_currency = self.db.get_setting("currency", "$")
        self.currency_menu = ctk.CTkOptionMenu(
            pref_card, values=["$", "₹", "€", "£", "¥", "C$", "A$", "CHF"],
            height=34, fg_color="#0a0d16", button_color="#1e263b",
            command=self.save_currency
        )
        self.currency_menu.set(saved_currency)
        self.currency_menu.pack(fill="x", padx=20, pady=(0, 14))

        compact_val = self.db.get_setting("compact_numbers", "False") == "True"
        self.compact_switch = ctk.CTkSwitch(
            pref_card, text="Compact Telemetry Notation (e.g. 7M / 70 Lakh)",
            command=self.save_display_options, progress_color="#f59e0b"
        )
        if compact_val:
            self.compact_switch.select()
        self.compact_switch.pack(anchor="w", padx=20, pady=(0, 14))

        ctk.CTkLabel(pref_card, text="Scale Notation Style:", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#cbd5e1").pack(anchor="w", padx=20, pady=(0, 2))
        saved_fmt = self.db.get_setting("number_format", "Millions / Billions")
        self.format_menu = ctk.CTkOptionMenu(
            pref_card, values=["Millions / Billions", "Lakhs / Crores", "Standard"],
            height=34, fg_color="#0a0d16", button_color="#1e263b",
            command=lambda _: self.save_display_options()
        )
        self.format_menu.set(saved_fmt)
        self.format_menu.pack(fill="x", padx=20, pady=(0, 14))

        shorthand_val = self.db.get_setting("allow_shorthand", "True") == "True"
        self.shorthand_switch = ctk.CTkSwitch(
            pref_card, text="Allow Financial Shorthand (e.g. 50k, 2m, 3cr)",
            command=self.save_display_options, progress_color="#f59e0b"
        )
        if shorthand_val:
            self.shorthand_switch.select()
        self.shorthand_switch.pack(anchor="w", padx=20, pady=(0, 20))

        # Right Card: Categories
        cat_card = ctk.CTkFrame(cards_grid, fg_color="#111625", corner_radius=14, border_width=1, border_color="#1e263b")
        cat_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        ctk.CTkLabel(cat_card, text="CLASSIFICATION TAXONOMY", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#10b981").pack(anchor="w", padx=20, pady=(20, 2))

        self.cat_type_toggle = ctk.CTkSegmentedButton(
            cat_card, values=["Expense Categories", "Income Categories"],
            height=32, fg_color="#0a0d16", selected_color="#10b981",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            command=self.load_categories_list
        )
        self.cat_type_toggle.set("Expense Categories")
        self.cat_type_toggle.pack(fill="x", padx=20, pady=(8, 10))

        add_box = ctk.CTkFrame(cat_card, fg_color="transparent")
        add_box.pack(fill="x", padx=20, pady=(0, 10))

        self.new_cat_entry = ctk.CTkEntry(add_box, placeholder_text="New Tag Name...", height=34, fg_color="#0a0d16", border_color="#1e263b")
        self.new_cat_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            add_box, text="+ Add", width=70, height=34,
            fg_color="#10b981", hover_color="#059669", text_color="#000000",
            font=ctk.CTkFont(family="Consolas", weight="bold"),
            command=self.add_category_inline
        ).pack(side="right")

        self.cat_scroll = ctk.CTkScrollableFrame(cat_card, height=180, fg_color="#0a0d16", corner_radius=8)
        self.cat_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Bottom Card: Utilities
        data_card = ctk.CTkFrame(self, fg_color="#111625", corner_radius=14, border_width=1, border_color="#1e263b")
        data_card.pack(fill="x", padx=40, pady=(0, 30))

        ctk.CTkLabel(data_card, text="LEDGER BACKUP & MAINTENANCE", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#38bdf8").pack(anchor="w", padx=20, pady=(20, 2))
        ctk.CTkLabel(data_card, text="Import third-party bank CSVs, produce filtered Excel reports, or purge local database.", font=ctk.CTkFont(size=11), text_color="#64748b").pack(anchor="w", padx=20, pady=(0, 16))

        action_box = ctk.CTkFrame(data_card, fg_color="transparent")
        action_box.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(
            action_box, text="📥 Ingest Excel / CSV", height=38,
            fg_color="#1e263b", hover_color="#2b3652", text_color="#f8fafc",
            font=ctk.CTkFont(family="Consolas", weight="bold"),
            command=self.import_excel_file
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            action_box, text="📤 Filter & Export Excel", height=38,
            fg_color="#0e2a22", hover_color="#144236", text_color="#10b981",
            border_width=1, border_color="#184e3f",
            font=ctk.CTkFont(family="Consolas", weight="bold"),
            command=self.open_export_dialog
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            action_box, text="⚠️ Purge Ledger", height=38,
            fg_color="#380b15", hover_color="#540f1f", text_color="#f43f5e",
            border_width=1, border_color="#540f1f",
            font=ctk.CTkFont(family="Consolas", weight="bold"),
            command=self.clear_all_records
        ).pack(side="left")

        self.load_categories_list()

    def save_currency(self, new_currency):
        self.db.set_setting("currency", new_currency)
        self.on_settings_changed()

    def save_display_options(self):
        is_compact = "True" if self.compact_switch.get() == 1 else "False"
        fmt = self.format_menu.get()
        allow_sh = "True" if self.shorthand_switch.get() == 1 else "False"

        self.db.set_setting("compact_numbers", is_compact)
        self.db.set_setting("number_format", fmt)
        self.db.set_setting("allow_shorthand", allow_sh)
        self.on_settings_changed()

    def get_active_type(self):
        return "Expense" if self.cat_type_toggle.get() == "Expense Categories" else "Income"

    def load_categories_list(self, _=None):
        for widget in self.cat_row_widgets:
            try: widget.destroy()
            except Exception: pass
        self.cat_row_widgets.clear()

        active_type = self.get_active_type()
        categories = self.db.get_categories(active_type)

        if not categories:
            lbl = ctk.CTkLabel(self.cat_scroll, text="// NO TAGS CONFIGURED", font=ctk.CTkFont(family="Consolas", size=10), text_color="#64748b")
            lbl.pack(pady=20)
            self.cat_row_widgets.append(lbl)
            return

        for cat in categories:
            row = ctk.CTkFrame(self.cat_scroll, fg_color="#111625", corner_radius=6)
            row.pack(fill="x", pady=2, padx=4)
            self.cat_row_widgets.append(row)

            ctk.CTkLabel(row, text=cat, font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#f8fafc").pack(side="left", padx=10, pady=6)

            del_btn = ctk.CTkButton(
                row, text="✕", width=24, height=24,
                fg_color="#1e263b", hover_color="#ef4444", text_color="#94a3b8",
                command=lambda c=cat: self.delete_category_action(c)
            )
            del_btn.pack(side="right", padx=6, pady=4)

    def add_category_inline(self):
        cat_name = self.new_cat_entry.get().strip()
        if not cat_name:
            messagebox.showwarning("Warning", "Tag name cannot be empty.")
            return

        active_type = self.get_active_type()
        self.db.add_category(cat_name, active_type)
        self.new_cat_entry.delete(0, "end")
        self.load_categories_list()
        self.on_settings_changed()

    def delete_category_action(self, cat_name):
        active_type = self.get_active_type()
        cats = self.db.get_categories(active_type)
        if len(cats) <= 1:
            messagebox.showwarning("Notice", f"At least one {active_type.lower()} tag must remain.")
            return

        if messagebox.askyesno("Confirm", f"Remove '{cat_name}'?"):
            self.db.delete_category(cat_name, active_type)
            self.load_categories_list()
            self.on_settings_changed()

    def import_excel_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Bank Statement or CSV Spreadsheet",
            filetypes=[("Spreadsheet Files", "*.xlsx *.xls *.csv"), ("Excel Files", "*.xlsx *.xls"), ("CSV Files", "*.csv")]
        )
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path) if file_path.lower().endswith(".csv") else pd.read_excel(file_path)
            if df.empty:
                messagebox.showwarning("Empty Ingestion", "File contains zero rows.")
                return

            imported_count = self.db.import_transactions_from_dataframe(df)
            messagebox.showinfo("Ingestion Complete", f"Successfully imported {imported_count} transactions into VaultFlow!\n\nSource: {file_path}")
            self.load_categories_list()
            self.on_settings_changed()

        except Exception as e:
            messagebox.showerror("Ingestion Error", f"Failed to parse spreadsheet:\n{str(e)}")

    def open_export_dialog(self):
        currency = self.db.get_setting("currency", "$")
        ExportFilterDialog(self, self.db, currency)

    def clear_all_records(self):
        confirm = messagebox.askyesno(
            "Confirm Ledger Purge",
            "⚠️ Purge all transactions?\n\nThis permanently resets all balances to zero."
        )
        if confirm:
            self.db.clear_all_transactions()
            messagebox.showinfo("Purged", "Ledger purged successfully.")
            self.on_settings_changed()
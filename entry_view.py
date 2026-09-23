from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from database import parse_amount
from dialogs import DateTimePickerDialog, AddCategoryDialog

class EntryView(ctk.CTkScrollableFrame):
    def __init__(self, parent, db, on_transaction_saved):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.on_transaction_saved = on_transaction_saved
        self._is_updating_amount = False

        title_box = ctk.CTkFrame(self, fg_color="transparent")
        title_box.pack(fill="x", padx=40, pady=(30, 20))

        ctk.CTkLabel(
            title_box, text="// ASSET INGESTION : TRANSACTION LOG",
            font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
            text_color="#f8fafc"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box, text="Commit an audited monetary transaction to your private offline ledger.",
            font=ctk.CTkFont(size=12),
            text_color="#64748b"
        ).pack(anchor="w")

        self.form_card = ctk.CTkFrame(
            self, fg_color="#111625", corner_radius=14,
            border_width=1, border_color="#1e263b"
        )
        self.form_card.pack(fill="x", padx=40, pady=(0, 30))
        self.form_card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(self.form_card, text="FLOW DIRECTION *", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#f59e0b").grid(row=0, column=0, columnspan=2, padx=25, pady=(20, 4), sticky="w")
        self.type_toggle = ctk.CTkSegmentedButton(
            self.form_card, values=["Expense", "Income"],
            height=36, fg_color="#0a0d16", selected_color="#f59e0b",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            command=self.on_type_switched
        )
        self.type_toggle.set("Expense")
        self.type_toggle.grid(row=1, column=0, columnspan=2, padx=25, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(self.form_card, text="TRANSACTION AMOUNT *", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#f59e0b").grid(row=2, column=0, padx=25, pady=(0, 4), sticky="w")
        self.amount_var = ctk.StringVar()
        self.amount_entry = ctk.CTkEntry(
            self.form_card, textvariable=self.amount_var, placeholder_text="0.00",
            height=38, fg_color="#0a0d16", border_color="#1e263b",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.amount_entry.grid(row=3, column=0, padx=25, pady=(0, 16), sticky="ew")
        self.amount_entry.bind("<KeyPress>", self._filter_keypress)
        self.amount_var.trace_add("write", self._on_amount_write)

        cat_header = ctk.CTkFrame(self.form_card, fg_color="transparent")
        cat_header.grid(row=2, column=1, padx=25, pady=(0, 4), sticky="ew")
        self.cat_title_lbl = ctk.CTkLabel(cat_header, text="EXPENSE CATEGORY *", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#94a3b8")
        self.cat_title_lbl.pack(side="left")

        self.category_menu = ctk.CTkOptionMenu(
            self.form_card, height=38,
            values=self.db.get_categories("Expense"),
            fg_color="#0a0d16", button_color="#1e263b"
        )
        self.category_menu.grid(row=3, column=1, padx=25, pady=(0, 16), sticky="ew")

        self.account_label = ctk.CTkLabel(self.form_card, text="DEBITED SOURCE ACCOUNT", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#94a3b8")
        self.account_label.grid(row=4, column=0, padx=25, pady=(0, 4), sticky="w")
        self.account_menu = ctk.CTkOptionMenu(
            self.form_card, values=["Bank", "Cash", "Portfolio", "Vault", "Other"],
            height=38, fg_color="#0a0d16", button_color="#1e263b"
        )
        self.account_menu.set("Bank")
        self.account_menu.grid(row=5, column=0, padx=25, pady=(0, 16), sticky="ew")

        ctk.CTkLabel(self.form_card, text="CONDUIT / PAYMENT MODE", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#94a3b8").grid(row=4, column=1, padx=25, pady=(0, 4), sticky="w")
        self.payment_menu = ctk.CTkOptionMenu(
            self.form_card,
            values=["UPI", "Wire / Net Banking", "Cash", "Credit Card", "Debit Card", "Cheque", "Other"],
            height=38, fg_color="#0a0d16", button_color="#1e263b"
        )
        self.payment_menu.set("UPI")
        self.payment_menu.grid(row=5, column=1, padx=25, pady=(0, 16), sticky="ew")

        date_header = ctk.CTkFrame(self.form_card, fg_color="transparent")
        date_header.grid(row=6, column=0, padx=25, pady=(0, 4), sticky="ew")
        ctk.CTkLabel(date_header, text="EXECUTION TIMESTAMP", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#94a3b8").pack(side="left")
        ctk.CTkButton(
            date_header, text="NOW", width=45, height=18,
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), fg_color="#1e263b", hover_color="#2b3652",
            command=self.set_now
        ).pack(side="right")

        dt_box = ctk.CTkFrame(self.form_card, fg_color="transparent")
        dt_box.grid(row=7, column=0, padx=25, pady=(0, 16), sticky="ew")

        self.date_entry = ctk.CTkEntry(dt_box, height=38, fg_color="#0a0d16", border_color="#1e263b", font=ctk.CTkFont(family="Consolas", size=11))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.date_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.cal_btn = ctk.CTkButton(
            dt_box, text="📅", width=42, height=38,
            fg_color="#1e263b", hover_color="#2b3652",
            command=self.open_calendar
        )
        self.cal_btn.pack(side="right")

        ctk.CTkLabel(self.form_card, text="AUDIT REMARK / NARRATION", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#94a3b8").grid(row=6, column=1, padx=25, pady=(0, 4), sticky="w")
        self.desc_entry = ctk.CTkEntry(
            self.form_card, placeholder_text="// transfer reference, party name, invoice code",
            height=38, fg_color="#0a0d16", border_color="#1e263b"
        )
        self.desc_entry.grid(row=7, column=1, padx=25, pady=(0, 16), sticky="ew")

        btn_box = ctk.CTkFrame(self.form_card, fg_color="transparent")
        btn_box.grid(row=8, column=0, columnspan=2, padx=25, pady=(10, 25), sticky="e")

        ctk.CTkButton(
            btn_box, text="Reset", width=90, height=40,
            fg_color="#181e2e", hover_color="#222b42", text_color="#94a3b8",
            font=ctk.CTkFont(family="Consolas", weight="bold"),
            command=self.clear_inputs
        ).pack(side="left", padx=(0, 12))

        self.submit_btn = ctk.CTkButton(
            btn_box, text="⚡ Commit to Ledger", width=190, height=40,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color="#f59e0b", hover_color="#d97706", text_color="#000000",
            command=self.submit
        )
        self.submit_btn.pack(side="left")

    def _filter_keypress(self, event):
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab", "Home", "End", "Return", "Escape", "Up", "Down"):
            return None
        if event.state & 4:
            return None

        allow_sh = self.db.get_setting("allow_shorthand", "False") == "True"
        if not allow_sh:
            if event.char and not (event.char.isdigit() or event.char == '.'):
                return "break"
            if event.char == '.' and '.' in self.amount_var.get():
                return "break"
        else:
            allowed_chars = set("0123456789.kmbcrolahstuindeKMBCROLAHSTEINDE ")
            if event.char and event.char not in allowed_chars:
                return "break"
        return None

    def _on_amount_write(self, *args):
        if self._is_updating_amount:
            return

        val = self.amount_var.get()
        if not val:
            return

        allow_sh = self.db.get_setting("allow_shorthand", "False") == "True"
        cleaned = ""

        if not allow_sh:
            has_dot = False
            for char in val:
                if char.isdigit():
                    cleaned += char
                elif char == '.' and not has_dot:
                    cleaned += char
                    has_dot = True
        else:
            allowed = set("0123456789.kmbcrolahstuindeKMBCROLAHSTEINDE ")
            has_dot = False
            for char in val:
                if char.isdigit():
                    cleaned += char
                elif char == '.' and not has_dot:
                    cleaned += char
                    has_dot = True
                elif char in allowed and char != '.':
                    cleaned += char

        if cleaned != val:
            self._is_updating_amount = True
            try:
                self.amount_var.set(cleaned)
            finally:
                self._is_updating_amount = False

    def on_type_switched(self, selected_type):
        self.cat_title_lbl.configure(text=f"{selected_type.upper()} CATEGORY *")
        self.refresh_categories()
        if selected_type == "Income":
            self.account_label.configure(text="CREDITED DESTINATION ACCOUNT")
        else:
            self.account_label.configure(text="DEBITED SOURCE ACCOUNT")

    def open_quick_add_category(self):
        active_type = self.type_toggle.get()
        AddCategoryDialog(self, self.db, tx_type=active_type, on_success=self.refresh_categories)

    def refresh_categories(self, new_category_name=None):
        active_type = self.type_toggle.get()
        cats = self.db.get_categories(active_type)
        self.category_menu.configure(values=cats)
        if new_category_name and new_category_name in cats:
            self.category_menu.set(new_category_name)
        elif cats:
            self.category_menu.set(cats[0])

    def set_now(self):
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))

    def open_calendar(self):
        current_val = self.date_entry.get().strip()
        DateTimePickerDialog(self, initial_datetime=current_val, include_time=True, on_select=self.set_date_time)

    def set_date_time(self, val):
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, val)

    def clear_inputs(self):
        self.amount_var.set("")
        self.desc_entry.delete(0, "end")
        self.set_now()

    def submit(self):
        amt_str = self.amount_var.get().strip()
        date_str = self.date_entry.get().strip()
        desc = self.desc_entry.get().strip()
        category = self.category_menu.get()
        account = self.account_menu.get()
        payment_mode = self.payment_menu.get()
        tx_type = self.type_toggle.get()

        allow_sh = self.db.get_setting("allow_shorthand", "False") == "True"
        try:
            amt = parse_amount(amt_str, allow_shorthand=allow_sh)
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
                date_str += " " + datetime.now().strftime("%H:%M")
            except ValueError:
                messagebox.showerror("Validation Error", "Date format must be YYYY-MM-DD HH:MM (or use 📅).")
                return

        self.db.add_transaction(tx_type, date_str, category, payment_mode, amt, desc, account=account)

        self.submit_btn.configure(text="✔ COMMITTED", fg_color="#10b981", text_color="#000000")
        self.after(900, lambda: self.submit_btn.configure(text="⚡ Commit to Ledger", fg_color="#f59e0b", text_color="#000000"))

        self.clear_inputs()
        self.on_transaction_saved()
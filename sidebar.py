from datetime import datetime
import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
from dialogs import AddCategoryDialog, DateTimePickerDialog, SettingsDialog
from database import parse_amount

class SidebarView(ctk.CTkFrame):
    def __init__(self, parent, db, on_add_callback, on_currency_change, on_open_export, on_open_settings):
        super().__init__(parent, width=280, corner_radius=0, fg_color="#111827")
        self.db = db
        self.on_add_callback = on_add_callback
        self.on_currency_change = on_currency_change
        self.on_open_export = on_open_export
        self.on_open_settings = on_open_settings
        self._is_updating_amount = False

        self.grid_rowconfigure(20, weight=1)

        # Title Header
        ctk.CTkLabel(self, text="🛡️ VaultFlow", font=ctk.CTkFont(size=22, weight="bold"), text_color="#38bdf8").grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        # Currency Selection
        ctk.CTkLabel(self, text="Preferred Currency:", font=ctk.CTkFont(size=11), text_color="#9ca3af").grid(row=1, column=0, padx=20, pady=(0, 2), sticky="w")
        saved_currency = self.db.get_setting("currency", "$")
        self.currency_menu = ctk.CTkOptionMenu(
            self, 
            values=["$", "₹", "€", "£", "¥", "C$", "A$"], 
            command=self.currency_selected,
            fg_color="#374151"
        )
        self.currency_menu.set(saved_currency)
        self.currency_menu.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")

        # Income / Expense Toggle
        self.type_toggle = ctk.CTkSegmentedButton(
            self, values=["Expense", "Income"], 
            fg_color="#1f2937", selected_color="#6366f1",
            command=self.on_type_switched
        )
        self.type_toggle.set("Expense")
        self.type_toggle.grid(row=3, column=0, padx=20, pady=(0, 12), sticky="ew")

        # Amount Entry with Keystroke Filter
        ctk.CTkLabel(self, text="Amount:", font=ctk.CTkFont(size=11), text_color="#9ca3af").grid(row=4, column=0, padx=20, pady=(0, 2), sticky="w")
        self.amount_var = ctk.StringVar()
        self.amount_entry = ctk.CTkEntry(self, textvariable=self.amount_var, placeholder_text="0.00")
        self.amount_entry.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.amount_entry.bind("<KeyPress>", self._filter_keypress)
        if hasattr(self.amount_entry, "_entry"):
            self.amount_entry._entry.bind("<KeyPress>", self._filter_keypress)
        self.amount_var.trace_add("write", self._on_amount_write)

        # Category Row
        cat_header = ctk.CTkFrame(self, fg_color="transparent")
        cat_header.grid(row=6, column=0, padx=20, pady=(0, 2), sticky="ew")
        self.cat_title_lbl = ctk.CTkLabel(cat_header, text="Expense Category:", font=ctk.CTkFont(size=11), text_color="#9ca3af")
        self.cat_title_lbl.pack(side="left")
        ctk.CTkButton(cat_header, text="+ Add", width=46, height=18, font=ctk.CTkFont(size=10), fg_color="#374151", hover_color="#4f46e5", command=self.open_add_category).pack(side="right")

        self.category_menu = ctk.CTkOptionMenu(self, values=self.db.get_categories("Expense"), fg_color="#374151")
        self.category_menu.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Account Field
        self.account_label = ctk.CTkLabel(self, text="Money Debited From:", font=ctk.CTkFont(size=11), text_color="#9ca3af")
        self.account_label.grid(row=8, column=0, padx=20, pady=(0, 2), sticky="w")
        self.account_menu = ctk.CTkOptionMenu(
            self,
            values=["Bank", "Cash", "Portfolio", "Other"],
            fg_color="#374151"
        )
        self.account_menu.set("Bank")
        self.account_menu.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Payment Mode Dropdown
        ctk.CTkLabel(self, text="Payment Mode:", font=ctk.CTkFont(size=11), text_color="#9ca3af").grid(row=10, column=0, padx=20, pady=(0, 2), sticky="w")
        self.payment_menu = ctk.CTkOptionMenu(
            self,
            values=["UPI", "Net Banking", "Cash", "Credit Card", "Debit Card", "Cheque", "Other"],
            fg_color="#374151"
        )
        self.payment_menu.set("UPI")
        self.payment_menu.grid(row=11, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Date & Time Row
        ctk.CTkLabel(self, text="Date & Time (YYYY-MM-DD HH:MM):", font=ctk.CTkFont(size=11), text_color="#9ca3af").grid(row=12, column=0, padx=20, pady=(0, 2), sticky="w")
        dt_frame = ctk.CTkFrame(self, fg_color="transparent")
        dt_frame.grid(row=13, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.date_entry = ctk.CTkEntry(dt_frame)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.date_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.cal_btn = ctk.CTkButton(dt_frame, text="📅", width=36, fg_color="#374151", hover_color="#4f46e5", command=self.open_calendar)
        self.cal_btn.pack(side="right")

        # Description Entry
        ctk.CTkLabel(self, text="Description:", font=ctk.CTkFont(size=11), text_color="#9ca3af").grid(row=14, column=0, padx=20, pady=(0, 2), sticky="w")
        self.desc_entry = ctk.CTkEntry(self, placeholder_text="e.g. Salary, Rent, Dinner")
        self.desc_entry.grid(row=15, column=0, padx=20, pady=(0, 15), sticky="ew")

        # Submit Button
        self.add_btn = ctk.CTkButton(
            self, text="Log Transaction", 
            font=ctk.CTkFont(weight="bold"),
            fg_color="#6366f1", hover_color="#4f46e5",
            command=self.submit
        )
        self.add_btn.grid(row=16, column=0, padx=20, pady=(0, 12), sticky="ew")

        # --- ACTION & UTILITY BUTTONS ---
        self.import_btn = ctk.CTkButton(
            self, text="📥 Import Excel / CSV", 
            fg_color="#2563eb", hover_color="#1d4ed8",
            command=self.import_excel_file
        )
        self.import_btn.grid(row=17, column=0, padx=20, pady=(0, 6), sticky="ew")

        self.export_btn = ctk.CTkButton(
            self, text="📤 Filter & Export Excel", 
            fg_color="#10b981", hover_color="#059669",
            command=self.on_open_export
        )
        self.export_btn.grid(row=18, column=0, padx=20, pady=(0, 6), sticky="ew")

        self.settings_btn = ctk.CTkButton(
            self, text="⚙️ Preferences & Categories", 
            fg_color="#374151", hover_color="#4b5563",
            command=self.on_open_settings
        )
        self.settings_btn.grid(row=19, column=0, padx=20, pady=(0, 6), sticky="ew")

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
        self.cat_title_lbl.configure(text=f"{selected_type} Category:")
        categories = self.db.get_categories(selected_type)
        self.category_menu.configure(values=categories)
        if categories:
            self.category_menu.set(categories[0])

        if selected_type == "Income":
            self.account_label.configure(text="Money Credited In:")
        else:
            self.account_label.configure(text="Money Debited From:")

    def open_calendar(self):
        current_val = self.date_entry.get().strip()
        DateTimePickerDialog(self, initial_datetime=current_val, include_time=True, on_select=self.set_date_time)

    def set_date_time(self, val):
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, val)

    def currency_selected(self, val):
        self.db.set_setting("currency", val)
        self.on_currency_change(val)

    def open_add_category(self):
        active_type = self.type_toggle.get()
        AddCategoryDialog(self, self.db, tx_type=active_type, on_success=self.refresh_categories)

    def refresh_categories(self, new_category_name=None):
        active_type = self.type_toggle.get()
        cats = self.db.get_categories(active_type)
        self.category_menu.configure(values=cats)
        if new_category_name and new_category_name in cats:
            self.category_menu.set(new_category_name)
        elif cats:
            self.category_menu.set(cats[-1])

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
                messagebox.showerror("Validation Error", "Date format must be YYYY-MM-DD HH:MM (use 📅).")
                return

        self.db.add_transaction(tx_type, date_str, category, payment_mode, amt, desc, account=account)
        
        self.add_btn.configure(text="✔ Added!", fg_color="#10b981")
        def reset_btn():
            try:
                if self.winfo_exists():
                    self.add_btn.configure(text="Log Transaction", fg_color="#6366f1")
            except Exception:
                pass
        self.after(800, reset_btn)

        self.amount_var.set("")
        self.desc_entry.delete(0, "end")
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        self.on_add_callback(highlight_new=True)

    def import_excel_file(self):
        """Opens file dialog and imports transactions from Excel or CSV."""
        file_path = filedialog.askopenfilename(
            title="Select Excel or CSV Spreadsheet to Import",
            filetypes=[
                ("Spreadsheet Files", "*.xlsx *.xls *.csv"),
                ("Excel Files", "*.xlsx *.xls"),
                ("CSV Files", "*.csv")
            ]
        )
        if not file_path:
            return

        try:
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            if df.empty:
                messagebox.showwarning("Import Warning", "The selected file contains no rows.")
                return

            imported_count = self.db.import_transactions_from_dataframe(df)
            messagebox.showinfo(
                "Import Complete",
                f"Successfully imported {imported_count} transactions into VaultFlow!\n\nSource: {file_path}"
            )
            self.refresh_categories()
            self.on_add_callback(highlight_new=True)

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import file:\n{str(e)}")

    def clear_all_records(self):
        """Prompts confirmation and clears all transaction data."""
        confirm = messagebox.askyesno(
            "Confirm Clear All",
            "⚠️ Are you sure you want to delete ALL logged transactions?\n\nThis will permanently reset your balance and charts to zero. This action cannot be undone."
        )
        if confirm:
            self.db.clear_all_transactions()
            messagebox.showinfo("VaultFlow Reset", "All transactions have been deleted successfully.")
            self.on_add_callback(highlight_new=False)
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from dialogs import AddCategoryDialog

class SidebarView(ctk.CTkFrame):
    def __init__(self, parent, db, on_add_callback, on_currency_change, on_open_export):
        super().__init__(parent, width=280, corner_radius=0, fg_color="#111827")
        self.db = db
        self.on_add_callback = on_add_callback
        self.on_currency_change = on_currency_change
        self.on_open_export = on_open_export

        self.grid_rowconfigure(15, weight=1)

        # Title
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
        self.type_toggle = ctk.CTkSegmentedButton(self, values=["Expense", "Income"], fg_color="#1f2937", selected_color="#6366f1")
        self.type_toggle.set("Expense")
        self.type_toggle.grid(row=3, column=0, padx=20, pady=(0, 12), sticky="ew")

        # Amount Entry
        ctk.CTkLabel(self, text="Amount:", font=ctk.CTkFont(size=11), text_color="#9ca3af").grid(row=4, column=0, padx=20, pady=(0, 2), sticky="w")
        self.amount_entry = ctk.CTkEntry(self, placeholder_text="0.00")
        self.amount_entry.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Category Row
        cat_header = ctk.CTkFrame(self, fg_color="transparent")
        cat_header.grid(row=6, column=0, padx=20, pady=(0, 2), sticky="ew")
        ctk.CTkLabel(cat_header, text="Category:", font=ctk.CTkFont(size=11), text_color="#9ca3af").pack(side="left")
        ctk.CTkButton(cat_header, text="+ Add", width=46, height=18, font=ctk.CTkFont(size=10), fg_color="#374151", hover_color="#4f46e5", command=self.open_add_category).pack(side="right")

        self.category_menu = ctk.CTkOptionMenu(self, values=self.db.get_categories(), fg_color="#374151")
        self.category_menu.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Payment Mode Dropdown
        ctk.CTkLabel(self, text="Payment Mode:", font=ctk.CTkFont(size=11), text_color="#9ca3af").grid(row=8, column=0, padx=20, pady=(0, 2), sticky="w")
        self.payment_menu = ctk.CTkOptionMenu(
            self,
            values=["UPI", "Cash", "Credit Card", "Debit Card", "Net Banking", "Other"],
            fg_color="#374151"
        )
        self.payment_menu.set("UPI")
        self.payment_menu.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Date Entry
        ctk.CTkLabel(self, text="Date (YYYY-MM-DD):", font=ctk.CTkFont(size=11), text_color="#9ca3af").grid(row=10, column=0, padx=20, pady=(0, 2), sticky="w")
        self.date_entry = ctk.CTkEntry(self)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=11, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Description Entry
        ctk.CTkLabel(self, text="Description:", font=ctk.CTkFont(size=11), text_color="#9ca3af").grid(row=12, column=0, padx=20, pady=(0, 2), sticky="w")
        self.desc_entry = ctk.CTkEntry(self, placeholder_text="e.g. Grocery run, Rent")
        self.desc_entry.grid(row=13, column=0, padx=20, pady=(0, 15), sticky="ew")

        # Add Entry Button
        self.add_btn = ctk.CTkButton(
            self, text="Log Transaction", 
            font=ctk.CTkFont(weight="bold"),
            fg_color="#6366f1", hover_color="#4f46e5",
            command=self.submit
        )
        self.add_btn.grid(row=14, column=0, padx=20, pady=(0, 15), sticky="ew")

        # Export Button
        self.export_btn = ctk.CTkButton(
            self, text="📥 Filter & Export Excel", 
            fg_color="#10b981", hover_color="#059669",
            command=self.on_open_export
        )
        self.export_btn.grid(row=16, column=0, padx=20, pady=(0, 20), sticky="ew")

    def currency_selected(self, val):
        self.db.set_setting("currency", val)
        self.on_currency_change(val)

    def open_add_category(self):
        AddCategoryDialog(self, self.db, on_success=self.refresh_categories)

    def refresh_categories(self):
        cats = self.db.get_categories()
        self.category_menu.configure(values=cats)
        if cats:
            self.category_menu.set(cats[-1])

    def submit(self):
        amt_str = self.amount_entry.get().strip()
        date_str = self.date_entry.get().strip()
        desc = self.desc_entry.get().strip()
        category = self.category_menu.get()
        payment_mode = self.payment_menu.get()
        tx_type = self.type_toggle.get()

        try:
            amt = float(amt_str)
            if amt <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Amount must be a positive number.")
            return

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation Error", "Date must follow YYYY-MM-DD format.")
            return

        self.db.add_transaction(tx_type, date_str, category, payment_mode, amt, desc)
        self.amount_entry.delete(0, "end")
        self.desc_entry.delete(0, "end")
        self.on_add_callback()
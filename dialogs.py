from datetime import datetime, timedelta
import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox

class AddCategoryDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, on_success):
        super().__init__(parent)
        self.db = db
        self.on_success = on_success
        self.title("Add New Category")
        self.geometry("340x200")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="New Category Name:", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(25, 10))
        self.entry = ctk.CTkEntry(self, width=240, placeholder_text="e.g. Freelance, Healthcare")
        self.entry.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Cancel", width=100, fg_color="#444", command=self.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Save", width=100, fg_color="#2eb872", hover_color="#24935b", command=self.save).pack(side="left", padx=5)

    def save(self):
        cat_name = self.entry.get().strip()
        if not cat_name:
            messagebox.showwarning("Warning", "Category name cannot be empty.")
            return
        self.db.add_category(cat_name)
        self.on_success()
        self.destroy()

class ExportFilterDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, currency: str):
        super().__init__(parent)
        self.db = db
        self.currency = currency
        self.title("Export Transactions to Excel")
        self.geometry("420x440")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="Filter & Export to Excel", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        ctk.CTkLabel(self, text="Quick Presets:", anchor="w").pack(fill="x", padx=30, pady=(5, 2))
        self.preset_menu = ctk.CTkOptionMenu(
            self,
            values=["All Time", "This Month", "Last Month", "Last 7 Days", "Last 30 Days", "Last 6 Months", "Custom Range"],
            command=self.on_preset_change
        )
        self.preset_menu.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(self, text="Start Date (YYYY-MM-DD):", anchor="w").pack(fill="x", padx=30, pady=(5, 2))
        self.start_entry = ctk.CTkEntry(self)
        self.start_entry.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkLabel(self, text="End Date (YYYY-MM-DD):", anchor="w").pack(fill="x", padx=30, pady=(5, 2))
        self.end_entry = ctk.CTkEntry(self)
        self.end_entry.pack(fill="x", padx=30, pady=(0, 15))

        self.on_preset_change("This Month")

        ctk.CTkButton(
            self, text="Generate & Download (.xlsx)", 
            fg_color="#10b981", hover_color="#059669",
            height=38, font=ctk.CTkFont(weight="bold"), 
            command=self.process_export
        ).pack(fill="x", padx=30, pady=20)

    def on_preset_change(self, preset):
        today = datetime.now()
        if preset == "All Time":
            self.start_entry.delete(0, "end")
            self.start_entry.insert(0, "2000-01-01")
            self.end_entry.delete(0, "end")
            self.end_entry.insert(0, today.strftime("%Y-%m-%d"))
        elif preset == "This Month":
            start = today.replace(day=1)
            self.start_entry.delete(0, "end")
            self.start_entry.insert(0, start.strftime("%Y-%m-%d"))
            self.end_entry.delete(0, "end")
            self.end_entry.insert(0, today.strftime("%Y-%m-%d"))
        elif preset == "Last Month":
            first_day_current = today.replace(day=1)
            last_day_prev = first_day_current - timedelta(days=1)
            first_day_prev = last_day_prev.replace(day=1)
            self.start_entry.delete(0, "end")
            self.start_entry.insert(0, first_day_prev.strftime("%Y-%m-%d"))
            self.end_entry.delete(0, "end")
            self.end_entry.insert(0, last_day_prev.strftime("%Y-%m-%d"))
        elif preset == "Last 7 Days":
            start = today - timedelta(days=7)
            self.start_entry.delete(0, "end")
            self.start_entry.insert(0, start.strftime("%Y-%m-%d"))
            self.end_entry.delete(0, "end")
            self.end_entry.insert(0, today.strftime("%Y-%m-%d"))
        elif preset == "Last 30 Days":
            start = today - timedelta(days=30)
            self.start_entry.delete(0, "end")
            self.start_entry.insert(0, start.strftime("%Y-%m-%d"))
            self.end_entry.delete(0, "end")
            self.end_entry.insert(0, today.strftime("%Y-%m-%d"))
        elif preset == "Last 6 Months":
            start = today - timedelta(days=180)
            self.start_entry.delete(0, "end")
            self.start_entry.insert(0, start.strftime("%Y-%m-%d"))
            self.end_entry.delete(0, "end")
            self.end_entry.insert(0, today.strftime("%Y-%m-%d"))

    def process_export(self):
        s_date = self.start_entry.get().strip()
        e_date = self.end_entry.get().strip()

        try:
            datetime.strptime(s_date, "%Y-%m-%d")
            datetime.strptime(e_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid dates formatted as YYYY-MM-DD.")
            return

        df = self.db.get_filtered_transactions(s_date, e_date)
        if df.empty:
            messagebox.showinfo("No Data", f"No records found between {s_date} and {e_date}.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile=f"VaultFlow_Report_{s_date}_to_{e_date}.xlsx"
        )
        if file_path:
            try:
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Transactions")
                messagebox.showinfo("Success", f"Report exported successfully!\n\nTotal records: {len(df)}")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

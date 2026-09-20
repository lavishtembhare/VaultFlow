import calendar
from datetime import datetime, timedelta
import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox

# =====================================================================
# 1. NATIVE CALENDAR & TIME PICKER POPUP
# =====================================================================
class DateTimePickerDialog(ctk.CTkToplevel):
    """Modern dark-themed popup to visually select date and time."""
    def __init__(self, parent, initial_datetime=None, include_time=True, on_select=None):
        super().__init__(parent)
        self.on_select = on_select
        self.include_time = include_time

        now = datetime.now()
        if initial_datetime:
            try:
                dt_obj = datetime.strptime(initial_datetime, "%Y-%m-%d %H:%M")
            except ValueError:
                try:
                    dt_obj = datetime.strptime(initial_datetime, "%Y-%m-%d")
                except ValueError:
                    dt_obj = now
        else:
            dt_obj = now

        self.current_year = dt_obj.year
        self.current_month = dt_obj.month
        self.selected_day = dt_obj.day
        self.selected_hour = dt_obj.hour
        self.selected_minute = dt_obj.minute

        self.title("Select Date & Time" if include_time else "Select Date")
        self.geometry("340x440" if include_time else "340x360")
        self.resizable(False, False)
        self.grab_set()

        self.month_names = ["", "January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"]

        # Month / Year Header
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=15, pady=(15, 8))

        ctk.CTkButton(nav_frame, text="◀", width=32, height=28, fg_color="#374151", command=self.prev_month).pack(side="left")
        self.header_lbl = ctk.CTkLabel(nav_frame, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.header_lbl.pack(side="left", expand=True)
        ctk.CTkButton(nav_frame, text="▶", width=32, height=28, fg_color="#374151", command=self.next_month).pack(side="right")

        # Calendar Days Grid
        self.days_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        self.days_frame.pack(padx=15, pady=5, fill="both", expand=True)

        # Time Selector Frame
        if self.include_time:
            time_frame = ctk.CTkFrame(self, fg_color="transparent")
            time_frame.pack(fill="x", padx=15, pady=(8, 0))

            ctk.CTkLabel(time_frame, text="Time:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(5, 10))

            self.hour_menu = ctk.CTkOptionMenu(
                time_frame, width=70, height=28,
                values=[f"{h:02d}" for h in range(24)],
                fg_color="#374151"
            )
            self.hour_menu.set(f"{self.selected_hour:02d}")
            self.hour_menu.pack(side="left", padx=2)

            ctk.CTkLabel(time_frame, text=":", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=2)

            self.min_menu = ctk.CTkOptionMenu(
                time_frame, width=70, height=28,
                values=[f"{m:02d}" for m in range(0, 60, 1)],
                fg_color="#374151"
            )
            self.min_menu.set(f"{self.selected_minute:02d}")
            self.min_menu.pack(side="left", padx=2)

        # Confirm Button
        ctk.CTkButton(
            self, text="Set Date & Time", height=32,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#6366f1", hover_color="#4f46e5",
            command=self.confirm_selection
        ).pack(fill="x", padx=15, pady=(10, 15))

        self.draw_calendar()

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.draw_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.draw_calendar()

    def draw_calendar(self):
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        self.header_lbl.configure(text=f"{self.month_names[self.current_month]} {self.current_year}")

        # Weekday labels
        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col, wd in enumerate(weekdays):
            lbl = ctk.CTkLabel(self.days_frame, text=wd, font=ctk.CTkFont(size=11, weight="bold"), text_color="#9ca3af")
            lbl.grid(row=0, column=col, pady=(6, 4))

        # Month matrix
        month_days = calendar.monthcalendar(self.current_year, self.current_month)
        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                if day != 0:
                    is_selected = (day == self.selected_day)
                    btn = ctk.CTkButton(
                        self.days_frame, text=str(day), width=34, height=28,
                        fg_color="#6366f1" if is_selected else "transparent",
                        hover_color="#4f46e5",
                        font=ctk.CTkFont(size=11),
                        command=lambda d=day: self.select_day(d)
                    )
                    btn.grid(row=r + 1, column=c, padx=2, pady=2)

    def select_day(self, day):
        self.selected_day = day
        self.draw_calendar()

    def confirm_selection(self):
        if self.include_time:
            h = self.hour_menu.get()
            m = self.min_menu.get()
            result = f"{self.current_year:04d}-{self.current_month:02d}-{self.selected_day:02d} {h}:{m}"
        else:
            result = f"{self.current_year:04d}-{self.current_month:02d}-{self.selected_day:02d}"

        if self.on_select:
            self.on_select(result)
        self.destroy()


# =====================================================================
# 2. TYPE-AWARE CATEGORY DIALOG
# =====================================================================
class AddCategoryDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, tx_type, on_success):
        super().__init__(parent)
        self.db = db
        self.tx_type = tx_type
        self.on_success = on_success

        self.title(f"Add {self.tx_type} Category")
        self.geometry("340x210")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(
            self, text=f"New {self.tx_type} Category:", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(25, 10))

        self.entry = ctk.CTkEntry(
            self, width=250, 
            placeholder_text="e.g. Salary, Dividend" if self.tx_type == "Income" else "e.g. Rent, Grocery"
        )
        self.entry.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Cancel", width=105, fg_color="#444", command=self.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Save", width=105, fg_color="#2eb872", hover_color="#24935b", command=self.save).pack(side="left", padx=5)

    def save(self):
        cat_name = self.entry.get().strip()
        if not cat_name:
            messagebox.showwarning("Warning", "Category name cannot be empty.")
            return
        self.db.add_category(cat_name, self.tx_type)
        self.on_success(cat_name)
        self.destroy()


# =====================================================================
# 3. EXCEL EXPORT DIALOG WITH CALENDAR PICKERS
# =====================================================================
class ExportFilterDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, currency: str):
        super().__init__(parent)
        self.db = db
        self.currency = currency
        self.title("Export Transactions to Excel")
        self.geometry("450x470")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="Filter & Export to Excel", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        # Quick Presets
        ctk.CTkLabel(self, text="Quick Presets:", anchor="w").pack(fill="x", padx=30, pady=(5, 2))
        self.preset_menu = ctk.CTkOptionMenu(
            self,
            values=["All Time", "This Month", "Last Month", "Last 7 Days", "Last 30 Days", "Last 6 Months", "Custom Range"],
            command=self.on_preset_change
        )
        self.preset_menu.pack(fill="x", padx=30, pady=(0, 15))

        # Start Date Row with Calendar Button
        ctk.CTkLabel(self, text="Start Date & Time:", anchor="w").pack(fill="x", padx=30, pady=(5, 2))
        start_row = ctk.CTkFrame(self, fg_color="transparent")
        start_row.pack(fill="x", padx=30, pady=(0, 10))
        self.start_entry = ctk.CTkEntry(start_row)
        self.start_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(start_row, text="📅", width=36, fg_color="#374151", command=self.pick_start_date).pack(side="right")

        # End Date Row with Calendar Button
        ctk.CTkLabel(self, text="End Date & Time:", anchor="w").pack(fill="x", padx=30, pady=(5, 2))
        end_row = ctk.CTkFrame(self, fg_color="transparent")
        end_row.pack(fill="x", padx=30, pady=(0, 15))
        self.end_entry = ctk.CTkEntry(end_row)
        self.end_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(end_row, text="📅", width=36, fg_color="#374151", command=self.pick_end_date).pack(side="right")

        self.on_preset_change("This Month")

        # Download Button
        ctk.CTkButton(
            self, text="Generate & Download (.xlsx)", 
            fg_color="#10b981", hover_color="#059669",
            height=38, font=ctk.CTkFont(weight="bold"), 
            command=self.process_export
        ).pack(fill="x", padx=30, pady=20)

    def pick_start_date(self):
        DateTimePickerDialog(self, initial_datetime=self.start_entry.get().strip(), include_time=True,
                             on_select=lambda val: self.set_entry(self.start_entry, val))

    def pick_end_date(self):
        DateTimePickerDialog(self, initial_datetime=self.end_entry.get().strip(), include_time=True,
                             on_select=lambda val: self.set_entry(self.end_entry, val))

    def set_entry(self, entry_widget, val):
        entry_widget.delete(0, "end")
        entry_widget.insert(0, val)

    def on_preset_change(self, preset):
        today = datetime.now()
        if preset == "All Time":
            self.set_entry(self.start_entry, "2000-01-01 00:00")
            self.set_entry(self.end_entry, today.strftime("%Y-%m-%d 23:59"))
        elif preset == "This Month":
            start = today.replace(day=1)
            self.set_entry(self.start_entry, start.strftime("%Y-%m-%d 00:00"))
            self.set_entry(self.end_entry, today.strftime("%Y-%m-%d 23:59"))
        elif preset == "Last Month":
            first_day_curr = today.replace(day=1)
            last_day_prev = first_day_curr - timedelta(days=1)
            first_day_prev = last_day_prev.replace(day=1)
            self.set_entry(self.start_entry, first_day_prev.strftime("%Y-%m-%d 00:00"))
            self.set_entry(self.end_entry, last_day_prev.strftime("%Y-%m-%d 23:59"))
        elif preset == "Last 7 Days":
            start = today - timedelta(days=7)
            self.set_entry(self.start_entry, start.strftime("%Y-%m-%d 00:00"))
            self.set_entry(self.end_entry, today.strftime("%Y-%m-%d 23:59"))
        elif preset == "Last 30 Days":
            start = today - timedelta(days=30)
            self.set_entry(self.start_entry, start.strftime("%Y-%m-%d 00:00"))
            self.set_entry(self.end_entry, today.strftime("%Y-%m-%d 23:59"))
        elif preset == "Last 6 Months":
            start = today - timedelta(days=180)
            self.set_entry(self.start_entry, start.strftime("%Y-%m-%d 00:00"))
            self.set_entry(self.end_entry, today.strftime("%Y-%m-%d 23:59"))

    def process_export(self):
        s_date = self.start_entry.get().strip()
        e_date = self.end_entry.get().strip()

        df = self.db.get_filtered_transactions(s_date, e_date)
        if df.empty:
            messagebox.showinfo("No Data", f"No records found between {s_date} and {e_date}.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile=f"VaultFlow_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        )
        if file_path:
            try:
                export_df = df.rename(columns={
                    "date": "Date & Time",
                    "type": "Type",
                    "category": "Category",
                    "payment_mode": "Payment Mode",
                    "amount": f"Amount ({self.currency})",
                    "description": "Description"
                })
                with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                    export_df.to_excel(writer, index=False, sheet_name="VaultFlow_Records")
                messagebox.showinfo("Success", f"Report saved successfully!\n\nRecords: {len(export_df)}")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Export Error", str(e))
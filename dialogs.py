import calendar
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

class AddCategoryDialog(ctk.CTkToplevel):
    def __init__(self, parent, db, tx_type, on_success):
        super().__init__(parent)
        self.db = db
        self.tx_type = tx_type
        self.on_success = on_success

        self.title(f"Add {self.tx_type} Category")
        self.geometry("340x210")
        self.resizable(False, False)
        self.configure(fg_color="#080a11")
        self.grab_set()

        ctk.CTkLabel(self, text=f"New {self.tx_type} Category:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f8fafc").pack(pady=(25, 10))
        self.entry = ctk.CTkEntry(self, width=250, placeholder_text="Category name...", fg_color="#111625", border_color="#1e263b")
        self.entry.pack(pady=5)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Cancel", width=105, fg_color="#1e263b", hover_color="#2b3652", text_color="#94a3b8", command=self.destroy).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Save", width=105, fg_color="#10b981", hover_color="#059669", text_color="#000000", font=ctk.CTkFont(weight="bold"), command=self.save).pack(side="left", padx=5)

    def save(self):
        cat_name = self.entry.get().strip()
        if not cat_name:
            messagebox.showwarning("Warning", "Category name cannot be empty.")
            return
        self.db.add_category(cat_name, self.tx_type)
        self.on_success(cat_name)
        self.destroy()


class DateTimePickerDialog(ctk.CTkToplevel):
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
        self.configure(fg_color="#080a11")
        self.grab_set()

        self.month_names = ["", "January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"]

        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=15, pady=(15, 8))

        ctk.CTkButton(nav_frame, text="◀", width=32, height=28, fg_color="#1e263b", hover_color="#2b3652", command=self.prev_month).pack(side="left")
        self.header_lbl = ctk.CTkLabel(nav_frame, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f8fafc")
        self.header_lbl.pack(side="left", expand=True)
        ctk.CTkButton(nav_frame, text="▶", width=32, height=28, fg_color="#1e263b", hover_color="#2b3652", command=self.next_month).pack(side="right")

        self.days_frame = ctk.CTkFrame(self, fg_color="#111625", corner_radius=8)
        self.days_frame.pack(padx=15, pady=5, fill="both", expand=True)

        if self.include_time:
            time_frame = ctk.CTkFrame(self, fg_color="transparent")
            time_frame.pack(fill="x", padx=15, pady=(8, 0))

            ctk.CTkLabel(time_frame, text="Time:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#94a3b8").pack(side="left", padx=(5, 10))

            self.hour_menu = ctk.CTkOptionMenu(
                time_frame, width=70, height=28,
                values=[f"{h:02d}" for h in range(24)],
                fg_color="#1e263b"
            )
            self.hour_menu.set(f"{self.selected_hour:02d}")
            self.hour_menu.pack(side="left", padx=2)

            ctk.CTkLabel(time_frame, text=":", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f8fafc").pack(side="left", padx=2)

            self.min_menu = ctk.CTkOptionMenu(
                time_frame, width=70, height=28,
                values=[f"{m:02d}" for m in range(0, 60, 1)],
                fg_color="#1e263b"
            )
            self.min_menu.set(f"{self.selected_minute:02d}")
            self.min_menu.pack(side="left", padx=2)

        ctk.CTkButton(
            self, text="Set Date & Time", height=32,
            font=ctk.CTkFont(weight="bold"),
            fg_color="#f59e0b", hover_color="#d97706", text_color="#000000",
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

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col, wd in enumerate(weekdays):
            lbl = ctk.CTkLabel(self.days_frame, text=wd, font=ctk.CTkFont(size=11, weight="bold"), text_color="#64748b")
            lbl.grid(row=0, column=col, pady=(6, 4))

        month_days = calendar.monthcalendar(self.current_year, self.current_month)
        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                if day != 0:
                    is_selected = (day == self.selected_day)
                    btn = ctk.CTkButton(
                        self.days_frame, text=str(day), width=34, height=28,
                        fg_color="#f59e0b" if is_selected else "transparent",
                        text_color="#000000" if is_selected else "#f8fafc",
                        hover_color="#d97706",
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
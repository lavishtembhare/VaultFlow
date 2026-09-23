import os
import sys
import ctypes
import customtkinter as ctk
from tkinter import messagebox
import matplotlib.pyplot as plt

from database import DatabaseManager
from metrics import MetricCardsView
from analytics import AnalyticsView
from history import TransactionHistoryView
from sidebar import SidebarView
from entry_view import EntryView
from settings_view import SettingsView

try:
    myappid = 'vaultflow.privateasset.desktop.2.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_asset_path(filename: str) -> str:
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)

class VaultFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VaultFlow — Private Asset & Liquid Flow Suite")
        self.geometry("1240x800")
        self.minsize(1080, 720)

        # Set custom VaultFlow Icon
        icon_path = get_asset_path("vaultflow_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Void Obsidian Root
        self.configure(fg_color="#080a11")
        self.db = DatabaseManager()
        self.currency = self.db.get_setting("currency", "$")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Titanium Navigation Sidebar
        self.sidebar = SidebarView(self, on_navigate=self.show_view)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. Main Content Host Area
        self.main_container = ctk.CTkFrame(self, fg_color="#0c0f18", corner_radius=0)
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # VIEW 1: DASHBOARD
        self.dashboard_view = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.dashboard_view.grid_columnconfigure(0, weight=1)
        self.dashboard_view.grid_rowconfigure(2, weight=1)

        dash_padding = ctk.CTkFrame(self.dashboard_view, fg_color="transparent")
        dash_padding.pack(fill="both", expand=True, padx=20, pady=20)
        dash_padding.grid_columnconfigure(0, weight=1)
        dash_padding.grid_rowconfigure(2, weight=1)

        self.metrics_view = MetricCardsView(dash_padding)
        self.metrics_view.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self.analytics_view = AnalyticsView(dash_padding, on_style_change=self.refresh_ui)
        self.analytics_view.grid(row=1, column=0, sticky="nsew", pady=(0, 12))

        self.history_view = TransactionHistoryView(
            dash_padding,
            on_delete_callback=self.delete_record,
            on_clear_all_callback=self.clear_all_records
        )
        self.history_view.grid(row=2, column=0, sticky="nsew")

        # VIEW 2: FULL-SCREEN DATA ENTRY
        self.entry_view = EntryView(
            self.main_container, self.db,
            on_transaction_saved=self.handle_transaction_saved
        )

        # VIEW 3: SETTINGS WORKSPACE
        self.settings_view = SettingsView(
            self.main_container, self.db,
            on_settings_changed=self.on_settings_updated
        )

        self.views = {
            "dashboard": self.dashboard_view,
            "add_entry": self.entry_view,
            "settings": self.settings_view
        }

        # Keyboard shortcuts
        self.bind("<Control-Key-1>", lambda e: self.navigate_hotkey("dashboard"))
        self.bind("<Control-Key-2>", lambda e: self.navigate_hotkey("add_entry"))
        self.bind("<Control-Key-3>", lambda e: self.navigate_hotkey("settings"))
        self.bind("<F5>", lambda e: self.refresh_ui())

        self.show_view("dashboard")
        self.refresh_ui(highlight_new=False)

    def navigate_hotkey(self, view_key: str):
        self.sidebar.set_active(view_key)
        self.show_view(view_key)

    def show_view(self, view_key: str):
        for k, view in self.views.items():
            if k == view_key:
                view.grid(row=0, column=0, sticky="nsew")
            else:
                view.grid_forget()

        if view_key == "add_entry":
            self.entry_view.refresh_categories()
        elif view_key == "dashboard":
            self.refresh_ui()

    def handle_transaction_saved(self):
        self.refresh_ui(highlight_new=True)
        self.sidebar.set_active("dashboard")
        self.show_view("dashboard")

    def on_settings_updated(self):
        self.currency = self.db.get_setting("currency", "$")
        self.entry_view.refresh_categories()
        self.refresh_ui()

    def delete_record(self, tx_id):
        if messagebox.askyesno("Purge Transaction", "Purge this ledger transaction record?"):
            self.db.delete_transaction(tx_id)
            self.refresh_ui(highlight_new=False)

    def clear_all_records(self):
        self.db.clear_all_transactions()
        self.refresh_ui(highlight_new=False)

    def refresh_ui(self, highlight_new=False):
        df = self.db.get_all_transactions()
        self.metrics_view.update_metrics(df, self.currency, self.db)
        self.analytics_view.render_charts(df, self.currency)
        self.history_view.render_list(df, self.currency, self.db, highlight_new=highlight_new)

    def on_close(self):
        try:
            plt.close('all')
            self.withdraw()
            self.quit()
            self.destroy()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        app = VaultFlowApp()
        app.mainloop()
    except (KeyboardInterrupt, SystemExit):
        pass
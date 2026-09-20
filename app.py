import sys
import customtkinter as ctk
from tkinter import messagebox

from database import DatabaseManager
from dialogs import ExportFilterDialog, SettingsDialog
from metrics import MetricCardsView
from analytics import AnalyticsView
from history import TransactionHistoryView
from sidebar import SidebarView

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VaultFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VaultFlow - Personal Finance & Expense Suite")
        self.geometry("1180x750")
        self.minsize(1020, 680)

        self.db = DatabaseManager()
        self.currency = self.db.get_setting("currency", "$")

        # Graceful exit handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar View
        self.sidebar = SidebarView(
            self, self.db,
            on_add_callback=lambda highlight_new=False: self.refresh_ui(highlight_new=highlight_new),
            on_currency_change=self.handle_currency_change,
            on_open_export=self.open_export_dialog,
            on_open_settings=self.open_settings_dialog
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. Main Workspace
        self.main_content = ctk.CTkFrame(self, fg_color="#0f172a")
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(2, weight=1)

        # Top Metric Cards
        self.metrics_view = MetricCardsView(self.main_content)
        self.metrics_view.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        # Charts Section
        self.analytics_view = AnalyticsView(self.main_content, on_style_change=self.refresh_ui)
        self.analytics_view.grid(row=1, column=0, sticky="nsew", pady=(0, 12))

        # Bottom Transactions List
        self.history_view = TransactionHistoryView(self.main_content, on_delete_callback=self.delete_record)
        self.history_view.grid(row=2, column=0, sticky="nsew")

        self.refresh_ui(highlight_new=False)

    def on_close(self):
        """Clean shutdown: stops the Tk event loop first before destroying widgets."""
        try:
            self.withdraw()
            self.quit()
            self.destroy()
        except Exception:
            pass

    def handle_currency_change(self, new_currency):
        self.currency = new_currency
        self.refresh_ui()

    def open_export_dialog(self):
        ExportFilterDialog(self, self.db, self.currency)

    def open_settings_dialog(self):
        SettingsDialog(self, self.db, on_settings_changed=self.on_settings_updated)

    def on_settings_updated(self):
        self.currency = self.db.get_setting("currency", "$")
        self.sidebar.refresh_categories()
        self.refresh_ui()

    def delete_record(self, tx_id):
        if messagebox.askyesno("Delete Record", "Are you sure you want to delete this transaction?"):
            self.db.delete_transaction(tx_id)
            self.refresh_ui(highlight_new=False)

    def refresh_ui(self, highlight_new=False):
        df = self.db.get_all_transactions()
        self.metrics_view.update_metrics(df, self.currency, self.db)
        self.analytics_view.render_charts(df, self.currency)
        self.history_view.render_list(df, self.currency, self.db, highlight_new=highlight_new)

if __name__ == "__main__":
    try:
        app = VaultFlowApp()
        app.mainloop()
    except (KeyboardInterrupt, SystemExit):
        pass
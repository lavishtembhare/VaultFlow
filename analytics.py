import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, parent, on_style_change=None):
        super().__init__(parent, corner_radius=12, fg_color="#1f2937")
        self.pie_type = "Donut"
        self.on_style_change = on_style_change

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(10, 0))

        ctk.CTkLabel(top_bar, text="Visual Analytics", font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")

        self.pie_selector = ctk.CTkSegmentedButton(
            top_bar, 
            values=["Donut", "Classic Pie", "Exploded"],
            command=self.change_pie_type
        )
        self.pie_selector.set("Donut")
        self.pie_selector.pack(side="right")

        self.canvas_widget = None

    def change_pie_type(self, value):
        self.pie_type = value
        if self.on_style_change:
            self.on_style_change()

    def render_charts(self, df: pd.DataFrame, currency: str):
        # Fix: Destroy the underlying Tk widget, not the canvas adapter directly
        if self.canvas_widget is not None:
            self.canvas_widget.get_tk_widget().destroy()
            self.canvas_widget = None

        fig, (ax_bar, ax_pie) = plt.subplots(1, 2, figsize=(8, 3.4), dpi=100)
        fig.patch.set_facecolor('#1f2937')
        
        expense_df = df[df["type"] == "Expense"] if not df.empty else pd.DataFrame()

        if expense_df.empty:
            for ax in (ax_bar, ax_pie):
                ax.set_facecolor('#1f2937')
                ax.text(0.5, 0.5, 'No expense data logged', horizontalalignment='center',
                        verticalalignment='center', color='#6b7280', fontsize=11, transform=ax.transAxes)
                ax.axis('off')
        else:
            cat_totals = expense_df.groupby("category")["amount"].sum().sort_values(ascending=True)
            palette = ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#fb7185", "#fbbf24", "#34d399", "#2dd4bf", "#f87171"]
            colors = (palette * ((len(cat_totals) // len(palette)) + 1))[:len(cat_totals)]

            # Horizontal Bar Chart (Expense Comparison)
            ax_bar.set_facecolor('#1f2937')
            bars = ax_bar.barh(cat_totals.index, cat_totals.values, color="#6366f1", height=0.55, edgecolor="none")
            ax_bar.set_title("Expense Comparison", color="#f3f4f6", fontsize=11, weight="bold", pad=8)
            ax_bar.tick_params(colors="#9ca3af", labelsize=8)
            ax_bar.spines['top'].set_visible(False)
            ax_bar.spines['right'].set_visible(False)
            ax_bar.spines['left'].set_color('#374151')
            ax_bar.spines['bottom'].set_color('#374151')
            ax_bar.grid(axis="x", color="#374151", linestyle="--", alpha=0.5)

            # Pie / Donut Chart
            ax_pie.set_facecolor('#1f2937')
            explode = [0.08] * len(cat_totals) if self.pie_type == "Exploded" else None
            wedge_width = 0.5 if self.pie_type == "Donut" else 1.0

            wedges, texts, autotexts = ax_pie.pie(
                cat_totals,
                labels=cat_totals.index,
                autopct='%1.0f%%',
                startangle=140,
                explode=explode,
                colors=colors,
                wedgeprops=dict(width=wedge_width, edgecolor='#1f2937', linewidth=1.5),
                textprops=dict(color="#d1d5db", fontsize=8)
            )
            for at in autotexts:
                at.set_color("#111827")
                at.set_weight("bold")
                at.set_fontsize(8)

            ax_pie.set_title(f"Distribution ({self.pie_type})", color="#f3f4f6", fontsize=11, weight="bold", pad=8)

        plt.tight_layout()
        self.canvas_widget = FigureCanvasTkAgg(fig, master=self)
        self.canvas_widget.draw()
        self.canvas_widget.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        plt.close(fig)
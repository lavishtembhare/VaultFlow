import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, parent, on_style_change=None):
        super().__init__(parent, corner_radius=12, fg_color="#1f2937")
        self.view_mode = "Categories"  # "Categories" or "Payment Modes"
        self.pie_type = "Donut"
        self.on_style_change = on_style_change

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(10, 0))

        # View Mode Toggle (Categories vs Payment Modes)
        self.mode_toggle = ctk.CTkSegmentedButton(
            top_bar,
            values=["Categories", "Payment Modes"],
            command=self.change_view_mode,
            selected_color="#6366f1"
        )
        self.mode_toggle.set("Categories")
        self.mode_toggle.pack(side="left")

        # Highlight Badge for Most Used Payment Mode
        self.highlight_lbl = ctk.CTkLabel(
            top_bar, text="", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#38bdf8"
        )
        self.highlight_lbl.pack(side="left", padx=15)

        # Pie Chart Style Selector
        self.pie_selector = ctk.CTkSegmentedButton(
            top_bar, 
            values=["Donut", "Classic Pie", "Exploded"],
            command=self.change_pie_type
        )
        self.pie_selector.set("Donut")
        self.pie_selector.pack(side="right")

        self.canvas_widget = None

    def change_view_mode(self, value):
        self.view_mode = value
        if self.on_style_change:
            self.on_style_change()

    def change_pie_type(self, value):
        self.pie_type = value
        if self.on_style_change:
            self.on_style_change()

    def render_charts(self, df: pd.DataFrame, currency: str):
        if self.canvas_widget is not None:
            self.canvas_widget.get_tk_widget().destroy()
            self.canvas_widget = None

        fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(8, 3.4), dpi=100)
        fig.patch.set_facecolor('#1f2937')
        for ax in (ax_left, ax_right):
            ax.set_facecolor('#1f2937')

        if df.empty:
            self.highlight_lbl.configure(text="")
            for ax in (ax_left, ax_right):
                ax.text(0.5, 0.5, 'No data logged yet', horizontalalignment='center',
                        verticalalignment='center', color='#6b7280', fontsize=11, transform=ax.transAxes)
                ax.axis('off')
        else:
            palette = ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#fb7185", "#fbbf24", "#34d399", "#2dd4bf"]

            if self.view_mode == "Payment Modes":
                # Ensure payment_mode column exists
                mode_series = df["payment_mode"] if "payment_mode" in df.columns else pd.Series(["UPI"] * len(df))
                mode_counts = mode_series.value_counts(ascending=True)
                top_mode = mode_counts.idxmax() if not mode_counts.empty else "N/A"
                top_count = mode_counts.max() if not mode_counts.empty else 0

                # Update Highlight Badge
                self.highlight_lbl.configure(text=f"⭐ Most Used: {top_mode} ({top_count} txs)")

                # LEFT CHART: Usage Frequency (Count of Transactions per Mode)
                bar_colors = ["#6366f1" if m != top_mode else "#10b981" for m in mode_counts.index]
                bars = ax_left.barh(mode_counts.index, mode_counts.values, color=bar_colors, height=0.55)
                ax_left.set_title("Mode Usage Frequency (Transactions)", color="#f3f4f6", fontsize=11, weight="bold", pad=8)
                ax_left.tick_params(colors="#9ca3af", labelsize=8)
                ax_left.spines['top'].set_visible(False)
                ax_left.spines['right'].set_visible(False)
                ax_left.spines['left'].set_color('#374151')
                ax_left.spines['bottom'].set_color('#374151')
                ax_left.grid(axis="x", color="#374151", linestyle="--", alpha=0.5)

                # Add value labels to bars
                for bar in bars:
                    w = bar.get_width()
                    ax_left.text(w + 0.1, bar.get_y() + bar.get_height() / 2, f"{int(w)}",
                                 ha='left', va='center', color='#d1d5db', fontsize=8, weight="bold")

                # RIGHT CHART: Spending Volume by Payment Mode
                expense_df = df[df["type"] == "Expense"]
                if not expense_df.empty and "payment_mode" in expense_df.columns:
                    mode_spend = expense_df.groupby("payment_mode")["amount"].sum()
                else:
                    mode_spend = pd.Series()

                if mode_spend.empty:
                    ax_right.text(0.5, 0.5, 'No expense volume to show', horizontalalignment='center',
                                 verticalalignment='center', color='#6b7280', fontsize=11, transform=ax_right.transAxes)
                    ax_right.axis('off')
                else:
                    explode = [0.08] * len(mode_spend) if self.pie_type == "Exploded" else None
                    wedge_width = 0.5 if self.pie_type == "Donut" else 1.0

                    wedges, texts, autotexts = ax_right.pie(
                        mode_spend,
                        labels=mode_spend.index,
                        autopct='%1.0f%%',
                        startangle=140,
                        explode=explode,
                        colors=palette[:len(mode_spend)],
                        wedgeprops=dict(width=wedge_width, edgecolor='#1f2937', linewidth=1.5),
                        textprops=dict(color="#d1d5db", fontsize=8)
                    )
                    for at in autotexts:
                        at.set_color("#111827")
                        at.set_weight("bold")
                        at.set_fontsize(8)

                    ax_right.set_title(f"Volume Share ({self.pie_type})", color="#f3f4f6", fontsize=11, weight="bold", pad=8)

            else:
                # CATEGORY BREAKDOWN VIEW
                self.highlight_lbl.configure(text="")
                expense_df = df[df["type"] == "Expense"] if not df.empty else pd.DataFrame()

                if expense_df.empty:
                    for ax in (ax_left, ax_right):
                        ax.text(0.5, 0.5, 'No expense data logged', horizontalalignment='center',
                                verticalalignment='center', color='#6b7280', fontsize=11, transform=ax.transAxes)
                        ax.axis('off')
                else:
                    cat_totals = expense_df.groupby("category")["amount"].sum().sort_values(ascending=True)

                    # Left: Expense Comparison Bar
                    ax_left.barh(cat_totals.index, cat_totals.values, color="#6366f1", height=0.55)
                    ax_left.set_title("Expense Comparison", color="#f3f4f6", fontsize=11, weight="bold", pad=8)
                    ax_left.tick_params(colors="#9ca3af", labelsize=8)
                    ax_left.spines['top'].set_visible(False)
                    ax_left.spines['right'].set_visible(False)
                    ax_left.spines['left'].set_color('#374151')
                    ax_left.spines['bottom'].set_color('#374151')
                    ax_left.grid(axis="x", color="#374151", linestyle="--", alpha=0.5)

                    # Right: Category Distribution Pie/Donut
                    explode = [0.08] * len(cat_totals) if self.pie_type == "Exploded" else None
                    wedge_width = 0.5 if self.pie_type == "Donut" else 1.0

                    wedges, texts, autotexts = ax_right.pie(
                        cat_totals,
                        labels=cat_totals.index,
                        autopct='%1.0f%%',
                        startangle=140,
                        explode=explode,
                        colors=palette[:len(cat_totals)],
                        wedgeprops=dict(width=wedge_width, edgecolor='#1f2937', linewidth=1.5),
                        textprops=dict(color="#d1d5db", fontsize=8)
                    )
                    for at in autotexts:
                        at.set_color("#111827")
                        at.set_weight("bold")
                        at.set_fontsize(8)

                    ax_right.set_title(f"Category Share ({self.pie_type})", color="#f3f4f6", fontsize=11, weight="bold", pad=8)

        plt.tight_layout()
        self.canvas_widget = FigureCanvasTkAgg(fig, master=self)
        self.canvas_widget.draw()
        self.canvas_widget.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        plt.close(fig)
import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, parent, on_style_change=None):
        super().__init__(parent, corner_radius=12, fg_color="#1f2937")
        self.view_mode = "Expenses"  # "Expenses", "Incomes", or "Payment Modes"
        self.pie_type = "Donut"
        self.on_style_change = on_style_change
        self._anim_job = None

        # --- Top Header Toolbar ---
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(10, 2))

        # View Mode Toggle
        self.mode_toggle = ctk.CTkSegmentedButton(
            top_bar,
            values=["Expenses", "Incomes", "Payment Modes"],
            command=self.change_view_mode,
            selected_color="#6366f1"
        )
        self.mode_toggle.set("Expenses")
        self.mode_toggle.pack(side="left")

        # Top Mode Highlight Badge
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

        # --- Persistent Matplotlib Figure & Canvas ---
        self.fig, (self.ax_left, self.ax_right) = plt.subplots(1, 2, figsize=(8.5, 3.4), dpi=100)
        self.fig.patch.set_facecolor('#1f2937')
        
        # Generous left margin so longer category names don't clip
        self.fig.subplots_adjust(left=0.22, right=0.96, top=0.88, bottom=0.14, wspace=0.35)

        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(2, 10))

    def change_view_mode(self, value):
        self.view_mode = value
        if self.on_style_change:
            self.on_style_change()

    def change_pie_type(self, value):
        self.pie_type = value
        if self.on_style_change:
            self.on_style_change()

    def render_charts(self, df: pd.DataFrame, currency: str, animate=True):
        # Cancel any active animation job safely
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

        # Clean axes
        self.ax_left.clear()
        self.ax_right.clear()
        self.ax_left.set_facecolor('#1f2937')
        self.ax_right.set_facecolor('#1f2937')

        # 1. Validate Input Data
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            self.show_empty_message("No transaction records logged yet.")
            return

        clean_df = df.copy()
        clean_df["amount"] = pd.to_numeric(clean_df["amount"], errors="coerce").fillna(0.0)
        clean_df = clean_df[clean_df["amount"] > 0]

        palette = ["#38bdf8", "#818cf8", "#c084fc", "#f472b6", "#fb7185", "#fbbf24", "#34d399", "#2dd4bf"]

        # 2. Extract Data Based on Selected View
        if self.view_mode == "Payment Modes":
            mode_series = clean_df["payment_mode"] if "payment_mode" in clean_df.columns else pd.Series(["UPI"] * len(clean_df))
            bar_data = mode_series.value_counts(ascending=True)

            if bar_data.empty or bar_data.sum() <= 0:
                self.show_empty_message("No payment mode data available.")
                return

            top_mode = bar_data.idxmax()
            top_count = bar_data.max()
            self.highlight_lbl.configure(text=f"⭐ Top Mode: {top_mode} ({top_count} txs)")

            pie_data = clean_df.groupby("payment_mode")["amount"].sum()
            bar_title = "Usage Count (Transactions)"
            pie_title = f"Volume Share ({self.pie_type})"
            bar_colors = ["#6366f1" if m != top_mode else "#10b981" for m in bar_data.index]
            is_currency_bar = False

        else:
            target_type = "Expense" if self.view_mode == "Expenses" else "Income"
            self.highlight_lbl.configure(text="")
            filtered_df = clean_df[clean_df["type"] == target_type]

            if filtered_df.empty:
                self.show_empty_message(f"No {target_type.lower()} records found.")
                return

            cat_totals = filtered_df.groupby("category")["amount"].sum().sort_values(ascending=True)
            if cat_totals.empty or cat_totals.sum() <= 0:
                self.show_empty_message(f"No {target_type.lower()} amounts to calculate.")
                return

            bar_data = cat_totals
            pie_data = cat_totals
            bar_title = f"{target_type} Comparison"
            pie_title = f"{target_type} Share ({self.pie_type})"
            solid_color = "#ef4444" if target_type == "Expense" else "#10b981"
            bar_colors = [solid_color] * len(bar_data)
            is_currency_bar = True

        max_val = float(bar_data.max()) if not bar_data.empty else 1.0
        x_limit = max_val * 1.28 if max_val > 0 else 1.0

        pie_data = pie_data[pie_data > 0]
        total_steps = 6 if animate else 1

        def animate_step(step):
            try:
                if not self.winfo_exists():
                    return
            except Exception:
                return

            p = 1.0 if not animate else 1.0 - (1.0 - (step / total_steps)) ** 2

            self.ax_left.clear()
            self.ax_right.clear()
            self.ax_left.set_facecolor('#1f2937')
            self.ax_right.set_facecolor('#1f2937')

            # ==========================================
            # A. HORIZONTAL BAR CHART
            # ==========================================
            current_vals = [float(v) * p for v in bar_data.values]
            bars = self.ax_left.barh(list(bar_data.index), current_vals, color=bar_colors, height=0.55)
            
            self.ax_left.set_title(bar_title, color="#f3f4f6", fontsize=11, weight="bold", pad=8)
            self.ax_left.tick_params(colors="#9ca3af", labelsize=9)
            self.ax_left.set_xlim(0, x_limit)

            self.ax_left.spines['top'].set_visible(False)
            self.ax_left.spines['right'].set_visible(False)
            self.ax_left.spines['left'].set_color('#374151')
            self.ax_left.spines['bottom'].set_color('#374151')
            self.ax_left.grid(axis="x", color="#374151", linestyle="--", alpha=0.4)

            for bar, orig_val in zip(bars, bar_data.values):
                w = bar.get_width()
                if orig_val > 0 and (p > 0.4 or not animate):
                    label_str = f"{currency}{orig_val:,.0f}" if is_currency_bar else f"{int(orig_val)}"
                    self.ax_left.text(
                        w + (max_val * 0.025), 
                        bar.get_y() + bar.get_height() / 2, 
                        label_str, 
                        ha='left', va='center', color='#f3f4f6', fontsize=8, weight="bold"
                    )

            # ==========================================
            # B. PIE / DONUT CHART (Matplotlib 3.11+ Safe)
            # ==========================================
            if not pie_data.empty and pie_data.sum() > 0:
                self.ax_right.set_aspect('equal')

                explode = [0.06] * len(pie_data) if (self.pie_type == "Exploded" and len(pie_data) > 1) else None
                slice_colors = (palette * ((len(pie_data) // len(palette)) + 1))[:len(pie_data)]
                
                if self.pie_type == "Donut":
                    ring_width = max(0.12, 0.50 * p)
                    wprops = dict(width=ring_width, edgecolor='#1f2937', linewidth=1.5)
                else:
                    wprops = dict(edgecolor='#1f2937', linewidth=1.5)

                # Direct render without tuple unpacking (handles PieContainer)
                self.ax_right.pie(
                    list(pie_data.values),
                    labels=list(pie_data.index) if (p > 0.6 or not animate) else None,
                    autopct='%1.0f%%' if (p > 0.6 or not animate) else None,
                    startangle=140,
                    explode=explode,
                    colors=slice_colors,
                    wedgeprops=wprops,
                    textprops=dict(color="#f3f4f6", fontsize=8, weight="bold"),
                    pctdistance=0.75 if self.pie_type == "Donut" else 0.6
                )
                self.ax_right.set_title(pie_title, color="#f3f4f6", fontsize=11, weight="bold", pad=8)

            self.canvas_widget.draw_idle()

            if step < total_steps and animate:
                self._anim_job = self.after(24, lambda: animate_step(step + 1))
            else:
                self._anim_job = None

        animate_step(1)

    def show_empty_message(self, message):
        self.highlight_lbl.configure(text="")
        self.ax_left.clear()
        self.ax_right.clear()
        self.ax_left.set_facecolor('#1f2937')
        self.ax_right.set_facecolor('#1f2937')
        self.ax_left.text(0.5, 0.5, message, ha='center', va='center', color='#9ca3af', fontsize=11, transform=self.ax_left.transAxes)
        self.ax_right.text(0.5, 0.5, "Charts will activate with data", ha='center', va='center', color='#6b7280', fontsize=11, transform=self.ax_right.transAxes)
        self.ax_left.axis('off')
        self.ax_right.axis('off')
        self.canvas_widget.draw_idle()
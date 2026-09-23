import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, parent, on_style_change=None):
        super().__init__(parent, corner_radius=12, fg_color="#111625", border_width=1, border_color="#1e263b")
        self.view_mode = "Expenses"
        self.pie_type = "Donut"
        self.on_style_change = on_style_change

        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=15, pady=(10, 2))

        self.mode_toggle = ctk.CTkSegmentedButton(
            top_bar,
            values=["Expenses", "Incomes", "Monthly Trends", "Accounts", "Payment Modes"],
            command=self.change_view_mode,
            selected_color="#f59e0b",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold")
        )
        self.mode_toggle.set("Expenses")
        self.mode_toggle.pack(side="left")

        self.highlight_lbl = ctk.CTkLabel(
            top_bar, text="", 
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), 
            text_color="#f59e0b"
        )
        self.highlight_lbl.pack(side="left", padx=15)

        self.pie_selector = ctk.CTkSegmentedButton(
            top_bar, 
            values=["Donut", "Classic Pie", "Exploded"],
            command=self.change_pie_type,
            selected_color="#2563eb",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold")
        )
        self.pie_selector.set("Donut")
        self.pie_selector.pack(side="right")

        self.fig, (self.ax_left, self.ax_right) = plt.subplots(1, 2, figsize=(8.5, 3.4), dpi=100)
        self.fig.patch.set_facecolor('#111625')
        self.fig.subplots_adjust(left=0.18, right=0.96, top=0.88, bottom=0.18, wspace=0.32)

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

    def render_charts(self, df: pd.DataFrame, currency: str, animate=False):
        self.ax_left.clear()
        self.ax_right.clear()
        self.ax_left.set_facecolor('#111625')
        self.ax_right.set_facecolor('#111625')

        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            self.show_empty_message("// NO LEDGER TRANSACTIONS LOGGED")
            return

        clean_df = df.copy()
        clean_df["amount"] = pd.to_numeric(clean_df["amount"], errors="coerce").fillna(0.0)
        clean_df = clean_df[clean_df["amount"] > 0]

        palette = ["#f59e0b", "#10b981", "#38bdf8", "#818cf8", "#c084fc", "#fb7185", "#2dd4bf", "#e2e8f0"]

        if self.view_mode == "Monthly Trends":
            clean_df["dt"] = pd.to_datetime(clean_df["date"], errors="coerce")
            valid_dt_df = clean_df.dropna(subset=["dt"]).copy()

            if valid_dt_df.empty:
                self.show_empty_message("// NO VALID CHRONO-DATA")
                return

            valid_dt_df["month_period"] = valid_dt_df["dt"].dt.to_period("M")
            unique_months = sorted(valid_dt_df["month_period"].unique())
            month_labels = [m.strftime("%b %Y") for m in unique_months]
            x_indices = list(range(len(unique_months)))

            exp_df = valid_dt_df[valid_dt_df["type"] == "Expense"]
            exp_map = exp_df.groupby("month_period")["amount"].sum().to_dict()
            exp_vals = [float(exp_map.get(m, 0.0)) for m in unique_months]

            inc_df = valid_dt_df[valid_dt_df["type"] == "Income"]
            inc_map = inc_df.groupby("month_period")["amount"].sum().to_dict()
            inc_vals = [float(inc_map.get(m, 0.0)) for m in unique_months]

            avg_exp = sum(exp_vals) / len(exp_vals) if exp_vals else 0
            avg_inc = sum(inc_vals) / len(inc_vals) if inc_vals else 0
            self.highlight_lbl.configure(text=f"// AVG/MO: OUTFLOW {currency}{avg_exp:,.0f} | INFLOW {currency}{avg_inc:,.0f}")

            self.render_line_graph(
                ax=self.ax_left, x_indices=x_indices, y_values=exp_vals, labels=month_labels,
                title="MONTHLY OUTFLOW FLOW", color="#f43f5e", currency=currency
            )
            self.render_line_graph(
                ax=self.ax_right, x_indices=x_indices, y_values=inc_vals, labels=month_labels,
                title="MONTHLY INFLOW RESERVE", color="#10b981", currency=currency
            )
            self.canvas_widget.draw()
            return

        elif self.view_mode == "Accounts":
            acc_series = clean_df["account"] if "account" in clean_df.columns else pd.Series(["Bank"] * len(clean_df))
            acc_totals = clean_df.groupby(acc_series)["amount"].sum().sort_values(ascending=True)

            if acc_totals.empty or acc_totals.sum() <= 0:
                self.show_empty_message("// NO ACCOUNT VOLUME DETECTED")
                return

            top_acc = acc_totals.idxmax()
            self.highlight_lbl.configure(text=f"⭐ PRIMARY: {top_acc} ({currency}{acc_totals.max():,.0f})")

            bar_data = acc_totals
            pie_data = acc_totals
            bar_title = f"VAULT DISTRIBUTION ({currency})"
            pie_title = f"PORTFOLIO SHARE ({self.pie_type})"
            bar_colors = ["#38bdf8" if a != top_acc else "#f59e0b" for a in bar_data.index]
            is_currency_bar = True

        elif self.view_mode == "Payment Modes":
            mode_series = clean_df["payment_mode"] if "payment_mode" in clean_df.columns else pd.Series(["UPI"] * len(clean_df))
            bar_data = mode_series.value_counts(ascending=True)

            if bar_data.empty or bar_data.sum() <= 0:
                self.show_empty_message("// NO CONDUIT DATA")
                return

            top_mode = bar_data.idxmax()
            top_count = bar_data.max()
            self.highlight_lbl.configure(text=f"⭐ LEADING CHANNEL: {top_mode} ({top_count} txs)")

            pie_data = clean_df.groupby("payment_mode")["amount"].sum()
            bar_title = "TRANSACTION FREQUENCY"
            pie_title = f"CONDUIT VOLUME ({self.pie_type})"
            bar_colors = ["#6366f1" if m != top_mode else "#10b981" for m in bar_data.index]
            is_currency_bar = False

        else:
            target_type = "Expense" if self.view_mode == "Expenses" else "Income"
            self.highlight_lbl.configure(text="")
            filtered_df = clean_df[clean_df["type"] == target_type]

            if filtered_df.empty:
                self.show_empty_message(f"// NO {target_type.upper()} TELEMETRY")
                return

            cat_totals = filtered_df.groupby("category")["amount"].sum().sort_values(ascending=True)
            if cat_totals.empty or cat_totals.sum() <= 0:
                self.show_empty_message(f"// NO {target_type.upper()} VOLUME")
                return

            bar_data = cat_totals
            pie_data = cat_totals
            bar_title = f"{target_type.upper()} ALLOCATION"
            pie_title = f"{target_type.upper()} SHARE ({self.pie_type})"
            solid_color = "#f43f5e" if target_type == "Expense" else "#10b981"
            bar_colors = [solid_color] * len(bar_data)
            is_currency_bar = True

        self.render_bar_and_pie(bar_data, pie_data, bar_colors, bar_title, pie_title, currency, is_currency_bar, palette)
        self.canvas_widget.draw()

    def render_line_graph(self, ax, x_indices, y_values, labels, title, color, currency):
        ax.set_facecolor('#111625')
        if len(x_indices) == 1:
            ax.scatter(x_indices, y_values, color=color, s=50, zorder=5)
            ax.set_xlim(-0.5, 0.5)
        else:
            ax.plot(x_indices, y_values, color=color, marker='o', linewidth=2.2, markersize=5, zorder=4)
            ax.fill_between(x_indices, y_values, color=color, alpha=0.15)
            ax.set_xlim(-0.3, len(x_indices) - 0.7)

        ax.set_xticks(x_indices)
        ax.set_xticklabels(labels, rotation=22, ha='right', color='#94a3b8', fontsize=8, fontfamily="sans-serif")
        ax.set_title(title, color="#f8fafc", fontsize=10, weight="bold", fontfamily="monospace", pad=8)
        ax.tick_params(colors="#64748b", labelsize=8)

        y_max = max(y_values) if y_values and max(y_values) > 0 else 1.0
        ax.set_ylim(0, y_max * 1.30)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#1e263b')
        ax.spines['bottom'].set_color('#1e263b')
        ax.grid(True, color="#1a2030", linestyle="--", alpha=0.5)

        for x, y in zip(x_indices, y_values):
            if y > 0:
                ax.text(x, y + (y_max * 0.035), f"{currency}{y:,.0f}", ha='center', va='bottom', color='#f8fafc', fontsize=8, weight='bold', fontfamily="monospace")

    def render_bar_and_pie(self, bar_data, pie_data, bar_colors, bar_title, pie_title, currency, is_currency_bar, palette):
        y_positions = list(range(len(bar_data)))
        bar_height = 0.45 if len(bar_data) == 1 else 0.52
        bars = self.ax_left.barh(y_positions, bar_data.values, color=bar_colors, height=bar_height)

        self.ax_left.set_yticks(y_positions)
        self.ax_left.set_yticklabels(list(bar_data.index), color="#cbd5e1", fontsize=8.5, weight="bold")
        self.ax_left.set_title(bar_title, color="#f8fafc", fontsize=10, weight="bold", fontfamily="monospace", pad=8)
        self.ax_left.tick_params(colors="#64748b", labelsize=8.5)

        max_val = float(bar_data.max()) if not bar_data.empty else 1.0
        self.ax_left.set_xlim(0, max_val * 1.30)
        self.ax_left.spines['top'].set_visible(False)
        self.ax_left.spines['right'].set_visible(False)
        self.ax_left.spines['left'].set_color('#1e263b')
        self.ax_left.spines['bottom'].set_color('#1e263b')
        self.ax_left.grid(axis="x", color="#1a2030", linestyle="--", alpha=0.5)

        for bar, orig_val in zip(bars, bar_data.values):
            w = bar.get_width()
            label_str = f"{currency}{orig_val:,.0f}" if is_currency_bar else f"{int(orig_val)}"
            self.ax_left.text(
                w + (max_val * 0.03), bar.get_y() + bar.get_height() / 2, label_str,
                ha='left', va='center', color='#f8fafc', fontsize=8, weight="bold", fontfamily="monospace"
            )

        pie_data = pie_data[pie_data > 0]
        if not pie_data.empty:
            self.ax_right.set_aspect('equal')
            explode = [0.06] * len(pie_data) if (self.pie_type == "Exploded" and len(pie_data) > 1) else None
            slice_colors = (palette * ((len(pie_data) // len(palette)) + 1))[:len(pie_data)]

            wprops = dict(width=0.46, edgecolor='#111625', linewidth=2) if self.pie_type == "Donut" else dict(edgecolor='#111625', linewidth=1.5)

            # Direct unpacking handles both older tuple returns and newer PieContainer objects
            wedges, texts, autotexts = self.ax_right.pie(
                list(pie_data.values), labels=list(pie_data.index), autopct='%1.0f%%',
                startangle=140, explode=explode, colors=slice_colors, wedgeprops=wprops,
                textprops=dict(color="#cbd5e1", fontsize=8, weight="bold"),
                pctdistance=0.74 if self.pie_type == "Donut" else 0.60
            )

            for at in autotexts:
                at.set_color("#000000")
                at.set_weight("bold")
                at.set_fontsize(7.5)

            self.ax_right.set_title(pie_title, color="#f8fafc", fontsize=10, weight="bold", fontfamily="monospace", pad=8)

    def show_empty_message(self, message):
        self.highlight_lbl.configure(text="")
        self.ax_left.clear()
        self.ax_right.clear()
        self.ax_left.set_facecolor('#111625')
        self.ax_right.set_facecolor('#111625')
        self.ax_left.text(0.5, 0.5, message, ha='center', va='center', color='#64748b', fontsize=10, fontfamily="monospace", transform=self.ax_left.transAxes)
        self.ax_right.text(0.5, 0.5, "// AWAITING LEDGER ENTRIES", ha='center', va='center', color='#475569', fontsize=10, fontfamily="monospace", transform=self.ax_right.transAxes)
        self.ax_left.axis('off')
        self.ax_right.axis('off')
        self.canvas_widget.draw()
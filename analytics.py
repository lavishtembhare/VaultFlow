import math
from collections import defaultdict
from datetime import datetime
import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def _compact_axis_formatter(val, _pos):
    """Formats Y-axis ticks cleanly (e.g. 15M / 50K) instead of 1e7 scientific notation."""
    abs_v = abs(val)
    sign = "-" if val < 0 else ""
    if abs_v >= 1_000_000_000:
        return f"{sign}{abs_v / 1_000_000_000:.1f}B"
    if abs_v >= 1_000_000:
        return f"{sign}{abs_v / 1_000_000:.1f}M"
    if abs_v >= 1_000:
        return f"{sign}{abs_v / 1_000:.0f}K"
    return f"{sign}{abs_v:.0f}"


class AnalyticsView(ctk.CTkFrame):
    def __init__(self, parent, on_style_change=None):
        super().__init__(parent, corner_radius=14, fg_color="#111625", border_width=1, border_color="#1e293b")
        self.view_mode = "Accounts"
        self.pie_type = "Donut"
        self.on_style_change = on_style_change

        # 1. Top Control Bar (Scaled for 1920x1080)
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=24, pady=(18, 10))

        self.mode_toggle = ctk.CTkSegmentedButton(
            top_bar,
            values=["Accounts", "Expenses", "Incomes", "Monthly Trends", "Payment Modes"],
            command=self.change_view_mode,
            height=36,
            selected_color="#38bdf8",
            selected_hover_color="#0284c7",
            text_color="#f8fafc",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.mode_toggle.set("Accounts")
        self.mode_toggle.pack(side="left")

        self.highlight_lbl = ctk.CTkLabel(
            top_bar, text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f59e0b"
        )
        self.highlight_lbl.pack(side="left", padx=20)

        self.pie_selector = ctk.CTkSegmentedButton(
            top_bar,
            values=["Donut", "Classic Pie", "Exploded"],
            command=self.change_pie_type,
            height=36,
            selected_color="#2563eb",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.pie_selector.set("Donut")
        self.pie_selector.pack(side="right")

        # 2. Remaining Account Balances Strip (Bank, Portfolio, Cash)
        self.balance_strip = ctk.CTkFrame(self, fg_color="transparent")
        self.balance_strip.pack(fill="x", padx=18, pady=(2, 8))
        self.balance_strip.grid_columnconfigure((0, 1, 2), weight=1)

        self.bank_val_lbl = self._create_account_pill(
            self.balance_strip, col=0, title="🏦   Bank Balance Left", default_color="#38bdf8"
        )
        self.portfolio_val_lbl = self._create_account_pill(
            self.balance_strip, col=1, title="📈   Portfolio Balance Left", default_color="#f59e0b"
        )
        self.cash_val_lbl = self._create_account_pill(
            self.balance_strip, col=2, title="💵   Cash Balance Left", default_color="#10b981"
        )

        # 3. 1080p Widescreen Matplotlib Dual Chart Canvas
        self.fig, (self.ax_left, self.ax_right) = plt.subplots(1, 2, figsize=(13.6, 5.6), dpi=100)
        self.fig.patch.set_facecolor('#111625')
        self.fig.subplots_adjust(left=0.07, right=0.97, top=0.88, bottom=0.16, wspace=0.22)

        self.canvas_widget = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget.get_tk_widget().pack(fill="both", expand=True, padx=16, pady=(4, 16))

    def _create_account_pill(self, parent, col, title, default_color):
        pill = ctk.CTkFrame(
            parent, fg_color="#0c101b", corner_radius=10,
            border_width=1, border_color="#1e293b"
        )
        pill.grid(row=0, column=col, sticky="ew", padx=6, pady=2)

        ctk.CTkLabel(
            pill, text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8"
        ).pack(side="left", padx=18, pady=12)

        val_lbl = ctk.CTkLabel(
            pill, text="$0.00",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=default_color
        )
        val_lbl.pack(side="right", padx=18, pady=12)
        return val_lbl

    def change_view_mode(self, value):
        self.view_mode = value
        if self.on_style_change:
            self.on_style_change()

    def change_pie_type(self, value):
        self.pie_type = value
        if self.on_style_change:
            self.on_style_change()

    def _update_account_balances_strip(self, df: pd.DataFrame, currency: str) -> dict:
        """Computes net remaining balance (Income - Expense) per account in O(n) time."""
        net_balances = {
            "Bank": 0.0,
            "Portfolio": 0.0,
            "Cash": 0.0
        }

        if df is not None and not df.empty:
            accounts_col = df["account"] if "account" in df.columns else ["Bank"] * len(df)
            for tx_type, acc, raw_amt in zip(df["type"], accounts_col, df["amount"]):
                try:
                    amt = float(raw_amt)
                except (ValueError, TypeError):
                    continue
                if amt <= 0:
                    continue

                acc_name = str(acc).strip() if pd.notna(acc) and str(acc).strip() else "Bank"
                if acc_name not in net_balances:
                    net_balances[acc_name] = 0.0

                if tx_type == "Income":
                    net_balances[acc_name] += amt
                else:
                    net_balances[acc_name] -= amt

        for acc_key, lbl, pos_color in (
            ("Bank", self.bank_val_lbl, "#38bdf8"),
            ("Portfolio", self.portfolio_val_lbl, "#f59e0b"),
            ("Cash", self.cash_val_lbl, "#10b981")
        ):
            bal = net_balances.get(acc_key, 0.0)
            sign = "-" if bal < 0 else ""
            lbl.configure(
                text=f"{sign}{currency}{abs(bal):,.2f}",
                text_color="#f43f5e" if bal < 0 else pos_color
            )

        return net_balances

    def render_charts(self, df: pd.DataFrame, currency: str, animate=False):
        self.ax_left.clear()
        self.ax_right.clear()
        self.ax_left.set_facecolor('#111625')
        self.ax_right.set_facecolor('#111625')

        net_balances = self._update_account_balances_strip(df, currency)

        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            self.show_empty_message("No transactions logged yet")
            return

        palette = ["#38bdf8", "#f59e0b", "#10b981", "#818cf8", "#c084fc", "#fb7185", "#2dd4bf", "#e2e8f0"]

        if self.view_mode == "Accounts":
            bar_labels = []
            bar_values = []
            for acc_name, bal in net_balances.items():
                if acc_name in ("Bank", "Portfolio", "Cash") or abs(bal) > 0:
                    bar_labels.append(acc_name)
                    bar_values.append(bal)

            top_acc = None
            top_val = float("-inf")
            for k, v in zip(bar_labels, bar_values):
                if v > top_val:
                    top_val = v
                    top_acc = k

            total_left = sum(bar_values)
            sign_str = "-" if total_left < 0 else ""
            self.highlight_lbl.configure(
                text=f"Total Net Left: {sign_str}{currency}{abs(total_left):,.0f}   |   Highest: {top_acc} ({currency}{top_val:,.0f})"
            )

            acc_color_map = {"Bank": "#38bdf8", "Portfolio": "#f59e0b", "Cash": "#10b981"}
            bar_colors = [
                "#f43f5e" if val < 0 else acc_color_map.get(lbl, "#818cf8")
                for lbl, val in zip(bar_labels, bar_values)
            ]

            pie_labels = [lbl for lbl, val in zip(bar_labels, bar_values) if val > 0]
            pie_values = [val for val in bar_values if val > 0]

            self.render_net_balance_charts(
                bar_labels, bar_values, pie_labels, pie_values,
                bar_colors, f"Remaining Balance ({currency})", f"Remaining Share ({self.pie_type})",
                currency, palette
            )
            self.canvas_widget.draw()
            return

        elif self.view_mode == "Monthly Trends":
            exp_map = defaultdict(float)
            inc_map = defaultdict(float)
            months_in_desc_order = []
            seen_months = set()

            for dt_str, tx_type, raw_amt in zip(df["date"], df["type"], df["amount"]):
                try:
                    amt = float(raw_amt)
                except (ValueError, TypeError):
                    continue
                if amt <= 0 or not dt_str:
                    continue

                ym = str(dt_str)[:7]
                if len(ym) != 7 or ym[4] != "-":
                    continue

                if ym not in seen_months:
                    seen_months.add(ym)
                    months_in_desc_order.append(ym)

                if tx_type == "Expense":
                    exp_map[ym] += amt
                elif tx_type == "Income":
                    inc_map[ym] += amt

            if not months_in_desc_order:
                self.show_empty_message("No valid chronological data")
                return

            unique_months = months_in_desc_order[::-1]
            month_labels = []
            for ym in unique_months:
                try:
                    dt_obj = datetime.strptime(ym, "%Y-%m")
                    month_labels.append(dt_obj.strftime("%b %Y"))
                except ValueError:
                    month_labels.append(ym)

            x_indices = list(range(len(unique_months)))
            exp_vals = [exp_map[m] for m in unique_months]
            inc_vals = [inc_map[m] for m in unique_months]

            avg_exp = sum(exp_vals) / len(exp_vals) if exp_vals else 0.0
            avg_inc = sum(inc_vals) / len(inc_vals) if inc_vals else 0.0
            self.highlight_lbl.configure(
                text=f"Monthly Avg  •  Outflow: {currency}{avg_exp:,.0f}   |   Inflow: {currency}{avg_inc:,.0f}"
            )

            self.render_line_graph(
                ax=self.ax_left, x_indices=x_indices, y_values=exp_vals, labels=month_labels,
                title="Monthly Outflow Trend", color="#f43f5e", currency=currency
            )
            self.render_line_graph(
                ax=self.ax_right, x_indices=x_indices, y_values=inc_vals, labels=month_labels,
                title="Monthly Inflow Trend", color="#10b981", currency=currency
            )
            self.canvas_widget.draw()
            return

        elif self.view_mode == "Payment Modes":
            mode_counts = defaultdict(int)
            mode_volume = defaultdict(float)
            top_mode = None
            top_count = -1

            modes_col = df["payment_mode"] if "payment_mode" in df.columns else ["UPI"] * len(df)
            for mode, raw_amt in zip(modes_col, df["amount"]):
                try:
                    amt = float(raw_amt)
                except (ValueError, TypeError):
                    continue
                if amt <= 0:
                    continue
                m_name = str(mode) if pd.notna(mode) and str(mode).strip() else "UPI"
                c = mode_counts[m_name] + 1
                mode_counts[m_name] = c
                mode_volume[m_name] += amt
                if c > top_count:
                    top_count = c
                    top_mode = m_name

            if not mode_counts:
                self.show_empty_message("No payment mode data available")
                return

            self.highlight_lbl.configure(text=f"Leading Channel: {top_mode} ({top_count} transactions)")
            bar_labels = list(mode_counts.keys())
            bar_values = list(mode_counts.values())
            pie_labels = list(mode_volume.keys())
            pie_values = list(mode_volume.values())
            bar_title = "Transaction Frequency"
            pie_title = f"Channel Volume ({self.pie_type})"
            bar_colors = ["#6366f1" if m != top_mode else "#10b981" for m in bar_labels]
            is_currency_bar = False

        else:
            target_type = "Expense" if self.view_mode == "Expenses" else "Income"
            self.highlight_lbl.configure(text="")
            cat_totals = defaultdict(float)

            for tx_type, cat, raw_amt in zip(df["type"], df["category"], df["amount"]):
                if tx_type != target_type:
                    continue
                try:
                    amt = float(raw_amt)
                except (ValueError, TypeError):
                    continue
                if amt <= 0:
                    continue
                c_name = str(cat) if pd.notna(cat) and str(cat).strip() else "Other"
                cat_totals[c_name] += amt

            if not cat_totals:
                self.show_empty_message(f"No {target_type.lower()} records found")
                return

            bar_labels = list(cat_totals.keys())
            bar_values = list(cat_totals.values())
            pie_labels = bar_labels
            pie_values = bar_values
            bar_title = f"{target_type} Allocation"
            pie_title = f"{target_type} Share ({self.pie_type})"
            solid_color = "#f43f5e" if target_type == "Expense" else "#10b981"
            bar_colors = [solid_color] * len(bar_labels)
            is_currency_bar = True

        self.render_bar_and_pie(
            bar_labels, bar_values, pie_labels, pie_values,
            bar_colors, bar_title, pie_title, currency, is_currency_bar, palette
        )
        self.canvas_widget.draw()

    def render_net_balance_charts(self, bar_labels, bar_values, pie_labels, pie_values, bar_colors, bar_title, pie_title, currency, palette):
        x_positions = list(range(len(bar_labels)))
        bar_width = 0.36 if len(bar_labels) <= 3 else 0.46

        min_val = float(min(bar_values)) if bar_values else 0.0
        max_val = float(max(bar_values)) if bar_values else 1.0
        span = max(abs(min_val), abs(max_val), 1.0)

        min_visual_height = span * 0.06
        plotted_values = [
            math.copysign(max(abs(v), min_visual_height), v) if v != 0 else 0.0
            for v in bar_values
        ]

        bars = self.ax_left.bar(x_positions, plotted_values, color=bar_colors, width=bar_width, zorder=3)

        self.ax_left.set_xticks(x_positions)
        rot = 16 if len(bar_labels) > 5 else 0
        ha_align = "right" if rot > 0 else "center"
        self.ax_left.set_xticklabels(bar_labels, rotation=rot, ha=ha_align, color="#cbd5e1", fontsize=10.5, weight="bold")
        self.ax_left.set_title(bar_title, color="#f8fafc", fontsize=12.5, weight="bold", pad=14)
        self.ax_left.tick_params(colors="#64748b", labelsize=10)
        self.ax_left.yaxis.set_major_formatter(FuncFormatter(_compact_axis_formatter))

        bottom_bound = (min(plotted_values) - span * 0.25) if min_val < 0 else 0.0
        top_bound = (max(plotted_values) + span * 0.25) if max_val > 0 else (span * 0.25)
        if bottom_bound == top_bound:
            top_bound = 1.0
        self.ax_left.set_ylim(bottom_bound, top_bound)

        if min_val < 0:
            self.ax_left.axhline(0, color="#475569", linewidth=1, linestyle="-", zorder=2)

        self.ax_left.spines['top'].set_visible(False)
        self.ax_left.spines['right'].set_visible(False)
        self.ax_left.spines['left'].set_color('#1e293b')
        self.ax_left.spines['bottom'].set_color('#1e293b')
        self.ax_left.grid(axis="y", color="#1a2234", linestyle="--", alpha=0.5, zorder=0)

        for bar, orig_val, plot_val in zip(bars, bar_values, plotted_values):
            sign = "-" if orig_val < 0 else ""
            label_str = f"{sign}{currency}{abs(orig_val):,.0f}"
            offset = span * 0.03 if orig_val >= 0 else -(span * 0.04)
            va_align = 'bottom' if orig_val >= 0 else 'top'
            self.ax_left.text(
                bar.get_x() + bar.get_width() / 2,
                plot_val + offset,
                label_str,
                ha='center', va=va_align,
                color='#f43f5e' if orig_val < 0 else '#f8fafc',
                fontsize=10, weight="bold"
            )

        if pie_values:
            self.ax_right.set_aspect('equal')
            explode = [0.06] * len(pie_values) if (self.pie_type == "Exploded" and len(pie_values) > 1) else None
            acc_color_map = {"Bank": "#38bdf8", "Portfolio": "#f59e0b", "Cash": "#10b981"}
            slice_colors = [acc_color_map.get(lbl, palette[i % len(palette)]) for i, lbl in enumerate(pie_labels)]

            wprops = dict(width=0.46, edgecolor='#111625', linewidth=2.5) if self.pie_type == "Donut" else dict(edgecolor='#111625', linewidth=1.8)

            wedges, texts, autotexts = self.ax_right.pie(
                pie_values, labels=pie_labels, autopct='%1.0f%%',
                startangle=140, explode=explode, colors=slice_colors, wedgeprops=wprops,
                textprops=dict(color="#cbd5e1", fontsize=10, weight="bold"),
                pctdistance=0.74 if self.pie_type == "Donut" else 0.60
            )

            for at in autotexts:
                at.set_color("#090d16")
                at.set_weight("bold")
                at.set_fontsize(9.5)

            self.ax_right.set_title(pie_title, color="#f8fafc", fontsize=12.5, weight="bold", pad=14)
        else:
            self.ax_right.text(
                0.5, 0.5, "No positive account balances yet\n(Log an Income to see share)",
                ha='center', va='center', color='#64748b', fontsize=11,
                transform=self.ax_right.transAxes
            )
            self.ax_right.axis('off')

    def render_line_graph(self, ax, x_indices, y_values, labels, title, color, currency):
        ax.set_facecolor('#111625')
        if len(x_indices) == 1:
            ax.scatter(x_indices, y_values, color=color, s=65, zorder=5)
            ax.set_xlim(-0.5, 0.5)
        else:
            ax.plot(x_indices, y_values, color=color, marker='o', linewidth=2.6, markersize=6, zorder=4)
            ax.fill_between(x_indices, y_values, color=color, alpha=0.15)
            ax.set_xlim(-0.3, len(x_indices) - 0.7)

        ax.set_xticks(x_indices)
        ax.set_xticklabels(labels, rotation=20, ha='right', color='#94a3b8', fontsize=10)
        ax.set_title(title, color="#f8fafc", fontsize=12.5, weight="bold", pad=14)
        ax.tick_params(colors="#64748b", labelsize=10)
        ax.yaxis.set_major_formatter(FuncFormatter(_compact_axis_formatter))

        y_max = max(y_values) if y_values and max(y_values) > 0 else 1.0
        ax.set_ylim(0, y_max * 1.28)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#1e293b')
        ax.spines['bottom'].set_color('#1e293b')
        ax.grid(True, color="#1a2234", linestyle="--", alpha=0.5)

        for x, y in zip(x_indices, y_values):
            if y > 0:
                ax.text(x, y + (y_max * 0.035), f"{currency}{y:,.0f}", ha='center', va='bottom', color='#f8fafc', fontsize=9.5, weight='bold')

    def render_bar_and_pie(self, bar_labels, bar_values, pie_labels, pie_values, bar_colors, bar_title, pie_title, currency, is_currency_bar, palette):
        x_positions = list(range(len(bar_labels)))
        bar_width = 0.36 if len(bar_labels) <= 3 else 0.48

        max_val = float(max(bar_values)) if bar_values else 1.0
        min_visual_height = max_val * 0.05
        plotted_values = [max(float(v), min_visual_height) if v > 0 else 0.0 for v in bar_values]

        bars = self.ax_left.bar(x_positions, plotted_values, color=bar_colors, width=bar_width, zorder=3)

        self.ax_left.set_xticks(x_positions)
        rot = 18 if len(bar_labels) > 4 else 0
        ha_align = "right" if rot > 0 else "center"
        self.ax_left.set_xticklabels(bar_labels, rotation=rot, ha=ha_align, color="#cbd5e1", fontsize=10, weight="bold")
        self.ax_left.set_title(bar_title, color="#f8fafc", fontsize=12.5, weight="bold", pad=14)
        self.ax_left.tick_params(colors="#64748b", labelsize=10)

        if is_currency_bar:
            self.ax_left.yaxis.set_major_formatter(FuncFormatter(_compact_axis_formatter))

        self.ax_left.set_ylim(0, max_val * 1.28)
        self.ax_left.spines['top'].set_visible(False)
        self.ax_left.spines['right'].set_visible(False)
        self.ax_left.spines['left'].set_color('#1e293b')
        self.ax_left.spines['bottom'].set_color('#1e293b')
        self.ax_left.grid(axis="y", color="#1a2234", linestyle="--", alpha=0.5, zorder=0)

        for bar, orig_val, plot_val in zip(bars, bar_values, plotted_values):
            label_str = f"{currency}{orig_val:,.0f}" if is_currency_bar else f"{int(orig_val)}"
            self.ax_left.text(
                bar.get_x() + bar.get_width() / 2,
                plot_val + (max_val * 0.03),
                label_str,
                ha='center', va='bottom', color='#f8fafc', fontsize=9.5, weight="bold"
            )

        if pie_values:
            self.ax_right.set_aspect('equal')
            explode = [0.06] * len(pie_values) if (self.pie_type == "Exploded" and len(pie_values) > 1) else None
            slice_colors = (palette * ((len(pie_values) // len(palette)) + 1))[:len(pie_values)]

            wprops = dict(width=0.46, edgecolor='#111625', linewidth=2.5) if self.pie_type == "Donut" else dict(edgecolor='#111625', linewidth=1.8)

            wedges, texts, autotexts = self.ax_right.pie(
                pie_values, labels=pie_labels, autopct='%1.0f%%',
                startangle=140, explode=explode, colors=slice_colors, wedgeprops=wprops,
                textprops=dict(color="#cbd5e1", fontsize=10, weight="bold"),
                pctdistance=0.74 if self.pie_type == "Donut" else 0.60
            )

            for at in autotexts:
                at.set_color("#090d16")
                at.set_weight("bold")
                at.set_fontsize(9.5)

            self.ax_right.set_title(pie_title, color="#f8fafc", fontsize=12.5, weight="bold", pad=14)

    def show_empty_message(self, message):
        self.highlight_lbl.configure(text="")
        self.ax_left.clear()
        self.ax_right.clear()
        self.ax_left.set_facecolor('#111625')
        self.ax_right.set_facecolor('#111625')
        self.ax_left.text(0.5, 0.5, message, ha='center', va='center', color='#64748b', fontsize=12, transform=self.ax_left.transAxes)
        self.ax_right.text(0.5, 0.5, "Add or import transactions to view analytics", ha='center', va='center', color='#475569', fontsize=11.5, transform=self.ax_right.transAxes)
        self.ax_left.axis('off')
        self.ax_right.axis('off')
        self.canvas_widget.draw()
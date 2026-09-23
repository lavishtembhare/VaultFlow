import os
import sqlite3
from datetime import datetime
import pandas as pd

DEFAULT_EXPORT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")

def format_currency_amount(amount, currency="$", format_style="Millions / Billions", compact_enabled=False):
    """Formats numeric values into Standard, Millions, or Lakhs/Crores notations."""
    if not compact_enabled or format_style == "Standard":
        return f"{currency}{amount:,.2f}"

    abs_amt = abs(amount)
    sign = "-" if amount < 0 else ""

    if format_style == "Millions / Billions":
        if abs_amt >= 1_000_000_000:
            return f"{sign}{currency}{abs_amt / 1_000_000_000:.2f}B"
        elif abs_amt >= 1_000_000:
            return f"{sign}{currency}{abs_amt / 1_000_000:.2f}M"
        elif abs_amt >= 1_000:
            return f"{sign}{currency}{abs_amt / 1_000:.2f}K"
        else:
            return f"{sign}{currency}{abs_amt:,.2f}"

    elif format_style == "Lakhs / Crores":
        if abs_amt >= 10_000_000:
            return f"{sign}{currency}{abs_amt / 10_000_000:.2f} Cr"
        elif abs_amt >= 100_000:
            return f"{sign}{currency}{abs_amt / 100_000:.2f} Lakh"
        elif abs_amt >= 1_000:
            return f"{sign}{currency}{abs_amt / 1_000:.2f} K"
        else:
            return f"{sign}{currency}{abs_amt:,.2f}"

    return f"{currency}{amount:,.2f}"


def parse_amount(amt_str, allow_shorthand=False):
    """Parses standard numbers and optional shorthand suffixes."""
    amt_str = amt_str.strip().lower().replace(",", "")
    if not amt_str:
        raise ValueError("Please enter an amount.")

    if allow_shorthand:
        multipliers = {
            'crores': 10_000_000, 'crore': 10_000_000, 'cr': 10_000_000,
            'billions': 1_000_000_000, 'billion': 1_000_000_000, 'b': 1_000_000_000,
            'millions': 1_000_000, 'million': 1_000_000, 'm': 1_000_000,
            'lakhs': 100_000, 'lakh': 100_000, 'lacs': 100_000, 'lac': 100_000, 'l': 100_000,
            'thousands': 1_000, 'thousand': 1_000, 'k': 1_000
        }
        for suffix, mult in sorted(multipliers.items(), key=lambda x: -len(x[0])):
            if amt_str.endswith(suffix):
                num_part = amt_str[:-len(suffix)].strip()
                try:
                    val = float(num_part) * mult
                except ValueError:
                    raise ValueError(f"Invalid numeric input before '{suffix}': {num_part}")
                if val <= 0:
                    raise ValueError("Amount must be greater than zero.")
                return val

    try:
        val = float(amt_str)
    except ValueError:
        raise ValueError("Invalid number. Only numeric digits (0-9) and a decimal point are permitted.")

    if val <= 0:
        raise ValueError("Amount must be greater than zero.")
    return val


class DatabaseManager:
    """Handles SQLite storage for transactions, categories, accounts, and settings."""
    def __init__(self, db_path="vaultflow.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    payment_mode TEXT NOT NULL DEFAULT 'UPI',
                    account TEXT NOT NULL DEFAULT 'Bank',
                    amount REAL NOT NULL,
                    description TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'Expense',
                    UNIQUE(name, type)
                )
            """)

            # Default categories
            expense_defaults = ["Food", "Bills", "Rent", "Shopping", "Transport", "Entertainment", "Healthcare", "Other"]
            for cat in expense_defaults:
                cursor.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'Expense')", (cat,))

            income_defaults = ["Salary", "Rent Received", "Freelance", "Revenue", "Investment", "Bonus", "Other"]
            for cat in income_defaults:
                cursor.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'Income')", (cat,))

            # Default Settings
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('currency', '$')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('compact_numbers', 'False')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('number_format', 'Millions / Billions')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('allow_shorthand', 'True')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('export_dir', ?)", (DEFAULT_EXPORT_PATH,))

            conn.commit()

    def add_transaction(self, tx_type, date, category, payment_mode, amount, description, account="Bank"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (type, date, category, payment_mode, account, amount, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (tx_type, date, category, payment_mode, account, amount, description)
            )
            conn.commit()

    def delete_transaction(self, tx_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
            conn.commit()

    def clear_all_transactions(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions")
            conn.commit()

    def import_transactions_from_dataframe(self, imported_df):
        col_map = {}
        for col in imported_df.columns:
            clean = str(col).strip().lower().replace("_", " ").replace("-", " ")
            if "date" in clean or "time" in clean: col_map["date"] = col
            elif "type" in clean: col_map["type"] = col
            elif "cat" in clean: col_map["category"] = col
            elif "acc" in clean or "credit" in clean or "debit" in clean: col_map["account"] = col
            elif "pay" in clean or "mode" in clean: col_map["payment_mode"] = col
            elif any(k in clean for k in ["amt", "amount", "price", "cost", "value"]): col_map["amount"] = col
            elif any(k in clean for k in ["desc", "note", "remark", "detail", "title"]): col_map["description"] = col

        if "amount" not in col_map:
            raise ValueError("Could not find an 'Amount' column in the uploaded file.")

        imported_count = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for _, row in imported_df.iterrows():
                try:
                    raw_amt = str(row[col_map["amount"]]).replace("$", "").replace("₹", "").replace("€", "").replace("£", "").replace(",", "").strip()
                    amt = float(raw_amt)
                    if amt == 0 or pd.isna(amt): continue
                except Exception:
                    continue

                if "type" in col_map and pd.notna(row[col_map["type"]]):
                    raw_type = str(row[col_map["type"]]).strip().capitalize()
                    tx_type = "Income" if any(x in raw_type.lower() for x in ["inc", "credit", "+"]) else "Expense"
                else:
                    tx_type = "Income" if amt < 0 else "Expense"

                amt = abs(amt)
                date_val = datetime.now().strftime("%Y-%m-%d %H:%M")
                if "date" in col_map and pd.notna(row[col_map["date"]]):
                    try:
                        parsed_dt = pd.to_datetime(row[col_map["date"]])
                        date_val = parsed_dt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        date_val = str(row[col_map["date"]]).strip()

                category = str(row[col_map["category"]]).strip() if "category" in col_map and pd.notna(row[col_map["category"]]) else "Other"
                account = str(row[col_map["account"]]).replace("📥 In:", "").replace("📤 From:", "").strip() if "account" in col_map and pd.notna(row[col_map["account"]]) else "Bank"
                payment_mode = str(row[col_map["payment_mode"]]).strip() if "payment_mode" in col_map and pd.notna(row[col_map["payment_mode"]]) else "UPI"
                desc = str(row[col_map["description"]]).strip() if "description" in col_map and pd.notna(row[col_map["description"]]) else ""

                cursor.execute(
                    "INSERT INTO transactions (type, date, category, payment_mode, account, amount, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (tx_type, date_val, category, payment_mode, account, amt, desc)
                )
                cursor.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)", (category, tx_type))
                imported_count += 1
            conn.commit()

        return imported_count

    def get_all_transactions(self):
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC, id DESC", conn)

    def get_filtered_transactions(self, start_date, end_date):
        with self.get_connection() as conn:
            query = """
                SELECT date, type, category, account, payment_mode, amount, description 
                FROM transactions 
                WHERE date BETWEEN ? AND ? 
                ORDER BY date ASC
            """
            return pd.read_sql_query(query, conn, params=(start_date, end_date))

    def get_categories(self, tx_type="Expense"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM categories WHERE type = ? ORDER BY name ASC", (tx_type,))
            rows = cursor.fetchall()
            return [r[0] for r in rows] if rows else ["Other"]

    def add_category(self, name, tx_type="Expense"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)", (name.strip(), tx_type))
            conn.commit()

    def delete_category(self, name, tx_type="Expense"):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM categories WHERE name = ? AND type = ?", (name.strip(), tx_type))
            conn.commit()

    def get_setting(self, key, default=""):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
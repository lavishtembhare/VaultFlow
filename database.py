import sqlite3
import pandas as pd

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
        if abs_amt >= 10_000_000:  # 1 Crore = 10,000,000
            return f"{sign}{currency}{abs_amt / 10_000_000:.2f} Cr"
        elif abs_amt >= 100_000:   # 1 Lakh = 100,000
            return f"{sign}{currency}{abs_amt / 100_000:.2f} Lakh"
        elif abs_amt >= 1_000:
            return f"{sign}{currency}{abs_amt / 1_000:.2f} K"
        else:
            return f"{sign}{currency}{abs_amt:,.2f}"

    return f"{currency}{amount:,.2f}"


def parse_amount(amt_str, allow_shorthand=False):
    """Parses standard numbers and optional shorthand suffixes (e.g. 5k, 7m, 2cr, 10lakh)."""
    amt_str = amt_str.strip().lower().replace(",", "")
    if not amt_str:
        raise ValueError("Please enter an amount.")

    if allow_shorthand:
        multipliers = {
            'crores': 10_000_000,
            'crore': 10_000_000,
            'cr': 10_000_000,
            'billions': 1_000_000_000,
            'billion': 1_000_000_000,
            'b': 1_000_000_000,
            'millions': 1_000_000,
            'million': 1_000_000,
            'm': 1_000_000,
            'lakhs': 100_000,
            'lakh': 100_000,
            'lacs': 100_000,
            'lac': 100_000,
            'l': 100_000,
            'thousands': 1_000,
            'thousand': 1_000,
            'k': 1_000
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
    """Handles SQLite storage for transactions, categories, and settings."""
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

            # Fix categories schema if needed
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='categories'")
            cat_meta = cursor.fetchone()
            if cat_meta:
                sql = cat_meta[0]
                if "name TEXT UNIQUE" in sql or "UNIQUE (name)" in sql or "UNIQUE(name)" in sql:
                    cursor.execute("PRAGMA table_info(categories)")
                    cols = [c[1] for c in cursor.fetchall()]
                    has_type = "type" in cols
                    if has_type:
                        cursor.execute("SELECT name, type FROM categories")
                        existing_cats = cursor.fetchall()
                    else:
                        cursor.execute("SELECT name FROM categories")
                        existing_cats = [(r[0], 'Expense') for r in cursor.fetchall()]

                    cursor.execute("DROP TABLE categories")
                    cursor.execute("""
                        CREATE TABLE categories (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            type TEXT NOT NULL DEFAULT 'Expense',
                            UNIQUE(name, type)
                        )
                    """)
                    for name, c_type in existing_cats:
                        cursor.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)", (name, c_type))
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL DEFAULT 'Expense',
                        UNIQUE(name, type)
                    )
                """)

            # Populate defaults
            expense_defaults = ["Food", "Bills", "Rent", "Shopping", "Transport", "Entertainment", "Healthcare", "Other"]
            for cat in expense_defaults:
                cursor.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'Expense')", (cat,))

            income_defaults = ["Salary", "Rent Received", "Freelance", "Revenue", "Investment", "Bonus", "Other"]
            for cat in income_defaults:
                cursor.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'Income')", (cat,))

            # Settings Defaults: Default strictly to False for allow_shorthand
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('currency', '$')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('compact_numbers', 'False')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('number_format', 'Millions / Billions')")
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('allow_shorthand', 'False')")
            
            # Reset any previously saved 'True' value to 'False' so existing databases use strict numeric mode
            cursor.execute("UPDATE settings SET value = 'False' WHERE key = 'allow_shorthand' AND value = 'True'")
            conn.commit()

    def add_transaction(self, tx_type, date, category, payment_mode, amount, description):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO transactions (type, date, category, payment_mode, amount, description) VALUES (?, ?, ?, ?, ?, ?)",
                (tx_type, date, category, payment_mode, amount, description)
            )
            conn.commit()

    def delete_transaction(self, tx_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
            conn.commit()

    def get_all_transactions(self):
        with self.get_connection() as conn:
            return pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC, id DESC", conn)

    def get_filtered_transactions(self, start_date, end_date):
        with self.get_connection() as conn:
            query = """
                SELECT date, type, category, payment_mode, amount, description 
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
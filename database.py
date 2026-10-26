import os
import sys
import sqlite3
from datetime import datetime
import pandas as pd

def get_app_dir() -> str:
    """Returns the folder containing the .exe (when frozen) or script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()
DEFAULT_EXPORT_PATH = os.path.join(APP_DIR, "exports")
DEFAULT_DB_PATH = os.path.join(APP_DIR, "vaultflow.db")

# Pre-sorted descending by suffix length once at import time -> O(1) lookup
SHORTHAND_MULTIPLIERS = (
    ('billions', 1_000_000_000), ('thousands', 1_000), ('millions', 1_000_000),
    ('billion', 1_000_000_000), ('thousand', 1_000), ('million', 1_000_000),
    ('crores', 10_000_000), ('crore', 10_000_000), ('lakhs', 100_000),
    ('lakh', 100_000), ('lacs', 100_000), ('lac', 100_000),
    ('cr', 10_000_000), ('b', 1_000_000_000), ('m', 1_000_000),
    ('l', 100_000), ('k', 1_000)
)


def format_currency_amount(amount, currency="$", format_style="Millions / Billions", compact_enabled=False):
    """Formats numeric values into Standard, Millions, or Lakhs/Crores notations in O(1)."""
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
        return f"{sign}{currency}{abs_amt:,.2f}"

    elif format_style == "Lakhs / Crores":
        if abs_amt >= 10_000_000:
            return f"{sign}{currency}{abs_amt / 10_000_000:.2f} Cr"
        elif abs_amt >= 100_000:
            return f"{sign}{currency}{abs_amt / 100_000:.2f} Lakh"
        elif abs_amt >= 1_000:
            return f"{sign}{currency}{abs_amt / 1_000:.2f} K"
        return f"{sign}{currency}{abs_amt:,.2f}"

    return f"{currency}{amount:,.2f}"


def parse_amount(amt_str, allow_shorthand=False):
    """Parses standard numbers and optional shorthand suffixes in O(1)."""
    amt_str = amt_str.strip().lower().replace(",", "")
    if not amt_str:
        raise ValueError("Please enter an amount.")

    if allow_shorthand:
        for suffix, mult in SHORTHAND_MULTIPLIERS:
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
    def __init__(self, db_path=DEFAULT_DB_PATH):
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
                CREATE INDEX IF NOT EXISTS idx_tx_date_id
                ON transactions (date DESC, id DESC)
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

            expense_defaults = [("Food",), ("Bills",), ("Rent",), ("Shopping",), ("Transport",), ("Entertainment",), ("Healthcare",), ("Other",)]
            cursor.executemany("INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'Expense')", expense_defaults)

            income_defaults = [("Salary",), ("Rent Received",), ("Freelance",), ("Revenue",), ("Investment",), ("Bonus",), ("Other",)]
            cursor.executemany("INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'Income')", income_defaults)

            default_settings = [
                ('currency', '$'),
                ('compact_numbers', 'False'),
                ('number_format', 'Millions / Billions'),
                ('allow_shorthand', 'True'),
                ('export_dir', DEFAULT_EXPORT_PATH)
            ]
            cursor.executemany("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", default_settings)
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

    def import_from_file(self, filepath: str) -> int:
        """Loads an Excel (.xlsx/.xls) or CSV file and imports records in O(n) time."""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        return self.import_transactions_from_dataframe(df)

    def import_transactions_from_dataframe(self, imported_df: pd.DataFrame) -> int:
        """O(n) single-pass bulk import using batched executemany."""
        if imported_df is None or imported_df.empty:
            return 0

        col_map = {}
        for idx, col in enumerate(imported_df.columns):
            clean = str(col).strip().lower().replace("_", " ").replace("-", " ")
            if ("date" in clean or "time" in clean) and "date" not in col_map:
                col_map["date"] = idx
            elif "type" in clean and "type" not in col_map:
                col_map["type"] = idx
            elif ("cat" in clean or "tag" in clean) and "category" not in col_map:
                col_map["category"] = idx
            elif ("acc" in clean or "credit" in clean or "debit" in clean) and "account" not in col_map:
                col_map["account"] = idx
            elif ("pay" in clean or "mode" in clean or "conduit" in clean) and "payment_mode" not in col_map:
                col_map["payment_mode"] = idx
            elif any(k in clean for k in ("amt", "amount", "price", "cost", "value")) and "amount" not in col_map:
                col_map["amount"] = idx
            elif any(k in clean for k in ("desc", "note", "remark", "detail", "title", "narration")) and "description" not in col_map:
                col_map["description"] = idx

        if "amount" not in col_map:
            raise ValueError("Could not find an 'Amount' column in the selected file.")

        amt_idx = col_map["amount"]
        type_idx = col_map.get("type")
        date_idx = col_map.get("date")
        cat_idx = col_map.get("category")
        acc_idx = col_map.get("account")
        pm_idx = col_map.get("payment_mode")
        desc_idx = col_map.get("description")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        tx_batch = []
        cat_batch = set()

        for row in imported_df.itertuples(index=False, name=None):
            raw_val = row[amt_idx]
            if pd.isna(raw_val):
                continue
            try:
                if isinstance(raw_val, (int, float)):
                    amt = float(raw_val)
                else:
                    cleaned_amt = (
                        str(raw_val)
                        .replace("$", "").replace("₹", "").replace("€", "")
                        .replace("£", "").replace("¥", "").replace(",", "").strip()
                    )
                    amt = float(cleaned_amt)
                if amt == 0:
                    continue
            except Exception:
                continue

            if type_idx is not None and pd.notna(row[type_idx]):
                raw_type = str(row[type_idx]).strip().lower()
                tx_type = "Income" if ("inc" in raw_type or "credit" in raw_type or "+" in raw_type) else "Expense"
            else:
                tx_type = "Income" if amt < 0 else "Expense"

            amt = abs(amt)

            date_val = now_str
            if date_idx is not None and pd.notna(row[date_idx]):
                cell_dt = row[date_idx]
                if hasattr(cell_dt, "strftime"):
                    date_val = cell_dt.strftime("%Y-%m-%d %H:%M")
                else:
                    raw_dt = str(cell_dt).strip()
                    if len(raw_dt) == 10 and raw_dt[4:5] == "-" and raw_dt[7:8] == "-":
                        date_val = f"{raw_dt} 00:00"
                    else:
                        date_val = raw_dt[:16] if len(raw_dt) >= 16 else raw_dt

            category = str(row[cat_idx]).strip() if (cat_idx is not None and pd.notna(row[cat_idx]) and str(row[cat_idx]).strip()) else "Other"
            account = (
                str(row[acc_idx]).replace("📥 In:", "").replace("📤 From:", "").strip()
                if (acc_idx is not None and pd.notna(row[acc_idx]) and str(row[acc_idx]).strip())
                else "Bank"
            )
            payment_mode = (
                str(row[pm_idx]).strip()
                if (pm_idx is not None and pd.notna(row[pm_idx]) and str(row[pm_idx]).strip())
                else "UPI"
            )
            desc = (
                str(row[desc_idx]).strip()
                if (desc_idx is not None and pd.notna(row[desc_idx]))
                else ""
            )

            tx_batch.append((tx_type, date_val, category, payment_mode, account, amt, desc))
            cat_batch.add((category, tx_type))

        if not tx_batch:
            return 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                "INSERT INTO transactions (type, date, category, payment_mode, account, amount, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                tx_batch
            )
            cursor.executemany(
                "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                list(cat_batch)
            )
            conn.commit()

        return len(tx_batch)

    def get_all_transactions(self):
        with self.get_connection() as conn:
            return pd.read_sql_query(
                "SELECT * FROM transactions INDEXED BY idx_tx_date_id ORDER BY date DESC, id DESC",
                conn
            )

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
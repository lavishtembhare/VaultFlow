import sqlite3
import pandas as pd

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
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'Expense',
                    UNIQUE(name, type)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Migration: Ensure payment_mode exists
            cursor.execute("PRAGMA table_info(transactions)")
            t_cols = [col[1] for col in cursor.fetchall()]
            if "payment_mode" not in t_cols:
                cursor.execute("ALTER TABLE transactions ADD COLUMN payment_mode TEXT DEFAULT 'UPI'")

            # Migration: Ensure type exists in categories
            cursor.execute("PRAGMA table_info(categories)")
            c_cols = [col[1] for col in cursor.fetchall()]
            if "type" not in c_cols:
                cursor.execute("ALTER TABLE categories ADD COLUMN type TEXT DEFAULT 'Expense'")

            # Default Expense Categories
            expense_defaults = ["Food", "Bills", "Rent", "Shopping", "Transport", "Entertainment", "Healthcare", "Other"]
            for cat in expense_defaults:
                cursor.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'Expense')", (cat,))

            # Default Income Categories
            income_defaults = ["Salary", "Rent Received", "Freelance", "Revenue", "Investment", "Bonus", "Other"]
            for cat in income_defaults:
                cursor.execute("INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'Income')", (cat,))

            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('currency', '$')")
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
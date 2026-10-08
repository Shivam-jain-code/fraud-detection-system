import sqlite3
from pathlib import Path

DB_NAME = Path(__file__).with_name("fraud_detection.db")

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                frequency INTEGER NOT NULL,
                country TEXT NOT NULL,
                login_country TEXT NOT NULL,
                tx_time TEXT NOT NULL,
                account_age INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

def save_transaction(data, risk_level, reason):
    with get_db_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO transactions
            (amount, frequency, country, login_country, tx_time, account_age, risk_level, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['amount'], data['frequency'], data['country'], data['login_country'],
              data['tx_time'], data['account_age'], risk_level, reason))
        return cursor.lastrowid

def get_all_transactions():
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM transactions ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]

def get_dashboard_stats():
    with get_db_connection() as conn:
        totals = {row['risk_level']: row['count'] for row in conn.execute(
            "SELECT risk_level, COUNT(*) AS count FROM transactions GROUP BY risk_level").fetchall()}
    total = sum(totals.values())
    fraud = totals.get('Fraud', 0)
    return {'total': total, 'safe': totals.get('Safe', 0), 'suspicious': totals.get('Suspicious', 0),
            'fraud': fraud, 'fraud_percentage': round((fraud / total) * 100, 2) if total else 0}

def get_analytics_data():
    with get_db_connection() as conn:
        country_rows = conn.execute("""
            SELECT country, COUNT(*) AS count FROM transactions
            WHERE risk_level = 'Fraud' GROUP BY country ORDER BY count DESC
        """).fetchall()
        daily_rows = conn.execute("""
            SELECT DATE(created_at) AS day, risk_level, COUNT(*) AS count FROM transactions
            GROUP BY DATE(created_at), risk_level ORDER BY day
        """).fetchall()
        amount_rows = conn.execute("SELECT amount, risk_level FROM transactions ORDER BY id").fetchall()
    return {'fraud_by_country': {row['country']: row['count'] for row in country_rows},
            'daily_stats': [dict(row) for row in daily_rows],
            'amounts': [dict(row) for row in amount_rows]}

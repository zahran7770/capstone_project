import sqlite3

DB_PATH = "finance.db"

def column_exists(cur, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table});")
    return col in [r[1] for r in cur.fetchall()]

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # transactions: add sentiment_score + sentiment_label if missing
    if not column_exists(cur, "transactions", "sentiment_score"):
        cur.execute("ALTER TABLE transactions ADD COLUMN sentiment_score FLOAT;")
    if not column_exists(cur, "transactions", "sentiment_label"):
        cur.execute("ALTER TABLE transactions ADD COLUMN sentiment_label VARCHAR(20);")

    # create feedback table if not exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sentiment_feedback (
        id INTEGER PRIMARY KEY,
        transaction_id INTEGER NOT NULL,
        predicted_label VARCHAR(20) NOT NULL,
        user_label VARCHAR(20) NOT NULL,
        is_correct INTEGER NOT NULL,
        created_at DATETIME,
        user_id INTEGER NOT NULL,
        FOREIGN KEY(transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    con.commit()
    con.close()
    print("✅ Sentiment migration applied.")

if __name__ == "__main__":
    main()
import sqlite3
from pathlib import Path

# Lokasi database
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "tiliek.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS berita (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sumber TEXT NOT NULL,
                judul TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                tanggal_terbit TEXT,
                ringkasan TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("Database TILIEK berhasil disiapkan.")

    finally:
        conn.close()


if __name__ == "__main__":
    init_db()

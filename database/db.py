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


        conn.execute("""
            CREATE TABLE IF NOT EXISTS hasil_preprocessing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                berita_id INTEGER NOT NULL UNIQUE,
                teks_preprocessing TEXT NOT NULL,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (berita_id)
                    REFERENCES berita(id)
                    ON DELETE CASCADE
            )
        """)


        conn.execute("""
            CREATE TABLE IF NOT EXISTS hasil_sentimen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                berita_id INTEGER NOT NULL UNIQUE,
                skor_sentimen REAL NOT NULL,
                label_sentimen TEXT NOT NULL,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (berita_id)
                    REFERENCES berita(id)
                    ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS hasil_clustering (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                berita_id INTEGER NOT NULL UNIQUE,
                cluster_id INTEGER NOT NULL,
                kata_kunci TEXT,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (berita_id)
                    REFERENCES berita(id)
                    ON DELETE CASCADE
            )
        """)


        # Tabel identitas topik
        conn.execute("""
            CREATE TABLE IF NOT EXISTS topik (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_topik TEXT NOT NULL,
                kata_kunci TEXT,
                nama_manual INTEGER DEFAULT 0,
                aktif INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migrasi database lama: tambahkan topik_id jika belum ada
        kolom_clustering = [
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(hasil_clustering)"
            ).fetchall()
        ]

        if "topik_id" not in kolom_clustering:
            conn.execute("""
                ALTER TABLE hasil_clustering
                ADD COLUMN topik_id INTEGER
            """)

        conn.commit()
        print("Database TILIEK berhasil disiapkan.")

    finally:
        conn.close()


if __name__ == "__main__":
    init_db()

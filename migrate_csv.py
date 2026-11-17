import csv
from database.db import get_connection

CSV_PATH = "berita.csv"


def migrate():
    conn = get_connection()

    try:
        with open(CSV_PATH, mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            data = [
                (
                    row["sumber"],
                    row["judul"],
                    row["url"],
                    row["tanggal_terbit"],
                    row["ringkasan"]
                )
                for row in reader
            ]

        conn.executemany("""
            INSERT OR IGNORE INTO berita
            (sumber, judul, url, tanggal_terbit, ringkasan)
            VALUES (?, ?, ?, ?, ?)
        """, data)

        conn.commit()

        total = conn.execute(
            "SELECT COUNT(*) FROM berita"
        ).fetchone()[0]

        print(f"Total data dalam database: {total}")
        print(f"Jumlah data dari CSV: {len(data)}")

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

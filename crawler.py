from collections import Counter
from urllib.parse import urlparse

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import feedparser
from bs4 import BeautifulSoup

from database.db import get_connection


FEEDS = [
    {
        "media": "detik",
        "rss": "https://news.detik.com/berita/rss",
    },
    {
        "media": "detik",
        "rss": "https://finance.detik.com/rss",
        "buang_kanal": {"foto-bisnis", "advertorial-news-block"},
        "buang_judul": ["yuk,", "accurate", "authen", "pelatihan"],
    },
    {
        "media": "cnn",
        "rss": "https://www.cnnindonesia.com/rss",
        "terima_kanal": {"nasional", "ekonomi", "internasional"},
    },
    {
        "media": "republika",
        "rss": "https://republika.co.id/rss",
        "buang_kategori": {
            "sport",
            "dailynews",
            "bina sarana informatika",
            "kolom",
        },
        "buang_path": ["/page/shorts/"],
    },
]


def bersihkan(html):
    return BeautifulSoup(
        html or "", "html.parser"
    ).get_text(" ", strip=True)


def berita_terbaru(tanggal):
    if not tanggal:
        return False

    try:
        waktu = parsedate_to_datetime(tanggal)

        if waktu.tzinfo is None:
            waktu = waktu.replace(tzinfo=timezone.utc)

        sekarang = datetime.now(timezone.utc)

        selisih = sekarang - waktu

        return timedelta(0) <= selisih <= timedelta(hours=24)

    except (ValueError, TypeError, OverflowError):
        return False


def kanal_url(url):
    bagian = urlparse(url).path.strip("/").split("/")
    return bagian[0] if bagian else ""


def kategori_entri(e):
    return {
        t.get("term", "").strip().lower()
        for t in e.get("tags", [])
    }


def lolos(cfg, e, url, judul):
    kanal = kanal_url(url)

    if cfg.get("terima_kanal") and kanal not in cfg["terima_kanal"]:
        return False

    if kanal in cfg.get("buang_kanal", set()):
        return False

    if cfg.get("buang_kategori") and kategori_entri(e) & cfg["buang_kategori"]:
        return False

    if any(p in url for p in cfg.get("buang_path", [])):
        return False

    j = judul.lower()

    if any(k in j for k in cfg.get("buang_judul", [])):
        return False

    return True


def url_tersimpan():
    conn = get_connection()

    try:
        rows = conn.execute(
            "SELECT url FROM berita"
        ).fetchall()

        return {row["url"] for row in rows}

    finally:
        conn.close()


def crawl():
    sudah = url_tersimpan()
    baru = []

    for cfg in FEEDS:
        feed = feedparser.parse(cfg["rss"])

        kanal = Counter(
            kanal_url(e.link) for e in feed.entries if e.get("link")
        )

        print(
            f"{cfg['media']}: {len(feed.entries)} entri "
            f"| kanal: {dict(kanal)}"
        )

        for e in feed.entries:
            if not e.get("link") or not e.get("title"):
                continue

            url = e.link.split("?")[0]
            judul = bersihkan(e.title)
            tanggal = e.get("published") or e.get("updated", "")

            if (
                url in sudah
                or not lolos(cfg, e, url, judul)
                or not berita_terbaru(tanggal)
            ):
                continue

            sudah.add(url)

            baru.append({
                "sumber": cfg["media"],
                "judul": judul,
                "url": url,
                "tanggal_terbit": tanggal,
                "ringkasan": bersihkan(e.get("description", "")),
            })

    return baru


def simpan_berita(data):
    if not data:
        return 0

    conn = get_connection()

    try:
        cursor = conn.executemany("""
            INSERT OR IGNORE INTO berita
            (sumber, judul, url, tanggal_terbit, ringkasan)
            VALUES (?, ?, ?, ?, ?)
        """, [
            (
                berita["sumber"],
                berita["judul"],
                berita["url"],
                berita["tanggal_terbit"],
                berita["ringkasan"],
            )
            for berita in data
        ])

        conn.commit()

        return cursor.rowcount

    finally:
        conn.close()


def total_berita():
    conn = get_connection()

    try:
        return conn.execute(
            "SELECT COUNT(*) FROM berita"
        ).fetchone()[0]

    finally:
        conn.close()


if __name__ == "__main__":
    data = crawl()

    jumlah_baru = simpan_berita(data)

    print(f"\nSelesai: {jumlah_baru} berita baru ditambahkan ke SQLite")
    print(f"Total berita dalam database: {total_berita()}")
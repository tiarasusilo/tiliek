import csv
import os
from collections import Counter
from urllib.parse import urlparse
import feedparser
from bs4 import BeautifulSoup

FEEDS = [
    {
        "media": "detik",
        "rss": "https://news.detik.com/berita/rss",
    },
    {
        "media": "detik",
        "rss": "https://finance.detik.com/rss",  # salin dari address bar
        "buang_kanal": {"foto-bisnis", "advertorial-news-block"},
        "buang_judul": ["yuk,", "accurate", "authen", "pelatihan"],
    },
    {
        "media": "cnn",
        "rss": "https://www.cnnindonesia.com/rss",  # salin dari address bar
        "terima_kanal": {"nasional", "ekonomi", "internasional"},
    },
    {
        "media": "republika",
        "rss": "https://republika.co.id/rss",
        "buang_kategori": {"sport", "dailynews", "bina sarana informatika", "kolom"},
        "buang_path": ["/page/shorts/"],
    },
]
FILE_CSV = "berita.csv"
KOLOM = ["sumber", "judul", "url", "tanggal_terbit", "ringkasan"]


def bersihkan(html):
    return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)


def kanal_url(url):
    bagian = urlparse(url).path.strip("/").split("/")
    return bagian[0] if bagian else ""


def kategori_entri(e):
    return {t.get("term", "").strip().lower() for t in e.get("tags", [])}


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
    if not os.path.exists(FILE_CSV):
        return set()
    with open(FILE_CSV, encoding="utf-8") as f:
        return {row["url"] for row in csv.DictReader(f)}


def crawl():
    sudah = url_tersimpan()
    baru = []
    for cfg in FEEDS:
        if cfg["rss"].startswith("URL_"):
            print(f"{cfg['media']}: DILEWATI (URL RSS belum diisi)")
            continue
        feed = feedparser.parse(cfg["rss"])
        kanal = Counter(kanal_url(e.link) for e in feed.entries)
        print(f"{cfg['media']}: {len(feed.entries)} entri | kanal: {dict(kanal)}")
        for e in feed.entries:
            url = e.link.split("?")[0]
            judul = bersihkan(e.title)
            if url in sudah or not lolos(cfg, e, url, judul):
                continue
            sudah.add(url)
            baru.append({
                "sumber": cfg["media"],
                "judul": judul,
                "url": url,
                "tanggal_terbit": e.get("published", ""),
                "ringkasan": bersihkan(e.get("description", "")),
            })
    return baru


if __name__ == "__main__":
    data = crawl()
    baru_file = not os.path.exists(FILE_CSV)
    with open(FILE_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOLOM)
        if baru_file:
            w.writeheader()
        w.writerows(data)
    print(f"Selesai: {len(data)} berita baru ditambahkan")
import re

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory


# Inisialisasi Sastrawi
stemmer = StemmerFactory().create_stemmer()
stopword_factory = StopWordRemoverFactory()

# Stopword bawaan Sastrawi
stopwords = set(stopword_factory.get_stop_words())

# Stopword tambahan untuk konteks berita
custom_stopwords = {
    "sedang",
    "telah",
    "sudah",
    "akan",
    "dapat",
    "bisa",
    "yakni",
    "yaitu",
    "tersebut",
    "menurut",
    "melalui",
    "terkait",
}

stopwords.update(custom_stopwords)

# Kata negasi yang harus tetap dipertahankan
negation_words = {
    "tidak",
    "tak",
    "bukan",
    "belum",
    "jangan",
    "tanpa",
}

stopwords.difference_update(negation_words)

# Kata yang tidak boleh diubah oleh stemming
stemming_exceptions = {
    "pemerintah",
    "indonesia",
}

# Nama tokoh, lembaga, perusahaan, dan istilah khusus
entity_exceptions = {
    "hadi",
    "santoso",
    "ahrie",
    "sonta",
    "prabowo",
    "kemendagri",
    "inalum",
    "citraraya",
    "promax",
    "ecopolis",
    "muratreis",
    "tangerang",
    "muratreis",
    "co2e",
    "ipb",
    "tnuk",
}

def case_folding(teks):
    """Mengubah seluruh teks menjadi huruf kecil."""
    return teks.lower()


def cleaning(teks):
    """Membersihkan teks dengan mempertahankan angka dan satuan."""

    teks = re.sub(r"https?://\S+|www\.\S+", " ", teks)
    teks = re.sub(r"<[^>]*>", " ", teks)

    # Menormalisasi angka dengan simbol subskrip
    teks = teks.replace("₂", "2")

    # Mengubah simbol persen menjadi kata
    teks = re.sub(r"(?<=\d)\s*%", " persen", teks)

    # Mempertahankan tanda desimal dan koma di antara angka
    teks = re.sub(r"(?<!\d)[,.]|[,.](?!\d)", " ", teks)

    # Mempertahankan huruf, angka, dan tanda desimal
    teks = re.sub(r"[^a-zA-Z0-9\s,.]", " ", teks)

    # Merapikan spasi
    teks = re.sub(r"\s+", " ", teks)

    return teks.strip()


def tokenizing(teks):
    """Memecah teks menjadi kumpulan kata."""
    return teks.split()


def stopword_removal(tokens):
    """Menghapus kata umum tanpa menghilangkan negasi."""
    return [
        kata for kata in tokens
        if kata not in stopwords
    ]


def stemming(tokens):
    """Mengubah kata menjadi bentuk dasar."""

    hasil = []

    for kata in tokens:
        if (
            any(karakter.isdigit() for karakter in kata)
            or kata in stemming_exceptions
            or kata in negation_words
            or kata in entity_exceptions
            or "-" in kata
        ):
            hasil.append(kata)
        else:
            hasil.append(stemmer.stem(kata))

    return hasil


def preprocessing(teks):
    """Menjalankan seluruh tahapan preprocessing."""

    teks = case_folding(teks)
    teks = cleaning(teks)

    tokens = tokenizing(teks)
    tokens = stopword_removal(tokens)
    tokens = stemming(tokens)

    return " ".join(tokens)


def proses_semua_berita():
    from database.db import get_connection, init_db

    init_db()
    conn = get_connection()

    try:
        berita_list = conn.execute("""
            SELECT
                b.id,
                b.judul,
                b.ringkasan
            FROM berita b
            LEFT JOIN hasil_preprocessing hp
                ON b.id = hp.berita_id
            WHERE hp.berita_id IS NULL
            ORDER BY b.id ASC
        """).fetchall()

        for berita in berita_list:
            teks_asli = (
                f"{berita['judul'] or ''} "
                f"{berita['ringkasan'] or ''}"
            )

            teks_hasil = preprocessing(teks_asli)

            conn.execute("""
                INSERT INTO hasil_preprocessing (
                    berita_id,
                    teks_preprocessing
                )
                VALUES (?, ?)
                ON CONFLICT(berita_id)
                DO UPDATE SET
                    teks_preprocessing = excluded.teks_preprocessing,
                    processed_at = CURRENT_TIMESTAMP
            """, (berita["id"], teks_hasil))

        conn.commit()

        print(f"Berhasil memproses {len(berita_list)} berita baru.")

    except Exception as e:
        conn.rollback()
        print(f"Terjadi kesalahan: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    proses_semua_berita()


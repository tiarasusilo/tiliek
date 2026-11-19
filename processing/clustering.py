import re
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from database.db import get_connection, init_db


# Konfigurasi
AMBANG_KEMIRIPAN_TOPIK = 0.25
AMBANG_KEMIRIPAN_TOPIK_MANUAL = 0.60
JUMLAH_KATA_KUNCI = 5
CLUSTER_LAINNYA = set()

STOPWORDS_NAMA = {
    "yang", "dan", "di", "ke", "dari", "pada", "untuk",
    "dengan", "dalam", "ini", "itu", "jadi", "karena",
    "oleh", "saat", "setelah", "sebelum", "hingga",
    "tersebut", "terkait", "sejumlah", "seorang",
    "orang", "temu", "ada", "akan", "telah", "bisa",
    "dapat", "masih", "juga", "lebih", "agar", "menjadi",
    "terjadi", "ungkap", "sebut", "kata", "ujar",
    "jelas", "republika", "detik", "kompas", "cnn",
    "tempo", "co", "id", "com", "news"
}

# Pemetaan kata kunci ke topik yang lebih mudah dipahami
KAMUS_TOPIK = {
    "kepolisian": {
        "polri", "polisi", "kepolisian", "polres", "polda"
    },
    "penyadapan": {
        "sadap", "penyadapan", "penyadap"
    },
    "keuangan": {
        "ojk", "dana", "uang", "bank", "investasi",
        "keuangan", "ekonomi", "pajak"
    },
    "harga emas": {
        "emas", "antam", "logam", "mulia"
    },
    "politik amerika serikat": {
        "trump", "amerika", "as", "washington"
    },
    "asean": {
        "asean", "ktt", "asia", "tenggara"
    },
    "dpr dan legislasi": {
        "dpr", "ruu", "rancangan", "undang", "komisi",
        "legislasi", "parlemen"
    },
    "pendidikan": {
        "sekolah", "siswa", "guru", "pendidikan",
        "kampus", "universitas", "mahasiswa"
    },
    "konservasi badak jawa": {
        "badak", "jawa", "kulon", "taman", "nasional",
        "ujung"
    },
    "pemerintahan": {
        "pemerintah", "menteri", "presiden", "wapres",
        "gubernur", "bupati", "wakil"
    },
    "bencana alam": {
        "gempa", "banjir", "longsor", "tsunami",
        "bencana", "gunung", "erupsi"
    },
    "kriminalitas": {
        "kriminal", "pembunuhan", "pencurian", "rampok",
        "penipuan", "tersangka", "pelaku", "kejahatan"
    },
    "lingkungan": {
        "lingkungan", "hutan", "sampah", "polusi",
        "karhutla", "tambang", "alam"
    },
    "kesehatan": {
        "kesehatan", "rumah", "sakit", "dokter",
        "pasien", "penyakit", "obat"
    },
    "perampasan aset": {
    "ampas", "aset", "rampas", "ruu",
    "undang", "sita", "korupsi"
    }
}


def ambil_data_berita():
    """Mengambil berita yang sudah melalui preprocessing."""
    conn = get_connection()

    try:
        return conn.execute("""
            SELECT
                hp.berita_id,
                hp.teks_preprocessing,
                b.judul
            FROM hasil_preprocessing hp
            JOIN berita b ON b.id = hp.berita_id
            WHERE hp.teks_preprocessing IS NOT NULL
              AND TRIM(hp.teks_preprocessing) != ''
            ORDER BY hp.berita_id ASC
        """).fetchall()
    finally:
        conn.close()


def tentukan_cluster(matrix):
    """Menentukan jumlah cluster terbaik berdasarkan Silhouette Score."""
    jumlah_data = matrix.shape[0]
    hasil_evaluasi = []

    batas_cluster = min(10, jumlah_data - 1)

    for k in range(2, batas_cluster + 1):
        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )

        labels = model.fit_predict(matrix)

        if len(set(labels)) != k:
            continue

        skor = silhouette_score(
            matrix,
            labels,
            metric="cosine"
        )

        hasil_evaluasi.append((skor, model, labels, k))

        print(f"Cluster: {k} | Silhouette Score: {skor:.4f}")

    if not hasil_evaluasi:
        raise ValueError("Tidak ditemukan konfigurasi cluster yang valid.")

    return max(hasil_evaluasi, key=lambda hasil: hasil[0])


def ambil_kata_kunci(model, feature_names):
    """Mengambil kata kunci utama setiap cluster."""
    hasil = {}

    for cluster_id, centroid in enumerate(model.cluster_centers_):
        indeks = centroid.argsort()[-JUMLAH_KATA_KUNCI:][::-1]

        hasil[cluster_id] = [
            feature_names[i] for i in indeks
        ]

    return hasil


def bersihkan_kata(teks):
    """Membersihkan kata untuk keperluan penamaan topik."""
    teks = teks.lower()
    teks = re.sub(r"[^a-zA-Z0-9\s]", " ", teks)

    kata = teks.split()

    return [
        item for item in kata
        if item not in STOPWORDS_NAMA
        and len(item) > 2
        and not any(angka.isdigit() for angka in item)
    ]



def normalisasi_kata(teks):
    """Membersihkan teks menjadi kumpulan kata."""
    teks = teks.lower()
    teks = re.sub(r"[^a-zA-Z0-9\s]", " ", teks)

    return [
        kata for kata in teks.split()
        if kata not in STOPWORDS_NAMA
        and len(kata) > 2
        and not any(angka.isdigit() for angka in kata)
    ]


def buat_nama_topik(judul_berita, kata_kunci):
    """
    Menentukan nama topik berdasarkan relevansi kata kunci
    dan kemunculannya pada keseluruhan judul berita.
    """

    # Menghitung kata dari seluruh judul berita
    frekuensi_judul = Counter()

    for judul in judul_berita:
        frekuensi_judul.update(normalisasi_kata(judul))

    # Mengambil kata kunci utama
    kata_cluster = set()

    for frasa in kata_kunci:
        kata_cluster.update(normalisasi_kata(frasa))

    if not kata_cluster:
        return "Lainnya"

    # Menghitung relevansi setiap kategori
    skor_topik = {}

    for nama, kata_kategori in KAMUS_TOPIK.items():
        kata_cocok = kata_cluster & kata_kategori

        if not kata_cocok:
            continue

        skor_kata_kunci = len(kata_cocok) / len(kata_kategori)
        skor_judul = sum(
            frekuensi_judul[kata]
            for kata in kata_cocok
        )

        skor_topik[nama] = (
            skor_kata_kunci * 3
            + skor_judul
        )

    if not skor_topik:
        return "Lainnya"

    # Memilih topik dengan skor tertinggi
    nama_terbaik = max(
        skor_topik,
        key=skor_topik.get
    )

    # Memastikan ada dukungan kata kunci dan judul
    kata_terpilih = kata_cluster & KAMUS_TOPIK[nama_terbaik]

    if len(kata_terpilih) < 1:
        return "Lainnya"

    return nama_terbaik.title()



def ambil_topik_lama(conn):
    """Mengambil hubungan topik lama dengan berita anggotanya."""
    hasil = conn.execute("""
        SELECT topik_id, berita_id
        FROM hasil_clustering
        WHERE topik_id IS NOT NULL
    """).fetchall()

    topik_lama = {}

    for row in hasil:
        topik_id = row["topik_id"]

        if topik_id not in topik_lama:
            topik_lama[topik_id] = set()

        topik_lama[topik_id].add(row["berita_id"])

    return topik_lama


def hitung_jaccard(anggota_baru, anggota_lama):
    """Menghitung kemiripan anggota dua topik."""
    gabungan = anggota_baru | anggota_lama

    if not gabungan:
        return 0

    irisan = anggota_baru & anggota_lama

    return len(irisan) / len(gabungan)


def cocokkan_topik(conn, anggota_baru, topik_lama, topik_terpakai):
    """Mencocokkan cluster baru dengan topik sebelumnya."""
    skor_terbaik = 0
    topik_terbaik = None

    for topik_id, anggota_lama in topik_lama.items():
        if topik_id in topik_terpakai:
            continue

        skor = hitung_jaccard(anggota_baru, anggota_lama)
        status_topik = conn.execute(
            "SELECT nama_manual FROM topik WHERE id = ?",
            (topik_id,)
        ).fetchone()

        nama_manual = bool(status_topik and status_topik["nama_manual"])
        ambang = (
            AMBANG_KEMIRIPAN_TOPIK_MANUAL
            if nama_manual
            else AMBANG_KEMIRIPAN_TOPIK
        )

        if skor >= ambang and skor > skor_terbaik:
            skor_terbaik = skor
            topik_terbaik = topik_id

    return topik_terbaik


def simpan_topik(conn, topik_id, nama_topik, kata_kunci):
    """Menyimpan topik baru atau memperbarui topik lama."""
    kata_kunci_teks = ", ".join(kata_kunci)

    if topik_id is None:
        cursor = conn.execute("""
            INSERT INTO topik (
                nama_topik,
                kata_kunci,
                nama_manual,
                aktif,
                created_at,
                updated_at
            )
            VALUES (?, ?, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (nama_topik, kata_kunci_teks))

        return cursor.lastrowid

    conn.execute("""
        UPDATE topik
        SET
            nama_topik = CASE
                WHEN nama_manual = 0 THEN ?
                ELSE nama_topik
            END,
            kata_kunci = ?,
            aktif = 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (nama_topik, kata_kunci_teks, topik_id))

    return topik_id


def simpan_hasil(berita_ids, labels, kata_kunci, judul_berita):
    """Menyimpan hasil clustering dan mengelola topik."""
    conn = get_connection()

    try:
        conn.execute("BEGIN")

        topik_lama = ambil_topik_lama(conn)
        topik_terpakai = set()
        topik_per_cluster = {}

        # Menonaktifkan topik lama sebelum memperbarui hasil
        conn.execute("""
            UPDATE topik
            SET aktif = 0
        """)

        for cluster_id in sorted(set(labels)):
            anggota = {
                berita_id
                for berita_id, label in zip(berita_ids, labels)
                if label == cluster_id
            }

            # Cluster tertentu ditampilkan sebagai Lainnya
            if cluster_id in CLUSTER_LAINNYA:
                topik_per_cluster[cluster_id] = None
                continue

            judul_cluster = [
                judul
                for judul, label in zip(judul_berita, labels)
                if label == cluster_id
            ]

            nama_topik = buat_nama_topik(
                judul_cluster,
                kata_kunci[cluster_id]
            )

            topik_id = cocokkan_topik(
                conn,
                anggota,
                topik_lama,
                topik_terpakai
            )

            topik_id = simpan_topik(
                conn,
                topik_id,
                nama_topik,
                kata_kunci[cluster_id]
            )

            topik_terpakai.add(topik_id)
            topik_per_cluster[cluster_id] = topik_id

        # Mengganti hasil clustering sebelumnya
        conn.execute("DELETE FROM hasil_clustering")

        data = [
            (
                berita_id,
                int(cluster_id),
                ", ".join(kata_kunci[int(cluster_id)]),
                topik_per_cluster[int(cluster_id)]
            )
            for berita_id, cluster_id in zip(berita_ids, labels)
        ]

        conn.executemany("""
            INSERT INTO hasil_clustering (
                berita_id,
                cluster_id,
                kata_kunci,
                topik_id
            )
            VALUES (?, ?, ?, ?)
        """, data)

        conn.commit()

        print(f"Berhasil menyimpan {len(data)} hasil clustering.")

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def ubah_nama_topik(topik_id, nama_baru):
    """Mengubah nama topik secara manual."""
    conn = get_connection()

    try:
        conn.execute("""
            UPDATE topik
            SET
                nama_topik = ?,
                nama_manual = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (nama_baru, topik_id))

        conn.commit()
        print("Nama topik berhasil diperbarui.")

    finally:
        conn.close()


def tampilkan_topik():
    """Menampilkan topik aktif beserta jumlah beritanya."""
    conn = get_connection()

    try:
        hasil = conn.execute("""
            SELECT
                t.id,
                t.nama_topik,
                t.kata_kunci,
                t.nama_manual,
                COUNT(h.berita_id) AS jumlah_berita
            FROM topik t
            JOIN hasil_clustering h ON h.topik_id = t.id
            WHERE t.aktif = 1
            GROUP BY t.id
            ORDER BY t.id
        """).fetchall()

        print("\nDAFTAR TOPIK")
        print("=" * 50)

        for row in hasil:
            print(f"\nID Topik: {row['id']}")
            print(f"Nama: {row['nama_topik']}")
            print(f"Kata kunci: {row['kata_kunci']}")
            print(f"Jumlah berita: {row['jumlah_berita']}")
            print(
                "Penamaan:",
                "Manual" if row["nama_manual"] else "Otomatis"
            )

        lainnya = conn.execute("""
            SELECT COUNT(*)
            FROM hasil_clustering
            WHERE topik_id IS NULL
        """).fetchone()[0]

        if lainnya:
            print("\nNama: Lainnya")
            print(f"Jumlah berita: {lainnya}")

    finally:
        conn.close()


def proses_clustering():
    """Menjalankan proses clustering berita."""
    init_db()

    print("Mengambil data berita...")
    data = ambil_data_berita()

    if len(data) < 3:
        print("Belum cukup berita untuk clustering.")
        return

    berita_ids = [row["berita_id"] for row in data]
    teks = [row["teks_preprocessing"] for row in data]
    judul_berita = [row["judul"] for row in data]

    print(f"Jumlah berita: {len(teks)}")
    print("Mengubah teks menjadi TF-IDF...")

    vectorizer = TfidfVectorizer(
        max_features=10000,
        min_df=2,
        max_df=0.90,
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    try:
        matrix = vectorizer.fit_transform(teks)
    except ValueError as error:
        print(f"Gagal membentuk TF-IDF: {error}")
        return

    if matrix.shape[1] == 0:
        print("Tidak ditemukan fitur teks untuk clustering.")
        return

    print(f"Jumlah fitur TF-IDF: {matrix.shape[1]}")
    print("\nMenentukan jumlah cluster terbaik...")

    skor, model, labels, jumlah_cluster = tentukan_cluster(matrix)

    feature_names = vectorizer.get_feature_names_out()
    kata_kunci = ambil_kata_kunci(model, feature_names)

    print("\nHASIL CLUSTERING")
    print("=" * 50)
    print(f"Jumlah cluster terbaik: {jumlah_cluster}")
    print(f"Silhouette Score: {skor:.4f}")

    for cluster_id in range(jumlah_cluster):
        jumlah_anggota = sum(labels == cluster_id)

        nama = (
            "Lainnya"
            if cluster_id in CLUSTER_LAINNYA
            else buat_nama_topik(
                [
                    judul
                    for judul, label in zip(judul_berita, labels)
                    if label == cluster_id
                ],
                kata_kunci[cluster_id]
            )
        )

        print(f"\nCluster {cluster_id}")
        print(f"Nama topik: {nama}")
        print(f"Jumlah berita: {jumlah_anggota}")
        print(f"Kata kunci: {', '.join(kata_kunci[cluster_id])}")

    simpan_hasil(
        berita_ids,
        labels,
        kata_kunci,
        judul_berita
    )

    tampilkan_topik()

    print("\nClustering berita selesai.")


if __name__ == "__main__":
    proses_clustering()

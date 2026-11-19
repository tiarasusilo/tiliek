import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from database.db import get_connection, init_db

MODEL_NAME = "dwili/bert-bahasa-sentimen-berita"

LABEL_MAPPING = {
    0: "negatif",
    1: "netral",
    2: "positif"
}

DEVICE = torch.device("cpu")


def load_model():
    """Memuat tokenizer dan model IndoBERT."""

    print("Memuat model IndoBERT...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME
    )

    model.to(DEVICE)
    model.eval()

    print("Model IndoBERT berhasil dimuat.")

    return tokenizer, model


def analisis_sentimen(teks, tokenizer, model):
    """Menganalisis sentimen teks menggunakan IndoBERT."""

    inputs = tokenizer(
        teks,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    inputs = {
        key: value.to(DEVICE)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        outputs = model(**inputs)

    probabilitas = torch.softmax(
        outputs.logits,
        dim=1
    )[0]

    prediksi = torch.argmax(probabilitas).item()

    label = LABEL_MAPPING[prediksi]
    confidence = probabilitas[prediksi].item()

    return label, round(confidence, 4)


def proses_semua_sentimen():
    """Memproses seluruh berita dan menyimpan hasilnya ke database."""

    init_db()

    tokenizer, model = load_model()

    conn = get_connection()

    try:
        berita_list = conn.execute("""
            SELECT
                b.id,
                b.judul,
                b.ringkasan
            FROM berita b
            LEFT JOIN hasil_sentimen hs
                ON b.id = hs.berita_id
            WHERE hs.berita_id IS NULL
            ORDER BY b.id ASC
        """).fetchall()

        total = len(berita_list)

        for nomor, berita in enumerate(berita_list, start=1):

            teks = (
                f"{berita['judul'] or ''}. "
                f"{berita['ringkasan'] or ''}"
            ).strip()

            label, confidence = analisis_sentimen(
                teks,
                tokenizer,
                model
            )

            conn.execute("""
                INSERT INTO hasil_sentimen (
                    berita_id,
                    skor_sentimen,
                    label_sentimen
                )
                VALUES (?, ?, ?)
                ON CONFLICT(berita_id)
                DO UPDATE SET
                    skor_sentimen = excluded.skor_sentimen,
                    label_sentimen = excluded.label_sentimen,
                    processed_at = CURRENT_TIMESTAMP
            """, (
                berita["id"],
                confidence,
                label
            ))

            if nomor % 10 == 0 or nomor == total:
                conn.commit()
                print(
                    f"Memproses berita {nomor}/{total}"
                )

        print(f"\nBerhasil menganalisis {total} berita baru.")

    except Exception as e:
        conn.rollback()
        print(f"Terjadi kesalahan: {e}")

    finally:
        conn.close()


if __name__ == "__main__":
    proses_semua_sentimen()
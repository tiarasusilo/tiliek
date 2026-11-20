import sqlite3
from pathlib import Path
from email.utils import parsedate_to_datetime

from flask import Flask, render_template, request


app = Flask(__name__)

# ==================================================
# DATABASE CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database" / "tiliek.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    connection.create_function(
        "PARSE_RSS_DATE",
        1,
        parse_rss_date
    )

    return connection

def parse_rss_date(value):
    if not value:
        return None

    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


# ==================================================
# HOME
# ==================================================

@app.route("/")
def index():
    return render_template("home.html")


# ==================================================
# TELUSUR
# ==================================================

@app.route("/telusur")
def telusur():
    keyword = request.args.get("q", "").strip()
    sumber = request.args.get("sumber", "").strip()
    tanggal_dari = request.args.get("dari", "").strip()
    tanggal_sampai = request.args.get("sampai", "").strip()

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    per_page = 10
    offset = (page - 1) * per_page

    conditions = []
    parameters = []

    # Search by title and summary
    if keyword:
        conditions.append(
            "(judul LIKE ? OR ringkasan LIKE ?)"
        )
        search_keyword = f"%{keyword}%"
        parameters.extend([search_keyword, search_keyword])

    # Filter by media source
    if sumber:
        conditions.append("sumber = ?")
        parameters.append(sumber)

    # Filter by publication date
    if tanggal_dari:
        conditions.append("PARSE_RSS_DATE(tanggal_terbit) >= ?")
        parameters.append(tanggal_dari)

    if tanggal_sampai:
        conditions.append("PARSE_RSS_DATE(tanggal_terbit) <= ?")
        parameters.append(tanggal_sampai)

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with get_db_connection() as connection:

        # Get available media sources
        sources = connection.execute("""
            SELECT DISTINCT sumber
            FROM berita
            WHERE sumber IS NOT NULL
            ORDER BY sumber ASC
        """).fetchall()

        # Count matching news
        total_news = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM berita
            {where_clause}
            """,
            parameters
        ).fetchone()[0]

        # Calculate pagination
        total_pages = (total_news + per_page - 1) // per_page

        if total_pages > 0 and page > total_pages:
            page = total_pages
            offset = (page - 1) * per_page

        # Get news data
        news = connection.execute(
            f"""
            SELECT
                id,
                sumber,
                judul,
                url,
                tanggal_terbit,
                ringkasan
            FROM berita
            {where_clause}
            ORDER BY
                PARSE_RSS_DATE(tanggal_terbit) DESC,
                created_at DESC
            LIMIT ? OFFSET ?
            """,
            parameters + [per_page, offset]
        ).fetchall()

    return render_template(
        "telusur.html",
        news=news,
        sources=sources,
        keyword=keyword,
        selected_source=sumber,
        tanggal_dari=tanggal_dari,
        tanggal_sampai=tanggal_sampai,
        total_news=total_news,
        page=page,
        total_pages=total_pages
    )


# ==================================================
# PETA ISU
# ==================================================

@app.route("/peta-isu")
def peta_isu():
    return render_template("home.html")


# ==================================================
# CHATBOT
# ==================================================

@app.route("/chatbot")
def chatbot():
    return render_template("home.html")


# ==================================================
# TENTANG
# ==================================================

@app.route("/tentang")
def tentang():
    return render_template("tentang.html")


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":
    app.run(debug=True)

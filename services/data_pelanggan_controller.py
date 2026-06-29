from flask import render_template, request
from connection import connection_db
import math
from datetime import datetime

def data_pelanggan_controller():
    page = request.args.get("page", 1, type=int)
    per_page = 13
    offset = (page - 1) * per_page

    now = datetime.now()
    selected_bulan = request.args.get("bulan", now.strftime("%m"))
    selected_tahun = request.args.get("tahun", now.strftime("%Y"))

    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    count_query = """
        SELECT COUNT(DISTINCT nama) as total
        FROM pelanggan
        WHERE MONTH(tanggal) = %s AND YEAR(tanggal) = %s
    """
    cursor.execute(count_query, (selected_bulan, selected_tahun))
    total_data = cursor.fetchone()["total"]

    total_pages = math.ceil(total_data / per_page) if total_data > 0 else 1

    query = """
        SELECT *
        FROM pelanggan
        WHERE MONTH(tanggal) = %s AND YEAR(tanggal) = %s
        ORDER BY tanggal DESC, id DESC
        LIMIT %s OFFSET %s
    """
    cursor.execute(query, (selected_bulan, selected_tahun, per_page, offset))
    pelanggan = cursor.fetchall()

    cursor.close()
    conn.close()

    daftar_tahun = [str(y) for y in range(2024, now.year + 2)]
    
    daftar_bulan = [
        {"value": "01", "label": "Januari"},
        {"value": "02", "label": "Februari"},
        {"value": "03", "label": "Maret"},
        {"value": "04", "label": "April"},
        {"value": "05", "label": "Mei"},
        {"value": "06", "label": "Juni"},
        {"value": "07", "label": "Juli"},
        {"value": "08", "label": "Agustus"},
        {"value": "09", "label": "September"},
        {"value": "10", "label": "Oktober"},
        {"value": "11", "label": "November"},
        {"value": "12", "label": "Desember"}
    ]

    return render_template(
        "pages/data_pelanggan.html",
        pelanggan=pelanggan,
        page=page,
        total_pages=total_pages,
        total_customer=total_data,
        selected_bulan=selected_bulan,
        selected_tahun=selected_tahun,
        daftar_bulan=daftar_bulan,
        daftar_tahun=daftar_tahun
    )
from flask import render_template, request
from connection import connection_db
import math

def data_pelanggan_controller():

    page = request.args.get("page", 1, type=int)

    per_page = 13

    offset = (page - 1) * per_page

    conn = connection_db()

    cursor = conn.cursor(dictionary=True)


    count_query = """
        SELECT COUNT(DISTINCT nama) as total
        FROM pelanggan
        WHERE tanggal >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
    """

    cursor.execute(count_query)

    total_data = cursor.fetchone()["total"]

    total_pages = math.ceil(total_data / per_page)

    # data pelanggan
    query = """
        SELECT *
        FROM pelanggan
        WHERE tanggal >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)
        ORDER BY tanggal DESC, id DESC
        LIMIT %s OFFSET %s
    """


    cursor.execute(query, (per_page, offset))

    pelanggan = cursor.fetchall()
    total_customer = total_data

    cursor.close()
    conn.close()

    return render_template(
        "pages/data_pelanggan.html",
        pelanggan=pelanggan,
        page=page,
        total_pages=total_pages,
        total_customer=total_customer
    )
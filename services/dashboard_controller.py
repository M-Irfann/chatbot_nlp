# from flask import render_template
# from flask import render_template, session, redirect

# from connection import connection_db

# def dashboard_controller():

#     if not session.get("is_login"):
#         return redirect("/")

#     conn = connection_db()

#     cursor = conn.cursor()

#     query = """
#         SELECT SUM(nominal)
#         FROM pelanggan
#         WHERE MONTH(tanggal) = MONTH(CURRENT_DATE())
#         AND YEAR(tanggal) = YEAR(CURRENT_DATE())
#     """

#     cursor.execute(query)

#     result = cursor.fetchone()

#     total_pendapatan = result[0]

#     if total_pendapatan is None:
#         total_pendapatan = 0

#     cursor.close()
#     conn.close()

#     return render_template(
#         "pages/dashboard.html",
#         total_pendapatan=total_pendapatan
#     )

from flask import render_template, session, redirect
from connection import connection_db

def dashboard_controller():

    if not session.get("is_login"):
        return redirect("/")

    conn = connection_db()
    cursor = conn.cursor()

    query = """
        SELECT SUM(nominal)
        FROM pelanggan
        WHERE MONTH(tanggal) = MONTH(CURRENT_DATE())
        AND YEAR(tanggal) = YEAR(CURRENT_DATE())
    """

    cursor.execute(query)

    result = cursor.fetchone()

    total_pendapatan = result[0]

    if total_pendapatan is None:
        total_pendapatan = 0

    cursor.close()
    conn.close()

    return render_template(
        "pages/dashboard.html",
        total_pendapatan=total_pendapatan,
        nama=session.get("nama")
    )
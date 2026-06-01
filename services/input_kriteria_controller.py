from flask import render_template, request, redirect, url_for

from connection import connection_db


def input_kriteria_controller():

    conn = connection_db()

    cursor = conn.cursor(dictionary=True)

    # =========================
    # GET
    # =========================
    if request.method == "GET":

        query = """
            SELECT *
            FROM bobot_kriteria
            WHERE id = 1
        """

        cursor.execute(query)

        bobot = cursor.fetchone()

        cursor.close()
        conn.close()

        return render_template(
            "pages/input_bobot_kriteria.html",
            bobot=bobot
        )

    # =========================
    # POST
    # =========================
    bobot_frekuensi = request.form.get("bobot_frekuensi")
    bobot_total_kg = request.form.get("bobot_total_kg")
    bobot_total_nominal = request.form.get("bobot_total_nominal")
    bobot_jenis_cuci = request.form.get("bobot_jenis_cuci")

    query = """
        UPDATE bobot_kriteria
        SET
            bobot_frekuensi = %s,
            bobot_total_kg = %s,
            bobot_total_nominal = %s,
            bobot_jenis_cuci = %s
        WHERE id = 1
    """

    values = (
        bobot_frekuensi,
        bobot_total_kg,
        bobot_total_nominal,
        bobot_jenis_cuci
    )

    cursor.execute(query, values)

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(
        url_for("page_routes.input_kriteria")
    )
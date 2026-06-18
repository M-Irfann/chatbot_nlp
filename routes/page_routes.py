from flask import Blueprint, render_template, session, redirect, request
from services.dashboard_controller import dashboard_controller
from services.input_kriteria_controller import input_kriteria_controller
from services.login_controller import login_controller
from services.search_pelanggan_controller import search_pelanggan_controller
from services.data_pelanggan_controller import data_pelanggan_controller
from datetime import date


from connection import connection_db

page_routes = Blueprint("page_routes", __name__)

@page_routes.route("/chatbot")
def chatbot_page():
    return render_template("chatbot/chatbot.html")

@page_routes.route("/dashboard")
def dashboard_page():
   return dashboard_controller()

@page_routes.route("/input_kriteria", methods=["GET", "POST"])
def input_kriteria():
    return input_kriteria_controller()

@page_routes.route(
    "/input_data_pelanggan",
    methods=["GET", "POST"]
)
def input_pelanggan():

    if request.method == "POST":

        nama = request.form.get("nama")
        jenis_cuci = request.form.get("jenis_cuci")
        
        # 1. Ambil data mentah dari form HTML
        berat_raw = request.form.get("berat")
        nominal_raw = request.form.get("nominal")

        # 2. PENCEGAHAN BERAT: Jika kosong atau salah ketik, paksa jadi 0.0
        if not berat_raw or berat_raw.strip() == "":
            berat = 0.0
        else:
            try:
                berat = float(berat_raw)
            except ValueError:
                berat = 0.0

        # 3. PENCEGAHAN NOMINAL: Jika kosong atau salah ketik, paksa jadi angka 0
        if not nominal_raw or nominal_raw.strip() == "":
            nominal = 0
        else:
            try:
                nominal = int(nominal_raw)
            except ValueError:
                nominal = 0

        no_telepon = (
            request.form.get("no_telepon") or None
        )

        tanggal = request.form.get("tanggal")

        conn = connection_db()
        cursor = conn.cursor()

        query = """
            INSERT INTO pelanggan
            (
                nama,
                nominal,
                jenis_cuci,
                berat,
                tanggal,
                no_telepon
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        # Gunakan variabel nominal dan berat yang sudah aman di atas
        values = (
            nama,
            nominal,
            jenis_cuci,
            berat,
            tanggal,
            no_telepon
        )

        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/dashboard")

    # ====================================================
    # PROSES GET (Membuka Halaman Form)
    # ====================================================
    nama = request.args.get("nama")
    pelanggan = None

    if nama:
        conn = connection_db()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT *
            FROM pelanggan
            WHERE nama = %s
            LIMIT 1
        """
        cursor.execute(query, (nama,))
        pelanggan = cursor.fetchone()
        cursor.close()
        conn.close()

    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    query_jenis = """
        SELECT *
        FROM jenis_cuci
    """
    cursor.execute(query_jenis)
    jenis_cuci = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "pages/input_data_pelanggan.html",
        pelanggan=pelanggan,
        jenis_cuci=jenis_cuci,
        today=date.today()
    )

@page_routes.route("/search_pelanggan")
def search_pelanggan():
    return search_pelanggan_controller()

@page_routes.route("/data_pelanggan")
def data_pelanggan():
    return data_pelanggan_controller()


#  login 

@page_routes.route("/", methods=["GET", "POST"])
def login_page():
    return login_controller()

# logout
@page_routes.route("/logout")
def logout():

    session.clear()

    return redirect("/")
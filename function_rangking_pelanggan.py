from datetime import datetime, timedelta
from connection import connection_db
import session_store
import uuid


# =========================
# HELPER
# =========================
def convert_number(value):
    angka_kata = {
        "satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5,
        "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9, "sepuluh": 10
    }
    if value is None:
        return None
    if str(value).isdigit():
        return int(value)
    return angka_kata.get(str(value).lower(), 10)


# =========================
# MAIN HANDLER
# =========================

def handle_tentukan_pelanggan_terbaik(entities):
    # =========================
    # FIX: COMPARISON → STATUS
    # =========================
    if not entities.get("STATUS") and entities.get("COMPARISON"):
        comp = entities["COMPARISON"][0].lower()

        if comp in ["tertinggi", "terbesar", "paling tinggi", "paling besar"]:
            entities["STATUS"] = ["terbaik"]
            entities["INTENSITY"] = ["sangat"]

        elif comp in ["terendah", "terkecil"]:
            entities["STATUS"] = ["biasa"]

    # =========================
    # HANDLE METRIC QUERY (FIX)
    # =========================
    if entities.get("METRIC") and entities.get("COMPARISON") and not entities.get("STATUS"):
        return handle_metric_query(entities)

    # Tanggal default untuk testing/sistem
    tanggal_akhir = datetime(2026, 1, 2, 23, 59, 59)
    tanggal_awal = None

    status_list = entities.get("STATUS", ["terbaik"])
    intensity_list = entities.get("INTENSITY", [])
    limit = convert_number(entities.get("RESULT_COUNT", [10])[0])

    # =========================
    # LIMIT DISTRIBUTION
    # =========================
    jumlah_status = len(status_list)
    limit_map = {}

    if jumlah_status == 1:
        limit_map[status_list[0]] = limit
    else:
        utama = int(limit * 0.7)
        sisa = limit - utama
        for status in status_list:
            if status == "terbaik":
                limit_map[status] = utama
            elif status == "biasa":
                limit_map[status] = sisa
            else:
                limit_map[status] = max(1, limit // jumlah_status)

    # =========================
    # TIME VALUE
    # =========================
    if entities.get("TIME_VALUE"):
        val = convert_number(entities["TIME_VALUE"][0])
        unit = entities.get("TIME_UNIT", ["bulan"])[0]

        if unit == "bulan":
            bulan_awal = tanggal_akhir.month - (val - 1)
            tahun_awal = tanggal_akhir.year
            while bulan_awal <= 0:
                bulan_awal += 12
                tahun_awal -= 1
            tanggal_awal = datetime(tahun_awal, bulan_awal, 1)
        elif unit == "minggu":
            tanggal_awal = tanggal_akhir - timedelta(weeks=val)
        else:
            tanggal_awal = tanggal_akhir - timedelta(days=val)

    # =========================
    # TIME EXPRESSION
    # =========================
    elif entities.get("TIME_EXPRESSION"):
        exp = entities["TIME_EXPRESSION"][0].lower()
        if "tahun ini" in exp:
            tanggal_awal = datetime(tanggal_akhir.year, 1, 1)
        elif "bulan ini" in exp:
            tanggal_awal = datetime(tanggal_akhir.year, tanggal_akhir.month, 1)
        elif "minggu ini" in exp:
            tanggal_awal = datetime(tanggal_akhir.year, tanggal_akhir.month, 1) # Fallback ke awal bulan
        elif "minggu lalu" in exp:
            tanggal_awal = tanggal_akhir - timedelta(days=14)
            tanggal_akhir = tanggal_akhir - timedelta(days=7)
        elif any(k in exp for k in ["periode sekarang", "sekarang", "terbaru", "latest"]):
            tanggal_awal = datetime(tanggal_akhir.year, tanggal_akhir.month, 1)
        else:
            tanggal_awal = tanggal_akhir - timedelta(days=30)

    # Fallback jika tanggal_awal masih kosong
    if not tanggal_awal:
        tanggal_awal = tanggal_akhir - timedelta(days=90)

    # ====================================
    # PROSES DATA (POSISI UUID SUDAH DI-FIX)
    # ====================================
    # Generate ID di sini terlebih dahulu agar bisa dioper ke fungsi di bawahnya
    new_chat_id = str(uuid.uuid4())

    hasil_semua = {}
    for i, status_req in enumerate(status_list):
        if i < len(intensity_list) and intensity_list[i]:
            status_final = f"{intensity_list[i]} {status_req}"
        else:
            status_final = status_req

        final_limit = limit_map.get(status_req, limit)
        
        # Jalankan fungsi Weighted Product dengan membawa parameter new_chat_id
        hasil = weigted_product_proses(
            tanggal_awal,
            tanggal_akhir,
            final_limit,
            status_final,
            new_chat_id
        )
        hasil_semua[status_req] = hasil

    # =========================
    # FORMAT TANGGAL & ID
    # =========================
    tgl_s = tanggal_awal.strftime('%d %b %Y') 
    tgl_e = tanggal_akhir.strftime('%d %b %Y')
    summary_text_final = f"Periode: {tgl_s} s/d {tgl_e}"

    # =========================
    # 🔥 SIMPAN KE SESSION GLOBAL
    # =========================
    session_store.LAST_RANKING_RESULT.clear()
    session_store.LAST_RANKING_RESULT.update({
        "data": hasil_semua.get(status_list[0], {}).get("data", []),
        "raw": hasil_semua,
        "summary": summary_text_final,
        "chat_id": new_chat_id,
        "periode": {
            "awal": tgl_s,
            "akhir": tgl_e
        }
    })

    # =========================
    # RETURN KE FLASK/UI
    # =========================
    return {
        "kategori": status_list,
        "summary": summary_text_final,
        "data": hasil_semua,
        "chat_id": new_chat_id
    }

# =========================
# METRIC HANDLER (BARU)
# =========================
def handle_metric_query(entities):
    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    tanggal_akhir = datetime(2026, 1, 2, 23, 59, 59)
    tanggal_awal = datetime(tanggal_akhir.year, tanggal_akhir.month, 1)

    metric = entities["METRIC"][0]
    comparison = entities["COMPARISON"][0]
    limit = convert_number(entities.get("RESULT_COUNT", [10])[0])

    tgl_str = f"Periode: {tanggal_awal.strftime('%Y-%m-%d')} s/d {tanggal_akhir.strftime('%Y-%m-%d')}"
    if metric == "transaksi":
        order_by = "COUNT(tanggal)"
    elif metric == "pendapatan":
        order_by = "SUM(nominal)"
    else:
        order_by = "COUNT(tanggal)"

    query = f"""
        SELECT 
            nama,
            COUNT(tanggal) as total_transaksi,
            SUM(nominal) as total_nominal
        FROM pelanggan
        WHERE tanggal BETWEEN %s AND %s
        GROUP BY nama
        ORDER BY {order_by} DESC
        LIMIT %s
    """

    cursor.execute(query, (tanggal_awal, tanggal_akhir, limit))
    data = cursor.fetchall()

    cursor.close()
    conn.close()


    return {
        "kategori": [comparison],
        "summary": tgl_str,
        "data": {comparison: data}
    }


# =========================
# WEIGHTED PRODUCT
# =========================
# def weigted_product_proses(tanggal_awal, tanggal_akhir, limit, status, chat_id):
#     conn = connection_db()
#     cursor = conn.cursor(dictionary=True)

#     try:
#         query = """
#             SELECT 
#                 nama,
#                 COUNT(tanggal) as frekuensi,
#                 SUM(berat) as jumlah_transaksi,
#                 SUM(nominal) as total_nominal,
#                 COALESCE(
#                     AVG(
#                         CASE LOWER(jenis_cuci)
#                             WHEN 'cuci basah' THEN 1
#                             WHEN 'setrika' THEN 2
#                             WHEN 'cuci kering' THEN 3
#                             WHEN 'cuci lipat' THEN 4
#                             WHEN 'cuci setrika' THEN 5
#                             WHEN 'bed cover' THEN 6
#                             ELSE 1
#                         END
#                     ), 1
#                 ) as jenis_level
#             FROM pelanggan
#             WHERE tanggal BETWEEN %s AND %s
#             GROUP BY nama
#         """

#         cursor.execute(query, (tanggal_awal, tanggal_akhir))
#         data = cursor.fetchall()

#         if not data:
#             return {"data": []}

#         w1, w2, w3, w4 = 0.40, 0.30, 0.20, 0.10
#         hasil_wp = []

#         for row in data:
#             s = (
#                 (float(row["frekuensi"]) ** w1) *
#                 (float(row["jumlah_transaksi"]) ** w2) *
#                 (float(row["jenis_level"]) ** w3) *
#                 (float(row["total_nominal"]) ** w4)
#             )

#             hasil_wp.append({
#                 "nama": row["nama"],
#                 "nilai_raw": float(s),
#                 "frekuensi": float(row["frekuensi"]),
#                 "total_transaksi": float(row["jumlah_transaksi"]),
#                 "total_nominal": float(row["total_nominal"]),
#             })

#         hasil_wp = sorted(hasil_wp, key=lambda x: x["nilai_raw"], reverse=True)

#         max_wp = max(x["nilai_raw"] for x in hasil_wp)

#         for x in hasil_wp:
#             x["nilai_wp"] = x["nilai_raw"] / max_wp if max_wp > 0 else 0

#         # Oper nilai chat_id asli ke dalam grouping logic
#         return grouping_logic(hasil_wp, limit, status, tanggal_awal, tanggal_akhir, chat_id)

#     finally:
#         cursor.close()
#         conn.close()

def weigted_product_proses(tanggal_awal, tanggal_akhir, limit, status, chat_id):

    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    try:

        # =========================
        # DATA PELANGGAN
        # =========================
        query = """
            SELECT 
                nama,
                COUNT(tanggal) as frekuensi,
                SUM(berat) as jumlah_transaksi,
                SUM(nominal) as total_nominal,
                COALESCE(
                    AVG(
                        CASE LOWER(jenis_cuci)
                            WHEN 'cuci basah' THEN 1
                            WHEN 'setrika' THEN 2
                            WHEN 'cuci kering' THEN 3
                            WHEN 'cuci lipat' THEN 4
                            WHEN 'cuci setrika' THEN 5
                            WHEN 'bed cover' THEN 6
                            ELSE 1
                        END
                    ), 1
                ) as jenis_level
            FROM pelanggan
            WHERE tanggal BETWEEN %s AND %s
            GROUP BY nama
        """

        cursor.execute(query, (tanggal_awal, tanggal_akhir))

        data = cursor.fetchall()

        if not data:
            return {"data": []}

        # =========================
        # AMBIL BOBOT DARI DATABASE
        # =========================
        query_bobot = """
            SELECT *
            FROM bobot_kriteria
            WHERE id = 1
        """

        cursor.execute(query_bobot)

        bobot = cursor.fetchone()

        w1 = float(bobot["bobot_frekuensi"])
        w2 = float(bobot["bobot_total_kg"])
        w3 = float(bobot["bobot_jenis_cuci"])
        w4 = float(bobot["bobot_total_nominal"])

        hasil_wp = []

        # =========================
        # PROSES WEIGHTED PRODUCT
        # =========================
        for row in data:

            s = (
                (float(row["frekuensi"]) ** w1) *
                (float(row["jumlah_transaksi"]) ** w2) *
                (float(row["jenis_level"]) ** w3) *
                (float(row["total_nominal"]) ** w4)
            )

            hasil_wp.append({
                "nama": row["nama"],
                "nilai_raw": float(s),
                "frekuensi": float(row["frekuensi"]),
                "total_transaksi": float(row["jumlah_transaksi"]),
                "total_nominal": float(row["total_nominal"]),
            })

        hasil_wp = sorted(
            hasil_wp,
            key=lambda x: x["nilai_raw"],
            reverse=True
        )

        max_wp = max(
            x["nilai_raw"]
            for x in hasil_wp
        )

        for x in hasil_wp:

            x["nilai_wp"] = (
                x["nilai_raw"] / max_wp
                if max_wp > 0 else 0
            )

        # =========================
        # GROUPING
        # =========================
        return grouping_logic(
            hasil_wp,
            limit,
            status,
            tanggal_awal,
            tanggal_akhir,
            chat_id
        )

    finally:

        cursor.close()
        conn.close()

# =========================
# GROUPING LOGIC (SUDAH FIX)
# =========================
def grouping_logic(hasil_wp, limit, status, tanggal_awal, tanggal_akhir, chat_id):

    if not hasil_wp:
        return {"data": []}

    # =========================
    # HITUNG RATA-RATA
    # =========================
    nilai_list = [item["nilai_wp"] for item in hasil_wp]

    mean = sum(nilai_list) / len(nilai_list)

    # =========================
    # KATEGORI
    # =========================
    terbaik = [
        x for x in hasil_wp
        if x["nilai_wp"] >= mean
    ]

    biasa = [
        x for x in hasil_wp
        if x["nilai_wp"] < mean
    ]

    # =========================
    # NORMALISASI STATUS
    # =========================
    status_map = {
        "terbaik": "terbaik",
        "unggulan": "terbaik",
        "loyal": "terbaik",
        "aktif": "terbaik",

        "biasa": "biasa",
        "normal": "biasa"
    }

    target_key = status_map.get(
        status.lower(),
        "terbaik"
    )

    # =========================
    # PILIH DATA
    # =========================
    if target_key == "terbaik":
        data_final = sorted(
            terbaik,
            key=lambda x: x["nilai_wp"],
            reverse=True
        )[:limit]
    else:
        data_final = sorted(
            biasa,
            key=lambda x: x["nilai_wp"]
        )[:limit]

    # fallback
    if not data_final:
        data_final = hasil_wp[:limit]

    # =========================
    # SAVE CHAT HISTORY
    # =========================
    # Pembuatan double UUID lama sudah dihapus agar ID singkron dengan chat_id utama

    session_store.CHAT_HISTORY.append({
        "id": chat_id,
        "data": {
            status: {
                "data": data_final
            }
        },
        "periode": {
            "awal": str(tanggal_awal),
            "akhir": str(tanggal_akhir)
        }
    })

    # batasi history
    if len(session_store.CHAT_HISTORY) > 20:
        session_store.CHAT_HISTORY.pop(0)

    return {
        "data": data_final,
        "chat_id": chat_id
    }
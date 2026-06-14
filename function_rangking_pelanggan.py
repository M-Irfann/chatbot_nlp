from datetime import datetime, timedelta
from connection import connection_db
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

    if not entities.get("STATUS") and entities.get("COMPARISON"):
        comp = entities["COMPARISON"][0].lower()

        if comp in ["tertinggi", "terbesar", "paling tinggi", "paling besar"]:
            entities["STATUS"] = ["terbaik"]
            entities["INTENSITY"] = ["sangat"]
        elif comp in ["terendah", "terkecil"]:
            entities["STATUS"] = ["biasa"]

    if entities.get("METRIC") and entities.get("COMPARISON") and not entities.get("STATUS"):
        return handle_metric_query(entities)

    tanggal_akhir = datetime(2026, 1, 2, 23, 59, 59)
    tanggal_awal = None

    status_list = entities.get("STATUS", ["terbaik"])
    intensity_list = entities.get("INTENSITY", [])
    limit = convert_number(entities.get("RESULT_COUNT", [10])[0])

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
            else:
                limit_map[status] = sisa

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

    elif entities.get("TIME_EXPRESSION"):
        exp = entities["TIME_EXPRESSION"][0].lower()

        if "tahun ini" in exp:
            tanggal_awal = datetime(tanggal_akhir.year, 1, 1)
        elif "bulan ini" in exp:
            tanggal_awal = datetime(tanggal_akhir.year, tanggal_akhir.month, 1)
        else:
            tanggal_awal = tanggal_akhir - timedelta(days=30)

    if not tanggal_awal:
        tanggal_awal = tanggal_akhir - timedelta(days=90)

    chat_id = str(uuid.uuid4())

    hasil_semua = {}

    for i, status_req in enumerate(status_list):

        chat_id = str(uuid.uuid4()) 
        
        intensity = intensity_list[i] if i < len(intensity_list) else ""
        status_final = f"{intensity} {status_req}".strip()

        final_limit = limit_map.get(status_req, limit)

        hasil = weigted_product_proses(
            tanggal_awal,
            tanggal_akhir,
            final_limit,
            status_final,
            chat_id
        )

        # Simpan data dan chat_id spesifiknya
        hasil_semua[status_req] = {
            "detail": hasil,
            "chat_id": chat_id
        }

    return {
        "kategori": status_list,
        "summary": f"{tanggal_awal} s/d {tanggal_akhir}",
        "data": hasil_semua
    }
    # === SAMPAI SINI ===


# =========================
# METRIC QUERY
# =========================
def handle_metric_query(entities):
    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    tanggal_akhir = datetime(2026, 1, 2, 23, 59, 59)
    tanggal_awal = datetime(tanggal_akhir.year, tanggal_akhir.month, 1)

    metric = entities["METRIC"][0]
    comparison = entities["COMPARISON"][0]
    limit = convert_number(entities.get("RESULT_COUNT", [10])[0])

    if metric == "transaksi":
        order_by = "COUNT(tanggal)"
    else:
        order_by = "SUM(nominal)"

    query = f"""
        SELECT nama,
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
        "summary": f"{tanggal_awal} s/d {tanggal_akhir}",
        "data": {comparison: data}
    }


# =========================
# WEIGHTED PRODUCT
# =========================
def weigted_product_proses(tanggal_awal, tanggal_akhir, limit, status, chat_id):

    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT nama,
                   COUNT(tanggal) as frekuensi,
                   SUM(berat) as jumlah_transaksi,
                   SUM(nominal) as total_nominal,
                   COALESCE(AVG(
                        CASE LOWER(jenis_cuci)
                            WHEN 'cuci basah' THEN 1
                            WHEN 'setrika' THEN 2
                            WHEN 'cuci kering' THEN 3
                            ELSE 1 END
                   ),1) as jenis_level
            FROM pelanggan
            WHERE tanggal BETWEEN %s AND %s
            GROUP BY nama
        """, (tanggal_awal, tanggal_akhir))

        data = cursor.fetchall()
        if not data:
            return {"data": []}

        cursor.execute("SELECT * FROM bobot_kriteria WHERE id=1")
        bobot = cursor.fetchone()

        w1 = float(bobot["bobot_frekuensi"])
        w2 = float(bobot["bobot_total_kg"])
        w3 = float(bobot["bobot_jenis_cuci"])
        w4 = float(bobot["bobot_total_nominal"])

        hasil = []

        for row in data:
            score = (
                (float(row["frekuensi"]) ** w1) *
                (float(row["jumlah_transaksi"]) ** w2) *
                (float(row["jenis_level"]) ** w3) *
                (float(row["total_nominal"]) ** w4)
            )

            hasil.append({
                "nama": row["nama"],
                "nilai_wp": score,
                "frekuensi": row["frekuensi"],
                "total_nominal": row["total_nominal"],
                "jumlah_transaksi": row["jumlah_transaksi"]
            })

        hasil.sort(key=lambda x: x["nilai_wp"], reverse=True)

        max_val = max(x["nilai_wp"] for x in hasil)
        for x in hasil:
            x["nilai_wp"] = x["nilai_wp"] / max_val if max_val else 0

        return grouping_logic(
            hasil, limit, status,
            tanggal_awal, tanggal_akhir, chat_id
        )

    finally:
        cursor.close()
        conn.close()

def grouping_logic(hasil_wp, limit, status, tanggal_awal, tanggal_akhir, chat_id):

    status_clean = str(status).strip().lower()

    if "biasa" in status_clean:
        target = "biasa"
    elif any(x in status_clean for x in ["terbaik", "unggulan", "loyal"]):
        target = "terbaik"
    else:
        target = "terbaik"

    print("STATUS =", status)
    print("TARGET =", target)

    # UPDATE DI SINI:
    if target == "terbaik":
        # Ambil dari peringkat teratas (WP terbesar)
        data_final = sorted(hasil_wp, key=lambda x: x["nilai_wp"], reverse=True)[:limit]
    else:
        # Ambil dari peringkat terbawah (WP terkecil) langsung tanpa filter kaku < 0.35
        data_final = sorted(hasil_wp, key=lambda x: x["nilai_wp"])[:limit]

    # =========================
    # SAVE DATABASE (HEADER + DETAIL)
    # =========================
    conn = connection_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO chat_sessions
            (id, created_at, updated_at, status, periode_awal, periode_akhir, type)
            VALUES (%s, NOW(), NOW(), %s, %s, %s, %s)
        """, (chat_id, target, tanggal_awal, tanggal_akhir, "ranking"))

        for i, row in enumerate(data_final):
            cursor.execute("""
                INSERT INTO chat_session_data
                (chat_id, nama, peringkat, nilai_wp, frekuensi, total_nominal, jumlah_transaksi)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                chat_id,
                row["nama"],
                i + 1,
                row["nilai_wp"],
                row["frekuensi"],
                row["total_nominal"],
                row["jumlah_transaksi"]
            ))

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    return {
        "data": data_final,
        "chat_id": chat_id
    }
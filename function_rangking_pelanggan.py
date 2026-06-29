from datetime import datetime, timedelta
from connection import connection_db
import uuid
import calendar
from flask import session, has_request_context

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

    # Set default waktu dasar (tahun 2026 sesuai context chat bot kamu)
    hari_ini = datetime.now()
    tahun_default = hari_ini.year
    
    tanggal_awal = None
    tanggal_akhir = None

    # [1] LOGIKA BULAN (MONTH)
    if entities.get("MONTH"):
        list_bulan = entities["MONTH"]
        mapping_bulan_angka = {
            "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
            "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12
        }
        
        tahun_target = int(entities["YEAR"][0]) if entities.get("YEAR") else tahun_default
        angka_bulan = [mapping_bulan_angka[m] for m in list_bulan if m in mapping_bulan_angka]
        
        if angka_bulan:
            bulan_awal = min(angka_bulan)
            bulan_akhir = max(angka_bulan)
            
            tanggal_awal = datetime(tahun_target, bulan_awal, 1, 0, 0, 0)
            hari_terakhir = calendar.monthrange(tahun_target, bulan_akhir)[1]
            tanggal_akhir = datetime(tahun_target, bulan_akhir, hari_terakhir, 23, 59, 59)

    # [2] PERBAIKAN LOGIKA: N-BULAN ATAU N-MINGGU (TIME_VALUE)
    # Diperbaiki agar menghitung mundur dari bulan saat ini secara akurat (April - Juni 2026)
    elif entities.get("TIME_VALUE"):
        val = convert_number(entities["TIME_VALUE"][0])
        unit = entities.get("TIME_UNIT", ["bulan"])[0]
        
        tanggal_akhir = hari_ini.replace(hour=23, minute=59, second=59, microsecond=0)

        if unit == "minggu":
            tanggal_awal = tanggal_akhir - timedelta(days=(val * 7))
        elif unit == "bulan":
            # Menghitung awal rentang dari N bulan yang lalu secara presisi kalender
            # Misal: Jika sekarang Juni, 3 bulan terakhir = April, Mei, Juni. Maka bulan_awal dimulai dari April (1)
            bulan_akhir_angka = tanggal_akhir.month
            tahun_awal = tanggal_akhir.year
            
            bulan_awal_angka = bulan_akhir_angka - (val - 1)
            while bulan_awal_angka <= 0:
                bulan_awal_angka += 12
                tahun_awal -= 1
                
            tanggal_awal = datetime(tahun_awal, bulan_awal_angka, 1, 0, 0, 0)
        else: # hari
            tanggal_awal = tanggal_akhir - timedelta(days=val)

    # [3] LOGIKA EXPRESSION (bulan ini, tahun ini)
    elif entities.get("TIME_EXPRESSION"):
        exp = entities["TIME_EXPRESSION"][0].lower()
        tanggal_akhir = hari_ini.replace(hour=23, minute=59, second=59, microsecond=0)
        
        if "tahun ini" in exp:
            tanggal_awal = datetime(tanggal_akhir.year, 1, 1)
        elif "bulan ini" in exp:
            tanggal_awal = datetime(tanggal_akhir.year, tanggal_akhir.month, 1)
        elif "kemarin" in exp or exp == "yesterday":
            kemarin = hari_ini - timedelta(days=1)
            tanggal_awal = kemarin.replace(hour=0, minute=0, second=0, microsecond=0)
            tanggal_akhir = kemarin.replace(hour=23, minute=59, second=59, microsecond=0)
        elif "bulan lalu" in exp:
            first_day_this_month = hari_ini.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            tanggal_awal = last_day_last_month.replace(day=1, hour=0, minute=0, second=0)
            tanggal_akhir = last_day_last_month.replace(hour=23, minute=59, second=59)
        else:
            tanggal_awal = tanggal_akhir - timedelta(days=60)

    # [4] DEFAULT (Jika kosong, set 3 bulan)
    if not tanggal_awal or not tanggal_akhir:
        tanggal_akhir = hari_ini.replace(hour=23, minute=59, second=59, microsecond=0)
        tanggal_awal = tanggal_akhir - timedelta(days=90)

    # --- Sisa logika di bawah ini tetap dipertahankan ---
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

        hasil_semua[status_req] = {
            "detail": hasil,
            "chat_id": chat_id
        }

    return {
        "kategori": status_list,
        "summary": f"{tanggal_awal.strftime('%Y-%m-%d')} s/d {tanggal_akhir.strftime('%Y-%m-%d')}",
        "data": hasil_semua
    }


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


def weigted_product_proses(tanggal_awal, tanggal_akhir, limit, status, chat_id):
    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    try:
        mapping_level = {
            "setrika": 1,
            "cuci setrika": 2,
            "cuci basah": 3,
            "cuci kering": 4,
            "cuci lipat": 5,
            "bed cover": 6
        }

        cursor.execute("""
            SELECT nama,
                   COUNT(tanggal) as frekuensi,
                   SUM(nominal) as total_nominal,
                   LOWER(jenis_cuci) as nama_layanan
            FROM pelanggan
            WHERE tanggal BETWEEN %s AND %s
            GROUP BY nama, LOWER(jenis_cuci)
        """, (tanggal_awal, tanggal_akhir))

        raw_data = cursor.fetchall()
        if not raw_data:
            return {"data": []}

        pelanggan_map = {}
        for row in raw_data:
            nama = row["nama"]
            layanan_clean = row["nama_layanan"].strip() if row["nama_layanan"] else ""
            level = mapping_level.get(layanan_clean, 1)
            
            if nama not in pelanggan_map:
                pelanggan_map[nama] = {
                    "nama": nama,
                    "frekuensi": 0,
                    "total_nominal": 0.0,
                    "total_level": 0.0,
                    "jumlah_layanan": 0
                }
            
            pelanggan_map[nama]["frekuensi"] += row["frekuensi"]
            pelanggan_map[nama]["total_nominal"] += float(row["total_nominal"])
            pelanggan_map[nama]["total_level"] += level
            pelanggan_map[nama]["jumlah_layanan"] += 1

        cursor.execute("SELECT * FROM bobot_kriteria WHERE id=1")
        bobot = cursor.fetchone()

        w1 = float(bobot["bobot_frekuensi"])
        w3 = float(bobot["bobot_jenis_cuci"])
        w4 = float(bobot["bobot_total_nominal"])

        hasil = []

        for nama, p in pelanggan_map.items():
            avg_jenis_level = p["total_level"] / p["jumlah_layanan"] if p["jumlah_layanan"] else 1.0

            score = (
                (float(p["frekuensi"]) ** w1) *
                (float(avg_jenis_level) ** w3) *
                (float(p["total_nominal"]) ** w4)
            )

            hasil.append({
                "nama": p["nama"],
                "nilai_wp": score,
                "frekuensi": p["frekuensi"],
                "total_nominal": p["total_nominal"],
                "jumlah_transaksi": 0
            })

        hasil.sort(key=lambda x: x["nilai_wp"], reverse=True)

        max_val = max(x["nilai_wp"] for x in hasil) if hasil else 0
        for x in hasil:
            x["nilai_wp"] = x["nilai_wp"] / max_val if max_val else 0

        return grouping_logic(
            hasil, limit, status,
            tanggal_awal, tanggal_akhir, chat_id
        )

    finally:
        cursor.close()
        conn.close()


def evaluate_weighted_product(tanggal_awal, tanggal_akhir):
    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT nama,
                   COUNT(tanggal) as frekuensi,
                   SUM(nominal) as total_nominal,
                   LOWER(jenis_cuci) as nama_layanan
            FROM pelanggan
            WHERE tanggal BETWEEN %s AND %s
            GROUP BY nama, LOWER(jenis_cuci)
        """, (tanggal_awal, tanggal_akhir))

        raw_data = cursor.fetchall()
        pelanggan_map = {}

        mapping_level = {
            "setrika": 1,
            "cuci setrika": 2,
            "cuci basah": 3,
            "cuci kering": 4,
            "cuci lipat": 5,
            "bed cover": 6
        }

        for row in raw_data:
            nama = row["nama"]
            layanan_clean = row["nama_layanan"].strip() if row["nama_layanan"] else ""
            level = mapping_level.get(layanan_clean, 1)

            if nama not in pelanggan_map:
                pelanggan_map[nama] = {
                    "nama": nama,
                    "frekuensi": 0,
                    "total_nominal": 0,
                    "total_level": 0,
                    "jumlah": 0
                }

            pelanggan_map[nama]["frekuensi"] += row["frekuensi"]
            pelanggan_map[nama]["total_nominal"] += float(row["total_nominal"])
            pelanggan_map[nama]["total_level"] += level
            pelanggan_map[nama]["jumlah"] += 1

        cursor.execute("SELECT * FROM bobot_kriteria WHERE id=1")
        bobot = cursor.fetchone()

        w1 = float(bobot["bobot_frekuensi"])
        w3 = float(bobot["bobot_jenis_cuci"])
        w4 = float(bobot["bobot_total_nominal"])

        hasil = []

        for nama, p in pelanggan_map.items():
            avg_level = p["total_level"] / p["jumlah"]
            score = (
                (p["frekuensi"] ** w1) *
                (avg_level ** w3) *
                (p["total_nominal"] ** w4)
            )

            hasil.append({
                "nama": nama,
                "score": score,
                "frekuensi": p["frekuensi"],
                "total_nominal": p["total_nominal"]
            })
        
        hasil.sort(key=lambda x: x["score"], reverse=True)
        max_val = max(x["score"] for x in hasil) if hasil else 0

        for x in hasil:
            x["nilai_wp"] = x["score"] / max_val if max_val else 0

        return hasil

    finally:
        cursor.close()
        conn.close()


# def grouping_logic(hasil_wp, limit, status, tanggal_awal, tanggal_akhir, chat_id):
#     status_clean = str(status).strip().lower()

#     biasa_keywords = ["biasa", "jarang", "sedikit", "pasif", "kurang", "sepi", 
#                       "males", "turun", "rendah", "kecil", "bawah", "terbawah"]
    
#     terbaik_keywords = ["terbaik", "rajin", "sering", "aktif", "loyal", "setia", 
#                         "top", "teratas", "prioritas", "banyak", "besar", "gede", "gacor"]

#     if any(x in status_clean for x in biasa_keywords):
#         target = "biasa"
#     elif any(x in status_clean for x in terbaik_keywords):
#         target = "terbaik"
#     else:
#         target = "terbaik"

#     print("STATUS =", status)
#     print("TARGET =", target)

#     if target == "terbaik":
#         data_final = sorted(hasil_wp, key=lambda x: x["nilai_wp"], reverse=True)[:limit]
#     else:
#         data_final = sorted(hasil_wp, key=lambda x: x["nilai_wp"])[:limit]

#     conn = connection_db()
#     cursor = conn.cursor()

#     user_id = session.get("user_id")

#     if not user_id:
#         raise Exception("User belum login")

#     try:
#         cursor.execute("""
#             INSERT INTO chat_sessions
#             (id, user_id, created_at, updated_at, status, periode_awal, periode_akhir, type)
#             VALUES (%s, %s, NOW(), NOW(), %s, %s, %s, %s)
#         """, (
#             chat_id,
#             user_id,
#             target,
#             tanggal_awal,
#             tanggal_akhir,
#             "ranking"
#         ))

#         for i, row in enumerate(data_final):
#             cursor.execute("""
#                 INSERT INTO chat_session_data
#                 (chat_id, nama, peringkat, nilai_wp, frekuensi, total_nominal)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#             """, (
#                 chat_id,
#                 row["nama"],
#                 i + 1,
#                 row["nilai_wp"],
#                 row["frekuensi"],
#                 row["total_nominal"]
#             ))

#         conn.commit()

#     finally:
#         cursor.close()
#         conn.close()

#     return {
#         "data": data_final,
#         "chat_id": chat_id
#     }
def grouping_logic(hasil_wp, limit, status, tanggal_awal, tanggal_akhir, chat_id):
    status_clean = str(status).strip().lower()

    biasa_keywords = [
        "biasa", "jarang", "sedikit", "pasif",
        "kurang", "sepi", "males", "turun",
        "rendah", "kecil", "bawah", "terbawah"
    ]

    terbaik_keywords = [
        "terbaik", "rajin", "sering", "aktif",
        "loyal", "setia", "top", "teratas",
        "prioritas", "banyak", "besar", "gede", "gacor"
    ]

    if any(x in status_clean for x in biasa_keywords):
        target = "biasa"
    elif any(x in status_clean for x in terbaik_keywords):
        target = "terbaik"
    else:
        target = "terbaik"

    print("STATUS =", status)
    print("TARGET =", target)

    if target == "terbaik":
        data_final = sorted(
            hasil_wp,
            key=lambda x: x["nilai_wp"],
            reverse=True
        )[:limit]
    else:
        data_final = sorted(
            hasil_wp,
            key=lambda x: x["nilai_wp"]
        )[:limit]

    conn = connection_db()
    cursor = conn.cursor()

    # ===============================
    # Ambil user_id
    # ===============================
    if has_request_context():
        user_id = session.get("user_id")

        if not user_id:
            raise Exception("User belum login")
    else:
        # Untuk testing melalui python naive_bayes.py
        user_id = 1

    try:

        cursor.execute("""
            INSERT INTO chat_sessions
            (id, user_id, created_at, updated_at, status,
             periode_awal, periode_akhir, type)
            VALUES (%s, %s, NOW(), NOW(), %s, %s, %s, %s)
        """, (
            chat_id,
            user_id,
            target,
            tanggal_awal,
            tanggal_akhir,
            "ranking"
        ))

        for i, row in enumerate(data_final):

            cursor.execute("""
                INSERT INTO chat_session_data
                (chat_id, nama, peringkat, nilai_wp,
                 frekuensi, total_nominal)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                chat_id,
                row["nama"],
                i + 1,
                row["nilai_wp"],
                row["frekuensi"],
                row["total_nominal"]
            ))

        conn.commit()

    finally:
        cursor.close()
        conn.close()

    return {
        "data": data_final,
        "chat_id": chat_id
    }
from datetime import datetime, timedelta
from connection import connection_db

def convert_number(value):

    angka_kata = {
        "satu": 1,
        "dua": 2,
        "tiga": 3,
        "empat": 4,
        "lima": 5,
        "enam": 6,
        "tujuh": 7,
        "delapan": 8,
        "sembilan": 9,
        "sepuluh": 10
    }

    if value.isdigit():
        return int(value)

    return angka_kata.get(value, None)

def handle_tentukan_pelanggan_terbaik(entities):

    bulan = None
    limit = None
    status = ""
    time_unit = None
    time_expression = None
    result_count = None

    if entities.get("TIME_VALUE"):
        bulan = convert_number(entities["TIME_VALUE"][0])
        # print(bulan)

    if entities.get("RESULT_COUNT"):
        limit = convert_number(entities["RESULT_COUNT"][0])
        # print(limit)

    if entities.get("STATUS"):
        status = entities["STATUS"][-1].lower()

    # if entities.get('RESULT_COUNT'):

    # untuk tanggal 
    # if entities.get('TIME_UNIT'):

    # if entities.get('TIME_EXPRESSION'):

    # if entities.get('result_count'):
        

    hasil = rangking_pelanggan(bulan=bulan, limit=limit)
    print(hasil)

    return hasil

def rangking_pelanggan(bulan=None, limit=None):
    if bulan is None:
        bulan = 2

    if limit is None:
        limit = 6
    
    hasil = weigted_product_proses(bulan, limit)
    return hasil 

# weighted product proses 
def weigted_product_proses(bulan, limit):
    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    tanggal_akhir = datetime(2026,1,2) 
    # tanggal_akhir = datetime.now()  

    tahun = tanggal_akhir.year
    bulan_sekarang = tanggal_akhir.month

    bulan_awal = bulan_sekarang - (bulan - 1)

    # kalau mundur melewati januari
    while bulan_awal <= 0:
        bulan_awal += 12
        tahun -= 1  

    tanggal_awal = datetime(tahun, bulan_awal, 1)


    # debugging
    print("Tanggal Awal  :", tanggal_awal)
    print("Tanggal Akhir :", tanggal_akhir)

    try:
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
            return {"message": "Tidak ada data pada periode tersebut"}

        # Bobot
        w1 = 0.40
        w2 = 0.30
        w3 = 0.20
        w4 = 0.10

        hasil_wp = []

        for row in data:
            frekuensi = float(row["frekuensi"])
            jumlah_transaksi = float(row["jumlah_transaksi"])
            jenis_level = float(row["jenis_level"])
            total_nominal = float(row["total_nominal"])

            s = (
                (frekuensi ** w1) *
                (jumlah_transaksi ** w2) *
                (jenis_level ** w3) *
                (total_nominal ** w4)
            )

            hasil_wp.append({
                "nama": row["nama"],
                "nilai_wp": s
            })

        # Ranking
        clasification_result = sorted(hasil_wp, key=lambda x: x["nilai_wp"], reverse=True)
        
        return grouping(clasification_result, limit)
    
    finally:
        cursor.close()
        conn.close()

def grouping(hasil_wp, limit):

    nilai_list = [item["nilai_wp"] for item in hasil_wp]

    mean = sum(nilai_list) / len(nilai_list)

    sangat_terbaik = []
    terbaik = []
    biasa = []

    for item in hasil_wp:
        nilai = item["nilai_wp"]

        if nilai > mean:
            kategori = "Sangat Terbaik"
            sangat_terbaik.append(item)

        elif nilai == mean:
            kategori = "Terbaik"
            terbaik.append(item)

        else:
            kategori = "Biasa"
            biasa.append(item)

    sangat_terbaik = sangat_terbaik[:limit]
    terbaik = terbaik[:limit]
    biasa = biasa[:limit]

    print("\n===== GROUPING PELANGGAN =====\n")

    print("\nSangat Terbaik:")
    for i, item in enumerate(sangat_terbaik, 1):
        print(f"{i}. {item['nama']:<20} | {item['nilai_wp']:.4f}")

    print("\nTerbaik:")
    for i, item in enumerate(terbaik, 1):
        print(f"{i}. {item['nama']:<20} | {item['nilai_wp']:.4f}")

    print("\nBiasa:")
    for i, item in enumerate(biasa, 1):
        print(f"{i}. {item['nama']:<20} | {item['nilai_wp']:.4f}")

    return {
        "sangat_terbaik": sangat_terbaik,
        "terbaik": terbaik,
        "biasa": biasa
    }

# rangking_pelanggan(4)
from connection import connection_db

# =========================
# RULE LAUNDRY
# =========================
LAUNDRY_RULES = {
    "basah": {
        "min_freq": 5,
        "label": "Cuci Basah",
        "price_per_kg": 10000
    },
    "kering": {
        "min_freq": 8,
        "label": "Cuci Kering",
        "price": 18000
    },
    "lipat": {
        "min_freq": 10,
        "label": "Cuci Lipat",
        "price": 23000
    }
}

# =========================
# REASON ENGINE (KITA KOSONGKAN AGAR TIDAK MENGULANG ANGKA)
# =========================
def build_reason(row):
    # Di menu hadiah, owner tidak butuh rumus matematika lagi. 
    # Cukup kembalikan string kosong agar tampilan chat bersih.
    return ""


# =========================
# DETEKSI LEVEL SERVICE
# =========================
def get_service_level(row):
    freq = row.get("frekuensi", 0)

    if freq >= 10:
        return LAUNDRY_RULES["lipat"]
    elif freq >= 8:
        return LAUNDRY_RULES["kering"]
    elif freq >= 5:
        return LAUNDRY_RULES["basah"]
    else:
        return None


# =========================
# REWARD LOGIC 
# =========================
def get_reward(rank, row):
    service = get_service_level(row)

    if not service:
        return "TIDAK_DAPAT_HADIAH"

    return f"Gratis {service['label']}"


# =========================
# REKOMENDASI TINDAKAN UNTUK OWNER (DIUBAH KE BAHASA SEDERHANA)
# =========================
def get_recommendation(row):
    freq = row.get("frekuensi", 0)

    # 1. Pelanggan Utama (Dapat hadiah tertinggi)
    if freq >= 10:
        return "Pelanggan ini sering banget. menurut saya sih berikan hadiahnya saat mereka datang biar makin betah langganan."
    
    # 2. Pelanggan Aktif Kering / Basah (Dapat hadiah menengah)
    elif freq >= 5 and freq < 10:
        return "Berikan ini kalau kamu mau dan ingatkan tipis-tipis kalau sering laundry di sini hadiahnya bisa naik level."
    
    # 3. Pelanggan Biasa (Belum memenuhi syarat reward)
    else:
        return "Pelanggan ini masih jarang laundry. Dorong supaya pelanggan ini tetap cuci di sini"


# =========================
# AMBIL SESSION
# =========================
def get_last_ranking_session(nama_target=None):
    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if nama_target:
            cursor.execute("""
                SELECT s.* FROM chat_sessions s
                JOIN chat_session_data d ON s.id = d.chat_id
                WHERE s.type = 'ranking' AND LOWER(d.nama) = LOWER(%s)
                ORDER BY s.created_at DESC
                LIMIT 1
            """, (nama_target,))
        else:
            cursor.execute("""
                SELECT * FROM chat_sessions
                WHERE type = 'ranking'
                ORDER BY created_at DESC
                LIMIT 1
            """)
            
        session = cursor.fetchone()

        if not session:
            return None, []

        cursor.execute("""
            SELECT nama, peringkat, nilai_wp, frekuensi, total_nominal
            FROM chat_session_data
            WHERE chat_id = %s
            ORDER BY peringkat ASC
        """, (session["id"],))

        data = cursor.fetchall()
        return session, data

    finally:
        cursor.close()
        conn.close()


# =========================
# MAIN HANDLER
# =========================
def handle_tanya_hadiah(entities):
    nama_target = None
    if entities.get("CUSTOMER_NAME"):
        nama_target = entities["CUSTOMER_NAME"][0]

    session, all_data = get_last_ranking_session(nama_target)

    if not session or not all_data:
        return {"message": "Belum ada data ranking."}

    periode = {
        "awal": str(session["periode_awal"]),
        "akhir": str(session["periode_akhir"])
    }

    # =========================
    # SINGLE CUSTOMER
    # =========================
    if nama_target:
        for i, row in enumerate(all_data):
            if row["nama"].lower() == nama_target.lower():
                rank = i + 1

                return {
                    "nama": row["nama"],
                    "peringkat": rank,
                    "hadiah": get_reward(rank, row),
                    "rekomendasi": get_recommendation(row),
                    "alasan": build_reason(row),
                    "periode": periode,
                    "chat_id": session["id"]
                }

        return {"message": f"{nama_target} tidak ditemukan dalam ranking."}

    # =========================
    # ALL CUSTOMER
    # =========================
    result = []
    for i, row in enumerate(all_data):
        rank = i + 1
        result.append({
            "nama": row["nama"],
            "peringkat": rank,
            "hadiah": get_reward(rank, row),
            "rekomendasi": get_recommendation(row),
            "alasan": build_reason(row)
        })

    return {
        "summary": f"Pemberian reward periode {periode['awal']} s/d {periode['akhir']}",
        "data": result,
        "chat_id": session["id"]
    }


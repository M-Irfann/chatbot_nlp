from connection import connection_db


# =========================
# GLOBAL CONTEXT
# =========================
def build_global_context(data):
    if not data:
        return None

    avg_freq = sum(r["frekuensi"] for r in data) / len(data)
    avg_nominal = sum(r["total_nominal"] for r in data) / len(data)

    return {
        "avg_freq": avg_freq,
        "avg_nominal": avg_nominal,
    }


# =========================
# REASON ENGINE
# =========================
def build_reason(row, context):
    if not context:
        return "data tidak tersedia"

    frekuensi = row.get("frekuensi", 0)
    total_kg = row.get("jumlah_transaksi", 0)
    total_nominal = row.get("total_nominal", 0)
    nilai_wp = row.get("nilai_wp", 0)

    return (
        f"karena memiliki frekuensi transaksi sebanyak {frekuensi:.0f} kali, "
        f"total cucian {total_kg:.1f} kg, "
        f"total nominal Rp {total_nominal:,.0f}, "
        f"dan nilai weighted product {nilai_wp:.3f}"
    )

# =========================
# AMBIL SESSION (BAGIAN INI DIUBAH)
# =========================
def get_last_chat_session(nama_target=None):
    conn = connection_db()
    cursor = conn.cursor(dictionary=True)

    try:
        if nama_target:
            # Mencari session terakhir yang mengandung nama pelanggan tersebut
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

        chat_id = session["id"]

        cursor.execute("""
            SELECT nama, peringkat, nilai_wp, frekuensi, total_nominal, jumlah_transaksi
            FROM chat_session_data
            WHERE chat_id = %s
            ORDER BY peringkat ASC
        """, (chat_id,))

        data = cursor.fetchall()
        return session, data

    finally:
        cursor.close()
        conn.close()


# =========================
# MAIN HANDLER (BAGIAN INI DIUBAH)
# =========================
def handle_tanya_alasan(entities):
    nama_target = None
    if entities.get("CUSTOMER_NAME"):
        nama_target = entities["CUSTOMER_NAME"][0]

    # SEKARANG KITA KIRIM nama_target KE FUNGSI QUERY
    session, all_data = get_last_chat_session(nama_target)

    if not session or not all_data:
        return {
            "message": "Belum ada data ranking. Jalankan ranking terlebih dahulu."
        }

    periode = {
        "awal": str(session["periode_awal"]),
        "akhir": str(session["periode_akhir"])
    }

    context = build_global_context(all_data)

    # =========================
    # JIKA HANYA 1 CUSTOMER
    # =========================
    if nama_target:
        for i, row in enumerate(all_data):
            if row.get("nama", "").lower() == nama_target.lower():
                return {
                    "nama": row.get("nama"),
                    "peringkat": i + 1,
                    "alasan": build_reason(row, context),
                    "periode": periode,
                    "chat_id": session["id"]
                }

        return {
            "message": f"Nama {nama_target} tidak ditemukan dalam ranking."
        }

    # =========================
    # SEMUA CUSTOMER
    # =========================
    result = []
    for i, row in enumerate(all_data):
        result.append({
            "nama": row.get("nama"),
            "peringkat": i + 1,
            "alasan": build_reason(row, context)
        })

    return {
        "summary": f"Penjelasan periode {periode['awal']} s/d {periode['akhir']}",
        "data": result,
        "chat_id": session["id"]
    }
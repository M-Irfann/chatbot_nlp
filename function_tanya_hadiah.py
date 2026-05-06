import session_store
import uuid

# =========================
# GLOBAL CONTEXT
# =========================
def build_global_context(data):
    if not data:
        return None
    try:
        avg_freq = sum(r.get("frekuensi", 0) for r in data) / len(data)
        avg_nominal = sum(r.get("total_nominal", 0) for r in data) / len(data)
        avg_wp = sum(r.get("nilai_wp", 0) for r in data) / len(data)
        return {
            "avg_freq": avg_freq,
            "avg_nominal": avg_nominal,
            "avg_wp": avg_wp
        }
    except:
        return None

# =========================
# REWARD ENGINE
# =========================
def build_reward(row, rank, context):
    if not context:
        return "hadiah tidak tersedia"
    
    wp = row.get("nilai_wp", 0)
    freq = row.get("frekuensi", 0)
    nominal = row.get("total_nominal", 0)
    avg_wp = context.get("avg_wp", 0)

    # 1. CEK DULU APAKAH DIA LAYAK DAPAT HADIAH UTAMA (Berdasarkan Nilai WP)
    # Pelanggan "Biasa" biasanya WP-nya rendah (misal di bawah 0.3)
    if wp < 0.3:
        if wp > 0.1:
            return "voucher diskon 5% untuk transaksi berikutnya"
        return "terima kasih telah berlangganan"

    # 2. JIKA WP LAYAK (DI ATAS 0.3), BARU CEK RANKING
    if rank == 1:
        return "GRAND PRIZE: cuci lipat gratis 10kg + prioritas layanan"
    if rank == 2:
        return "cuci kering gratis 7kg + bonus prioritas"
    if rank == 3:
        return "cuci kering gratis 7kg"

    # 3. LOGIK DINAMIS UNTUK SISANYA
    if wp >= avg_wp * 1.1:
        return "cuci basah gratis 7kg"
    if freq > context.get("avg_freq", 0) and nominal > context.get("avg_nominal", 0):
        return "cuci basah gratis 5kg"
    
    return "diskon 10%"

# =========================
# TERMS
# =========================
def build_terms(row, context):
    if not context:
        return "syarat tidak tersedia"
    terms = []
    if row.get("frekuensi", 0) < context.get("avg_freq", 0):
        terms.append("tingkatkan frekuensi transaksi")
    if row.get("total_nominal", 0) < context.get("avg_nominal", 0):
        terms.append("tingkatkan total belanja")
    if not terms:
        return "langsung bisa diklaim"
    return ", ".join(terms)

# =========================
# MAIN HANDLER
# =========================
def handle_tanya_hadiah(entities):
    reply_id = entities.get("REPLY_ID")
    store = None

    if reply_id:
        for item in reversed(session_store.CHAT_HISTORY):
            if str(item.get("id")) == str(reply_id):
                store = item
                break

    if not store and session_store.CHAT_HISTORY:
        store = session_store.CHAT_HISTORY[-1]

    if not store:
        return {"message": "Belum ada data ranking di memori."}


    raw_data = store.get("data", {})
    periode = store.get("periode", {"awal": "N/A", "akhir": "N/A"})
    all_data = []

    try:
        if isinstance(raw_data, list):
            all_data = raw_data
        elif isinstance(raw_data, dict):
            for k, v in raw_data.items():
                if isinstance(v, dict) and "data" in v:
                    all_data.extend(v["data"])
                elif isinstance(v, list):
                    all_data.extend(v)
    except:
        return {"message": "Struktur data rusak"}

    context = build_global_context(all_data)
    nama_target = entities.get("CUSTOMER_NAME")[0] if entities.get("CUSTOMER_NAME") else None
    
    new_chat_id = str(uuid.uuid4())
    session_store.CHAT_HISTORY.append({"id": new_chat_id, "data": raw_data, "periode": periode})

    if nama_target:
        for i, row in enumerate(all_data):
            if row.get("nama", "").lower() == nama_target.lower():
                return {
                    "nama": row.get("nama"),
                    "rank": i + 1,
                    "hadiah": build_reward(row, i + 1, context),
                    "syarat": build_terms(row, context),
                    "periode": periode,
                    "chat_id": new_chat_id
                }
        return {"message": f"Nama {nama_target} tidak ada.", "chat_id": new_chat_id}

    result = []
    for i, row in enumerate(all_data):
        result.append({
            "nama": row.get("nama"),
            "rank": i + 1,
            "hadiah": build_reward(row, i + 1, context),
            "syarat": build_terms(row, context)
        })

    return {
        "summary": f"Rekomendasi hadiah periode {periode.get('awal')} s/d {periode.get('akhir')}",
        "data": result,
        "chat_id": new_chat_id
    }
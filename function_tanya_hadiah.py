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
        return "reward tidak tersedia"

    wp = row.get("nilai_wp", 0)
    freq = row.get("frekuensi", 0)
    nominal = row.get("total_nominal", 0)

    avg_wp = context.get("avg_wp", 0)
    avg_freq = context.get("avg_freq", 0)
    avg_nominal = context.get("avg_nominal", 0)

    if wp < 0.15:
        return "gratis setrika 1kg"

    if rank == 1:
        return "gratis cuci lipat 1x"

    if rank == 2:
        return "gratis cuci kering 7kg"

    if rank == 3:
        return "gratis cuci basah 7kg"

    if freq >= avg_freq and nominal >= avg_nominal and wp >= avg_wp:
        return "gratis cuci basah 7kg"

    if wp >= avg_wp * 0.7:
        return "gratis setrika 1kg"

    return "gratis cuci basah 1x"

# =========================
# TERMS
# =========================
def build_terms(row, context):
    if not context:
        return "syarat tidak tersedia"

    terms = []
    if row.get("frekuensi", 0) < context.get("avg_freq", 0):
        terms.append("meningkatkan frekuensi transaksi")

    if row.get("total_nominal", 0) < context.get("avg_nominal", 0):
        terms.append("meningkatkan total nominal transaksi")

    if not terms:
        return "reward dapat langsung diklaim"

    return "perlu " + " dan ".join(terms)

# =========================
# MAIN HANDLER (FIXED LOGIC)
# =========================
def handle_tanya_hadiah(entities):
    reply_id = entities.get("REPLY_ID")
    store = None

    # 1. Bersihkan format string ID-nya agar sinkron dengan database memori
    if reply_id:
        reply_id = str(reply_id).strip().lower()

    # 2. PROSES CARI BERDASARKAN REPLY ID
    if reply_id:
        for item in reversed(session_store.CHAT_HISTORY):
            item_id = str(item.get("id", "")).strip().lower()
            if item_id == reply_id:
                store = item
                break

    # 3. FALLBACK AMAN: Lewati chat penjelasan, ambil data master ranking terakhir
    if not store and session_store.CHAT_HISTORY:
        for item in reversed(session_store.CHAT_HISTORY):
            if item.get("type") != "explanation":
                store = item
                break

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

    if not all_data:
        return {"message": "Data ranking kosong atau format salah."}

    context = build_global_context(all_data)
    nama_target = entities.get("CUSTOMER_NAME")[0] if entities.get("CUSTOMER_NAME") else None
    
    # 4. BUAT ID BARU UNTUK CHAT HADIAH INI
    new_chat_id = str(uuid.uuid4())
    
    # Kunci sebagai "explanation" agar tidak merusak antrean fallback berikutnya
    session_store.CHAT_HISTORY.append({
        "id": new_chat_id, 
        "data": all_data, 
        "periode": periode,
        "type": "explanation"
    })

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
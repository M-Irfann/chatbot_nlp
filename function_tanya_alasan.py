import session_store
import uuid

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

    alasan = []

    if not context:
        return "karena data tidak tersedia"

    if row["frekuensi"] > context["avg_freq"]:
        alasan.append("frekuensi transaksi di atas rata-rata")

    if row["total_nominal"] > context["avg_nominal"]:
        alasan.append("total belanja lebih tinggi")

    if row["frekuensi"] >= context["avg_freq"] * 1.5:
        alasan.append("sangat aktif bertransaksi")

    if not alasan:
        alasan.append("memiliki pola transaksi normal/stabil")

    return "karena " + ", ".join(alasan)

# =========================         
# MAIN HANDLER
# =========================
def handle_tanya_alasan(entities):
    reply_id = entities.get("REPLY_ID")
    store = None

    # 1. Cari berdasarkan Reply ID
    if reply_id:
        for item in reversed(session_store.CHAT_HISTORY):
            if str(item.get("id")) == str(reply_id):
                store = item
                break
    
    # 2. Fallback: Ambil history terakhir jika tidak ada reply
    if not store and session_store.CHAT_HISTORY:
        store = session_store.CHAT_HISTORY[-1]

    if not store:
        return {"message": "Silakan tampilkan daftar ranking dulu atau klik reply pada daftar."}


    # Ambil data dari store
    periode = store.get("periode", {})
    raw_data = store.get("data", {})
    all_data = []

    # UNWRAPPING
    try:
        if isinstance(raw_data, dict):
            for k, v in raw_data.items():
                if isinstance(v, dict) and "data" in v:
                    all_data.extend(v["data"])
                elif isinstance(v, list):
                    all_data.extend(v)
        elif isinstance(raw_data, list):
            all_data = raw_data
    except Exception as e:
        return {"message": f"Gagal memproses data: {str(e)}"}

    if not all_data:
        return {"message": "Data ranking kosong."}

    context = build_global_context(all_data)
    nama_target = entities.get("CUSTOMER_NAME")[0] if entities.get("CUSTOMER_NAME") else None

    # BUAT ID BARU UNTUK CHAINING REPLY
    new_chat_id = str(uuid.uuid4())
    session_store.CHAT_HISTORY.append({
        "id": new_chat_id,
        "data": raw_data, 
        "periode": periode
    })

    if nama_target:
        for i, row in enumerate(all_data):
            if row.get("nama", "").lower() == nama_target.lower():
                return {
                    "nama": row.get("nama"),
                    "rank": i + 1,
                    "alasan": build_reason(row, context),
                    "periode": periode,
                    "chat_id": new_chat_id
                }
        return {"message": f"Nama {nama_target} tidak ditemukan.", "chat_id": new_chat_id}

    result = []
    for i, row in enumerate(all_data):
        result.append({
            "nama": row.get("nama"),
            "rank": i + 1,
            "alasan": build_reason(row, context)
        })
    
    return {
        "summary": f"Penjelasan periode {periode.get('awal')} s/d {periode.get('akhir')}",
        "data": result,
        "chat_id": new_chat_id
    }
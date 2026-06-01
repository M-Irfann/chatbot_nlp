
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
    if not context:
        return "data tidak tersedia"

    frekuensi = row.get("frekuensi", 0)
    total_nominal = row.get("total_nominal", 0)
    total_transaksi = row.get("total_transaksi", 0)
    nilai_wp = row.get("nilai_wp", 0)

    alasan = (
        f"karena memiliki frekuensi transaksi sebanyak "
        f"{frekuensi:.0f} kali, "
        f"jumlah transaksi {total_transaksi:.1f} kg, "
        f"total nominal Rp {total_nominal:,.0f}, "
        f"dan nilai weighted product "
        f"{nilai_wp:.3f}"
    )
    return alasan

# =========================         
# MAIN HANDLER
# =========================
def handle_tanya_alasan(entities):
    reply_id = entities.get("REPLY_ID")
    store = None

    # 1. Bersihkan format string ID-nya biar gak miss saat dicocokkan
    if reply_id:
        reply_id = str(reply_id).strip().lower()

    # 2. PROSES CARI BERDASARKAN REPLY ID
    if reply_id:
        for item in reversed(session_store.CHAT_HISTORY):
            item_id = str(item.get("id", "")).strip().lower()
            if item_id == reply_id:
                store = item
                break
    
    # 3. FALLBACK AMAN: Kalau gak klik reply / ID gak ketemu, ambil data master ranking terakhir (bukan data penjelasan)
    if not store and session_store.CHAT_HISTORY:
        for item in reversed(session_store.CHAT_HISTORY):
            if item.get("type") != "explanation":
                store = item
                break

    if not store:
        return {"message": "Silakan tampilkan daftar ranking dulu atau gunakan fitur reply."}

    # Ambil data dari store yang terpilih
    periode = store.get("periode", {})
    raw_data = store.get("data", {})
    all_data = []

    # UNWRAP DATA
    try:
        if isinstance(raw_data, dict):
            if "data" in raw_data:
                raw_data = raw_data["data"]
            
            if isinstance(raw_data, dict):
                for k, v in raw_data.items():
                    if isinstance(v, dict) and "data" in v:
                        all_data.extend(v["data"])
                    elif isinstance(v, list):
                        all_data.extend(v)
            elif isinstance(raw_data, list):
                all_data = raw_data
        elif isinstance(raw_data, list):
            all_data = raw_data
    except Exception as e:
        return {"message": f"Gagal memproses data: {str(e)}"}

    if not all_data:
        return {"message": "Data ranking kosong."}

    context = build_global_context(all_data)
    nama_target = entities.get("CUSTOMER_NAME")[0] if entities.get("CUSTOMER_NAME") else None

    # 4. BUAT ID BARU UNTUK CHAT PENJELASAN INI
    new_chat_id = str(uuid.uuid4())
    
    # Kunci tipe datanya sebagai "explanation" agar tidak merusak antrean fallback nanti
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
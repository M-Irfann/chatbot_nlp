import re

def validate_intent(message):
    """
    Menyaring input user:
    - Return (intent, error_message)
    - Jika intent terdeteksi, error_message = None
    """
    msg = message.lower().strip()
    
    # --- 1. FILTER: CEK INPUT NGAWUR (Spam/Gibberish) ---
    # Jika input terlalu pendek (kurang dari 3 huruf)
    if len(msg) < 3:
        return "INT_UNKNOWN", "Tolong masukkan pertanyaan yang lebih jelas ya kak."
        
    # Jika input kata tanpa spasi tapi panjang banget (spam keyboard)
    if len(msg) > 15 and " " not in msg:
        return "INT_UNKNOWN", "Input kakak sepertinya tidak valid. Ada yang bisa saya bantu terkait data laundry?"

    # --- 2. SISTEM SKORING UNTUK RANKING ---
    score_ranking = 0
    # Kata Kerja (Bobot: 2)
    if any(x in msg for x in ["siapa", "daftar", "tampilkan", "berikan", "cek", "ranking"]):
        score_ranking += 2
    # Subjek Utama (Bobot: 2)
    if any(x in msg for x in ["pelanggan", "customer", "pemenang", "loyal", "terbaik"]):
        score_ranking += 2
    # Keterangan Waktu (Bobot: 1)
    if any(x in msg for x in ["bulan", "minggu", "hari", "tahun", "periode"]):
        score_ranking += 1

    # --- 3. LOGIKA PENENTUAN (THRESHOLD) ---
    
    # A. Cek Ranking (Butuh minimal skor 4)
    if score_ranking >= 4:
        return "INT_RANKING_PELANGGAN", None
        
    # B. Cek Alasan
    if any(x in msg for x in ["kenapa", "alasan", "mengapa", "sebab"]):
        # Pastikan tidak cuma ngetik 'kenapa' tanpa konteks
        if len(msg.split()) >= 1:
            return "INT_TANYA_ALASAN", None
            
    # C. Cek Hadiah
    if any(x in msg for x in ["hadiah", "bonus", "reward", "kasih apa"]):
        return "INT_REKOMENDASI_HADIAH", None

    # --- 4. FALLBACK (Jika tidak ada yang cocok) ---
    return "INT_UNKNOWN", "Maaf, saya hanya bisa membantu cek Ranking, Alasan, dan Hadiah pelanggan. Bisa diperjelas?"


def validate_message(text):
    if not text:
        return False, "Ketikkan sesuatu dulu ya kak."
        
    msg = text.lower().strip()

    # 1. Cek Pesan Terlalu Pendek
    if len(msg) < 3:
        return False, "Input terlalu pendek nih kak, coba ketik yang lebih jelas."

    # 2. Cek Gibberish (Spam ketikan asal tanpa spasi)
    if len(msg) > 15 and " " not in msg:
        return False, "Waduh, saya bingung baca itu. Bisa pakai bahasa manusia saja kak? 😊"

    # 3. Daftar Keyword Wajib
    # Ini adalah filter 'pintu depan'. Kalau gak ada kata-kata ini, 
    # jangan biarkan Naive Bayes menebak-nebak (biar gak salah paham).
    keywords = [
        "siapa", "daftar", "ranking", "terbaik", "pelanggan", "customer",
        "kenapa", "alasan", "mengapa", "sebab", "hadiah", "bonus", "reward", "loyal"
    ]
    
    if not any(word in msg for word in keywords):
        return False, "Maaf kak, saat ini saya hanya bisa membantu terkait Ranking Pelanggan, Alasan, dan Hadiah laundry."

    # Jika semua syarat terpenuhi, berikan lampu hijau (True)
    return True, None
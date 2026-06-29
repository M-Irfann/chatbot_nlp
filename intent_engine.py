# import re

# def validate_intent(message):
#     """
#     Menyaring input user:
#     - Return (intent, error_message)
#     - Jika intent terdeteksi, error_message = None
#     """
#     msg = message.lower().strip()
    
#     # Jika input terlalu pendek kurang dari 3 huruf
#     if len(msg) < 3:
#         return "INT_UNKNOWN", "Tolong masukkan pertanyaan yang lebih jelas ya kak."
        
#     # Jika input kata tanpa spasi tapi panjang banget 
#     if len(msg) > 15 and " " not in msg:
#         return "INT_UNKNOWN", "Input kakak sepertinya tidak valid. Ada yang bisa saya bantu terkait data laundry?"

#     # SISTEM SKORING UNTUK RANKING 
#     score_ranking = 0
#     if any(x in msg for x in ["siapa", "daftar", "tampilkan", "berikan", "cek", "ranking"]):
#         score_ranking += 2
#     if any(x in msg for x in ["pelanggan", "customer", "pemenang", "loyal", "terbaik"]):
#         score_ranking += 2
#     if any(x in msg for x in ["bulan", "minggu", "hari", "tahun", "periode"]):
#         score_ranking += 1

    
#     if score_ranking >= 4:
#         return "INT_RANKING_PELANGGAN", None
        
#     # B. Cek Alasan
#     if any(x in msg for x in ["kenapa", "alasan", "mengapa", "sebab"]):
#         if len(msg.split()) >= 1:
#             return "INT_TANYA_ALASAN", None
            
#     if any(x in msg for x in ["hadiah", "bonus", "reward", "kasih apa"]):
#         return "INT_REKOMENDASI_HADIAH", None

#     return "INT_UNKNOWN", "Maaf, saya hanya bisa membantu cek Ranking, Alasan, dan Hadiah pelanggan. Bisa diperjelas?"


# def validate_message(text):
#     if not text:
#         return False, "Ketikkan sesuatu dulu ya kak."
        
#     msg = text.lower().strip()

#     # Cek Pesan Terlalu Pendek
#     if len(msg) < 3:
#         return False, "Input terlalu pendek nih kak, coba ketik yang lebih jelas."

#     if len(msg) > 15 and " " not in msg:
#         return False, "Waduh, saya bingung baca itu. Bisa pakai bahasa manusia saja kak?"

#     keywords = [
#         "siapa", "daftar", "ranking", "terbaik", "pelanggan", "customer",
#         "kenapa", "alasan", "mengapa", "sebab", "hadiah", "bonus", "reward", "loyal"
#     ]
    
#     if not any(word in msg for word in keywords):
#         return False, "Maaf kak, saat ini saya hanya bisa membantu terkait Ranking Pelanggan, Alasan, dan Hadiah laundry."

#     return True, None


import re

def validate_intent(message):
    """
    Menyaring input user:
    - Return (intent, error_message)
    - Jika intent terdeteksi, error_message = None
    """
    msg = message.lower().strip()
    
    # 1. Antisipasi Pesan Terlalu Pendek atau Karakter Berulang (Spam)
    if len(msg) < 3:
        return "INT_UNKNOWN", "Tolong masukkan pertanyaan yang lebih jelas ya kak."
        
    if len(msg) > 15 and " " not in msg:
        return "INT_UNKNOWN", "Input kakak sepertinya tidak valid. Ada yang bisa saya bantu terkait data laundry?"

    # 2. SISTEM SKORING UNTUK RANKING (DIPERKETAT)
    score_ranking = 0
    if any(x in msg for x in ["siapa", "daftar", "tampilkan", "berikan", "cek", "ranking", "lihat"]):
        score_ranking += 2
    if any(x in msg for x in ["pelanggan", "customer", "pemenang", "loyal", "terbaik", "biasa", "sering", "jarang"]):
        score_ranking += 2
    if any(x in msg for x in ["bulan", "minggu", "hari", "tahun", "periode", "tiga", "3"]):
        score_ranking += 1
    # Tambahan intervensi konteks laundry
    if any(x in msg for x in ["cuci", "laundry", "setrika", "transaksi", "nominal", "wp", "weighted"]):
        score_ranking += 1

    # Skor 4 ke atas baru dianggap mau melihat ranking laundry
    if score_ranking >= 4:
        return "INT_RANKING_PELANGGAN", None
        
    # 3. Cek Alasan (Pastikan konteks bertanya alasan dari hasil ranking)
    if any(x in msg for x in ["kenapa", "alasan", "mengapa", "sebab"]):
        # Mencegah asal ketik kata 'kenapa' tanpa arti yang jelas
        if len(msg) <= 15 or any(x in msg for x in ["ia", "ya", "itu", "gitu", "emang", "pelanggan", "dia"]):
            return "INT_TANYA_ALASAN", None
            
    # 4. Cek Rekomendasi Hadiah
    if any(x in msg for x in ["hadiah", "bonus", "reward", "kasih apa", "kompensasi", "gratis"]):
        return "INT_REKOMENDASI_HADIAH", None

    return "INT_UNKNOWN", "Maaf, saya hanya bisa membantu cek Ranking, Alasan, dan Hadiah pelanggan. Bisa diperjelas?"


def validate_message(text):
    if not text:
        return False, "Ketikkan sesuatu dulu ya kak."
        
    msg = text.lower().strip()

    # Cek Pesan Terlalu Pendek
    if len(msg) < 3:
        return False, "Input terlalu pendek nih kak, coba ketik yang lebih jelas."

    # Cek spam kata panjang tanpa spasi
    if len(msg) > 15 and " " not in msg:
        return False, "Waduh, saya bingung baca itu. Bisa pakai bahasa manusia saja kak?"

    # Daftar Kata Kunci Inti untuk filter awal
    keywords = [
        "siapa", "daftar", "ranking", "terbaik", "pelanggan", "customer", "loyal",
        "kenapa", "alasan", "mengapa", "sebab", "hadiah", "bonus", "reward", 
        "cuci", "laundry", "sering", "jarang", "biasa"
    ]
    
    if not any(word in msg for word in keywords):
        return False, "Maaf kak, saat ini saya hanya bisa membantu terkait Ranking Pelanggan, Alasan, dan Hadiah laundry."

    return True, None
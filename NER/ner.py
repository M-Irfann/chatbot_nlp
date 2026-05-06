from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import re

training_sentences = [
    "siapa pelanggan yang jarang mencuci",
    "pelanggan yang jarang cuci siapa",
    "berapa total pendapatan bulan ini",
    "total pendapatan bulan ini berapa",
    "pelanggan mana yang paling sering transaksi",
    "siapa pelanggan dengan nominal cucian terbesar",
    "berapa jumlah transaksi pelanggan bulan ini",
    "siapa pelanggan baru bulan ini",
    "apakah ada pelanggan yang tidak aktif",
    "siapa pelanggan yang direkomendasikan untuk reward",
    "berapa rata rata transaksi pelanggan bulan ini",
    "tampilkan daftar pelanggan loyal",
    "tampilkan pelanggan dengan transaksi kecil",
    "tampilkan riwayat transaksi pelanggan andi"
]

training_labels = [
    "pelanggan_jarang_cuci",
    "pelanggan_jarang_cuci",
    "tanya_pendapatan",
    "tanya_pendapatan",
    "ranking_frekuensi_transaksi",
    "ranking_nominal_transaksi",
    "tanya_jumlah_transaksi",
    "pelanggan_baru",
    "pelanggan_tidak_aktif",
    "rekomendasi_reward",
    "tanya_rata_transaksi",
    "pelanggan_loyal",
    "pelanggan_transaksi_kecil",
    "riwayat_transaksi"
]

# vectorizer
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(training_sentences)

# model NB
model = MultinomialNB()
model.fit(X, training_labels)

def classify_intent(text):
    vec = vectorizer.transform([text])
    intent = model.predict(vec)[0]
    return intent

# def ner_extractor(text):
#     text = text.lower()
#     entities = {}

#     if "bulan ini" in text:
#         entities["PERIOD"] = "bulan ini"

#     if "total" in text:
#         entities["METRIC"] = "total"

#     if "rata rata" in text or "rata-rata" in text:
#         entities["METRIC"] = "rata-rata"

#     if "loyal" in text:
#         entities["STATUS"] = "loyal"

#     if "tidak aktif" in text:
#         entities["STATUS"] = "tidak aktif"

#     if "jarang" in text:
#         entities["FREQUENCY"] = "jarang"

#     if "terbesar" in text:
#         entities["SIZE"] = "besar"

#     # nama pelanggan
#     name = re.findall(r"pelanggan\s+([a-z]+)", text)
#     if name:
#         entities["CUSTOMER_NAME"] = name[0].capitalize()

#     return entities


def ner_extractor(text):
    text = text.lower()
    entities = {}

    # ===== PERIOD / TIME =====
    period_map = {
        "hari ini": "hari ini",
        "kemarin": "kemarin",
        "minggu ini": "minggu ini",
        "bulan ini": "bulan ini",
        "bulan lalu": "bulan lalu",
        "tahun ini": "tahun ini",
        "tahun lalu": "tahun lalu"
    }
    for k, v in period_map.items():
        if k in text:
            entities["PERIOD"] = v

    # ===== DATE RANGE =====
    if "periode" in text or "rentang" in text:
        entities["DATE_RANGE"] = "custom"

    # ===== METRIC =====
    metric_map = {
        "total": "total",
        "jumlah": "jumlah",
        "rata rata": "rata-rata",
        "rata-rata": "rata-rata",
        "nominal": "nominal",
        "pendapatan": "pendapatan"
    }
    for k, v in metric_map.items():
        if k in text:
            entities["METRIC"] = v

    # ===== RANK / COMPARISON =====
    rank_map = {
        "paling": "paling",
        "terbanyak": "terbanyak",
        "tersedikit": "tersedikit",
        "terbesar": "terbesar",
        "terkecil": "terkecil"
    }
    for k, v in rank_map.items():
        if k in text:
            entities["RANK"] = v

    # ===== AMOUNT SIZE =====
    if "kecil" in text:
        entities["AMOUNT_SIZE"] = "kecil"
    elif "besar" in text:
        entities["AMOUNT_SIZE"] = "besar"

    # ===== FREQUENCY =====
    freq_map = {
        "jarang": "jarang",
        "sering": "sering",
        "rutin": "rutin"
    }
    for k, v in freq_map.items():
        if k in text:
            entities["FREQUENCY"] = v

    # ===== STATUS =====
    status_map = {
        "baru": "baru",
        "lama": "lama",
        "tidak aktif": "tidak aktif",
        "aktif": "aktif"
    }
    for k, v in status_map.items():
        if k in text:
            entities["STATUS"] = v

    # ===== LOYALTY =====
    if "loyal" in text or "setia" in text:
        entities["LOYALTY_LEVEL"] = "loyal"

    # ===== ACTION =====
    action_map = {
        "transaksi": "transaksi",
        "cuci": "cuci",
        "mencuci": "cuci",
        "menggunakan": "gunakan",
        "pakai": "gunakan"
    }
    for k, v in action_map.items():
        if k in text:
            entities["ACTION"] = v

    # ===== OBJECT =====
    object_map = {
        "pelanggan": "pelanggan",
        "customer": "pelanggan",
        "riwayat": "riwayat",
        "data": "data"
    }
    for k, v in object_map.items():
        if k in text:
            entities["OBJECT"] = v

    # ===== SERVICE TYPE =====
    # service_map = {
    #     "kiloan": "kiloan",
    #     "satuan": "satuan",
    #     "express": "express",
    #     "dry clean": "dry clean"
    # }
    # for k, v in service_map.items():
    #     if k in text:
    #         entities["SERVICE_TYPE"] = v

    # ===== CONDITION =====
    if "dengan" in text:
        entities["CONDITION"] = "filter"
    if "tanpa" in text:
        entities["CONDITION"] = "exclude"

    # ===== CUSTOMER NAME =====
    name = re.findall(r"pelanggan\s+([a-z]+)", text)
    if name:
        entities["CUSTOMER_NAME"] = name[0].capitalize()

    return entities


def process_text(text):
    # intent = classify_intent(text)
    entities = ner_extractor(text)

    return {
        # "text": text,
        # "intent": intent,
        "entities": entities
    }

print(process_text("Siapa pelanggan yang jarang dan sering mencuci 3 bulan ini?"))
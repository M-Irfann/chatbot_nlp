import re

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

    # ===== CONDITION =====
    if "dengan" in text:
        entities["CONDITION"] = "filter"
    if "tanpa" in text:
        entities["CONDITION"] = "exclude"

    # ===== CUSTOMER NAME =====
    # di query saja di database
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

print(process_text("Siapa pelanggan yang jarang dan sering mencuci 2 minggu ini?"))
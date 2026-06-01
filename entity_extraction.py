import re
import pandas as pd
from connection import connection_db

# ==============================
# CONFIG
# ==============================

DEBUG = False

def load_customer_names():
    conn = connection_db()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT nama FROM pelanggan")
    names = list(set([row[0].lower() for row in cursor.fetchall()]))

    cursor.close()
    conn.close()

    return names

CUSTOMER_NAME = load_customer_names()

# ==============================
# MASTER DATA
# ==============================

STATUS = [
    "sangat terbaik","terbaik","biasa","loyal","setia",
    "aktif","pasif","sering","jarang","prioritas",
    "unggulan","top","teratas","unggul",
    "top customer","favorit","langganan",
    "setia banget","tidak aktif","kurang aktif"
]

NUMBER_WORDS = {
    "dua puluh": 20,"sembilan belas": 19,"delapan belas": 18,"tujuh belas": 17,
    "enam belas": 16,"lima belas": 15,"empat belas": 14,"tiga belas": 13,
    "dua belas": 12,"sebelas": 11,"sepuluh": 10,"sembilan": 9,
    "delapan": 8,"tujuh": 7,"enam": 6,"lima": 5,
    "empat": 4,"tiga": 3,"dua": 2,"satu": 1
}

TIME_EXPRESSION = list(set([
    "awal tahun sampai sekarang",
    "bulan ini","minggu ini","hari ini","tahun ini","saat ini",
    "terakhir ini","terakhir","terahir","sekarang","kemarin",
    "bulan lalu","minggu lalu","tahun lalu",
    "periode ini","periode sekarang","periode berjalan","terbaru"
]))

TIME_UNIT = ["hari","minggu","bulan","tahun"]
FREQUENCY = ["kali"]

MONTH = [
    "januari","februari","maret","april","mei","juni",
    "juli","agustus","september","oktober","november","desember"
]

METRIC = [
    "pendapatan","omset","penghasilan","income",
    "transaksi","frekuensi","jumlah","total"
]

METRIC_NORMALIZATION = {
    "omset": "pendapatan",
    "penghasilan": "pendapatan",
    "income": "pendapatan",
    "frekuensi": "transaksi",
    "jumlah": "total"
}

TRANSACTION_TYPE = [
    "cuci setrika","cuci","laundry","setrika","kiloan","satuan"
]

COMPARISON = [
    "terbanyak","tertinggi","terendah","paling","lebih","kurang"
]

REWARD = ["hadiah","reward","bonus","diskon","voucher"]

REASON = [
    "apa yang menyebabkan","apa yang membuat","apa penyebabnya",
    "kenapa","mengapa","alasan","penyebab","faktor"
]

# ==============================
# REGEX
# ==============================

DATE_PATTERN = r"\b\d{1,2}\s(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s\d{4}\b"
YEAR_PATTERN = r"\b20\d{2}\b"

RESULT_COUNT_PATTERN = r"\b(\d+)\s+pelanggan\b"
TIME_VALUE_PATTERN = r"\b(\d+)\s+(hari|minggu|bulan|tahun)\b"
TOP_N_PATTERN = r"\b(top\s*\d+|\d+\s*(teratas|terbaik|top))\b"

# ==============================
# SORTING
# ==============================

STATUS_SORTED = sorted(STATUS, key=len, reverse=True)
TIME_EXPRESSION_SORTED = sorted(TIME_EXPRESSION, key=len, reverse=True)
NUMBER_WORDS_SORTED = sorted(NUMBER_WORDS.items(), key=lambda x: len(x[0]), reverse=True)

CURRENT_TIME = ["bulan ini","minggu ini","tahun ini","hari ini","saat ini","sekarang"]
LAST_TIME = ["terakhir","terakhir ini","terahir"]

STATUS_NORMALIZATION = {
    "top customer": "terbaik",
    "top": "terbaik",
    "teratas": "terbaik",
    "unggul": "terbaik",
    "unggulan": "terbaik"
}

TIME_EXPRESSION_NORMALIZATION = {
    "terakhir ini": "terakhir",
    "terahir": "terakhir"
}

TIME_NORMALIZATION_MAP = {
    "hari ini": "today",
    "minggu ini": "this_week",
    "bulan ini": "this_month",
    "tahun ini": "this_year",
    "kemarin": "yesterday",
    "minggu lalu": "last_week",
    "bulan lalu": "last_month",
    "tahun lalu": "last_year",
    "sekarang": "now",
    "saat ini": "now",
    "terakhir": "recent",
    "periode ini": "current_period",
    "periode sekarang": "current_period",
    "periode berjalan": "current_period",
    "terbaru": "latest"
}

def extract_customer_name(text, customer_list):
    for name in customer_list:
        pattern = r'\b' + re.escape(name) + r'\b'
        if re.search(pattern, text):
            return [name]
    return []
# ==============================
# CLEAN TEXT
# ==============================

def replace_number_words(text):
    for word, num in NUMBER_WORDS_SORTED:
        text = re.sub(r'\b' + word + r'\b', str(num), text)
    return text

def clean_text(text):
    text = text.lower()
    text = replace_number_words(text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ==============================
# GENERIC EXTRACT
# ==============================

def extract_single(text, data):
    for item in sorted(data, key=len, reverse=True):
        if re.search(r'\b' + re.escape(item) + r'\b', text):
            return [item]
    return []

def extract_multiple(text, data):
    result = []
    temp_text = text

    for item in sorted(data, key=len, reverse=True):
        pattern = r'\b' + re.escape(item) + r'\b'
        match = re.search(pattern, temp_text)

        if match:
            result.append(item)
            temp_text = re.sub(pattern, ' ', temp_text)

    return result

# ==============================
# MAIN FUNCTION
# ==============================

def extract_entities(text):

    text = clean_text(text)
    entities = {}

    # =================
    # CUSTOMER
    # =================
    # entities["CUSTOMER_NAME"] = extract_single(text, CUSTOMER_NAME)
    entities["CUSTOMER_NAME"] = extract_customer_name(text, CUSTOMER_NAME)

    # =================
    # STATUS
    # =================
    status = extract_multiple(text, STATUS_SORTED)

    normalized_status = []
    intensity = []

    for raw in status:
        temp = raw

        if "sangat" in temp:
            intensity.append("sangat")
            temp = temp.replace("sangat", "").strip()
        else:
            intensity.append(None)

        normalized = STATUS_NORMALIZATION.get(temp, temp)
        normalized_status.append(normalized)

    entities["STATUS_RAW"] = status
    entities["STATUS"] = normalized_status
    entities["INTENSITY"] = intensity

    # =================
    # BASIC
    # =================
    entities["FREQUENCY"] = extract_single(text, FREQUENCY)
    entities["MONTH"] = extract_single(text, MONTH)

    metric = extract_single(text, METRIC)
    if metric:
        metric = [METRIC_NORMALIZATION.get(metric[0], metric[0])]
    entities["METRIC"] = metric

    entities["TRANSACTION_TYPE"] = extract_single(text, TRANSACTION_TYPE)
    entities["COMPARISON"] = extract_single(text, COMPARISON)
    entities["REWARD"] = extract_single(text, REWARD)
    entities["REASON"] = extract_single(text, REASON)

    entities["DATE"] = re.findall(DATE_PATTERN, text)
    entities["YEAR"] = re.findall(YEAR_PATTERN, text)

    # =================
    # RESULT COUNT
    # =================
    result = re.findall(RESULT_COUNT_PATTERN, text)
    top = re.findall(TOP_N_PATTERN, text)

    result = [int(x) for x in result]

    for match in top:
        num = re.findall(r'\d+', match[0])
        if num:
            result.append(int(num[0]))

    entities["RESULT_COUNT"] = sorted(set(result)) or [10]

    # =================
    # TIME VALUE
    # =================
    time_values = re.findall(TIME_VALUE_PATTERN, text)
    entities["TIME_VALUE"] = [int(t[0]) for t in time_values]
    entities["TIME_UNIT"] = [t[1] for t in time_values]

    # =================
    # 🔥 FIX UTAMA: "bulan terakhir", dll
    # =================
    if not entities["TIME_VALUE"]:
        for unit in TIME_UNIT:
            pattern = rf"\b{unit}\s+(terakhir|terakhir ini|terahir)\b"
            if re.search(pattern, text):
                entities["TIME_VALUE"] = [1]
                entities["TIME_UNIT"] = [unit]
                break

    # =================
    # TIME EXPRESSION
    # =================
    entities["TIME_EXPRESSION"] = extract_multiple(text, TIME_EXPRESSION_SORTED)

    if entities["TIME_EXPRESSION"]:
        entities["TIME_EXPRESSION"] = [
            TIME_EXPRESSION_NORMALIZATION.get(exp, exp)
            for exp in entities["TIME_EXPRESSION"]
        ]

    # =================
    # PRIORITAS VALUE
    # =================
    if entities["TIME_VALUE"]:
        entities["TIME_EXPRESSION"] = []

    # =================
    # TIME NORMALIZED
    # =================
    time_normalized = None

    if entities["TIME_VALUE"] and entities["TIME_UNIT"]:
        time_normalized = f"last_{entities['TIME_VALUE'][0]}_{entities['TIME_UNIT'][0]}"

    elif entities["TIME_EXPRESSION"]:
        exp = entities["TIME_EXPRESSION"][0]
        time_normalized = TIME_NORMALIZATION_MAP.get(exp)

    entities["TIME_NORMALIZED"] = time_normalized

    # =================
    # CLEAN LOGIC
    # =================
    if entities["REASON"]:
        entities["RESULT_COUNT"] = []

    if DEBUG:
        print("TEXT:", text)
        print("ENTITIES:", entities)

    return entities
import re
import pandas as pd
from connection import connection_db

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

# PERBAIKAN: Masukkan kata "rajin" ke daftar STATUS utama agar bisa diekstrak
STATUS = [
    "sangat terbaik","terbaik","biasa","loyal","setia",
    "aktif","pasif","sering","jarang","prioritas",
    "unggulan","top","teratas","unggul","rajin",
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

# regex
DATE_PATTERN = r"\b\d{1,2}\s(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s\d{4}\b"
YEAR_PATTERN = r"\b20\d{2}\b"

RESULT_COUNT_PATTERN = r"\b(\d+)\s+pelanggan\b"
TIME_VALUE_PATTERN = r"\b(\d+)\s+(hari|minggu|bulan|tahun)\b"
TOP_N_PATTERN = r"\b(top\s*\d+|\d+\s*(teratas|terbaik|top))\b"

# SORTING
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
    "unggulan": "terbaik",
    "rajin": "terbaik" # Tambahan normalisasi eksplisit
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

MONTH_DIGITS = {
    "1": "januari", "2": "februari", "3": "maret", "4": "april",
    "5": "mei", "6": "juni", "7": "juli", "8": "agustus",
    "9": "september", "10": "oktober", "11": "november", "12": "desember"
}

MONTH_RANGE_PATTERN = r"\b(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s+(sampai|s\s*/\s*d|dan)\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b"
DIGIT_RANGE_PATTERN = r"\b(\d{1,2})\s+(sampai|s\s*/\s*d|dan)\s+(\d{1,2})\b"

def convert_number(value):
    angka_kata = {
        "satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5,
        "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9, "sepuluh": 10
    }
    if value is None:
        return None
    if str(value).isdigit():
        return int(value)
    return angka_kata.get(str(value).lower(), 10)

def extract_customer_name(text, customer_list):
    for name in customer_list:
        pattern = r'\b' + re.escape(name) + r'\b'
        if re.search(pattern, text):
            return [name]
    return []

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

def extract_entities(text):
    raw_text_for_month = text  # Simpan teks asli sebelum dibersihkan/dipotong untuk bulan
    text = clean_text(text)
    entities = {}
    
    # [1] Deteksi nama, status/kategori
    entities["CUSTOMER_NAME"] = extract_customer_name(text, CUSTOMER_NAME)
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
        
        if temp in ["rajin", "sering", "aktif"]:
            normalized = "terbaik"
        elif temp in ["jarang", "sedikit", "pasif", "kurang aktif", "tidak aktif"]:
            normalized = "biasa"
        else:
            normalized = STATUS_NORMALIZATION.get(temp, temp)
        normalized_status.append(normalized)

    entities["STATUS_RAW"] = status
    entities["STATUS"] = normalized_status
    entities["INTENSITY"] = intensity
    
    # [2] Deteksi TIME_VALUE & TIME_UNIT (Didahulukan agar angkanya tidak dicuri oleh logika bulan)
    time_values = re.findall(TIME_VALUE_PATTERN, text)
    entities["TIME_VALUE"] = [int(t[0]) for t in time_values]
    entities["TIME_UNIT"] = [t[1] for t in time_values]

    if not entities["TIME_VALUE"]:
        for unit in TIME_UNIT:
            pattern = rf"\b{unit}\s+(terakhir|terakhir ini|terahir)\b"
            if re.search(pattern, text):
                entities["TIME_VALUE"] = [1]
                entities["TIME_UNIT"] = [unit]
                break

    # [3] Deteksi YEAR (Tahun)
    entities["YEAR"] = re.findall(YEAR_PATTERN, text)
    
    # [4] DETEKSI BULAN (Eksplisit atau Angka)
    detected_months = []
    
    # JIKA USER MENGGUNAKAN FORMAT "N BULAN TERAKHIR", JANGAN EKSTRAK BULAN ANGKA!
    # Ini mencegah angka "3" dari "3 bulan" dibaca sebagai Maret (Bulan 3)
    is_time_value_active = len(entities["TIME_VALUE"]) > 0 and entities["TIME_UNIT"][0] == "bulan"

    # Perbaikan proteksi kebocoran angka pelanggan ke bulan
    result_count_digits = re.findall(RESULT_COUNT_PATTERN, text)
    top_n_matches = re.findall(TOP_N_PATTERN, text)
    excluded_digits = [x for x in result_count_digits]
    for match in top_n_matches:
        num = re.findall(r'\d+', match[0])
        if num: excluded_digits.extend(num)

    if not is_time_value_active:
        range_match = re.search(MONTH_RANGE_PATTERN, text)
        digit_range_match = re.search(DIGIT_RANGE_PATTERN, text)
        
        if range_match:
            m1, _, m2 = range_match.groups()
            if m1 in MONTH and m2 in MONTH:
                idx1 = MONTH.index(m1)
                idx2 = MONTH.index(m2)
                if idx1 <= idx2:
                    detected_months = MONTH[idx1:idx2+1]
                else:
                    detected_months = [m1, m2]
        elif digit_range_match:
            d1, _, d2 = digit_range_match.groups()
            m1 = MONTH_DIGITS.get(d1)
            m2 = MONTH_DIGITS.get(d2)
            if m1 and m2:
                idx1 = MONTH.index(m1)
                idx2 = MONTH.index(m2)
                if idx1 <= idx2:
                    detected_months = MONTH[idx1:idx2+1]
                else:
                    detected_months = [m1, m2]
        else:
            # Cari nama bulan teks satuan
            for m in MONTH:
                if re.search(r'\b' + re.escape(m) + r'\b', text):
                    detected_months.append(m)
            
            # Cari angka bulan mandiri (1-12) yang bukan bagian dari tahun atau result count
            digit_matches = re.findall(r'\b\d{1,2}\b', text)
            for d in digit_matches:
                if d in excluded_digits:
                    continue
                if d in MONTH_DIGITS:
                    # Pastikan bukan bagian dari angka tahun 2026
                    if not any(d in y for y in entities.get("YEAR", [])):
                        # Kasus khusus: "bulan 4,5 dan 6" -> Tangkap semua angka bulan yang valid
                        if MONTH_DIGITS[d] not in detected_months:
                            detected_months.append(MONTH_DIGITS[d])
                            
            # Sortir urutan bulan berdasarkan kalender agar berurutan (Jan -> Des)
            detected_months = sorted(detected_months, key=lambda x: MONTH.index(x))

    entities["MONTH"] = detected_months

    # [5] Sisa kodingan ekstraksi kriteria lainnya
    entities["FREQUENCY"] = extract_single(text, FREQUENCY)
    metric = extract_single(text, METRIC)
    if metric:
        metric = [METRIC_NORMALIZATION.get(metric[0], metric[0])]
    entities["METRIC"] = metric

    entities["TRANSACTION_TYPE"] = extract_single(text, TRANSACTION_TYPE)
    entities["COMPARISON"] = extract_single(text, COMPARISON)
    entities["REWARD"] = extract_single(text, REWARD)
    entities["REASON"] = extract_single(text, REASON)
    entities["DATE"] = re.findall(DATE_PATTERN, text)

    result = re.findall(RESULT_COUNT_PATTERN, text)
    top = re.findall(TOP_N_PATTERN, text)
    result = [int(x) for x in result]
    for match in top:
        num = re.findall(r'\d+', match[0])
        if num: result.append(int(num[0]))
    
    # RAPIKAN OUTPUT ENTITIES: Mengonversi value ke Tipe Data Tunggal / Bersih
    raw_count = sorted(set(result)) or [10]
    entities["RESULT_COUNT"] = convert_number(raw_count[0])

    entities["TIME_EXPRESSION"] = extract_multiple(text, TIME_EXPRESSION_SORTED)
    if entities["TIME_EXPRESSION"]:
        entities["TIME_EXPRESSION"] = [TIME_EXPRESSION_NORMALIZATION.get(exp, exp) for exp in entities["TIME_EXPRESSION"]]

    if entities["TIME_VALUE"]:
        entities["TIME_VALUE"] = convert_number(entities["TIME_VALUE"][0])
        entities["TIME_EXPRESSION"] = []
    else:
        entities["TIME_VALUE"] = None

    time_normalized = None
    if entities["TIME_VALUE"] and entities["TIME_UNIT"]:
        time_normalized = f"last_{entities['TIME_VALUE']}_{entities['TIME_UNIT'][0]}"
    elif entities["TIME_EXPRESSION"]:
        time_normalized = TIME_NORMALIZATION_MAP.get(entities["TIME_EXPRESSION"][0])
    entities["TIME_NORMALIZED"] = time_normalized

    if entities["REASON"]:
        entities["RESULT_COUNT"] = 0

    return entities
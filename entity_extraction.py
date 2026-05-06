import re
from connection import connection_db

def load_customer_names():

    conn = connection_db()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT nama FROM pelanggan")
    names = list(set([row[0].lower() for row in cursor.fetchall()]))

    cursor.close()
    conn.close()

    return names

CUSTOMER_NAME = load_customer_names()

STATUS = [
    "terbaik",
    "sangat terbaik",
    "biasa",
    "loyal",
    "setia",
    "aktif",
    "pasif",
    "sering",
    "jarang",
    "prioritas"
]

NUMBER_WORDS = {
    "satu": 1,
    "dua": 2,
    "tiga": 3,
    "empat": 4,
    "lima": 5,
    "enam": 6,
    "tujuh": 7,
    "delapan": 8,
    "sembilan": 9,
    "sepuluh": 10,
    "sebelas": 11,
    "dua belas": 12,
    "tiga belas": 13,
    "empat belas": 14,
    "lima belas": 15,
    "enam belas": 16,
    "tujuh belas": 17,
    "delapan belas": 18,
    "sembilan belas": 19,
    "dua puluh": 20,
}

NUMBER_WORDS_SORTED = sorted(
    NUMBER_WORDS.items(),
    key=lambda x: len(x[0]),
    reverse=True
)

TIME_EXPRESSION = [
    "ini",
    "lalu",
    "terakhir",
    "terahir",
    "sekarang",
    "kemarin",
    "selama",
    "saat",
    "bulan ini",
    "minggu ini",
    "hari ini",
    "saat ini",
]

MONTH = [
    "januari","februari","maret","april","mei","juni",
    "juli","agustus","september","oktober","november","desember"
]

FREQUENCY = [
    "kali"
]

TIME_UNIT = [
    "hari",
    "minggu",
    "bulan",
    "tahun"
]

METRIC = [
    "pendapatan","omset","penghasilan","income",
    "transaksi","frekuensi","jumlah","total"
]

TRANSACTION_TYPE = [
    "cuci",
    "laundry",
    "setrika",
    "cuci setrika",
    "kiloan",
    "satuan"
]

COMPARISON = [
    "terbanyak",
    "tertinggi",
    "terendah",
    "paling",
    "lebih",
    "kurang"
]

REWARD = [
    "hadiah",
    "reward",
    "bonus",
    "diskon",
    "voucher"
]

REASON = [
    "kenapa",
    "mengapa",
    "alasan",
    "penyebab",
    "faktor"
]

DATE_PATTERN = r"\b\d{1,2}\s(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\s\d{4}\b"

YEAR_PATTERN = r"\b20\d{2}\b"

RESULT_COUNT_PATTERN = r"\b(\d+)\s+pelanggan\b"

TIME_VALUE_PATTERN = r"\b(\d+)\s+(hari|minggu|bulan|tahun)\b"

STATUS_SORTED = sorted(STATUS, key=len, reverse=True)


def extract_list(text, data):

    result = []

    data_sorted = sorted(data, key=len, reverse=True)

    for item in data_sorted:

        pattern = r'\b' + re.escape(item) + r'\b' 

        if re.search(pattern, text):
            result.append(item)
            break

    return result


def extract_regex(text, pattern):

    return re.findall(pattern, text)


def extract_entities(text):

    text = text.lower()

    entities = {}

    entities["CUSTOMER_NAME"] = extract_list(text, CUSTOMER_NAME)

    entities["STATUS"] = extract_list(text, STATUS_SORTED)

    entities["TIME_EXPRESSION"] = extract_list(text, TIME_EXPRESSION)
    
    entities["TIME_UNIT"] = extract_list(text, TIME_UNIT)

    if entities.get('TIME_EXPRESSION'):
        exp = entities["TIME_EXPRESSION"][0]

        if exp in ["bulan ini", "minggu ini", "tahun ini", "hari ini", "saat ini", "sekarang"]:
            entities["TIME_UNIT"] = []

    entities["FREQUENCY"] = extract_list(text, FREQUENCY)

    entities["MONTH"] = extract_list(text, MONTH)

    entities["METRIC"] = extract_list(text, METRIC)

    entities["TRANSACTION_TYPE"] = extract_list(text, TRANSACTION_TYPE)

    entities["COMPARISON"] = extract_list(text, COMPARISON)

    entities["REWARD"] = extract_list(text, REWARD)

    entities["REASON"] = extract_list(text, REASON)

    entities["DATE"] = extract_regex(text, DATE_PATTERN)

    entities["YEAR"] = extract_regex(text, YEAR_PATTERN)

    # RESULT COUNT (contoh: 10 pelanggan)
    digit_result = extract_regex(text, RESULT_COUNT_PATTERN)

    word_result = []

    for word, number in NUMBER_WORDS_SORTED:
        pattern = r'\b' + word + r'\s+pelanggan\b'
        if re.search(pattern, text):
            word_result.append(str(number))

    entities["RESULT_COUNT"] = list(set(digit_result + word_result))

    # TIME VALUE (contoh: 2 bulan)
    time_values = re.findall(TIME_VALUE_PATTERN, text)
    time_digit = [t[0] for t in time_values]

    time_word = []

    for word, number in NUMBER_WORDS_SORTED:
        for unit in TIME_UNIT:
            pattern = r'\b' + word + r'\s+' + unit + r'\b'
            if re.search(pattern, text):
                time_word.append(str(number))

    entities["TIME_VALUE"] = list(set(time_digit + time_word))

    return entities


# TESTING

# text = "berikan sebelas pelanggan yang sangat terbaik dalam 2 bulan terakhir ini"

# print(text)

# hasil = extract_entities(text.lower().strip())

# print("\nHASIL ENTITY:")

# for key, value in hasil.items():

#     if value:
#         print(key, ":", value)
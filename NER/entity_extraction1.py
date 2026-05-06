import re

STATUS = [
    "terbaik",
    "loyal",
    "setia",
    "sering",
    "jarang",
    "aktif",
    "pasif",
    "prioritas"
]

TIME_UNIT = [
    "hari",
    "minggu",
    "bulan",
    "tahun"
]

TIME_REF = [
    "ini",
    "terakhir",
    "kemarin",
    "sekarang"
]

METRIC = [
    "pendapatan",
    "income",
    "omzet",
    "penghasilan"
]

CUSTOMER_TYPE = [
    "vip",
    "prioritas",
    "utama"
]


def extract_entity(sentence):

    sentence = sentence.lower()
    words = sentence.split()

    result = {}

    # STATUS
    for word in words:
        if word in STATUS:
            result['STATUS'] = word

    # TIME NUMBER
    number = re.findall(r'\d+', sentence)
    if number:
        result['TIME_NUMBER'] = number[0]

    # TIME UNIT
    for word in words:
        if word in TIME_UNIT:
            result['TIME_UNIT'] = word

    # TIME REF
    for word in words:
        if word in TIME_REF:
            result['TIME_REF'] = word

    # METRIC
    for word in words:
        if word in METRIC:
            result['METRIC'] = word

    # CUSTOMER TYPE
    for word in words:
        if word in CUSTOMER_TYPE:
            result['CUSTOMER_TYPE'] = word

    return result


print(extract_entity("hadiah terbaik untuk pelanggan loyal"))


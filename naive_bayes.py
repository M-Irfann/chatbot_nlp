import re
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

from entity_extraction import extract_entities, clean_text
from connection import connection_db
from router import intent_router

# ===========================
# CONNECTION
# ===========================
conn = connection_db()

# ===========================
# PREPROCESS FUNCTION
# ===========================
def preprocess(sentence):

    sentence = clean_text(sentence)

    return sentence.strip()


# ===========================
# TRAINING MODEL
# ===========================
query = "SELECT kalimat, intent FROM dataset_intent_2"

df = pd.read_sql(query, conn)

sentences = df['kalimat'].apply(preprocess).tolist()

labels = df['intent'].tolist()


# ===========================
# TFIDF VECTORIZER
# unigram + bigram
# ===========================
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2)
)

X = vectorizer.fit_transform(sentences)


# ===========================
# TRAIN MODEL
# ===========================
model = MultinomialNB()

model.fit(X, labels)


# ===========================
# RULE BASED INTENT
# ===========================
def rule_based_intent(processed):

    # ====================================
    # PRIORITY 1
    # TANYA ALASAN
    # ====================================

    alasan_keywords = [
        "kenapa",
        "mengapa",
        "alasan",
        "penyebab",
        "jelaskan",
        "apa yang membuat",
        "apa sebab"
    ]

    hadiah_keywords = [
        "hadiah",
        "reward",
        "bonus"
    ]

    # ====================================
    # SPECIAL CASE
    # contoh:
    # kenapa pelanggan dapat reward
    # ====================================
    if (
        any(k in processed for k in alasan_keywords)
        and
        any(k in processed for k in hadiah_keywords)
    ):
        return "INT_TANYA_ALASAN"

    # ====================================
    # NORMAL ALASAN
    # ====================================
    if any(k in processed for k in alasan_keywords):
        return "INT_TANYA_ALASAN"

    # ====================================
    # PRIORITY 2
    # REKOMENDASI HADIAH
    # ====================================
    hadiah_full_keywords = [
        "hadiah",
        "reward",
        "bonus",
        "rekomendasi hadiah",
        "saran hadiah",
        "hadiah apa",
        "reward apa"
    ]

    if any(k in processed for k in hadiah_full_keywords):
        return "INT_REKOMENDASI_HADIAH"

    # ====================================
    # PRIORITY 3
    # RANKING PELANGGAN
    # ====================================
    ranking_keywords = [
        "siapa",
        "tampilkan",
        "daftar",
        "ranking",
        "peringkat",
        "pelanggan terbaik",
        "pelanggan biasa",
        "pelanggan unggulan",
        "nilai tertinggi",
        "posisi teratas",
        "berikan pelanggan",
        "top pelanggan",
        "pelanggan teratas",
        "ranking pelanggan"
    ]

    if any(k in processed for k in ranking_keywords):
        return "INT_RANKING_PELANGGAN"

    return None


# ===========================
# CLASSIFY FUNCTION
# ===========================
def classify_intents(text):

    text = clean_text(text)

    parts = [text]

    results = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

        # ===========================
        # ENTITY EXTRACTION
        # ===========================
        entities = extract_entities(part)

        # ===========================
        # PREPROCESS
        # ===========================
        processed = preprocess(part)

        # ===========================
        # RULE BASED
        # ===========================
        intent = rule_based_intent(processed)

        # ===========================
        # FALLBACK MACHINE LEARNING
        # ===========================
        if intent is None:

            vec = vectorizer.transform([processed])

            probabilities = model.predict_proba(vec)[0]

            max_prob = probabilities.max()

            predicted_intent = model.predict(vec)[0]

            # ====================================
            # kalau confidence terlalu rendah
            # fallback default
            # ====================================
            if max_prob < 0.45:
                intent = "INT_RANKING_PELANGGAN"
            else:
                intent = predicted_intent

        # ===========================
        # SAVE RESULT
        # ===========================
        results.append({
            "kalimat": part,
            "intent": intent,
            "entities": entities
        })

    return results



# ===========================
# TEST FROM EXCEL
# ===========================
# df_test = pd.read_excel("insert_data/check_question_addition_2.xlsx")

# correct = 0
# total = 0

# for index, row in df_test.iterrows():

#     text = row["kalimat"]
#     expected_intent = row["intent"]

#     results = classify_intents(text)

#     for r in results:

#         total += 1

#         print("\n====================================")
#         print("Kalimat :", r["kalimat"])
#         print("Expected :", expected_intent)
#         print("Predict  :", r["intent"])

#         if r["intent"] == expected_intent:
#             print("✅ BENAR")
#             correct += 1
#         else:
#             print("❌ SALAH")

#         # entities
#         for k, v in r["entities"].items():

#             if v:
#                 print(k, ":", v)

#         # response test
#         response = intent_router(
#             r['intent'],
#             r['entities']
#         )

#         print("response :", response)


# ===========================
# ACCURACY
# ===========================
# print("\n====================================")
# print("TOTAL :", total)
# print("BENAR :", correct)

# if total > 0:
#     accuracy = (correct / total) * 100
#     print("ACCURACY :", round(accuracy, 2), "%")


# ===========================
# TEST SINGLE EXAMPLE
# ===========================
# text = "siapa pelanggan terbaik bulan ini" 

# results = classify_intents(text)

# for r in results:
    
#     print("\nKalimat :", r["kalimat"])  
#     print("Intent :", r["intent"])

#     # print("Entities :", r['entities'])

#     for k, v in r["entities"].items():

#         if v:
#             print(" ", k, ":", v)

#     response = intent_router(r['intent'], r['entities'])
#     print("response",response)
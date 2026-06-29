import re
import pandas as pd
import time

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from function_rangking_pelanggan import evaluate_weighted_product

from entity_extraction import extract_entities, clean_text
from connection import connection_db
from router import intent_router

conn = connection_db()


def preprocess(sentence):

    sentence = clean_text(sentence)

    return sentence.strip()


# TRAINING MODEL
query = "SELECT kalimat, intent FROM dataset_intent_2"

df = pd.read_sql(query, conn)

sentences = df['kalimat'].apply(preprocess).tolist()

labels = df['intent'].tolist()


# TFIDF VECTORIZER
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2)
)

X = vectorizer.fit_transform(sentences)


# TRAIN MODEL
model = MultinomialNB()

model.fit(X, labels)


def rule_based_intent(processed):


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

    if (
        any(k in processed for k in alasan_keywords)
        and
        any(k in processed for k in hadiah_keywords)
    ):
        return "INT_TANYA_ALASAN"


    if any(k in processed for k in alasan_keywords):
        return "INT_TANYA_ALASAN"

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


# CLASSIFY FUNCTION
def classify_intents(text):

    text = clean_text(text)

    parts = [text]

    results = []

    for part in parts:

        part = part.strip()

        if not part:
            continue

   
        entities = extract_entities(part)

        processed = preprocess(part)

        intent = rule_based_intent(processed)

        if intent is None:

            vec = vectorizer.transform([processed])

            probabilities = model.predict_proba(vec)[0]

            max_prob = probabilities.max()

            predicted_intent = model.predict(vec)[0]

            if max_prob < 0.45:
                intent = "INT_RANKING_PELANGGAN"
            else:
                intent = predicted_intent

        results.append({
            "kalimat": part,
            "intent": intent,
            "entities": entities
        })

    return results



# TEST FROM EXCEL

df_test = pd.read_excel("check_question_addition_uji_coba_entity.xlsx")

correct = 0
total = 0

for index, row in df_test.iterrows():

    text = row["kalimat"]
    expected_intent = row["intent"]

    result = classify_intents(text)

    if isinstance(result, list):
        result = result[0]  

    predicted_intent = result["intent"]

    total += 1

    print("\n====================================")
    print("Kalimat :", text)
    print("Expected :", expected_intent)
    print("Predict  :", predicted_intent)

    if predicted_intent == expected_intent:
        print("✅ BENAR")
        correct += 1

    else:
        print("❌ SALAH")

    entities = result.get("entities", {})

    for k, v in entities.items():
        if v:
            print(k, ":", v)

    # =========================
    # RESPONSE
    # =========================
    response = intent_router(
        predicted_intent,
        entities
    )

    print("response :", response)

    time.sleep(0.5)


# #     # for testing 
#     if predicted_intent == "INT_RANKING_PELANGGAN":

#         print("\n========== FULL RANKING (DEBUG) ==========")

#         full_rank = evaluate_weighted_product(
#             "2026-05-01",
#             "2026-06-23"
#         )

#         for i, r in enumerate(full_rank):
#             print(
#                 i + 1,
#                 r["nama"],
#                 "S:", round(r["score"], 2),
#                 "V:", round(r["nilai_wp"], 4)
#             )



# ACCURACY

# print("\n====================================")
# print("TOTAL :", total)
# print("BENAR :", correct)

# if total > 0:
#     accuracy = (correct / total) * 100
#     print("ACCURACY :", round(accuracy, 2), "%")











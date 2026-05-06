import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

from entity_extraction_1 import extract_entities, clean_text
from connection import connection_db
from router import intent_router

# conn = connection_db()
conn = connection_db()

# ===========================
# PREPROCESS FUNCTION
# ===========================
def preprocess(sentence):

    sentence = clean_text(sentence)
    return sentence

# ===========================
# TRAINING MODEL
# ===========================
query = "SELECT kalimat, intent FROM dataset_intent_2"
df = pd.read_sql(query, conn)

sentences = df['kalimat'].apply(preprocess).tolist()
labels = df['intent'].tolist()

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(sentences)

model = MultinomialNB()
model.fit(X, labels)

# ===========================
# CLASSIFY FUNCTION
# ===========================
def classify_intents(text):

    text = clean_text(text)

    # pisahkan berdasarkan kata hubung dan tanda baca
    parts = [text]
    
    results = []

    for part in parts:
 
        part = part.strip()

        if part:

            # ambil entity dari kalimat asli
            entities = extract_entities(part)

            # untuk intent, proses kalimat tanpa stopword removal
            processed = preprocess(part)

            vec = vectorizer.transform([processed])

            intent = model.predict(vec)[0]

            results.append({
                "kalimat": part,
                "intent": intent,
                "entities": entities
            })

    return results


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


# TEST FROM EXCEL
# ===========================
df_test = pd.read_excel("check_question_addition_2.xlsx")

for index, row in df_test.iterrows():
    text = row["kalimat"]        
    expected_intent = row["intent"]

    results = classify_intents(text)

    for r in results:
        print("\n====================================")
        print("Kalimat :", r["kalimat"])
        print("My Intent :", r["intent"])
        # print("expected Intent :", expected_intent)

        # if r["intent"] == expected_intent:
        #     print("✅ Benar")
        # else:
        #     print("❌ Salah")

        for k, v in r["entities"].items():

            if v:
                print(" ", k, ":", v)
        
        response = intent_router(r['intent'], r['entities'])
        print("response",response)

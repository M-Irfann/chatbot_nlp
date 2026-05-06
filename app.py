from flask import Flask, request, jsonify
from flask_cors import CORS
from router import intent_router
from naive_bayes import classify_intents
# --- IMPORT FILE BARU ---
from intent_engine import validate_message 

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    text = data.get("message", "")
    reply_id = data.get("reply_id")

    # --- LANGKAH 1: VALIDASI AWAL ---
    is_valid, error_msg = validate_message(text)
    
    if not is_valid:
        return jsonify({
            "intent": "INT_UNKNOWN",
            "entities": {},
            "reply_id": reply_id,
            "response": {
                "message": error_msg,
                "chat_id": None
            }
        })

    # --- LANGKAH 2: PROSES NAIVE BAYES (Jika Lolos Validasi) ---
    results = classify_intents(text)
    r = results[0]
    entities = r["entities"]
    
    # Inject ke entities
    entities["REPLY_ID"] = reply_id

    # Proses ke Router
    response = intent_router(r["intent"], entities)

    return jsonify({
        "intent": r["intent"],
        "entities": entities,
        "reply_id": reply_id, 
        "response": response
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
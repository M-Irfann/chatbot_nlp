from flask import Blueprint, request, jsonify

from router import intent_router
from naive_bayes import classify_intents
from intent_engine import validate_message

api_routes = Blueprint("api_routes", __name__)

@api_routes.route("/chat", methods=["POST"])
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

    # --- LANGKAH 2: PROSES NAIVE BAYES ---
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
from flask import Blueprint, request, jsonify

from router import intent_router
from naive_bayes import classify_intents
from intent_engine import validate_message

api_routes = Blueprint("api_routes", __name__)

@api_routes.route("/chat", methods=["POST"])
def chat():

    data = request.json
    text = data.get("message", "")
    chat_id = data.get("chat_id")

    is_valid, error_msg = validate_message(text)

    if not is_valid:
        return jsonify({
            "intent": "INT_UNKNOWN",
            "entities": {},
            "response": {
                "message": error_msg,
                "chat_id": chat_id
            }
        })

    results = classify_intents(text)

    r = results[0]

    entities = r["entities"]

    entities["CHAT_ID"] = chat_id

    response = intent_router(r["intent"], entities)

    return jsonify({
        "intent": r["intent"],
        "entities": entities,
        "response": response
    })
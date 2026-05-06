from function_rangking_pelanggan import handle_tentukan_pelanggan_terbaik
from function_tanya_alasan import handle_tanya_alasan
from function_tanya_hadiah import handle_tanya_hadiah

ROUTES = {
    "INT_RANKING_PELANGGAN": handle_tentukan_pelanggan_terbaik,
    "INT_TANYA_ALASAN": handle_tanya_alasan,
    "INT_REKOMENDASI_HADIAH": handle_tanya_hadiah,
}

def intent_router(intent, entities):

    handler = ROUTES.get(intent)

    if handler:
        return handler(entities)

    return "Intent tidak dikenali"
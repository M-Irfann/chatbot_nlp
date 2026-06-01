from flask import request, jsonify
from connection import connection_db

def search_pelanggan_controller():

    keyword = request.args.get("keyword")

    conn = connection_db()

    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT DISTINCT nama
        FROM pelanggan
        WHERE nama LIKE %s
        LIMIT 10
    """

    cursor.execute(query, (f"%{keyword}%",))

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)
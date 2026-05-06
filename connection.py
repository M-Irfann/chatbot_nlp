import mysql.connector

def connection_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="python_api"
    )

    return conn
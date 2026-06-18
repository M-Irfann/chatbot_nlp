import mysql.connector

# for docker 
def connection_db():
    conn = mysql.connector.connect(
        host="mysql_db",
        user="root",
        password="",
        database="python_api"
    )

    return conn

# def connection_db():
#     conn = mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="",
#         database="python_api"
#     )

#     return conn
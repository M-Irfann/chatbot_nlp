import pandas as pd
import mysql.connector

# koneksi ke database
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="python_api"
)

cursor = conn.cursor()

# baca file excel
# df = pd.read_excel("400-dataset-28-3-28.xlsx")

for index, row in df.iterrows():
    sql = "INSERT INTO dataset_intent_2 (kalimat, intent) VALUES (%s, %s)"
    values = (row['kalimat'], row['intent'])
    cursor.execute(sql, values)

# 4. Commit dan tutup koneksi
conn.commit()
cursor.close()
conn.close()

print("Data berhasil dimasukkan ke MySQL!")
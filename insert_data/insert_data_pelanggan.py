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
# df = pd.read_excel("data_pelanggan_sebagian_5_2.xlsx")

df.columns = df.columns.str.strip()
# print(df.columns.tolist())
# loop insert
for index, row in df.iterrows():

    nama = str(row['Nama']).strip().lower()
    nominal = int(row['Nominal'])
    jenis = str(row['Jenis Cuci']).strip().lower()
    berat = float(row['Berat (kg)'])

    tanggal = pd.to_datetime(row['Tanggal']).strftime('%Y-%m-%d')


    query = """
    INSERT INTO pelanggan (nama, nominal, jenis_cuci, berat, tanggal)
    VALUES (%s, %s, %s, %s, %s)
    """

    cursor.execute(query, (nama, nominal, jenis, berat, tanggal))


conn.commit()

print("DATA BERHASIL DIIMPORT")

cursor.close()
conn.close()

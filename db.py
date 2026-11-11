import os
import pymysql
from dotenv import load_dotenv
from flask import request

load_dotenv()


def get_db():
    """Membuka koneksi ke database MySQL."""
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
    )


def catat_log(aksi, detail=None, user_id=None, username=None):
    """Menulis satu baris ke buku tamu (tabel log_aktivitas)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO log_aktivitas (user_id, username, aksi, detail, ip_address) "
                "VALUES (%s, %s, %s, %s, %s)",
                (user_id, username, aksi, detail, request.remote_addr),
            )
        conn.commit()
    finally:
        conn.close()
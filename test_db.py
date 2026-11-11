from db import get_db

conn = get_db()
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) AS jumlah FROM users")
    print("Koneksi berhasil!", cur.fetchone())
conn.close()
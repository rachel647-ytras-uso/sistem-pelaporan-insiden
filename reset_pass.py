import getpass
from werkzeug.security import generate_password_hash
from db import get_db

username = input("Username yang mau di-reset: ").strip()
password = getpass.getpass("Password baru (tidak tampil saat diketik): ")
ulang = getpass.getpass("Ulangi password baru: ")

if password != ulang:
    print("Password tidak sama. Dibatalkan.")
elif len(password) < 12:
    print("Password minimal 12 karakter. Dibatalkan.")
else:
    conn = get_db()
    try:
        with conn.cursor() as cur:
            jumlah = cur.execute(
                "UPDATE users SET password_hash = %s, failed_attempts = 0, locked_until = NULL "
                "WHERE username = %s",
                (generate_password_hash(password), username),
            )
        conn.commit()
        if jumlah:
            print("Password berhasil diganti.")
        else:
            print("Username tidak ditemukan.")
    finally:
        conn.close()
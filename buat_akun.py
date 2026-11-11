import getpass
from werkzeug.security import generate_password_hash
from db import get_db

ROLE_VALID = ("user", "admin", "superadmin")

username = input("Username: ").strip()
role = input("Role (user/admin/superadmin): ").strip().lower()
password = getpass.getpass("Password (tidak tampil saat diketik): ")
ulang = getpass.getpass("Ulangi password: ")

if role not in ROLE_VALID:
    print("Role tidak valid. Dibatalkan.")
elif password != ulang:
    print("Password tidak sama. Dibatalkan.")
elif len(password) < 12:
    print("Password minimal 12 karakter. Dibatalkan.")
else:
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, generate_password_hash(password), role),
            )
        conn.commit()
        print(f"Akun {username} ({role}) berhasil dibuat.")
    finally:
        conn.close()
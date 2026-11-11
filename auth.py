from functools import wraps
from flask import session, redirect, url_for, flash, abort, request
from db import get_db, catat_log

def login_required(f):
    """Satpam 1: harus sudah login, dan akunnya masih aktif."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "info")
            return redirect(url_for("login"))

        # Cek ulang ke database, jangan cuma percaya kartu
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role, is_active FROM users WHERE id = %s",
                    (session["user_id"],),
                )
                user = cur.fetchone()
        finally:
            conn.close()

        if user is None or not user["is_active"]:
            session.clear()
            flash("Sesi berakhir. Silakan login kembali.", "info")
            return redirect(url_for("login"))

        session["role"] = user["role"]  # ikuti role terbaru dari database
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Satpam 2: hanya role tertentu yang boleh masuk."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("role") not in roles:
                catat_log(
                    "akses_ditolak",
                    f"role {session.get('role')} mencoba membuka {request.path}",
                    session.get("user_id"),
                    session.get("username"),
                )
                abort(403)
            return f(*args, **kwargs)
        return login_required(wrapper)
    return decorator
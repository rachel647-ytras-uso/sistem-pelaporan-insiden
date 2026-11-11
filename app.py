import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, session, abort
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db, catat_log
from form import LoginForm, LaporanForm, TanganiForm, AkunBaruForm, UbahAkunForm
from auth import login_required, role_required

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

MAKS_GAGAL = 5
LAMA_KUNCI = timedelta(minutes=15)


# =====================================================
# 1. HALAMAN UMUM: beranda, login, logout, dashboard
# =====================================================

@app.route("/")
def beranda():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data

        conn = get_db()
        try:
            with conn.cursor() as cur:
                # 1. Cari akun (pakai %s = anti SQL Injection)
                cur.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cur.fetchone()

                # 2. Username tidak terdaftar
                if user is None:
                    catat_log("login_gagal", "username tidak terdaftar", username=username)
                    flash("Username atau password salah.", "danger")
                    return redirect(url_for("login"))

                # 3. Akun sedang dikunci
                if user["locked_until"] and user["locked_until"] > datetime.now():
                    sisa = int((user["locked_until"] - datetime.now()).total_seconds() // 60) + 1
                    catat_log("login_ditolak", "akun terkunci", user["id"], username)
                    flash(f"Akun dikunci sementara. Coba lagi dalam {sisa} menit.", "danger")
                    return redirect(url_for("login"))

                # 4. Password salah
                if not check_password_hash(user["password_hash"], password):
                    gagal = user["failed_attempts"] + 1
                    if gagal >= MAKS_GAGAL:
                        cur.execute(
                            "UPDATE users SET failed_attempts = 0, locked_until = %s WHERE id = %s",
                            (datetime.now() + LAMA_KUNCI, user["id"]),
                        )
                        conn.commit()
                        catat_log("akun_dikunci", f"{MAKS_GAGAL}x password salah", user["id"], username)
                    else:
                        cur.execute(
                            "UPDATE users SET failed_attempts = %s WHERE id = %s",
                            (gagal, user["id"]),
                        )
                        conn.commit()
                        catat_log("login_gagal", f"password salah ({gagal}/{MAKS_GAGAL})", user["id"], username)
                    flash("Username atau password salah.", "danger")
                    return redirect(url_for("login"))

                # 5. Akun dinonaktifkan
                if not user["is_active"]:
                    catat_log("login_ditolak", "akun nonaktif", user["id"], username)
                    flash("Akun ini dinonaktifkan. Hubungi super admin.", "danger")
                    return redirect(url_for("login"))

                # 6. Semua lolos: reset hitungan gagal
                cur.execute(
                    "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = %s",
                    (user["id"],),
                )
                conn.commit()
        finally:
            conn.close()

        # 7. Beri kartu akses (session)
        session.clear()
        session.permanent = True
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        catat_log("login_berhasil", None, user["id"], username)
        return redirect(url_for("dashboard"))

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    if "user_id" in session:
        catat_log("logout", None, session["user_id"], session["username"])
    session.clear()
    flash("Kamu sudah keluar.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# =====================================================
# 2. RUANGAN USER: buat laporan, laporan saya
# =====================================================

@app.route("/laporan/baru", methods=["GET", "POST"])
@role_required("user")
def laporan_baru():
    form = LaporanForm()
    if form.validate_on_submit():
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO laporan (user_id, judul, deskripsi, kategori, tingkat) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (session["user_id"], form.judul.data.strip(), form.deskripsi.data.strip(),
                     form.kategori.data, form.tingkat.data),
                )
                laporan_id = cur.lastrowid
            conn.commit()
        finally:
            conn.close()
        catat_log("buat_laporan", f"laporan #{laporan_id}", session["user_id"], session["username"])
        flash("Laporan berhasil dikirim.", "info")
        return redirect(url_for("laporan_saya"))
    return render_template("laporan_form.html", form=form)


@app.route("/laporan/saya")
@role_required("user")
def laporan_saya():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, judul, kategori, tingkat, status, created_at FROM laporan "
                "WHERE user_id = %s ORDER BY created_at DESC",
                (session["user_id"],),
            )
            daftar = cur.fetchall()
    finally:
        conn.close()
    return render_template("laporan_list.html", judul="Laporan saya", daftar=daftar, tampil_pelapor=False)


# =====================================================
# 3. RUANGAN ADMIN: semua laporan, detail & tangani
# =====================================================

@app.route("/admin/laporan")
@role_required("admin", "superadmin")
def semua_laporan():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT l.id, l.judul, l.kategori, l.tingkat, l.status, l.created_at, "
                "u.username AS pelapor FROM laporan l JOIN users u ON l.user_id = u.id "
                "ORDER BY FIELD(l.tingkat, 'kritis', 'tinggi', 'sedang', 'rendah'), l.created_at DESC"
            )
            daftar = cur.fetchall()
    finally:
        conn.close()
    return render_template("laporan_list.html", judul="Semua laporan", daftar=daftar, tampil_pelapor=True)


@app.route("/laporan/<int:laporan_id>", methods=["GET", "POST"])
@login_required
def laporan_detail(laporan_id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT l.*, p.username AS pelapor, a.username AS penangan "
                "FROM laporan l JOIN users p ON l.user_id = p.id "
                "LEFT JOIN users a ON l.ditangani_oleh = a.id WHERE l.id = %s",
                (laporan_id,),
            )
            laporan = cur.fetchone()

            if laporan is None:
                abort(404)

            # Anti IDOR: user hanya boleh membuka laporannya sendiri
            if session["role"] == "user" and laporan["user_id"] != session["user_id"]:
                catat_log("akses_ditolak", f"mencoba membuka laporan #{laporan_id} milik orang lain",
                          session["user_id"], session["username"])
                abort(403)

            form = None
            if session["role"] in ("admin", "superadmin"):
                form = TanganiForm(data={
                    "status": laporan["status"],
                    "catatan_admin": laporan["catatan_admin"] or "",
                })
                if form.validate_on_submit():
                    cur.execute(
                        "UPDATE laporan SET status = %s, catatan_admin = %s, ditangani_oleh = %s "
                        "WHERE id = %s",
                        (form.status.data, form.catatan_admin.data.strip() or None,
                         session["user_id"], laporan_id),
                    )
                    conn.commit()
                    catat_log("ubah_laporan",
                              f"laporan #{laporan_id}: {laporan['status']} -> {form.status.data}",
                              session["user_id"], session["username"])
                    flash("Laporan berhasil diperbarui.", "info")
                    return redirect(url_for("laporan_detail", laporan_id=laporan_id))
    finally:
        conn.close()
    return render_template("laporan_detail.html", laporan=laporan, form=form)


# =====================================================
# 4. RUANGAN SUPER ADMIN: kelola akun, log aktivitas
# =====================================================

@app.route("/superadmin/akun", methods=["GET", "POST"])
@role_required("superadmin")
def kelola_akun():
    form_baru = AkunBaruForm()
    if form_baru.validate_on_submit():
        username = form_baru.username.data.strip()
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    flash("Username sudah dipakai.", "danger")
                else:
                    cur.execute(
                        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                        (username, generate_password_hash(form_baru.password.data), form_baru.role.data),
                    )
                    conn.commit()
                    catat_log("buat_akun", f"{username} sebagai {form_baru.role.data}",
                              session["user_id"], session["username"])
                    flash(f"Akun {username} berhasil dibuat.", "info")
        finally:
            conn.close()
        return redirect(url_for("kelola_akun"))

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, role, is_active, locked_until, created_at FROM users ORDER BY id"
            )
            daftar = cur.fetchall()
    finally:
        conn.close()

    form_ubah = {
        u["id"]: UbahAkunForm(
            prefix=f"u{u['id']}",
            data={"role": u["role"], "is_active": "1" if u["is_active"] else "0"},
        )
        for u in daftar
    }
    return render_template("akun.html", form_baru=form_baru, daftar=daftar,
                           form_ubah=form_ubah, sekarang=datetime.now())


@app.route("/superadmin/akun/<int:user_id>", methods=["POST"])
@role_required("superadmin")
def ubah_akun(user_id):
    form = UbahAkunForm(prefix=f"u{user_id}")
    if not form.validate_on_submit():
        flash("Permintaan tidak valid.", "danger")
        return redirect(url_for("kelola_akun"))

    if user_id == session["user_id"]:
        flash("Kamu tidak bisa mengubah akunmu sendiri.", "danger")
        return redirect(url_for("kelola_akun"))

    aktif = form.is_active.data == "1"
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, role, is_active FROM users WHERE id = %s", (user_id,))
            target = cur.fetchone()
            if target is None:
                abort(404)
            cur.execute(
                "UPDATE users SET role = %s, is_active = %s, failed_attempts = 0, locked_until = NULL "
                "WHERE id = %s",
                (form.role.data, aktif, user_id),
            )
            conn.commit()
    finally:
        conn.close()

    catat_log(
        "ubah_akun",
        f"{target['username']}: role {target['role']} -> {form.role.data}, "
        f"{'aktif' if aktif else 'nonaktif'}",
        session["user_id"], session["username"],
    )
    flash(f"Akun {target['username']} diperbarui.", "info")
    return redirect(url_for("kelola_akun"))


@app.route("/superadmin/log")
@role_required("superadmin")
def lihat_log():
    aksi = request.args.get("aksi", "")
    conn = get_db()
    try:
        with conn.cursor() as cur:
            if aksi:
                cur.execute(
                    "SELECT * FROM log_aktivitas WHERE aksi = %s ORDER BY id DESC LIMIT 200",
                    (aksi,),
                )
            else:
                cur.execute("SELECT * FROM log_aktivitas ORDER BY id DESC LIMIT 200")
            logs = cur.fetchall()
            cur.execute("SELECT DISTINCT aksi FROM log_aktivitas ORDER BY aksi")
            daftar_aksi = [r["aksi"] for r in cur.fetchall()]
    finally:
        conn.close()
    return render_template("log.html", logs=logs, daftar_aksi=daftar_aksi, aksi=aksi)


# =====================================================
# 5. HALAMAN ERROR
# =====================================================

@app.errorhandler(403)
def dilarang(e):
    return render_template("403.html"), 403


if __name__ == "__main__":
    app.run(debug=True)
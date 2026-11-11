# Sistem Pelaporan Insiden Keamanan

Tugas UAS Keamanan Sistem Informasi — [Nama], [NIM]

Sistem web untuk melaporkan dan menangani insiden keamanan siber di sebuah organisasi,
dengan 3 role: User (pelapor), Admin (penangan), Super admin (kelola akun & log).

## Teknologi
Python 3.11, Flask, MySQL 8, PyMySQL, Flask-WTF

## Fitur keamanan
- Password disimpan sebagai hash (scrypt), tidak pernah dalam bentuk asli
- Parameterized query di semua query (anti SQL Injection)
- Token CSRF di semua formulir
- Auto-escape template Jinja (anti XSS)
- Akun dikunci 15 menit setelah 5x salah password (anti brute force)
- Pesan error login yang sama untuk semua kasus (anti user enumeration)
- Role-based access control + pengecekan ulang ke database di setiap request
- Anti IDOR: user hanya bisa membuka laporannya sendiri
- Session cookie HttpOnly, SameSite=Lax, kedaluwarsa 30 menit
- Akun database dengan hak minimal (least privilege)
- Rahasia disimpan di .env, tidak ikut ke repository
- Log aktivitas lengkap dengan alamat IP

## Cara menjalankan
1. `python -m venv venv` lalu `venv\Scripts\activate`
2. `pip install -r requirements.txt`
3. Jalankan `database/schema.sql` di MySQL
4. Buat akun MySQL `app_insiden` dengan hak SELECT, INSERT, UPDATE
5. Salin `.env.example` menjadi `.env`, lalu isi nilainya
6. `python buat_akun.py` untuk membuat super admin pertama
7. `python app.py`, lalu buka http://127.0.0.1:5000

## Penggunaan AI
Sistem ini dibangun langkah demi langkah dengan bantuan AI (Claude) sebagai pemandu.
Setiap bagian kode dipelajari, dijalankan, dan diuji sendiri.
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Masuk")


class LaporanForm(FlaskForm):
    judul = StringField("Judul", validators=[DataRequired(), Length(max=150)])
    kategori = SelectField("Kategori", choices=[
        ("phishing", "Phishing"),
        ("malware", "Malware"),
        ("akses_ilegal", "Akses ilegal"),
        ("kebocoran_data", "Kebocoran data"),
        ("lainnya", "Lainnya"),
    ])
    tingkat = SelectField("Tingkat bahaya", choices=[
        ("rendah", "Rendah"),
        ("sedang", "Sedang"),
        ("tinggi", "Tinggi"),
        ("kritis", "Kritis"),
    ])
    deskripsi = TextAreaField("Deskripsi kejadian", validators=[DataRequired(), Length(max=5000)])
    submit = SubmitField("Kirim laporan")


class TanganiForm(FlaskForm):
    status = SelectField("Status", choices=[
        ("baru", "Baru"),
        ("diproses", "Diproses"),
        ("selesai", "Selesai"),
    ])
    catatan_admin = TextAreaField("Catatan untuk pelapor", validators=[Length(max=5000)])
    submit = SubmitField("Simpan perubahan")


PILIHAN_ROLE = [("user", "User"), ("admin", "Admin"), ("superadmin", "Super admin")]


class AkunBaruForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(),
        Length(min=3, max=50),
        Regexp(r"^[A-Za-z0-9_]+$"),
    ])
    role = SelectField("Role", choices=PILIHAN_ROLE)
    password = PasswordField("Password awal", validators=[DataRequired(), Length(min=12, max=128)])
    submit = SubmitField("Buat akun")


class UbahAkunForm(FlaskForm):
    role = SelectField("Role", choices=PILIHAN_ROLE)
    is_active = SelectField("Status", choices=[("1", "Aktif"), ("0", "Nonaktif")])
    submit = SubmitField("Simpan")
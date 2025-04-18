from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class MasterKaryawan(db.Model):
    __tablename__ = 'tblMstKaryawan'
    NIK = db.Column(db.String(20), primary_key=True)
    Nama = db.Column(db.String(100))
    Bagian = db.Column(db.String(50))
    Jabatan = db.Column(db.String(50))
    IuranWajib = db.Column(db.Float)
    JK = db.Column(db.String(1))  # L/P
    Status = db.Column(db.Integer)
    TMKBaru = db.Column(db.DateTime)  # TMK in Access
    TglKeluar = db.Column(db.DateTime)
    F13 = db.Column(db.Float)
    MaxPlafon = db.Column(db.Float)
    IDKhusus = db.Column(db.String(20))
    ID1 = db.Column(db.String(20))
    MaxPlafonSembako = db.Column(db.Float)

class TransaksiPembelian(db.Model):
    __tablename__ = 'tblTransaksiPembelian'
    NoFakPembelian = db.Column(db.String(20), primary_key=True)
    Periode = db.Column(db.Integer)
    Tanggal = db.Column(db.DateTime)
    Keterangan = db.Column(db.String(200))

class TransaksiPembelianDtl(db.Model):
    __tablename__ = 'tblTransaksiPembelianDtl'
    NoFakPembelian = db.Column(db.String(20), db.ForeignKey('tblTransaksiPembelian.NoFakPembelian'))
    Kode = db.Column(db.String(20))
    NamaBarang = db.Column(db.String(100))
    Qty = db.Column(db.Float)
    Harga = db.Column(db.Float)
    Harga2 = db.Column(db.Float)
    Total = db.Column(db.Float)
    Keterangan = db.Column(db.String(200))
    __table_args__ = (
        db.PrimaryKeyConstraint('NoFakPembelian', 'Kode'),
    )

class TagihanSimpananPinjaman(db.Model):
    __tablename__ = 'tagSimpPinjFix'
    NIK = db.Column(db.String(20), db.ForeignKey('tblMstKaryawan.NIK'), primary_key=True)
    Nama = db.Column(db.String(100))
    Bagian = db.Column(db.String(50))
    Jabatan = db.Column(db.String(50))
    JK = db.Column(db.String(1))
    TMK = db.Column(db.DateTime)
    Iuran = db.Column(db.Float)
    JumlahAngsuran = db.Column(db.Float)
    Jumlah = db.Column(db.Float)

# Additional tables for application functionality
class JenisSimpanan(db.Model):
    __tablename__ = 'jenis_simpanan'
    jenis_id = db.Column(db.String(10), primary_key=True)
    keterangan = db.Column(db.String(100))
    operator = db.Column(db.String(1))  # +/-

class Periode(db.Model):
    __tablename__ = 'periode'
    periode_id = db.Column(db.String(10), primary_key=True)
    periode = db.Column(db.String(50))
    awal = db.Column(db.Date)
    akhir = db.Column(db.Date)

class Pinjaman(db.Model):
    __tablename__ = 'pinjaman'
    no_pinjaman = db.Column(db.String(20), primary_key=True)
    nik = db.Column(db.String(20), db.ForeignKey('tblMstKaryawan.NIK'))
    tanggal_pinjam = db.Column(db.Date)
    jumlah_pinjaman = db.Column(db.Float, default=0)
    bunga = db.Column(db.Float, default=0)
    lama_pinjaman = db.Column(db.Integer)  # in months
    status = db.Column(db.String(20))  # Active/Closed

class Angsuran(db.Model):
    __tablename__ = 'angsuran'
    id = db.Column(db.Integer, primary_key=True)
    no_pinjaman = db.Column(db.String(20), db.ForeignKey('pinjaman.no_pinjaman'))
    tanggal_bayar = db.Column(db.Date)
    angsuran_ke = db.Column(db.Integer)
    jumlah_angsuran = db.Column(db.Float, default=0)
    bunga = db.Column(db.Float, default=0)
    total_bayar = db.Column(db.Float, default=0)

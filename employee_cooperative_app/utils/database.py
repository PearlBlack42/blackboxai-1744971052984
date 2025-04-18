from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

def import_data():
    """Import sample data"""
    try:
        # Add sample employee
        employee = Employee(
            nik="EMP001",
            nama="John Doe",
            bagian="IT",
            jabatan="Staff",
            jk="L",
            tmk=datetime.now(),
            iuran_wajib=100000,
            status=True,
            khusus=False,
            max_plafon=5000000,
            max_plafon_sembako=1000000
        )
        db.session.add(employee)

        # Add sample savings type
        savings_type = JenisSimpanan(
            kode="SMP001",
            nama="Simpanan Pokok",
            keterangan="Simpanan wajib anggota"
        )
        db.session.add(savings_type)

        # Add sample goods
        good = Barang(
            kode="BRG001",
            nama="Beras",
            satuan="Kg",
            harga_beli=10000,
            harga_jual=11000,
            stok=100
        )
        db.session.add(good)

        # Add sample supplier
        supplier = Supplier(
            nama="PT Supplier Utama",
            alamat="Jl. Supplier No. 123",
            telepon="021-1234567",
            email="supplier@example.com",
            npwp="12.345.678.9-012.345",
            status=True
        )
        db.session.add(supplier)

        db.session.commit()
        return True
    except Exception as e:
        print(f"Error importing data: {e}")
        db.session.rollback()
        return False

# Database Models
class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(20), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    bagian = db.Column(db.String(50))
    jabatan = db.Column(db.String(50))
    jk = db.Column(db.String(1))
    tmk = db.Column(db.Date)
    iuran_wajib = db.Column(db.Float, default=0)
    status = db.Column(db.Boolean, default=True)
    khusus = db.Column(db.Boolean, default=False)
    max_plafon = db.Column(db.Float, default=0)
    max_plafon_sembako = db.Column(db.Float, default=0)

class JenisSimpanan(db.Model):
    __tablename__ = 'jenis_simpanan'
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(10), unique=True, nullable=False)
    nama = db.Column(db.String(50), nullable=False)
    keterangan = db.Column(db.Text)

class Barang(db.Model):
    __tablename__ = 'barang'
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(10), unique=True, nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    satuan = db.Column(db.String(20))
    harga_beli = db.Column(db.Float, default=0)
    harga_jual = db.Column(db.Float, default=0)
    stok = db.Column(db.Integer, default=0)

class Simpanan(db.Model):
    __tablename__ = 'simpanan'
    id = db.Column(db.Integer, primary_key=True)
    no_transaksi = db.Column(db.String(20), unique=True, nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    nik = db.Column(db.String(20), db.ForeignKey('employees.nik'), nullable=False)
    jenis_simpanan = db.Column(db.String(10), db.ForeignKey('jenis_simpanan.kode'), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    keterangan = db.Column(db.Text)

class Pinjaman(db.Model):
    __tablename__ = 'pinjaman'
    id = db.Column(db.Integer, primary_key=True)
    no_transaksi = db.Column(db.String(20), unique=True, nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    nik = db.Column(db.String(20), db.ForeignKey('employees.nik'), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    bunga = db.Column(db.Float, default=0)
    lama_angsuran = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    keterangan = db.Column(db.Text)

class Angsuran(db.Model):
    __tablename__ = 'angsuran'
    id = db.Column(db.Integer, primary_key=True)
    no_transaksi = db.Column(db.String(20), db.ForeignKey('pinjaman.no_transaksi'), nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    angsuran_ke = db.Column(db.Integer, nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    keterangan = db.Column(db.Text)

class Periode(db.Model):
    __tablename__ = 'periode'
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(10), unique=True, nullable=False)
    nama = db.Column(db.String(50), nullable=False)
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Active')

class Penjualan(db.Model):
    __tablename__ = 'penjualan'
    id = db.Column(db.Integer, primary_key=True)
    faktur = db.Column(db.String(20), unique=True, nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    nik = db.Column(db.String(20), db.ForeignKey('employees.nik'), nullable=False)
    periode_id = db.Column(db.String(10), db.ForeignKey('periode.kode'), nullable=False)
    keterangan = db.Column(db.String(50))  # Tunai/Kredit
    total = db.Column(db.Float, nullable=False)
    bayar = db.Column(db.Float, nullable=False)
    kembali = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    employee = db.relationship('Employee', backref='penjualan')
    periode = db.relationship('Periode', backref='penjualan')

class Supplier(db.Model):
    __tablename__ = 'supplier'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.Text)
    telepon = db.Column(db.String(20))
    email = db.Column(db.String(100))
    npwp = db.Column(db.String(20))
    status = db.Column(db.Boolean, default=True)

class Pembelian(db.Model):
    __tablename__ = 'pembelian'
    id = db.Column(db.Integer, primary_key=True)
    faktur = db.Column(db.String(20), unique=True, nullable=False)
    tanggal = db.Column(db.Date, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    periode_id = db.Column(db.String(10), db.ForeignKey('periode.kode'), nullable=False)
    keterangan = db.Column(db.Text)
    ppn = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    total_ppn = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    supplier = db.relationship('Supplier', backref='pembelian')
    periode = db.relationship('Periode', backref='pembelian')

class PembelianDetail(db.Model):
    __tablename__ = 'pembelian_detail'
    id = db.Column(db.Integer, primary_key=True)
    faktur = db.Column(db.String(20), db.ForeignKey('pembelian.faktur'), nullable=False)
    kode_barang = db.Column(db.String(10), db.ForeignKey('barang.kode'), nullable=False)
    harga = db.Column(db.Float, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Float, nullable=False)

    # Relationships
    pembelian = db.relationship('Pembelian', backref='details')
    barang = db.relationship('Barang', backref='pembelian_details')

class PenjualanDetail(db.Model):
    __tablename__ = 'penjualan_detail'
    id = db.Column(db.Integer, primary_key=True)
    faktur = db.Column(db.String(20), db.ForeignKey('penjualan.faktur'), nullable=False)
    kode_barang = db.Column(db.String(10), db.ForeignKey('barang.kode'), nullable=False)
    harga = db.Column(db.Float, nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Float, nullable=False)

    # Relationships
    penjualan = db.relationship('Penjualan', backref='details')
    barang = db.relationship('Barang', backref='penjualan_details')

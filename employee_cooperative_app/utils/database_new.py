import pyodbc
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

import subprocess
import csv
from io import StringIO

def get_table_data(table_name):
    """Get data from Access database table using mdbtools"""
    try:
        # Export table to CSV format
        cmd = f"mdb-export /project/sandbox/user-workspace/simkopkar.mDB {table_name}"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error exporting table {table_name}: {result.stderr}")
            return []
        
        # Parse CSV data
        csv_data = StringIO(result.stdout)
        reader = csv.DictReader(csv_data)
        return list(reader)
    except Exception as e:
        print(f"Error reading table {table_name}: {e}")
        return []

def import_data():
    """Import data from Access database to SQLite"""
    try:
        
        # Import employees (Karyawan)
        print("Importing employees...")
        cursor.execute("SELECT * FROM Karyawan")
        employees = cursor.fetchall()
        for emp in employees:
            employee = Employee(
                nik=emp.NIK,
                nama=emp.Nama,
                bagian=emp.Bagian,
                jabatan=emp.Jabatan,
                jk=emp.JK,
                tmk=datetime.strptime(emp.TMK, '%Y-%m-%d') if emp.TMK else None,
                iuran_wajib=float(emp.IuranWajib or 0),
                status=bool(emp.Status),
                khusus=bool(emp.Khusus),
                max_plafon=float(emp.MaxPlafon or 0),
                max_plafon_sembako=float(emp.MaxPlafonSembako or 0)
            )
            db.session.add(employee)
        
        # Import savings types (JenisSimpanan)
        print("Importing savings types...")
        cursor.execute("SELECT * FROM JenisSimpanan")
        savings_types = cursor.fetchall()
        for st in savings_types:
            savings_type = JenisSimpanan(
                kode=st.Kode,
                nama=st.Nama,
                keterangan=st.Keterangan
            )
            db.session.add(savings_type)
        
        # Import goods (Barang)
        print("Importing goods...")
        cursor.execute("SELECT * FROM Barang")
        goods = cursor.fetchall()
        for g in goods:
            good = Barang(
                kode=g.Kode,
                nama=g.Nama,
                satuan=g.Satuan,
                harga_beli=float(g.HargaBeli or 0),
                harga_jual=float(g.HargaJual or 0),
                stok=int(g.Stok or 0)
            )
            db.session.add(good)

        # Import savings (Simpanan)
        print("Importing savings...")
        cursor.execute("SELECT * FROM Simpanan")
        savings = cursor.fetchall()
        for s in savings:
            saving = Simpanan(
                no_transaksi=s.NoTransaksi,
                tanggal=datetime.strptime(s.Tanggal, '%Y-%m-%d') if s.Tanggal else None,
                nik=s.NIK,
                jenis_simpanan=s.JenisSimpanan,
                jumlah=float(s.Jumlah or 0),
                keterangan=s.Keterangan
            )
            db.session.add(saving)

        # Import loans (Pinjaman)
        print("Importing loans...")
        cursor.execute("SELECT * FROM Pinjaman")
        loans = cursor.fetchall()
        for l in loans:
            loan = Pinjaman(
                no_transaksi=l.NoTransaksi,
                tanggal=datetime.strptime(l.Tanggal, '%Y-%m-%d') if l.Tanggal else None,
                nik=l.NIK,
                jumlah=float(l.Jumlah or 0),
                bunga=float(l.Bunga or 0),
                lama_angsuran=int(l.LamaAngsuran or 0),
                status=l.Status or 'Pending',
                keterangan=l.Keterangan
            )
            db.session.add(loan)

        # Import installments (Angsuran)
        print("Importing installments...")
        cursor.execute("SELECT * FROM Angsuran")
        installments = cursor.fetchall()
        for i in installments:
            installment = Angsuran(
                no_transaksi=i.NoTransaksi,
                tanggal=datetime.strptime(i.Tanggal, '%Y-%m-%d') if i.Tanggal else None,
                angsuran_ke=int(i.AngsuranKe or 0),
                jumlah=float(i.Jumlah or 0),
                keterangan=i.Keterangan
            )
            db.session.add(installment)

        # Import periods (Periode)
        print("Importing periods...")
        cursor.execute("SELECT * FROM Periode")
        periods = cursor.fetchall()
        for p in periods:
            period = Periode(
                kode=p.Kode,
                nama=p.Nama,
                tanggal_mulai=datetime.strptime(p.TanggalMulai, '%Y-%m-%d') if p.TanggalMulai else None,
                tanggal_selesai=datetime.strptime(p.TanggalSelesai, '%Y-%m-%d') if p.TanggalSelesai else None,
                status=p.Status or 'Active'
            )
            db.session.add(period)

        db.session.commit()
        print("Data import completed successfully")
        return True
    except Exception as e:
        print(f"Error importing data: {e}")
        db.session.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

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

    # Relationships
    simpanan = db.relationship('Simpanan', backref='employee', lazy=True)
    pinjaman = db.relationship('Pinjaman', backref='employee', lazy=True)

class JenisSimpanan(db.Model):
    __tablename__ = 'jenis_simpanan'
    id = db.Column(db.Integer, primary_key=True)
    kode = db.Column(db.String(10), unique=True, nullable=False)
    nama = db.Column(db.String(50), nullable=False)
    keterangan = db.Column(db.Text)

    # Relationships
    simpanan = db.relationship('Simpanan', backref='jenis', lazy=True)

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

    # Relationships
    angsuran = db.relationship('Angsuran', backref='loan', lazy=True)

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

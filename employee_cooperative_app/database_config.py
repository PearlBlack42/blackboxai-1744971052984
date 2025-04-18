import os
import sqlite3
from datetime import datetime

class DatabaseConfig:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'cooperative.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def get_connection(self):
        """Get a connection to the SQLite database"""
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_tables(self):
        """Create database tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create MasterKaryawan table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tblMstKaryawan (
                    NIK TEXT PRIMARY KEY,
                    Nama TEXT,
                    Bagian TEXT,
                    Jabatan TEXT,
                    IuranWajib REAL,
                    JK TEXT,
                    Status INTEGER,
                    TMKBaru DATE,
                    TglKeluar DATE,
                    F13 REAL,
                    MaxPlafon REAL,
                    IDKhusus TEXT,
                    ID1 TEXT,
                    MaxPlafonSembako REAL
                )
            ''')

            # Create TransaksiPembelian table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tblTransaksiPembelian (
                    NoFakPembelian TEXT PRIMARY KEY,
                    Periode INTEGER,
                    Tanggal DATE,
                    Keterangan TEXT
                )
            ''')

            # Create TransaksiPembelianDtl table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tblTransaksiPembelianDtl (
                    NoFakPembelian TEXT,
                    Kode TEXT,
                    NamaBarang TEXT,
                    Qty REAL,
                    Harga REAL,
                    Harga2 REAL,
                    Total REAL,
                    Keterangan TEXT,
                    PRIMARY KEY (NoFakPembelian, Kode),
                    FOREIGN KEY (NoFakPembelian) REFERENCES tblTransaksiPembelian(NoFakPembelian)
                )
            ''')

            # Create TagihanSimpananPinjaman table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tagSimpPinjFix (
                    NIK TEXT PRIMARY KEY,
                    Nama TEXT,
                    Bagian TEXT,
                    Jabatan TEXT,
                    JK TEXT,
                    TMK DATE,
                    Iuran REAL,
                    JumlahAngsuran REAL,
                    Jumlah REAL,
                    FOREIGN KEY (NIK) REFERENCES tblMstKaryawan(NIK)
                )
            ''')

            # Create JenisSimpanan table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jenis_simpanan (
                    jenis_id TEXT PRIMARY KEY,
                    keterangan TEXT,
                    operator TEXT
                )
            ''')

            # Create Periode table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS periode (
                    periode_id TEXT PRIMARY KEY,
                    periode TEXT,
                    awal DATE,
                    akhir DATE
                )
            ''')

            # Create Pinjaman table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pinjaman (
                    no_pinjaman TEXT PRIMARY KEY,
                    nik TEXT,
                    tanggal_pinjam DATE,
                    jumlah_pinjaman REAL,
                    bunga REAL,
                    lama_pinjaman INTEGER,
                    status TEXT,
                    FOREIGN KEY (nik) REFERENCES tblMstKaryawan(NIK)
                )
            ''')

            # Create Angsuran table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS angsuran (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    no_pinjaman TEXT,
                    tanggal_bayar DATE,
                    angsuran_ke INTEGER,
                    jumlah_angsuran REAL,
                    bunga REAL,
                    total_bayar REAL,
                    FOREIGN KEY (no_pinjaman) REFERENCES pinjaman(no_pinjaman)
                )
            ''')

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

# Create global database instance
db = DatabaseConfig()

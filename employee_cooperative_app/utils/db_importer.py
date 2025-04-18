import subprocess
import csv
from io import StringIO
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

def get_table_data(table_name):
    """Get data from Access database table using mdbtools"""
    try:
        # Export table to CSV format
        cmd = f"mdb-export /project/sandbox/user-workspace/simkopkar.mDB {table_name}"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error exporting table {table_name}: {result.stderr}")
            return []

        # Split into lines
        lines = result.stdout.strip().split('\n')
        if not lines:
            return []

        # Define expected headers for each table
        table_headers = {
            "tblMstKaryawan": ['NIK', 'Nama', 'Bagian', 'Jabatan', 'IuranWajib', 'JK', 'Status', 
                              'TMKBaru', 'TglKeluar', 'F13', 'MaxPlafon', 'IDKhusus', 'ID1', 'MaxPlafonSembako'],
            "tblTransaksiPembelianDtl": ['NoFakPembelian', 'Kode', 'NamaBarang', 'Qty', 'Harga', 'Harga2', 'Total', 'Keterangan'],
            "tblTtrSimpananTmp": ['TrID', 'TglTr', 'NIK', 'Jenis', 'Jumlah', 'Keterangan'],
            "tmpTagPinjaman": ['NIK', 'Jumlah', 'Angsuran'],
            "Periode": ['Kode', 'Nama', 'TanggalMulai', 'TanggalSelesai', 'Status']
        }

        # Get expected headers for the table
        expected_headers = table_headers.get(table_name, [])
        if not expected_headers:
            print(f"Warning: No expected headers defined for table {table_name}")
            # Parse headers from the first line
            headers = [h.strip('"') for h in lines[0].split(',')]
        else:
            headers = expected_headers

        print(f"Using headers: {headers}")  # Debug print

        # Process data rows
        data = []
        for line in lines[1:]:
            try:
                # Split by quotes and clean up
                raw_values = line.split('"')
                values = []
                for val in raw_values:
                    val = val.strip()
                    if val and val != ' ':  # Skip empty or space-only values
                        # Clean up numeric values
                        if 'e+' in val:
                            try:
                                val = str(float(val))
                            except ValueError:
                                pass
                        values.append(val)

                print(f"Cleaned values: {values}")  # Debug print

                if len(values) >= len(headers):
                    row_data = {}
                    for i, header in enumerate(headers):
                        row_data[header] = values[i]
                    data.append(row_data)
                else:
                    print(f"Skipping line due to insufficient values: {line}")
            except Exception as e:
                print(f"Error processing line: {line}")
                print(f"Error details: {str(e)}")

        print(f"Processed data: {data}")  # Debug print
        return data
    except Exception as e:
        print(f"Error reading table {table_name}: {e}")
        return []

def import_data():
    """Import data from Access database to SQLite"""
    try:
        # Import employees (tblMstKaryawan)
        print("Importing employees...")
        employees = get_table_data("tblMstKaryawan")
        for emp in employees:
            try:
                # Clean and convert data
                nik = emp['NIK'].strip('"') if emp.get('NIK') else None
                if not nik:
                    print(f"Skipping employee record - missing NIK: {emp}")
                    continue

                # Convert dates with error handling
                tmk = None
                if emp.get('TMKBaru'):
                    try:
                        tmk = datetime.strptime(emp['TMKBaru'].strip('"'), '%m/%d/%y %H:%M:%S')
                    except ValueError as e:
                        print(f"Error parsing TMKBaru for NIK {nik}: {e}")

                tgl_keluar = None
                if emp.get('TglKeluar'):
                    try:
                        tgl_keluar = datetime.strptime(emp['TglKeluar'].strip('"'), '%m/%d/%y %H:%M:%S')
                    except ValueError as e:
                        print(f"Error parsing TglKeluar for NIK {nik}: {e}")

                # Convert numeric fields with error handling
                def safe_float_convert(value, field_name, default=0.0):
                    if not value:
                        return default
                    try:
                        # Remove quotes and handle scientific notation
                        clean_val = value.strip('"').replace('e+05', 'e5').replace('e+06', 'e6')
                        return float(clean_val)
                    except ValueError as e:
                        print(f"Error converting {field_name} value '{value}' for NIK {nik}: {e}")
                        return default

                employee = MasterKaryawan(
                    NIK=nik,
                    Nama=emp.get('Nama', '').strip('"'),
                    Bagian=emp.get('Bagian', '').strip('"'),
                    Jabatan=emp.get('Jabatan', '').strip('"'),
                    IuranWajib=safe_float_convert(emp.get('IuranWajib'), 'IuranWajib'),
                    JK=emp.get('JK', '').strip('"'),
                    Status=int(emp.get('Status', '0').strip('"') or '0'),
                    TMKBaru=tmk,
                    TglKeluar=tgl_keluar,
                    F13=safe_float_convert(emp.get('F13'), 'F13'),
                    MaxPlafon=safe_float_convert(emp.get('MaxPlafon'), 'MaxPlafon'),
                    IDKhusus=emp.get('IDKhusus', '').strip('"'),
                    ID1=emp.get('ID1', '').strip('"'),
                    MaxPlafonSembako=safe_float_convert(emp.get('MaxPlafonSembako'), 'MaxPlafonSembako')
                )
                db.session.add(employee)
                print(f"Added employee: {nik}")
            except Exception as e:
                print(f"Error processing employee record: {e}")
                print(f"Problematic record: {emp}")
                continue

        # Import goods/purchases (tblTransaksiPembelianDtl)
        print("\nImporting goods/purchases...")
        purchases = get_table_data("tblTransaksiPembelianDtl")
        for idx, p in enumerate(purchases, 1):
            try:
                # Generate a unique transaction ID if not present
                nofak = p.get('NoFakPembelian', '').strip('"') or f'IMP-{idx:06d}'
                
                purchase = TransaksiPembelianDtl(
                    NoFakPembelian=nofak,
                    Kode=p.get('Kode', '').strip('"'),
                    NamaBarang=p.get('NamaBarang', '').strip('"'),
                    Qty=safe_float_convert(p.get('Qty'), 'Qty'),
                    Harga=safe_float_convert(p.get('Harga'), 'Harga'),
                    Harga2=safe_float_convert(p.get('Harga2'), 'Harga2'),
                    Total=safe_float_convert(p.get('Total'), 'Total'),
                    Keterangan=p.get('Keterangan', '').strip('"')
                )
                db.session.add(purchase)
                print(f"Added purchase: {nofak}")
            except Exception as e:
                print(f"Error processing purchase record: {e}")
                print(f"Problematic record: {p}")
                continue

        # Import savings/loans (tagSimpPinjFix)
        print("\nImporting savings/loans...")
        tagsimpin = get_table_data("tagSimpPinjFix")
        for t in tagsimpin:
            try:
                nik = t.get('NIK', '').strip('"')
                if not nik:
                    print("Skipping savings/loan record - missing NIK")
                    continue

                record = TagihanSimpananPinjaman(
                    NIK=nik,
                    Nama=t.get('Nama', '').strip('"'),
                    Bagian=t.get('Bagian', '').strip('"'),
                    Jabatan=t.get('Jabatan', '').strip('"'),
                    JK=t.get('JK', '').strip('"'),
                    TMK=datetime.strptime(t['TMK'].strip('"'), '%m/%d/%y %H:%M:%S') if t.get('TMK') else None,
                    Iuran=safe_float_convert(t.get('Iuran'), 'Iuran'),
                    JumlahAngsuran=safe_float_convert(t.get('JumlahAngsuran'), 'JumlahAngsuran'),
                    Jumlah=safe_float_convert(t.get('Jumlah'), 'Jumlah')
                )
                db.session.add(record)
                print(f"Added savings/loan record for NIK: {nik}")
            except Exception as e:
                print(f"Error processing savings/loan record: {e}")
                print(f"Problematic record: {t}")
                continue

        # Import periods
        print("\nImporting periods...")
        periods = get_table_data("Periode")
        for p in periods:
            try:
                period_id = p.get('periode_id', '').strip('"')
                if not period_id:
                    print("Skipping period record - missing periode_id")
                    continue

                period = Periode(
                    periode_id=period_id,
                    periode=p.get('periode', '').strip('"'),
                    awal=datetime.strptime(p['awal'].strip('"'), '%Y-%m-%d') if p.get('awal') else None,
                    akhir=datetime.strptime(p['akhir'].strip('"'), '%Y-%m-%d') if p.get('akhir') else None
                )
                db.session.add(period)
                print(f"Added period: {period_id}")
            except Exception as e:
                print(f"Error processing period record: {e}")
                print(f"Problematic record: {p}")
                continue

        # Commit all changes
        try:
            db.session.commit()
            print("\nData import completed successfully")
            return True
        except Exception as e:
            print(f"\nError committing changes to database: {e}")
            db.session.rollback()
            return False

    except Exception as e:
        print(f"\nCritical error during import process: {e}")
        db.session.rollback()
        return False

def sync_data():
    """
    Synchronize data between Access database and SQLite
    This function checks for new or updated records and applies changes
    """
    try:
        print("Starting database synchronization...")
        changes_made = False

        # Sync employees
        print("\nSynchronizing employees...")
        employees = get_table_data("tblMstKaryawan")
        for emp in employees:
            try:
                nik = emp.get('NIK', '').strip('"')
                if not nik:
                    continue

                # Check if employee exists
                existing_emp = MasterKaryawan.query.filter_by(NIK=nik).first()
                if existing_emp:
                    # Update existing employee if data is different
                    updates = {}
                    if emp.get('Nama', '').strip('"') != existing_emp.Nama:
                        updates['Nama'] = emp.get('Nama', '').strip('"')
                    if emp.get('Bagian', '').strip('"') != existing_emp.Bagian:
                        updates['Bagian'] = emp.get('Bagian', '').strip('"')
                    if emp.get('Jabatan', '').strip('"') != existing_emp.Jabatan:
                        updates['Jabatan'] = emp.get('Jabatan', '').strip('"')
                    
                    if updates:
                        print(f"Updating employee {nik} with changes: {updates}")
                        for key, value in updates.items():
                            setattr(existing_emp, key, value)
                        changes_made = True
                else:
                    # Add new employee
                    print(f"Adding new employee: {nik}")
                    new_emp = MasterKaryawan(
                        NIK=nik,
                        Nama=emp.get('Nama', '').strip('"'),
                        Bagian=emp.get('Bagian', '').strip('"'),
                        Jabatan=emp.get('Jabatan', '').strip('"'),
                        IuranWajib=safe_float_convert(emp.get('IuranWajib'), 'IuranWajib'),
                        JK=emp.get('JK', '').strip('"'),
                        Status=int(emp.get('Status', '0').strip('"') or '0'),
                        TMKBaru=datetime.strptime(emp['TMKBaru'].strip('"'), '%m/%d/%y %H:%M:%S') if emp.get('TMKBaru') else None,
                        TglKeluar=datetime.strptime(emp['TglKeluar'].strip('"'), '%m/%d/%y %H:%M:%S') if emp.get('TglKeluar') else None,
                        F13=safe_float_convert(emp.get('F13'), 'F13'),
                        MaxPlafon=safe_float_convert(emp.get('MaxPlafon'), 'MaxPlafon'),
                        IDKhusus=emp.get('IDKhusus', '').strip('"'),
                        ID1=emp.get('ID1', '').strip('"'),
                        MaxPlafonSembako=safe_float_convert(emp.get('MaxPlafonSembako'), 'MaxPlafonSembako')
                    )
                    db.session.add(new_emp)
                    changes_made = True
            except Exception as e:
                print(f"Error syncing employee {nik}: {e}")
                continue

        # Sync purchases
        print("\nSynchronizing purchases...")
        purchases = get_table_data("tblTransaksiPembelianDtl")
        for p in purchases:
            try:
                nofak = p.get('NoFakPembelian', '').strip('"')
                if not nofak:
                    continue

                existing_purchase = TransaksiPembelianDtl.query.filter_by(NoFakPembelian=nofak).first()
                if not existing_purchase:
                    print(f"Adding new purchase: {nofak}")
                    new_purchase = TransaksiPembelianDtl(
                        NoFakPembelian=nofak,
                        Kode=p.get('Kode', '').strip('"'),
                        NamaBarang=p.get('NamaBarang', '').strip('"'),
                        Qty=safe_float_convert(p.get('Qty'), 'Qty'),
                        Harga=safe_float_convert(p.get('Harga'), 'Harga'),
                        Harga2=safe_float_convert(p.get('Harga2'), 'Harga2'),
                        Total=safe_float_convert(p.get('Total'), 'Total'),
                        Keterangan=p.get('Keterangan', '').strip('"')
                    )
                    db.session.add(new_purchase)
                    changes_made = True
            except Exception as e:
                print(f"Error syncing purchase {nofak}: {e}")
                continue

        # Commit changes if any were made
        if changes_made:
            try:
                db.session.commit()
                print("\nDatabase synchronization completed successfully")
                return True
            except Exception as e:
                print(f"\nError committing synchronization changes: {e}")
                db.session.rollback()
                return False
        else:
            print("\nNo changes needed during synchronization")
            return True

    except Exception as e:
        print(f"\nCritical error during synchronization: {e}")
        db.session.rollback()
        return False

def safe_float_convert(value, field_name, default=0.0):
    """Helper function to safely convert string values to float"""
    if not value:
        return default
    try:
        # Remove quotes and handle scientific notation
        clean_val = value.strip('"').replace('e+05', 'e5').replace('e+06', 'e6')
        return float(clean_val)
    except ValueError as e:
        print(f"Error converting {field_name} value '{value}': {e}")
        return default

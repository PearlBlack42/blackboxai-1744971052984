import os
import subprocess
from datetime import datetime
from database_config import db

def parse_date(date_str):
    """Parse date string from Access format"""
    if not date_str or date_str == '0':
        return None
    try:
        # Remove quotes
        clean_str = date_str.strip('"')
        # Try parsing Access date format MM/DD/YY HH:MM:SS
        return datetime.strptime(clean_str, '%m/%d/%y %H:%M:%S')
    except:
        try:
            # Try parsing MMDDYYYY format
            return datetime.strptime(clean_str, '%m%d%Y')
        except:
            return None

def parse_number(num_str):
    """Parse scientific notation numbers from Access"""
    if not num_str or num_str == '0':
        return 0
    try:
        # Remove quotes and convert scientific notation
        clean_str = num_str.strip('"')
        if 'e+' in clean_str.lower():  # Handle scientific notation
            return float(clean_str)
        return float(clean_str)
    except:
        return 0

def split_fields(line):
    """Split fields by double quotes, handling concatenated fields"""
    fields = []
    current = ''
    in_quotes = False
    
    for char in line:
        if char == '"':
            if in_quotes:
                fields.append(current)
                current = ''
            in_quotes = not in_quotes
        elif in_quotes:
            current += char
            
    return fields

def parse_mdb_line(line, table_name):
    """Parse a line from mdb-export output"""
    if not line.strip():
        return None
        
    # Split fields
    fields = split_fields(line)
    
    if table_name == 'tblMstKaryawan' and len(fields) >= 13:
        return {
            'NIK': fields[2],
            'Nama': fields[0],
            'Bagian': fields[1],
            'Jabatan': fields[3],
            'IuranWajib': parse_number(fields[4]),
            'JK': fields[5],
            'Status': int(parse_number(fields[6])),
            'TMKBaru': parse_date(fields[7]),
            'TglKeluar': parse_date(fields[8] if fields[8] != '0' else None),
            'F13': parse_number(fields[9]),
            'MaxPlafon': parse_number(fields[10]),
            'IDKhusus': fields[11],
            'ID1': fields[12],
            'MaxPlafonSembako': parse_number(fields[13] if len(fields) > 13 else '0')
        }
            
    elif table_name == 'tagSimpPinjFix' and len(fields) >= 8:
        return {
            'NIK': fields[0],
            'Nama': fields[1],
            'Bagian': fields[2],
            'Jabatan': fields[3],
            'JK': fields[4],
            'TMK': parse_date(fields[5]),
            'Iuran': parse_number(fields[6]),
            'JumlahAngsuran': parse_number(fields[7].split(',')[0] if ',' in fields[7] else fields[7]),
            'Jumlah': parse_number(fields[7].split(',')[1] if ',' in fields[7] and len(fields[7].split(',')) > 1 else '0')
        }
            
    elif table_name == 'tblTransaksiPembelian' and len(fields) >= 3:
        return {
            'NoFakPembelian': fields[0],
            'Periode': int(fields[1]),
            'Tanggal': parse_date(fields[2]),
            'Keterangan': fields[3] if len(fields) > 3 else ''
        }
            
    elif table_name == 'tblTransaksiPembelianDtl' and len(fields) >= 7:
        return {
            'NoFakPembelian': fields[0],
            'Kode': fields[1],
            'NamaBarang': fields[2],
            'Qty': parse_number(fields[3]),
            'Harga': parse_number(fields[4] if len(fields) > 4 else '0'),
            'Harga2': parse_number(fields[5] if len(fields) > 5 else '0'),
            'Total': parse_number(fields[6] if len(fields) > 6 else '0'),
            'Keterangan': fields[7] if len(fields) > 7 else ''
        }
            
    return None

def get_table_names():
    """Get list of tables from the MS Access database using mdbtools"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'simkopkar.mDB')
        
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found: {db_path}")
            
        result = subprocess.run(['mdb-tables', '-1', db_path], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to get tables: {result.stderr}")
            
        tables = result.stdout.strip().split('\n')
        # Filter only the main tables we need
        required_tables = [
            'tblMstKaryawan',
            'tblTransaksiPembelian',
            'tblTransaksiPembelianDtl',
            'tagSimpPinjFix'
        ]
        return [t for t in tables if t in required_tables]
        
    except Exception as e:
        raise Exception(f"Error getting table names: {str(e)}")

def get_table_data(table_name):
    """Get data from a specific table using mdbtools"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'simkopkar.mDB')
        
        # Use specific export options for better formatting
        result = subprocess.run(
            ['mdb-export', db_path, table_name],
            capture_output=True,
            text=True
        )
                              
        if result.returncode != 0:
            raise Exception(f"Failed to export table {table_name}: {result.stderr}")
            
        # Parse CSV data
        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:  # Need at least header and one row
            return []
            
        data = []
        # Skip header line
        for line in lines[1:]:
            row_data = parse_mdb_line(line, table_name)
            if row_data:
                data.append(row_data)
                
        return data
        
    except Exception as e:
        raise Exception(f"Error getting data from table {table_name}: {str(e)}")

def create_insert_query(table_name, row):
    """Create parameterized INSERT query for a table"""
    columns = list(row.keys())
    columns_str = ', '.join(columns)
    placeholders = ', '.join(['?' for _ in columns])
    return f"INSERT INTO [{table_name}] ({columns_str}) VALUES ({placeholders})", [row[col] for col in columns]

def import_database():
    """Import data from simkopkar.mdb to the application database"""
    try:
        tables = get_table_names()
        
        import_summary = {
            'success': True,
            'tables_processed': 0,
            'total_rows': 0,
            'details': []
        }

        for table_name in tables:
            try:
                rows = get_table_data(table_name)
                
                table_summary = {
                    'table_name': table_name,
                    'rows_imported': 0,
                    'status': 'success'
                }
                
                for row in rows:
                    try:
                        query, values = create_insert_query(table_name, row)
                        db.execute_query(query, values)
                        table_summary['rows_imported'] += 1
                    except Exception as e:
                        if table_summary['status'] == 'success':
                            table_summary['status'] = f'partial: {str(e)}'
                
                import_summary['tables_processed'] += 1
                import_summary['total_rows'] += table_summary['rows_imported']
                import_summary['details'].append(table_summary)
                
            except Exception as e:
                import_summary['details'].append({
                    'table_name': table_name,
                    'status': f'failed: {str(e)}'
                })
                continue
        
        return import_summary
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def handle_database_import():
    """Handle the import process and return results"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'simkopkar.mDB')
        
        if not os.path.exists(db_path):
            return False, 'Source database file (simkopkar.mDB) not found'
            
        result = import_database()
        
        if result['success']:
            message = (
                f"Successfully imported {result['tables_processed']} tables "
                f"with {result['total_rows']} total rows. "
                "Check details for per-table results."
            )
            return True, {'message': message, 'details': result['details']}
        else:
            return False, f"Import failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return False, f'Error during import: {str(e)}'

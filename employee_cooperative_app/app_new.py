from flask import Flask, jsonify, request, render_template, flash, redirect, url_for, send_from_directory
from utils.db_importer import db, Employee, JenisSimpanan, Barang, Simpanan, Pinjaman, Angsuran, Periode, import_data
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cooperative.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

# Configure static files directory
app.static_folder = 'static'
app.static_url_path = '/static'

db.init_app(app)

# Add current year to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Create database tables and import data if needed
with app.app_context():
    db.create_all()
    if not Employee.query.first():
        import_data()

# Routes
@app.route('/')
def index():
    # Get summary data
    total_employees = Employee.query.count()
    total_savings = db.session.query(db.func.sum(Simpanan.jumlah)).scalar() or 0
    total_loans = db.session.query(db.func.sum(Pinjaman.jumlah)).scalar() or 0
    total_goods = Barang.query.count()

    # Get recent transactions (combine savings, loans, and installments)
    recent_savings = Simpanan.query.order_by(Simpanan.tanggal.desc()).limit(5).all()
    recent_loans = Pinjaman.query.order_by(Pinjaman.tanggal.desc()).limit(5).all()
    recent_installments = Angsuran.query.order_by(Angsuran.tanggal.desc()).limit(5).all()

    transactions = []
    for saving in recent_savings:
        transactions.append({
            'tanggal': saving.tanggal,
            'employee': saving.employee,
            'type': 'savings',
            'amount': saving.jumlah
        })
    for loan in recent_loans:
        transactions.append({
            'tanggal': loan.tanggal,
            'employee': loan.employee,
            'type': 'loan',
            'amount': loan.jumlah
        })
    for installment in recent_installments:
        transactions.append({
            'tanggal': installment.tanggal,
            'employee': installment.loan.employee,
            'type': 'installment',
            'amount': installment.jumlah
        })

    # Sort transactions by date and get the 10 most recent
    recent_transactions = sorted(transactions, key=lambda x: x['tanggal'], reverse=True)[:10]

    # Get low stock items
    low_stock_items = Barang.query.filter(Barang.stok <= 10).all()

    # Get transaction data for charts (last 6 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    transaction_months = []
    savings_data = []
    loan_data = []
    
    current_date = start_date
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        if current_date.month == 12:
            month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
        
        # Get total savings for the month
        month_savings = db.session.query(db.func.sum(Simpanan.jumlah))\
            .filter(Simpanan.tanggal.between(month_start, month_end))\
            .scalar() or 0
            
        # Get total loans for the month
        month_loans = db.session.query(db.func.sum(Pinjaman.jumlah))\
            .filter(Pinjaman.tanggal.between(month_start, month_end))\
            .scalar() or 0
        
        transaction_months.append(current_date.strftime('%b %Y'))
        savings_data.append(float(month_savings))
        loan_data.append(float(month_loans))
        
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)

    # Get loan status data for pie chart
    pending_loans = Pinjaman.query.filter_by(status='Pending').count()
    approved_loans = Pinjaman.query.filter_by(status='Approved').count()
    rejected_loans = Pinjaman.query.filter_by(status='Rejected').count()
    completed_loans = Pinjaman.query.filter_by(status='Completed').count()
    
    loan_status_data = [pending_loans, approved_loans, rejected_loans, completed_loans]

    return render_template('index_final.html',
        total_employees=total_employees,
        total_savings=total_savings,
        total_loans=total_loans,
        total_goods=total_goods,
        recent_transactions=recent_transactions,
        low_stock_items=low_stock_items,
        transaction_months=transaction_months,
        savings_data=savings_data,
        loan_data=loan_data,
        loan_status_data=loan_status_data
    )

@app.route('/master_karyawan')
def master_karyawan():
    employees = Employee.query.all()
    return render_template('master_karyawan.html', employees=employees)

@app.route('/simpanan')
def simpanan():
    savings = Simpanan.query.all()
    savings_types = JenisSimpanan.query.all()
    employees = Employee.query.all()
    return render_template('simpanan.html', savings=savings, savings_types=savings_types, employees=employees)

@app.route('/pinjaman')
def pinjaman():
    loans = Pinjaman.query.all()
    employees = Employee.query.all()
    return render_template('pinjaman.html', loans=loans, employees=employees)

@app.route('/angsuran')
def angsuran():
    installments = Angsuran.query.all()
    loans = Pinjaman.query.all()
    return render_template('angsuran.html', installments=installments, loans=loans)

@app.route('/master_barang')
def master_barang():
    goods = Barang.query.all()
    return render_template('master_barang.html', goods=goods)

@app.route('/periode')
def periode():
    periods = Periode.query.all()
    return render_template('periode.html', periods=periods)

# API endpoints
@app.route('/api/employees', methods=['GET'])
def get_employees():
    employees = Employee.query.all()
    result = []
    for emp in employees:
        result.append({
            'id': emp.id,
            'nik': emp.nik,
            'nama': emp.nama,
            'bagian': emp.bagian,
            'jabatan': emp.jabatan,
            'jk': emp.jk,
            'tmk': emp.tmk.strftime('%Y-%m-%d') if emp.tmk else None,
            'iuran_wajib': emp.iuran_wajib,
            'status': emp.status,
            'khusus': emp.khusus,
            'max_plafon': emp.max_plafon,
            'max_plafon_sembako': emp.max_plafon_sembako
        })
    return jsonify(result)

@app.route('/api/employees', methods=['POST'])
def add_employee():
    data = request.json
    
    # Validate required fields
    required_fields = ['nik', 'nama', 'bagian', 'jabatan', 'jk', 'tmk']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'Field {field} is required'}), 400

    try:
        # Parse and validate date
        try:
            tmk_date = datetime.strptime(data['tmk'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Parse and validate numeric fields
        try:
            iuran_wajib = float(data.get('iuran_wajib', 0))
            max_plafon = float(data.get('max_plafon', 0))
            max_plafon_sembako = float(data.get('max_plafon_sembako', 0))
        except ValueError:
            return jsonify({'message': 'Invalid numeric value'}), 400

        employee = Employee(
            nik=data['nik'],
            nama=data['nama'],
            bagian=data['bagian'],
            jabatan=data['jabatan'],
            jk=data['jk'],
            tmk=tmk_date,
            iuran_wajib=iuran_wajib,
            status=bool(data.get('status', True)),
            khusus=bool(data.get('khusus', False)),
            max_plafon=max_plafon,
            max_plafon_sembako=max_plafon_sembako
        )
        
        db.session.add(employee)
        db.session.commit()
        return jsonify({'message': 'Success', 'id': employee.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to add employee: {str(e)}'}), 400

@app.route('/api/employees/<int:id>', methods=['PUT'])
def update_employee(id):
    employee = Employee.query.get_or_404(id)
    data = request.json
    try:
        employee.nik = data.get('nik', employee.nik)
        employee.nama = data.get('nama', employee.nama)
        employee.bagian = data.get('bagian', employee.bagian)
        employee.jabatan = data.get('jabatan', employee.jabatan)
        employee.jk = data.get('jk', employee.jk)
        if data.get('tmk'):
            employee.tmk = datetime.strptime(data['tmk'], '%Y-%m-%d')
        employee.iuran_wajib = float(data.get('iuran_wajib', employee.iuran_wajib))
        employee.status = bool(data.get('status', employee.status))
        employee.khusus = bool(data.get('khusus', employee.khusus))
        employee.max_plafon = float(data.get('max_plafon', employee.max_plafon))
        employee.max_plafon_sembako = float(data.get('max_plafon_sembako', employee.max_plafon_sembako))
        
        db.session.commit()
        return jsonify({'message': 'Success'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@app.route('/api/employees/<int:id>', methods=['DELETE'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    try:
        db.session.delete(employee)
        db.session.commit()
        return jsonify({'message': 'Success'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@app.route('/api/savings', methods=['POST'])
def add_saving():
    data = request.json
    try:
        saving = Simpanan(
            no_transaksi=data['no_transaksi'],
            tanggal=datetime.strptime(data['tanggal'], '%Y-%m-%d'),
            nik=data['nik'],
            jenis_simpanan=data['jenis_simpanan'],
            jumlah=float(data['jumlah']),
            keterangan=data.get('keterangan')
        )
        db.session.add(saving)
        db.session.commit()
        return jsonify({'message': 'Success', 'id': saving.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@app.route('/api/loans', methods=['POST'])
def add_loan():
    data = request.json
    try:
        loan = Pinjaman(
            no_transaksi=data['no_transaksi'],
            tanggal=datetime.strptime(data['tanggal'], '%Y-%m-%d'),
            nik=data['nik'],
            jumlah=float(data['jumlah']),
            bunga=float(data['bunga']),
            lama_angsuran=int(data['lama_angsuran']),
            status='Pending',
            keterangan=data.get('keterangan')
        )
        db.session.add(loan)
        db.session.commit()
        return jsonify({'message': 'Success', 'id': loan.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@app.route('/api/installments', methods=['POST'])
def add_installment():
    data = request.json
    try:
        installment = Angsuran(
            no_transaksi=data['no_transaksi'],
            tanggal=datetime.strptime(data['tanggal'], '%Y-%m-%d'),
            angsuran_ke=int(data['angsuran_ke']),
            jumlah=float(data['jumlah']),
            keterangan=data.get('keterangan')
        )
        db.session.add(installment)
        db.session.commit()
        return jsonify({'message': 'Success', 'id': installment.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@app.route('/api/goods', methods=['POST'])
def add_good():
    data = request.json
    try:
        good = Barang(
            kode=data['kode'],
            nama=data['nama'],
            satuan=data['satuan'],
            harga_beli=float(data['harga_beli']),
            harga_jual=float(data['harga_jual']),
            stok=int(data['stok'])
        )
        db.session.add(good)
        db.session.commit()
        return jsonify({'message': 'Success', 'id': good.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

@app.route('/api/periods', methods=['POST'])
def add_period():
    data = request.json
    try:
        period = Periode(
            kode=data['kode'],
            nama=data['nama'],
            tanggal_mulai=datetime.strptime(data['tanggal_mulai'], '%Y-%m-%d'),
            tanggal_selesai=datetime.strptime(data['tanggal_selesai'], '%Y-%m-%d'),
            status='Active'
        )
        db.session.add(period)
        db.session.commit()
        return jsonify({'message': 'Success', 'id': period.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)

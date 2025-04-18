from datetime import datetime, timedelta
from flask import Flask, jsonify, request, render_template, flash, redirect, url_for
from employee_cooperative_app.utils.database import db, Employee, JenisSimpanan, Barang, Simpanan, Pinjaman, Angsuran, Periode, Penjualan, PenjualanDetail, Supplier, Pembelian, PembelianDetail
from employee_cooperative_app.utils.db_importer import import_data, sync_data
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cooperative.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)

# Import blueprints after app creation to avoid circular imports
from employee_cooperative_app.routes.import_routes import import_bp
from employee_cooperative_app.routes.sales_routes import sales_bp
from employee_cooperative_app.routes.purchase_routes import purchase_bp
from employee_cooperative_app.routes.report_routes import report_bp
from employee_cooperative_app.routes.item_routes import item_bp

# Register blueprints
app.register_blueprint(import_bp, url_prefix='/import-database')
app.register_blueprint(sales_bp)
app.register_blueprint(purchase_bp)
app.register_blueprint(report_bp)
app.register_blueprint(item_bp)

@app.route('/master-barang')
def master_barang():
    try:
        # Get list of items for table
        items = Barang.query.order_by(Barang.kode).all()
        total_items = len(items)
        total_stock = sum(item.stok for item in items)
        
        return render_template('master_barang.html',
            items=items,
            total_items=total_items,
            total_stock=total_stock,
            today=datetime.now().strftime('%Y-%m-%d')
        )
    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/jenis-simpanan')
def jenis_simpanan():
    try:
        # Get list of savings types
        savings_types = JenisSimpanan.query.order_by(JenisSimpanan.kode).all()
        return render_template('jenis_simpanan.html',
            savings_types=savings_types,
            today=datetime.now().strftime('%Y-%m-%d')
        )
    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/jenis-pinjaman')
def jenis_pinjaman():
    try:
        loan_types = JenisPinjaman.query.order_by(JenisPinjaman.kode).all()
        return render_template('jenis_pinjaman.html',
            loan_types=loan_types,
            today=datetime.now().strftime('%Y-%m-%d')
        )
    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/savings-types', methods=['GET'])
def get_savings_types():
    """Get list of savings types"""
    try:
        savings_types = JenisSimpanan.query.all()
        result = []
        for st in savings_types:
            result.append({
                'kode': st.kode,
                'nama': st.nama,
                'keterangan': st.keterangan
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/savings-types', methods=['POST'])
def add_savings_type():
    """Add a new savings type"""
    data = request.json
    try:
        savings_type = JenisSimpanan(
            kode=data['kode'],
            nama=data['nama'],
            keterangan=data.get('keterangan')
        )
        db.session.add(savings_type)
        db.session.commit()
        return jsonify({'message': 'Success', 'kode': savings_type.kode}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/savings-types/<kode>', methods=['PUT'])
def update_savings_type(kode):
    """Update a savings type"""
    try:
        savings_type = JenisSimpanan.query.filter_by(kode=kode).first()
        if not savings_type:
            return jsonify({'error': 'Savings type not found'}), 404

        data = request.json
        savings_type.nama = data.get('nama', savings_type.nama)
        savings_type.keterangan = data.get('keterangan', savings_type.keterangan)
        
        db.session.commit()
        return jsonify({'message': 'Success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/savings-types/<kode>', methods=['DELETE'])
def delete_savings_type(kode):
    """Delete a savings type"""
    try:
        savings_type = JenisSimpanan.query.filter_by(kode=kode).first()
        if not savings_type:
            return jsonify({'error': 'Savings type not found'}), 404

        db.session.delete(savings_type)
        db.session.commit()
        return jsonify({'message': 'Success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/laporan')
def laporan():
    try:
        # Get list of periods for dropdown
        periods = Periode.query.order_by(Periode.periode_id.desc()).all()
        
        return render_template('laporan.html',
            periods=periods,
            today=datetime.now().strftime('%Y-%m-%d')
        )
    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'error')
        return redirect(url_for('index'))

# Initialize extensions
db.init_app(app)

# Create database tables and import data if needed
with app.app_context():
    db.create_all()
    if not Employee.query.first():
        import_data()

# Routes for different modules
@app.route('/')
def index():
    # Calculate total employees
    total_employees = Employee.query.count()
    
    # Calculate total savings
    total_savings = db.session.query(db.func.sum(Simpanan.jumlah)).scalar() or 0
    
    # Calculate total loans
    total_loans = db.session.query(db.func.sum(Pinjaman.jumlah)).scalar() or 0
    
    # Calculate total goods
    total_goods = Barang.query.count()
    
    # Get recent transactions (combine savings and loans)
    recent_savings = (Simpanan.query
        .join(Employee, Simpanan.nik == Employee.nik)
        .add_columns(Employee.nama)
        .order_by(Simpanan.tanggal.desc())
        .limit(5)
        .all())
    
    recent_loans = (Pinjaman.query
        .join(Employee, Pinjaman.nik == Employee.nik)
        .add_columns(Employee.nama)
        .order_by(Pinjaman.tanggal.desc())
        .limit(5)
        .all())
    
    # Combine and sort transactions
    recent_transactions = []
    for saving in recent_savings:
        recent_transactions.append({
            'tanggal': saving[0].tanggal,
            'employee': {'nama': saving.nama},
            'type': 'savings',
            'amount': saving[0].jumlah
        })
    
    for loan in recent_loans:
        recent_transactions.append({
            'tanggal': loan[0].tanggal,
            'employee': {'nama': loan.nama},
            'type': 'loan',
            'amount': loan[0].jumlah
        })
    
    # Sort combined transactions by date
    recent_transactions.sort(key=lambda x: x['tanggal'], reverse=True)
    recent_transactions = recent_transactions[:5]  # Keep only 5 most recent
    
    # Get low stock items (items with stock below 10)
    low_stock_items = Barang.query.filter(Barang.stok < 10).all()
    
    # Get data for transaction chart (last 6 months)
    # Calculate the date 6 months ago
    six_months_ago = datetime.now() - timedelta(days=180)
    
    # Get monthly savings totals
    monthly_savings = db.session.query(
        db.func.strftime('%Y-%m', Simpanan.tanggal).label('month'),
        db.func.sum(Simpanan.jumlah).label('total')
    ).filter(
        Simpanan.tanggal >= six_months_ago
    ).group_by('month').order_by('month').all()

    # Get monthly loan totals
    monthly_loans = db.session.query(
        db.func.strftime('%Y-%m', Pinjaman.tanggal).label('month'),
        db.func.sum(Pinjaman.jumlah).label('total')
    ).filter(
        Pinjaman.tanggal >= six_months_ago
    ).group_by('month').order_by('month').all()

    # Process the data for the chart
    transaction_months = []
    savings_data = []
    loan_data = []
    
    # Create a list of the last 6 months
    current_date = datetime.now()
    for i in range(5, -1, -1):
        month_date = current_date - timedelta(days=30*i)
        month_str = month_date.strftime('%Y-%m')
        transaction_months.append(month_date.strftime('%b %Y'))
        
        # Find savings for this month
        month_savings = next((s[1] for s in monthly_savings if s[0] == month_str), 0)
        savings_data.append(month_savings)
        
        # Find loans for this month
        month_loans = next((l[1] for l in monthly_loans if l[0] == month_str), 0)
        loan_data.append(month_loans)
    
    # Get loan status data for pie chart
    loan_status_counts = db.session.query(
        Pinjaman.status, 
        db.func.count(Pinjaman.id)
    ).group_by(Pinjaman.status).all()
    
    loan_status_data = [0, 0, 0, 0]  # [Pending, Disetujui, Ditolak, Lunas]
    for status, count in loan_status_counts:
        if status == 'Pending':
            loan_status_data[0] = count
        elif status == 'Disetujui':
            loan_status_data[1] = count
        elif status == 'Ditolak':
            loan_status_data[2] = count
        elif status == 'Lunas':
            loan_status_data[3] = count
    
    return render_template('index.html',
        total_employees=total_employees,
        total_savings=total_savings,
        total_loans=total_loans,
        total_goods=total_goods,
        recent_transactions=recent_transactions,
        low_stock_items=low_stock_items,
        transaction_months=transaction_months,
        savings_data=savings_data,
        loan_data=loan_data,
        loan_status_data=loan_status_data,
        now=datetime.now()
    )

@app.route('/master_karyawan')
def master_karyawan():
    employees = Employee.query.all()
    return render_template('master_karyawan.html', 
        employees=employees,
        now=datetime.now()
    )

@app.route('/simpanan')
def simpanan():
    savings = Simpanan.query.all()
    savings_types = JenisSimpanan.query.all()
    employees = Employee.query.all()
    total_simpanan = db.session.query(db.func.sum(Simpanan.jumlah)).scalar() or 0
    return render_template('simpanan.html', 
        savings=savings, 
        savings_types=savings_types, 
        employees=employees,
        total_simpanan=total_simpanan,
        now=datetime.now()
    )

@app.route('/pinjaman')
def pinjaman():
    loans = Pinjaman.query.all()
    employees = Employee.query.all()
    total_pinjaman = db.session.query(db.func.sum(Pinjaman.jumlah)).scalar() or 0
    return render_template('pinjaman.html', 
        loans=loans, 
        employees=employees,
        total_pinjaman=total_pinjaman,
        now=datetime.now()
    )

@app.route('/angsuran')
def angsuran():
    installments = Angsuran.query.all()
    loans = Pinjaman.query.all()
    
    # Calculate totals
    total_angsuran_pokok = db.session.query(db.func.sum(Angsuran.jumlah)).scalar() or 0
    total_bunga = db.session.query(db.func.sum(Pinjaman.bunga)).scalar() or 0
    total_pinjaman = db.session.query(db.func.sum(Pinjaman.jumlah)).scalar() or 0
    
    # Calculate total angsuran (pokok + bunga)
    total_angsuran = total_angsuran_pokok + total_bunga
    
    # Calculate sisa angsuran
    sisa_angsuran = total_pinjaman - total_angsuran_pokok
    
    return render_template('angsuran.html', 
        installments=installments, 
        loans=loans,
        total_angsuran_pokok=total_angsuran_pokok,
        total_bunga=total_bunga,
        total_pinjaman=total_pinjaman,
        total_angsuran=total_angsuran,
        sisa_angsuran=sisa_angsuran,
        now=datetime.now()
    )

@app.route('/periode')
def periode():
    periods = Periode.query.all()
    return render_template('periode.html', 
        periods=periods,
        now=datetime.now()
    )

@app.route('/penjualan')
def penjualan():
    try:
        # Get list of periods for dropdown
        periods = Periode.query.order_by(Periode.periode_id.desc()).all()
        
        # Get list of employees for dropdown
        employees = Employee.query.all()
        
        # Get list of items for dropdown
        items = Barang.query.order_by(Barang.kode).all()
        
        return render_template('penjualan.html',
            periods=periods,
            employees=employees,
            items=items,
            today=datetime.now().strftime('%Y-%m-%d')
        )
    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/pembelian')
def pembelian():
    try:
        # Get list of periods for dropdown
        periods = Periode.query.order_by(Periode.periode_id.desc()).all()
        
        # Get list of suppliers for dropdown
        suppliers = Supplier.query.filter_by(status=True).all()
        
        # Get list of items for dropdown
        items = Barang.query.order_by(Barang.kode).all()
        
        return render_template('pembelian.html',
            periods=periods,
            suppliers=suppliers,
            items=items,
            today=datetime.now().strftime('%Y-%m-%d')
        )
    except Exception as e:
        flash(f'Error loading data: {str(e)}', 'error')
        return redirect(url_for('index'))

# API endpoints for different modules
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
            'tgl_keluar': emp.tgl_keluar.strftime('%Y-%m-%d') if emp.tgl_keluar else None,
            'status': emp.status,
            'khusus': emp.khusus,
            'max_plafon': emp.max_plafon,
            'max_plafon_sembako': emp.max_plafon_sembako
        })
    return jsonify(result)

@app.route('/api/employees/<nik>')
def get_employee(nik):
    """Get employee details by NIK"""
    try:
        employee = Employee.query.filter_by(nik=nik).first()
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
            
        return jsonify({
            'id': employee.id,
            'nik': employee.nik,
            'nama': employee.nama,
            'bagian': employee.bagian,
            'jabatan': employee.jabatan,
            'jk': employee.jk,
            'tmk': employee.tmk.strftime('%Y-%m-%d') if employee.tmk else None,
            'iuran_wajib': employee.iuran_wajib,
            'tgl_keluar': employee.tgl_keluar.strftime('%Y-%m-%d') if employee.tgl_keluar else None,
            'status': employee.status,
            'khusus': employee.khusus,
            'max_plafon': employee.max_plafon,
            'max_plafon_sembako': employee.max_plafon_sembako
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items')
def get_items():
    """Get list of items"""
    try:
        items = Barang.query.all()
        result = []
        for item in items:
            result.append({
                'kode': item.kode,
                'nama': item.nama,
                'satuan': item.satuan,
                'harga_jual': item.harga_jual,
                'stok': item.stok
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items/<kode>')
def get_item(kode):
    """Get item details by code"""
    try:
        item = Barang.query.filter_by(kode=kode).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404
            
        return jsonify({
            'kode': item.kode,
            'nama': item.nama,
            'satuan': item.satuan,
            'harga_jual': item.harga_jual,
            'stok': item.stok
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<nik>/balance')
def get_employee_balance(nik):
    """Get employee's outstanding balance"""
    try:
        # Get total sales (penjualan) where keterangan = 'Kredit'
        credit_sales = db.session.query(db.func.sum(Penjualan.total)).filter(
            Penjualan.nik == nik,
            Penjualan.keterangan == 'Kredit'
        ).scalar() or 0

        # Get total payments
        payments = db.session.query(db.func.sum(Penjualan.bayar)).filter(
            Penjualan.nik == nik,
            Penjualan.keterangan == 'Kredit'
        ).scalar() or 0

        # Calculate outstanding balance
        balance = credit_sales - payments

        return jsonify({
            'nik': nik,
            'total': balance
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees', methods=['POST'])
def add_employee():
    data = request.json
    print("Received data:", data)  # Debug print
    
    # Validate required fields
    required_fields = ['nik', 'nama', 'bagian', 'jabatan', 'jk', 'tmk']
    for field in required_fields:
        if not data.get(field):
            error_msg = f'Field {field} is required'
            print("Validation error:", error_msg)  # Debug print
            return jsonify({'message': error_msg}), 400

    try:
        # Parse and validate date
        try:
            tmk_date = datetime.strptime(data['tmk'], '%Y-%m-%d')
        except ValueError as e:
            print("Date parsing error:", str(e))  # Debug print
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Parse and validate numeric fields
        try:
            iuran_wajib = float(data.get('iuran_wajib', 0))
            max_plafon = float(data.get('max_plafon', 0))
            max_plafon_sembako = float(data.get('max_plafon_sembako', 0))
        except ValueError as e:
            print("Numeric parsing error:", str(e))  # Debug print
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
        print("Employee added successfully")  # Debug print
        return jsonify({'message': 'Success', 'id': employee.id}), 201
    except Exception as e:
        db.session.rollback()
        print("Error adding employee:", str(e))  # Debug print
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
        flash('Data karyawan berhasil diperbarui', 'success')
        return jsonify({'message': 'Success'}), 200
    except Exception as e:
        db.session.rollback()
        flash('Gagal memperbarui data karyawan', 'error')
        return jsonify({'message': str(e)}), 400

@app.route('/api/employees/<int:id>', methods=['DELETE'])
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    try:
        db.session.delete(employee)
        db.session.commit()
        flash('Karyawan berhasil dihapus', 'success')
        return jsonify({'message': 'Success'}), 200
    except Exception as e:
        db.session.rollback()
        flash('Gagal menghapus karyawan', 'error')
        return jsonify({'message': str(e)}), 400

if __name__ == '__main__':
    import sys
    with app.app_context():
        db.create_all()
        if len(sys.argv) > 1 and sys.argv[1] == 'import-data':
            from employee_cooperative_app.utils.db_importer import import_data
            success = import_data()
            if success:
                print("Data import completed successfully.")
            else:
                print("Data import failed.")
        else:
            app.run(debug=True, port=8000)

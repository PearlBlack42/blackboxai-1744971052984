
from flask import Blueprint, jsonify, request
from datetime import datetime
from employee_cooperative_app.utils.database import db, Penjualan, PenjualanDetail

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/api/sales/next-invoice/<periode_id>')
def get_next_invoice(periode_id):
    """Get next available invoice number for the given period"""
    try:
        # Get period
        period = Periode.query.get(periode_id)
        if not period:
            return jsonify({'error': 'Period not found'}), 404

        # Get latest invoice number for this period
        latest_sale = Penjualan.query.filter_by(periode_id=periode_id).order_by(Penjualan.faktur.desc()).first()
        
        if not latest_sale:
            # No sales yet, start with 001
            invoice_number = f'PJ{period.kode}001'
        else:
            # Extract number from latest invoice and increment
            current_number = int(latest_sale.faktur[-3:])
            next_number = current_number + 1
            invoice_number = f'PJ{period.kode}{next_number:03d}'

        return jsonify({'invoice_number': invoice_number})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/api/sales', methods=['POST'])
def create_sale():
    """Create a new sale transaction"""
    try:
        data = request.get_json()
        
        # Create new sale
        sale = Penjualan(
            faktur=data['faktur'],
            tanggal=datetime.strptime(data['tanggal'], '%Y-%m-%d'),
            nik=data['nik'],
            periode_id=data['periode_id'],
            keterangan=data.get('keterangan', 'Tunai'),
            total=data['total'],
            bayar=data['bayar'],
            kembali=data['kembali']
        )
        
        db.session.add(sale)
        
        # If payment type is credit, check credit limit
        if data.get('keterangan') == 'Kredit':
            # Get employee
            employee = Employee.query.filter_by(nik=data['nik']).first()
            if not employee:
                raise Exception("Karyawan tidak ditemukan")

            # Get current outstanding balance
            current_balance = db.session.query(db.func.sum(Penjualan.total)).filter(
                Penjualan.nik == data['nik'],
                Penjualan.keterangan == 'Kredit'
            ).scalar() or 0

            # Calculate new total balance
            new_balance = current_balance + data['total']

            # Check if exceeds credit limit
            if new_balance > employee.max_plafon:
                raise Exception(f"Total kredit ({new_balance:,.0f}) melebihi batas kredit ({employee.max_plafon:,.0f})")

        # Create sale details and update stock
        for item in data['items']:
            # Get the item
            barang = Barang.query.filter_by(kode=item['kode_barang']).first()
            if not barang:
                raise Exception(f"Barang dengan kode {item['kode_barang']} tidak ditemukan")
            
            # Check stock
            if barang.stok < item['qty']:
                raise Exception(f"Stok {barang.nama} tidak mencukupi (tersedia: {barang.stok})")
            
            # Create sale detail
            detail = PenjualanDetail(
                faktur=sale.faktur,
                kode_barang=item['kode_barang'],
                harga=item['harga'],
                qty=item['qty'],
                total=item['total']
            )
            db.session.add(detail)
            
            # Update stock
            barang.stok -= item['qty']
            db.session.add(barang)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Gagal menyimpan transaksi: {str(e)}")
        
        return jsonify({
            "message": "Sale created successfully",
            "id": sale.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@sales_bp.route('/api/sales/<faktur>', methods=['GET'])
def get_sale(faktur):
    """Get sale details by invoice number"""
    try:
        sale = Penjualan.query.filter_by(faktur=faktur).first()
        if not sale:
            return jsonify({"error": "Sale not found"}), 404
            
        result = {
            "id": sale.id,
            "faktur": sale.faktur,
            "tanggal": sale.tanggal.strftime('%Y-%m-%d'),
            "nik": sale.nik,
            "nama": sale.employee.nama,
            "periode_id": sale.periode_id,
            "keterangan": sale.keterangan,
            "total": sale.total,
            "bayar": sale.bayar,
            "kembali": sale.kembali,
            "items": []
        }
        
        for detail in sale.details:
            result["items"].append({
                "kode_barang": detail.kode_barang,
                "nama_barang": detail.barang.nama,
                "harga": detail.harga,
                "qty": detail.qty,
                "total": detail.total
            })
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

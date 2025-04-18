from flask import Blueprint, jsonify, request
from datetime import datetime
from employee_cooperative_app.utils.database import db, Pembelian, PembelianDetail, Barang, Periode, Supplier

purchase_bp = Blueprint('purchase', __name__)

@purchase_bp.route('/api/suppliers')
def get_suppliers():
    """Get list of suppliers"""
    try:
        suppliers = Supplier.query.filter_by(status=True).all()
        result = []
        for supplier in suppliers:
            result.append({
                'id': supplier.id,
                'nama': supplier.nama,
                'alamat': supplier.alamat,
                'telepon': supplier.telepon,
                'email': supplier.email,
                'npwp': supplier.npwp
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@purchase_bp.route('/api/suppliers/<int:id>')
def get_supplier(id):
    """Get supplier details"""
    try:
        supplier = Supplier.query.get_or_404(id)
        return jsonify({
            'id': supplier.id,
            'nama': supplier.nama,
            'alamat': supplier.alamat,
            'telepon': supplier.telepon,
            'email': supplier.email,
            'npwp': supplier.npwp
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@purchase_bp.route('/api/purchases/next-invoice/<periode_id>')
def get_next_invoice(periode_id):
    """Get next available invoice number for the given period"""
    try:
        # Get period
        period = Periode.query.get(periode_id)
        if not period:
            return jsonify({'error': 'Period not found'}), 404

        # Get latest invoice number for this period
        latest_purchase = Pembelian.query.filter_by(periode_id=periode_id).order_by(Pembelian.faktur.desc()).first()
        
        if not latest_purchase:
            # No purchases yet, start with 001
            invoice_number = f'PB{period.kode}001'
        else:
            # Extract number from latest invoice and increment
            current_number = int(latest_purchase.faktur[-3:])
            next_number = current_number + 1
            invoice_number = f'PB{period.kode}{next_number:03d}'

        return jsonify({'invoice_number': invoice_number})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@purchase_bp.route('/api/purchases', methods=['POST'])
def create_purchase():
    """Create a new purchase transaction"""
    try:
        data = request.json
        
        # Create purchase
        purchase = Pembelian(
            faktur=data['faktur'],
            tanggal=datetime.strptime(data['tanggal'], '%Y-%m-%d'),
            supplier_id=data['supplier_id'],
            periode_id=data['periode_id'],
            keterangan=data.get('keterangan'),
            ppn=data.get('ppn', 0),
            total=data['total'],
            total_ppn=data['total_ppn']
        )
        
        db.session.add(purchase)
        
        # Create purchase details and update stock
        for item in data['items']:
            # Get the item
            barang = Barang.query.filter_by(kode=item['kode_barang']).first()
            if not barang:
                raise Exception(f"Barang dengan kode {item['kode_barang']} tidak ditemukan")
            
            # Create purchase detail
            detail = PembelianDetail(
                faktur=purchase.faktur,
                kode_barang=item['kode_barang'],
                harga=item['harga'],
                qty=item['qty'],
                total=item['total']
            )
            db.session.add(detail)
            
            # Update stock
            barang.stok += item['qty']
            db.session.add(barang)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Gagal menyimpan transaksi: {str(e)}")
        
        return jsonify({
            "message": "Purchase created successfully",
            "id": purchase.id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

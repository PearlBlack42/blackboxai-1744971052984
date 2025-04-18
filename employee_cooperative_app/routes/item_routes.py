from flask import Blueprint, jsonify, request
from employee_cooperative_app.utils.database import db, Barang

item_bp = Blueprint('item', __name__)

@item_bp.route('/api/items', methods=['GET'])
def get_items():
    """Get list of items"""
    try:
        items = Barang.query.order_by(Barang.kode).all()
        result = []
        for item in items:
            result.append({
                'kode': item.kode,
                'nama': item.nama,
                'satuan': item.satuan,
                'stok': item.stok,
                'harga_beli': item.harga_beli,
                'harga_jual': item.harga_jual
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/api/items/<kode>', methods=['GET'])
def get_item(kode):
    """Get item details"""
    try:
        item = Barang.query.filter_by(kode=kode).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        return jsonify({
            'kode': item.kode,
            'nama': item.nama,
            'satuan': item.satuan,
            'stok': item.stok,
            'harga_beli': item.harga_beli,
            'harga_jual': item.harga_jual
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@item_bp.route('/api/items', methods=['POST'])
def create_item():
    """Create a new item"""
    try:
        data = request.json
        
        # Check if item code already exists
        existing_item = Barang.query.filter_by(kode=data['kode']).first()
        if existing_item:
            return jsonify({'error': 'Kode barang sudah digunakan'}), 400

        # Create new item
        item = Barang(
            kode=data['kode'],
            nama=data['nama'],
            satuan=data['satuan'],
            stok=data['stok'],
            harga_beli=data['harga_beli'],
            harga_jual=data['harga_jual']
        )
        
        db.session.add(item)
        db.session.commit()
        
        return jsonify({
            'message': 'Item created successfully',
            'kode': item.kode
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@item_bp.route('/api/items/<kode>', methods=['PUT'])
def update_item(kode):
    """Update an item"""
    try:
        data = request.json
        item = Barang.query.filter_by(kode=kode).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        # Update item fields
        item.nama = data['nama']
        item.satuan = data['satuan']
        item.stok = data['stok']
        item.harga_beli = data['harga_beli']
        item.harga_jual = data['harga_jual']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Item updated successfully',
            'kode': item.kode
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@item_bp.route('/api/items/<kode>', methods=['DELETE'])
def delete_item(kode):
    """Delete an item"""
    try:
        item = Barang.query.filter_by(kode=kode).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        db.session.delete(item)
        db.session.commit()
        
        return jsonify({
            'message': 'Item deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

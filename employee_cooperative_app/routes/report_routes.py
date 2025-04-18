from flask import Blueprint, jsonify, request, render_template
from datetime import datetime
from employee_cooperative_app.utils.database import db, Penjualan, PenjualanDetail, Pembelian, PembelianDetail, Employee, Supplier, Barang, Periode
import pandas as pd
from io import BytesIO

report_bp = Blueprint('report', __name__)

def generate_sales_report(periode_id, payment_type):
    """Generate sales report data"""
    # Get period details
    period = Periode.query.get(periode_id)
    if not period:
        raise Exception("Period not found")

    # Query sales data
    sales = (Penjualan.query
        .filter(Penjualan.periode_id == periode_id)
        .filter(Penjualan.keterangan == payment_type.title())
        .join(Employee, Penjualan.nik == Employee.nik)
        .add_columns(Employee.nama)
        .order_by(Penjualan.tanggal)
        .all())

    # Prepare report data
    report_data = []
    total_amount = 0
    for sale, employee_name in sales:
        # Get sale details
        details = (PenjualanDetail.query
            .filter_by(faktur=sale.faktur)
            .join(Barang, PenjualanDetail.kode_barang == Barang.kode)
            .add_columns(Barang.nama)
            .all())
        
        # Format details
        items = [f"{detail[1]} ({detail[0].qty} x {detail[0].harga:,.0f})" 
                for detail in details]
        
        report_data.append({
            'tanggal': sale.tanggal.strftime('%d/%m/%Y'),
            'faktur': sale.faktur,
            'karyawan': employee_name,
            'items': ', '.join(items),
            'total': sale.total
        })
        total_amount += sale.total

    return {
        'period': period.periode,
        'payment_type': payment_type,
        'data': report_data,
        'total': total_amount
    }

def generate_purchase_report(periode_id):
    """Generate purchase report data"""
    # Get period details
    period = Periode.query.get(periode_id)
    if not period:
        raise Exception("Period not found")

    # Query purchase data
    purchases = (Pembelian.query
        .filter(Pembelian.periode_id == periode_id)
        .join(Supplier, Pembelian.supplier_id == Supplier.id)
        .add_columns(Supplier.nama)
        .order_by(Pembelian.tanggal)
        .all())

    # Prepare report data
    report_data = []
    total_amount = 0
    total_ppn = 0
    for purchase, supplier_name in purchases:
        # Get purchase details
        details = (PembelianDetail.query
            .filter_by(faktur=purchase.faktur)
            .join(Barang, PembelianDetail.kode_barang == Barang.kode)
            .add_columns(Barang.nama)
            .all())
        
        # Format details
        items = [f"{detail[1]} ({detail[0].qty} x {detail[0].harga:,.0f})" 
                for detail in details]
        
        report_data.append({
            'tanggal': purchase.tanggal.strftime('%d/%m/%Y'),
            'faktur': purchase.faktur,
            'supplier': supplier_name,
            'items': ', '.join(items),
            'total': purchase.total,
            'ppn': purchase.ppn,
            'total_ppn': purchase.total_ppn
        })
        total_amount += purchase.total
        total_ppn += purchase.total_ppn

    return {
        'period': period.periode,
        'data': report_data,
        'total': total_amount,
        'total_ppn': total_ppn
    }

@report_bp.route('/api/reports/preview')
def preview_report():
    """Generate HTML preview of report"""
    try:
        periode_id = request.args.get('periode')
        payment_type = request.args.get('payment_type', 'credit')

        if payment_type == 'purchase':
            report_data = generate_purchase_report(periode_id)
            html = render_template('report_purchase.html', **report_data)
        else:
            report_data = generate_sales_report(periode_id, payment_type)
            html = render_template('report_sales.html', **report_data)

        return jsonify({'html': html})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@report_bp.route('/api/reports/export')
def export_report():
    """Export report to Excel"""
    try:
        periode_id = request.args.get('periode')
        payment_type = request.args.get('payment_type', 'credit')

        if payment_type == 'purchase':
            report_data = generate_purchase_report(periode_id)
            df = pd.DataFrame(report_data['data'])
            filename = f"purchase_report_{report_data['period']}.xlsx"
        else:
            report_data = generate_sales_report(periode_id, payment_type)
            df = pd.DataFrame(report_data['data'])
            filename = f"sales_report_{report_data['period']}_{payment_type}.xlsx"

        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
            
            # Auto-adjust columns width
            worksheet = writer.sheets['Sheet1']
            for idx, col in enumerate(df.columns):
                series = df[col]
                max_len = max(
                    series.astype(str).map(len).max(),
                    len(str(series.name))
                ) + 1
                worksheet.set_column(idx, idx, max_len)

        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'Content-Disposition': f'attachment; filename={filename}'
        }
    except Exception as e:
        return jsonify({'error': str(e)}), 500

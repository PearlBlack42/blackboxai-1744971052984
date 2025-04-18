from flask import Blueprint, render_template, jsonify
from employee_cooperative_app.utils.db_importer import import_data, sync_data

import_bp = Blueprint('import', __name__)

@import_bp.route('/')
def import_database_page():
    """Render the database import/sync management page"""
    return render_template('import_database.html')

@import_bp.route('/execute', methods=['POST'])
def import_database():
    """API endpoint to trigger database import"""
    try:
        success = import_data()
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Database import completed successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Database import failed. Check logs for details.'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error during import: {str(e)}'
        }), 500

@import_bp.route('/sync', methods=['POST'])
def sync_database():
    """API endpoint to trigger database synchronization"""
    try:
        success = sync_data()
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Database synchronization completed successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Database synchronization failed. Check logs for details.'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error during synchronization: {str(e)}'
        }), 500

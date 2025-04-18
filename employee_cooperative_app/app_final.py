from flask import Flask, request, render_template, flash, redirect, url_for, jsonify
from models import db
from datetime import datetime
import os

app = Flask(__name__)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config.update(
    SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(basedir, 'instance', 'cooperative.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY='dev-key-123',
    UPLOAD_FOLDER=os.path.join(basedir, 'uploads'),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
)

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize SQLAlchemy
db.init_app(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/import-database', methods=['GET'])
def import_database_page():
    return render_template('import_database.html')

@app.route('/import-database/execute', methods=['POST'])
def execute_import():
    from database_import import handle_database_import
    try:
        success, result = handle_database_import()
        
        if success:
            flash('Database imported successfully', 'success')
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'details': result['details']
            })
        else:
            flash('Import failed: ' + str(result), 'error')
            return jsonify({
                'status': 'error',
                'message': str(result)
            }), 400
            
    except Exception as e:
        flash('Error during import: ' + str(e), 'error')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables from SQLAlchemy models
        db.create_all()
        
    app.run(host='0.0.0.0', port=8000, debug=True)

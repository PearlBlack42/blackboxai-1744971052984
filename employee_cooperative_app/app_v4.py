from flask import Flask, jsonify, request, render_template, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
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

db = SQLAlchemy(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/import-database', methods=['GET', 'POST'])
def import_database():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'database_file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['database_file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
            
        if not file.filename.endswith(('.mdb', '.accdb')):
            flash('Invalid file type. Please upload .mdb or .accdb file')
            return redirect(request.url)
            
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            flash('Database file uploaded successfully')
            return redirect(url_for('import_database'))
            
        except Exception as e:
            flash(f'Error uploading file: {str(e)}')
            return redirect(request.url)
            
    return render_template('import_database_simple.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)

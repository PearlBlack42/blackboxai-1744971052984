from flask import Flask, jsonify, request, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'cooperative.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Upload folder configuration
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/import-database', methods=['GET', 'POST'])
def import_database():
    if request.method == 'POST':
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
            flash(f'Error: {str(e)}')
            return redirect(request.url)
            
    return render_template('import_database.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

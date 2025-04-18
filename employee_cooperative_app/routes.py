from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os

routes = Blueprint('routes', __name__)

@routes.route('/import-database', methods=['GET', 'POST'])
def import_database():
    """Handle database import functionality"""
    if request.method == 'POST':
        if 'database_file' not in request.files:
            flash('No file uploaded')
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
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            flash('Database file uploaded successfully')
            return redirect(url_for('routes.import_database'))
            
        except Exception as e:
            flash(f'Error uploading file: {str(e)}')
            return redirect(request.url)
            
    return render_template('import_database.html')

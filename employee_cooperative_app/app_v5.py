from flask import Flask, request, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'dev-key-123'  # Required for flash messages

# Upload folder configuration
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/import-test', methods=['GET', 'POST'])
def import_test():
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
            flash('File uploaded successfully')
            return redirect(url_for('import_test'))
            
        except Exception as e:
            flash(f'Error uploading file: {str(e)}')
            return redirect(request.url)
            
    return render_template('import_test.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

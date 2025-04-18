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

db = SQLAlchemy(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/import-database')
def import_database():
    return render_template('import_database.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

from flask import Flask, render_template, request, redirect, url_for, flash, session
import logging
from datetime import datetime, timedelta
from functools import wraps
from config import SECRET_KEY
from database import get_tables, get_table_data, execute_query, sanitize_table_name

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(minutes=30)  # Session timeout after 30 minutes

# Add datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Redirect to login if not authenticated, otherwise to dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == "sa" and password == "0711321277":
            session.permanent = True  # Use permanent session
            session['user_id'] = username
            session['login_time'] = datetime.utcnow().isoformat()
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            logging.warning(f"Failed login attempt for username: {username}")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Display the main dashboard"""
    tables = get_tables()
    if not tables:
        flash('An error occurred while accessing the database', 'error')
    
    return render_template('dashboard.html', tables=tables)

@app.route('/table/<table_name>')
@login_required
def view_table(table_name):
    """Display contents of a specific table"""
    # Sanitize table name
    safe_table_name = sanitize_table_name(table_name)
    if not safe_table_name:
        flash('Invalid table name', 'error')
        return redirect(url_for('dashboard'))
    
    columns, rows = get_table_data(safe_table_name)
    if not columns:
        flash('An error occurred while accessing the table', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('table.html', 
                         table_name=safe_table_name,
                         columns=columns,
                         rows=rows)

@app.route('/table/<table_name>/add', methods=['GET', 'POST'])
@login_required
def add_record(table_name):
    """Add a new record to a table"""
    # Sanitize table name
    safe_table_name = sanitize_table_name(table_name)
    if not safe_table_name:
        flash('Invalid table name', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get column information
        columns, _ = get_table_data(safe_table_name)
        if not columns:
            raise ValueError("Could not get column information")
        
        if request.method == 'POST':
            # Build INSERT query dynamically
            field_names = []
            field_values = []
            query_params = []
            
            for column in columns:
                value = request.form.get(column)
                if value:  # Only include non-empty values
                    field_names.append(column)
                    field_values.append('?')
                    query_params.append(value)
            
            if field_names:
                query = f"INSERT INTO [{safe_table_name}] ([{'],['.join(field_names)}]) VALUES ({','.join(field_values)})"
                if execute_query(safe_table_name, query, query_params):
                    flash('Record added successfully!', 'success')
                    return redirect(url_for('view_table', table_name=safe_table_name))
                else:
                    flash('Failed to add record', 'error')
        
        return render_template('add_record.html',
                             table_name=safe_table_name,
                             columns=[{'name': col} for col in columns])
    
    except Exception as e:
        logging.error(f"Error in add_record: {str(e)}")
        flash('An error occurred while adding the record', 'error')
        return redirect(url_for('view_table', table_name=safe_table_name))

@app.route('/table/<table_name>/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_record(table_name, id):
    """Edit an existing record"""
    # Sanitize table name
    safe_table_name = sanitize_table_name(table_name)
    if not safe_table_name:
        flash('Invalid table name', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Get column information and record data
        columns, rows = get_table_data(safe_table_name)
        if not columns:
            raise ValueError("Could not get column information")
        
        # Find record with matching ID
        record = next((row for row in rows if row.get('ID') == str(id)), None)
        if not record:
            flash('Record not found', 'error')
            return redirect(url_for('view_table', table_name=safe_table_name))
        
        if request.method == 'POST':
            # Build UPDATE query dynamically
            updates = []
            query_params = []
            
            for column in columns:
                if column.lower() != 'id':  # Skip ID field
                    value = request.form.get(column)
                    if value is not None:
                        updates.append(f"[{column}] = ?")
                        query_params.append(value)
            
            if updates:
                query_params.append(id)  # For WHERE clause
                query = f"UPDATE [{safe_table_name}] SET {', '.join(updates)} WHERE ID = ?"
                
                if execute_query(safe_table_name, query, query_params):
                    flash('Record updated successfully!', 'success')
                    return redirect(url_for('view_table', table_name=safe_table_name))
                else:
                    flash('Failed to update record', 'error')
        
        return render_template('edit_record.html',
                             table_name=safe_table_name,
                             columns=[{'name': col} for col in columns],
                             record=record)
    
    except Exception as e:
        logging.error(f"Error in edit_record: {str(e)}")
        flash('An error occurred while editing the record', 'error')
        return redirect(url_for('view_table', table_name=safe_table_name))

@app.route('/table/<table_name>/delete/<int:id>')
@login_required
def delete_record(table_name, id):
    """Delete a record"""
    # Sanitize table name
    safe_table_name = sanitize_table_name(table_name)
    if not safe_table_name:
        flash('Invalid table name', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        query = f"DELETE FROM [{safe_table_name}] WHERE ID = ?"
        if execute_query(safe_table_name, query, [id]):
            flash('Record deleted successfully!', 'success')
        else:
            flash('Failed to delete record', 'error')
    
    except Exception as e:
        logging.error(f"Error in delete_record: {str(e)}")
        flash('An error occurred while deleting the record', 'error')
    
    return redirect(url_for('view_table', table_name=safe_table_name))

if __name__ == '__main__':
    app.run(debug=True, port=8000)

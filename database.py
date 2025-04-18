import logging
import subprocess
from typing import Tuple, List, Dict, Optional
import re

def sanitize_table_name(table_name: str) -> str:
    """Sanitize table name to prevent command injection"""
    # Remove any characters that aren't alphanumeric, space, or underscore
    sanitized = re.sub(r'[^a-zA-Z0-9\s_]', '', table_name)
    return sanitized

def get_tables() -> List[str]:
    """Get list of tables from the database"""
    try:
        result = subprocess.run(
            ['mdb-tables', '-1', 'simkopkar.mDB'],
            capture_output=True,
            text=True,
            check=True
        )
        tables = result.stdout.strip().split('\n')
        return [table for table in tables if table]  # Remove empty strings
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting tables: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error getting tables: {str(e)}")
        return []

def get_table_data(table_name: str) -> Tuple[List[str], List[Dict]]:
    """Get data from a specific table"""
    try:
        # Sanitize table name
        safe_table_name = sanitize_table_name(table_name)
        if not safe_table_name:
            logging.error("Invalid table name provided")
            return [], []

        # Get table data
        result = subprocess.run(
            ['mdb-export', 'simkopkar.mDB', safe_table_name],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse CSV output
        lines = result.stdout.strip().split('\n')
        if not lines:
            return [], []

        # Get headers from first line
        headers = [h.strip('"') for h in lines[0].split(',')]

        # Parse data rows
        rows = []
        for line in lines[1:]:
            # Handle empty lines
            if not line.strip():
                continue

            # Split by comma but respect quoted values
            values = []
            current = ''
            in_quotes = False
            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    values.append(current.strip('"'))
                    current = ''
                else:
                    current += char
            values.append(current.strip('"'))

            # Create row dictionary
            row_dict = dict(zip(headers, values))
            rows.append(row_dict)

        return headers, rows

    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting table data: {str(e)}")
        return [], []
    except Exception as e:
        logging.error(f"Unexpected error getting table data: {str(e)}")
        return [], []

def execute_query(table_name: str, query: str, params: Optional[List] = None) -> bool:
    """Execute a query on the specified table"""
    try:
        # Sanitize table name
        safe_table_name = sanitize_table_name(table_name)
        if not safe_table_name:
            logging.error("Invalid table name provided")
            return False

        # Build and execute command
        cmd = ['mdb-sql', 'simkopkar.mDB']
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send query to process
        stdout, stderr = process.communicate(input=query)

        if process.returncode != 0:
            logging.error(f"Query execution failed: {stderr}")
            return False

        return True

    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing query: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error executing query: {str(e)}")
        return False

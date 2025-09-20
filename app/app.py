from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import json

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_db_schema(db_path='database.db'):
    """
    Generates a detailed schema of the database with statistics for each column.
    """
    if not os.path.exists(db_path):
        return "Database not found."

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    schema_str = ""
    for table in tables:
        table_name = table[0]
        
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = c.fetchone()[0]
        
        schema_str += f"Table '{table_name}' ({row_count} rows):\n"
        
        c.execute(f"PRAGMA table_info({table_name});")
        columns = c.fetchall()
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            
            schema_str += f"  - Column '{col_name}' (type: {col_type})"
            
            try:
                if col_type in ['INTEGER', 'REAL', 'FLOAT', 'DOUBLE', 'BIGINT', 'DECIMAL']:
                    stats_query = f'SELECT MIN("{col_name}"), MAX("{col_name}"), AVG("{col_name}") FROM "{table_name}"'
                    min_val, max_val, avg_val = c.execute(stats_query).fetchone()
                    schema_str += f" | Stats: min={min_val}, max={max_val}, avg={avg_val:.2f if avg_val else 0.00}\n"
                elif col_type == 'TEXT':
                    top_values_query = f'SELECT "{col_name}", COUNT(*) as freq FROM "{table_name}" WHERE "{col_name}" IS NOT NULL GROUP BY "{col_name}" ORDER BY freq DESC LIMIT 3'
                    top_values = c.execute(top_values_query).fetchall()
                    top_values_str = ", ".join([f"'{val}' ({freq}x)" for val, freq in top_values])
                    if top_values:
                        schema_str += f" | Top values: {top_values_str}\n"
                    else:
                        schema_str += "\n"
                else:
                    schema_str += "\n"
            except Exception:
                 schema_str += " | (Could not compute stats)\n"

        schema_str += "\n"
        
    conn.close()
    return schema_str

def parse_schema_for_frontend(schema_text, table_name, row_count):
    """
    Parse the schema text to extract column information for frontend display
    """
    columns = []
    lines = schema_text.split('\n')
    
    in_table = False
    for line in lines:
        if f"Table '{table_name}'" in line:
            in_table = True
            continue
        elif line.startswith("Table '") and in_table:
            break
        elif in_table and line.strip().startswith("- Column '"):
            # Parse column information
            # Example: "  - Column 'customer_id' (type: TEXT) | Stats: min=1001, max=1020, avg=1010.50"
            try:
                parts = line.split("'")
                if len(parts) >= 2:
                    col_name = parts[1]
                    
                    # Extract type
                    type_part = line.split("(type: ")[1].split(")")[0] if "(type: " in line else "TEXT"
                    
                    # Map SQLite types to frontend types
                    frontend_type = "string"
                    if type_part in ["INTEGER", "BIGINT"]:
                        frontend_type = "number"
                    elif type_part in ["REAL", "FLOAT", "DOUBLE", "DECIMAL"]:
                        frontend_type = "number"
                    elif "DATE" in type_part or "TIME" in type_part:
                        frontend_type = "date"
                    elif type_part == "BOOLEAN":
                        frontend_type = "boolean"
                    
                    # Extract stats - improved parsing
                    stats = "No stats available"
                    if "| Stats: " in line:
                        stats_part = line.split("| Stats: ")[1].strip()
                        stats = stats_part
                    elif "| Top values: " in line:
                        stats_part = line.split("| Top values: ")[1].strip()
                        stats = f"Top values: {stats_part}"
                    elif "| (Could not compute stats)" in line:
                        stats = "Stats unavailable"
                    elif "|" in line:
                        # Fallback - extract whatever comes after the |
                        stats_part = line.split("|")[1].strip()
                        if stats_part and stats_part != "(Could not compute stats)":
                            stats = stats_part
                    
                    columns.append({
                        "name": col_name,
                        "type": frontend_type,
                        "stats": stats
                    })
            except Exception as e:
                # If parsing fails, add basic info
                print(f"Warning: Could not parse line: {line}, error: {e}")
                continue
    
    return {
        "table_name": table_name,
        "row_count": row_count,
        "columns": columns
    }

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.csv'):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        db_name = os.path.splitext(filename)[0] + ".db"
        db_path = os.path.join(app.config['UPLOAD_FOLDER'], db_name)
        
        df = pd.read_csv(filepath)
        conn = sqlite3.connect(db_path)
        table_name = os.path.splitext(filename)[0].replace(" ", "_")
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()

        context = get_db_schema(db_path)
        context_filepath = os.path.join(app.config['UPLOAD_FOLDER'], os.path.splitext(filename)[0] + "_context.json")
        with open(context_filepath, 'w') as f:
            json.dump({'schema': context, 'db_path': db_path}, f)

        # Parse schema to return structured information
        schema_info = parse_schema_for_frontend(context, table_name, len(df))

        return jsonify({
            'message': 'File processed successfully', 
            'filename': filename,
            'schema': context,
            'schema_info': schema_info
        }), 200

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schema', methods=['GET'])
def get_schema():
    """Get database schema for frontend"""
    try:
        schema = get_db_schema()
        
        # Get table names and row counts to provide structured info
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        
        schema_info = {
            "table_name": "multiple_tables",
            "row_count": 0,
            "columns": []
        }
        
        # If there's only one table, provide detailed info for it
        if len(tables) == 1:
            table_name = tables[0][0]
            c.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = c.fetchone()[0]
            schema_info = parse_schema_for_frontend(schema, table_name, row_count)
        elif len(tables) > 1:
            # Multiple tables - provide summary
            total_rows = 0
            for table in tables:
                table_name = table[0]
                c.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_rows += c.fetchone()[0]
            
            schema_info = {
                "table_name": f"{len(tables)} tables",
                "row_count": total_rows,
                "columns": [{"name": f"Tables: {', '.join([t[0] for t in tables])}", "type": "string", "stats": "Multiple tables available"}]
            }
        
        conn.close()
        
        return jsonify({
            'schema': schema,
            'schema_info': schema_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_sql', methods=['POST'])
def generate_sql():
    question = request.json['question']
    
    schema = None
    db_path = 'database.db' 
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            if file.endswith('_context.json'):
                context_filepath = os.path.join(app.config['UPLOAD_FOLDER'], file)
                with open(context_filepath, 'r') as f:
                    context_data = json.load(f)
                    schema = context_data['schema']
                    db_path = context_data['db_path']
                break 

    if not schema:
        schema = get_db_schema()

    model = genai.GenerativeModel('gemini-2.0-flash')

    prompt = f"""
    You are an expert SQL developer. Your task is to generate a precise SQL query to answer the user's question based on the provided database schema.

    If the user's question is a valid request for data, generate the SQL query.
    If the user's question is NOT a valid request for data (e.g., it's a greeting, a random statement, or doesn't make sense in a data context), return the single word "INVALID".

    ### Database Schema and Statistics:
    {schema}

    ### User Question:
    "{question}"

    ### Output (SQL Query or "INVALID"):
    """

    try:
        response = model.generate_content(prompt)
        output = response.text.strip().replace("```sql", "").replace("```", "").strip()

        if output.upper() == 'INVALID':
            return jsonify({'error': "I'm sorry, I can only answer questions related to the data. Please ask a question about the database content."}), 400

        sql_query = output
        
        # Safety Check: Only allow SELECT statements
        if not sql_query.strip().upper().startswith('SELECT'):
            return jsonify({'error': 'For security reasons, only SELECT queries are allowed.'}), 403

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(sql_query)
        result = c.fetchall()
        column_names = [description[0] for description in c.description]
        conn.close()
        
        return jsonify({'sql_query': sql_query, 'result': result, 'columns': column_names})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)

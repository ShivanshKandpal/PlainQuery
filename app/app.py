from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import json
import time
from datetime import datetime
import urllib3

# Suppress SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

app = Flask(__name__)
# Enable CORS (restrict to env origins in production if provided)
cors_origins = os.getenv('CORS_ORIGINS')
if cors_origins:
    origins_list = [o.strip() for o in cors_origins.split(',') if o.strip()]
    CORS(app, resources={r"/*": {"origins": origins_list}})
else:
    CORS(app)  # Enable CORS for all routes (needed for frontend)

# Configure uploads folder (env override) and ensure it exists in all runtimes
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Monitoring data
monitoring_data = {
    'requests': [],
    'feedback_sessions': [],  # Store feedback and regenerations
    'total_cost': 0.0,
    'cost_cap': 10.0  # $10 daily limit
}

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
    start_time = time.time()
    
    # Check cost cap
    if monitoring_data['total_cost'] >= monitoring_data['cost_cap']:
        return jsonify({'error': 'Daily cost cap reached. Please try again tomorrow.'}), 429
    
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

    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an expert SQL query generator with a focus on security and accuracy. Generate ONLY a SELECT statement to answer the user's question.

    CRITICAL SECURITY RULES:
    1. ONLY generate SELECT statements - no INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, or any data modification commands
    2. Do NOT use any SQL functions that could modify data or system state
    3. If the question asks for data modification, return "INVALID"

    QUERY OPTIMIZATION RULES:
    1. Use INNER JOIN by default for relationships - only use LEFT JOIN when explicitly asked to include records with no matches
    2. Always use proper WHERE clauses to filter data efficiently
    3. Use aggregate functions (COUNT, SUM, AVG, MAX, MIN) when appropriate
    4. Include ORDER BY clauses when logical (e.g., sorting by date, amount, name)
    5. Use LIMIT when appropriate to prevent excessive results
    6. Group by the correct columns when using aggregate functions
    7. Use proper aliases for readability: table aliases (t1, c, p) and column aliases (AS total_amount)

    VALIDATION RULES:
    1. If the question is not a data query (greetings, random statements, non-data questions), return exactly "INVALID"
    2. If the question asks to modify, delete, or create data, return exactly "INVALID"
    3. Ensure all column names and table names exist in the provided schema
    4. Use proper SQL syntax for the SQLite dialect

    ### Database Schema:
    {schema}

    ### User Question:
    "{question}"

    ### Instructions:
    Generate a syntactically correct SELECT query that accurately answers the question. Return ONLY the SQL query without any explanation, formatting, or code blocks. If the question is invalid or asks for data modification, return exactly "INVALID".

    ### SQL Query:
    """

    try:
        response = model.generate_content(prompt)
        output = response.text.strip().replace("```sql", "").replace("```", "").strip()
        
        # Calculate latency and estimated cost
        latency = time.time() - start_time
        estimated_cost = estimate_api_cost(prompt, output)
        monitoring_data['total_cost'] += estimated_cost
        
        # Generate unique request ID for feedback tracking
        request_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(monitoring_data['requests'])}"
        
        # Log request for monitoring
        monitoring_data['requests'].append({
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'sql_query': output,
            'latency': latency,
            'cost': estimated_cost,
            'total_cost': monitoring_data['total_cost']
        })

        if output.upper() == 'INVALID':
            return jsonify({'error': "I'm sorry, I can only answer questions related to the data. Please ask a question about the database content."}), 400

        sql_query = output
        
        # Enhanced Safety Check: Only allow SELECT statements and block dangerous patterns
        sql_upper = sql_query.strip().upper()
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'EXEC', 'EXECUTE', '--', ';', 'PRAGMA']
        
        if not sql_upper.startswith('SELECT'):
            return jsonify({'error': 'Security violation: Only SELECT statements are allowed.'}), 403
            
        # Check for dangerous patterns within the query
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return jsonify({'error': f'Security violation: Dangerous SQL pattern detected ({keyword}). Only read-only SELECT queries are permitted.'}), 403

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(sql_query)
        result = c.fetchall()
        column_names = [description[0] for description in c.description]
        conn.close()
        
        return jsonify({
            'request_id': request_id,
            'sql_query': sql_query, 
            'result': result, 
            'columns': column_names,
            'latency': round(latency, 3),
            'cost': round(estimated_cost, 6),
            'total_cost': round(monitoring_data['total_cost'], 6)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def estimate_api_cost(prompt, response):
    """Estimate API cost based on token usage (approximate)"""
    # Gemini 1.5 Flash pricing: roughly $0.075 per 1M input tokens, $0.30 per 1M output tokens
    input_tokens = len(prompt.split()) * 1.3  # Rough approximation
    output_tokens = len(response.split()) * 1.3
    
    input_cost = (input_tokens / 1_000_000) * 0.075
    output_cost = (output_tokens / 1_000_000) * 0.30
    
    return input_cost + output_cost


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback submission and regenerate SQL with user clarification"""
    start_time = time.time()
    
    # Check cost cap
    if monitoring_data['total_cost'] >= monitoring_data['cost_cap']:
        return jsonify({'error': 'Daily cost cap reached. Please try again tomorrow.'}), 429
    
    data = request.json
    original_question = data.get('original_question', '')
    feedback = data.get('feedback', '')
    request_id = data.get('request_id', '')
    
    if not original_question or not feedback:
        return jsonify({'error': 'Both original_question and feedback are required.'}), 400
    
    # Get database schema
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

    model = genai.GenerativeModel('gemini-1.5-flash')

    # Enhanced prompt with feedback context
    prompt = f"""
    You are an expert SQL query generator with a focus on security and accuracy. Generate ONLY a SELECT statement to answer the user's question.

    CRITICAL SECURITY RULES:
    1. ONLY generate SELECT statements - no INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, or any data modification commands
    2. Do NOT use any SQL functions that could modify data or system state
    3. If the question asks for data modification, return "INVALID"

    QUERY OPTIMIZATION RULES:
    1. Use INNER JOIN by default for relationships - only use LEFT JOIN when explicitly asked to include records with no matches
    2. Always use proper WHERE clauses to filter data efficiently
    3. Use aggregate functions (COUNT, SUM, AVG, MAX, MIN) when appropriate
    4. Include ORDER BY clauses when logical (e.g., sorting by date, amount, name)
    5. Use LIMIT when appropriate to prevent excessive results
    6. Group by the correct columns when using aggregate functions
    7. Use proper aliases for readability: table aliases (t1, c, p) and column aliases (AS total_amount)

    VALIDATION RULES:
    1. If the question is not a data query (greetings, random statements, non-data questions), return exactly "INVALID"
    2. If the question asks to modify, delete, or create data, return exactly "INVALID"
    3. Ensure all column names and table names exist in the provided schema
    4. Use proper SQL syntax for the SQLite dialect

    ### Database Schema:
    {schema}

    ### Original User Question:
    "{original_question}"

    ### User Feedback/Clarification:
    "{feedback}"

    ### Instructions:
    The user has provided feedback about their original question. Use this feedback to understand what they actually meant and generate a more accurate SQL query. Pay close attention to the clarification provided in the feedback to correct any misunderstandings from the original query.

    Generate a syntactically correct SELECT query that accurately answers the question based on the user's clarification. Return ONLY the SQL query without any explanation, formatting, or code blocks. If the question is invalid or asks for data modification, return exactly "INVALID".

    ### SQL Query:
    """

    try:
        response = model.generate_content(prompt)
        output = response.text.strip().replace("```sql", "").replace("```", "").strip()
        
        # Calculate latency and estimated cost
        latency = time.time() - start_time
        estimated_cost = estimate_api_cost(prompt, output)
        monitoring_data['total_cost'] += estimated_cost
        
        # Generate new request ID for the feedback-based query
        feedback_request_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_fb_{len(monitoring_data['feedback_sessions'])}"
        
        # Log feedback session
        feedback_session = {
            'feedback_request_id': feedback_request_id,
            'original_request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'original_question': original_question,
            'feedback': feedback,
            'regenerated_sql': output,
            'latency': latency,
            'cost': estimated_cost,
            'total_cost': monitoring_data['total_cost']
        }
        
        monitoring_data['feedback_sessions'].append(feedback_session)

        # Also log this feedback request in the main requests array for proper monitoring
        monitoring_data['requests'].append({
            'request_id': feedback_request_id,
            'timestamp': datetime.now().isoformat(),
            'question': f"{original_question} [FEEDBACK: {feedback}]",
            'sql_query': output,
            'latency': latency,
            'cost': estimated_cost,
            'total_cost': monitoring_data['total_cost'],
            'feedback_applied': True,
            'original_request_id': request_id
        })

        if output.upper() == 'INVALID':
            return jsonify({'error': "I'm sorry, I can only answer questions related to the data. Please ask a question about the database content."}), 400

        sql_query = output
        
        # Enhanced Safety Check: Only allow SELECT statements and block dangerous patterns
        sql_upper = sql_query.strip().upper()
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'EXEC', 'EXECUTE', '--', ';', 'PRAGMA']
        
        if not sql_upper.startswith('SELECT'):
            return jsonify({'error': 'Security violation: Only SELECT statements are allowed.'}), 403
            
        # Check for dangerous patterns within the query
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return jsonify({'error': f'Security violation: Dangerous SQL pattern detected ({keyword}). Only read-only SELECT queries are permitted.'}), 403

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(sql_query)
        result = c.fetchall()
        column_names = [description[0] for description in c.description]
        conn.close()
        
        return jsonify({
            'request_id': feedback_request_id,
            'original_request_id': request_id,
            'sql_query': sql_query, 
            'result': result, 
            'columns': column_names,
            'latency': round(latency, 3),
            'cost': round(estimated_cost, 6),
            'total_cost': round(monitoring_data['total_cost'], 6),
            'feedback_applied': True
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/monitoring', methods=['GET'])
def get_monitoring():
    """Get monitoring data including latency, cost, and request history"""
    return jsonify({
        'total_requests': len(monitoring_data['requests']),
        'total_feedback_sessions': len(monitoring_data['feedback_sessions']),
        'total_cost': round(monitoring_data['total_cost'], 6),
        'cost_cap': monitoring_data['cost_cap'],
        'remaining_budget': round(monitoring_data['cost_cap'] - monitoring_data['total_cost'], 6),
        'recent_requests': monitoring_data['requests'][-10:],  # Last 10 requests
        'recent_feedback_sessions': monitoring_data['feedback_sessions'][-5:],  # Last 5 feedback sessions
        'average_latency': round(
            sum(req['latency'] for req in monitoring_data['requests']) / len(monitoring_data['requests'])
            if monitoring_data['requests'] else 0, 3
        ),
        'feedback_improvement_rate': round(
            (len(monitoring_data['feedback_sessions']) / len(monitoring_data['requests']) * 100) 
            if monitoring_data['requests'] else 0, 1
        )
    })


@app.route('/reset_monitoring', methods=['POST'])
def reset_monitoring():
    """Reset monitoring data (for testing/daily reset)"""
    monitoring_data['requests'] = []
    monitoring_data['feedback_sessions'] = []
    monitoring_data['total_cost'] = 0.0
    return jsonify({'message': 'Monitoring data reset successfully'})


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template
import sqlite3
import os
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd
import json
import time
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Monitoring data
monitoring_data = {
    'requests': [],
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

        return jsonify({'message': 'File processed successfully', 'filename': filename}), 200

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/')
def index():
    return render_template('index.html')

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
        
        # Log request for monitoring
        monitoring_data['requests'].append({
            'timestamp': datetime.now().isoformat(),
            'question': question,
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


@app.route('/monitoring', methods=['GET'])
def get_monitoring():
    """Get monitoring data including latency, cost, and request history"""
    return jsonify({
        'total_requests': len(monitoring_data['requests']),
        'total_cost': round(monitoring_data['total_cost'], 6),
        'cost_cap': monitoring_data['cost_cap'],
        'remaining_budget': round(monitoring_data['cost_cap'] - monitoring_data['total_cost'], 6),
        'recent_requests': monitoring_data['requests'][-10:],  # Last 10 requests
        'average_latency': round(
            sum(req['latency'] for req in monitoring_data['requests']) / len(monitoring_data['requests'])
            if monitoring_data['requests'] else 0, 3
        )
    })


@app.route('/reset_monitoring', methods=['POST'])
def reset_monitoring():
    """Reset monitoring data (for testing/daily reset)"""
    monitoring_data['requests'] = []
    monitoring_data['total_cost'] = 0.0
    return jsonify({'message': 'Monitoring data reset successfully'})


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)

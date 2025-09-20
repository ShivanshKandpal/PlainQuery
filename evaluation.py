import sqlite3
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
from app.app import get_db_schema
import time

load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_sql_for_question(question, schema):
    """Generates SQL for a given question and schema."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert SQL developer. Your task is to generate a precise SQL query to answer the user's question based on the provided database schema.

    Follow these rules:
    1. When asked to count items or join tables, only include results where a match exists. Use INNER JOIN by default. Use LEFT JOIN only when the user explicitly asks to include records with no matches (e.g., "including those with zero...").
    2. If the user's question is NOT a valid request for data (e.g., it's a greeting, a random statement, or doesn't make sense in a data context), return the single word "INVALID".

    ### Database Schema and Statistics:
    {schema}

    ### User Question:
    "{question}"

    ### Output (SQL Query or "INVALID"):
    """
    
    try:
        response = model.generate_content(prompt)
        output = response.text.strip().replace("```sql", "").replace("```", "").strip()
        return output
    except Exception as e:
        print(f"Error generating SQL: {e}")
        return None

def execute_query(db_path, query):
    """Executes a query and returns the results as a set of tuples for comparison."""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(query)
        results = c.fetchall()
        conn.close()
        # Convert to a set of tuples to make the result order-independent
        return set(results)
    except Exception as e:
        print(f"Error executing query '{query}': {e}")
        return None

def run_evaluation():
    """Runs the offline evaluation."""
    db_path = 'academic.db'
    dataset_path = 'evaluation_dataset.json'

    if not os.path.exists(db_path):
        print(f"Database '{db_path}' not found. Please generate it first.")
        return

    with open(dataset_path, 'r') as f:
        evaluation_data = json.load(f)

    schema = get_db_schema(db_path)
    correct_predictions = 0
    total_questions = len(evaluation_data)

    print("--- Starting Offline Evaluation ---")

    for i, item in enumerate(evaluation_data):
        question = item['question']
        gold_query = item['query']

        print(f"\\nProcessing Question {i+1}/{total_questions}: {question}")

        # Generate SQL from our model
        generated_query = generate_sql_for_question(question, schema)
        
        if not generated_query or generated_query.upper() == 'INVALID':
            print("  -> Model failed to generate a valid query.")
            continue

        print(f"  - Gold SQL:      {gold_query}")
        print(f"  - Generated SQL: {generated_query}")

        # Execute both queries and compare results
        gold_results = execute_query(db_path, gold_query)
        generated_results = execute_query(db_path, generated_query)

        if gold_results is not None and generated_results is not None and gold_results == generated_results:
            print("  -> \\033[92mCorrect\\033[0m (Results match)")
            correct_predictions += 1
        else:
            print("  -> \\033[91mIncorrect\\033[0m (Results do not match)")
            print(f"    - Gold Results:      {gold_results}")
            print(f"    - Generated Results: {generated_results}")
        
        # Add a delay to avoid hitting API rate limits
        if i < total_questions - 1:  # Don't sleep after the last question
            print("  -> Waiting 5 seconds to avoid rate limits...")
            time.sleep(5)

    accuracy = (correct_predictions / total_questions) * 100
    print(f"\\n--- Evaluation Complete ---")
    print(f"Execution Accuracy: {accuracy:.2f}% ({correct_predictions}/{total_questions})")

if __name__ == '__main__':
    run_evaluation()

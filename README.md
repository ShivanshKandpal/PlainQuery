# AI Copilot for Data Teams

This project is an AI-powered assistant that translates natural language questions into SQL queries. It's a web-based application that allows users to get data from a database without writing SQL.

## Architecture Sketch

```
+-----------------+      +-----------------+      +-----------------+
|   Frontend      |----->|   Flask Backend   |----->|   Gemini API    |
| (HTML/CSS/JS)   |      |   (app.py)        |      | (for NL-to-SQL) |
+-----------------+      +-----------------+      +-----------------+
       ^                      |
       |                      |
       |                      v
       +-----------------+
       |   SQLite DB     |
       | (database.db)   |
       +-----------------+
```

- **Frontend**: A simple web interface to input a question.
- **Flask Backend**: 
    - Serves the frontend.
    - Receives the user's question.
    - Gets the database schema.
    - Creates a prompt for the Gemini API.
    - Sends the prompt to the Gemini API.
    - Executes the generated SQL on the database.
    - Returns the SQL query and the result to the frontend.
- **Gemini API**: A Large Language Model that generates SQL from the natural language prompt.
- **SQLite DB**: A sample database to query against.

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up your Gemini API key:**
    - Open the `.env` file.
    - Replace `"YOUR_GEMINI_API_KEY"` with your actual Gemini API key.

3.  **Create the database:**
    ```bash
    python create_db.py
    ```

4.  **Run the Flask application:**
    ```bash
    python app/app.py
    ```

5.  Open your browser and go to `http://127.0.0.1:5000`.

## 1-Pager

### Problem
Data analysts and other team members often spend significant time writing boilerplate SQL queries to get insights from data. This process can be slow and requires specific technical knowledge, creating a bottleneck for data-driven decision-making.

### Solution
An AI-powered web application that allows users to ask questions in natural language and receive both the generated SQL query and the query's result from the database. This democratizes data access and speeds up the process of getting insights.

### User
- Data Analysts
- Product Managers
- Business Intelligence Professionals

### Context
The application is aware of the database schema (tables and columns), which allows it to generate accurate and relevant SQL queries.

### Metrics
- **Time saved**: Users can get data in seconds instead of minutes or hours.
- **% auto-resolved**: A high percentage of natural language questions can be successfully converted to SQL.
- **Exec-accuracy**: The generated SQL is syntactically correct and semantically answers the user's question.




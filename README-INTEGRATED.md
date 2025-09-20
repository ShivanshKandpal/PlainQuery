# PlainQuery - Integrated Frontend & Backend

An AI-powered SQL query generator with a modern React frontend and Flask backend.

## Architecture

```
Frontend (React/TypeScript)     Backend (Flask/Python)     AI (Gemini)
Port: 8080                     Port: 5000                  API: Google Gemini
┌─────────────────┐           ┌─────────────────┐         ┌─────────────────┐
│                 │           │                 │         │                 │
│  - Modern UI    │ ◄────────►│  - API Endpoints│ ◄──────►│  - Natural Lang │
│  - Real-time    │           │  - SQL Generation│         │  - SQL Conversion│
│  - Tailwind CSS │           │  - Database Ops │         │  - Smart Queries │
│                 │           │                 │         │                 │
└─────────────────┘           └─────────────────┘         └─────────────────┘
```

## Features

- 🎯 **Natural Language to SQL**: Ask questions in plain English
- 🎨 **Modern UI**: Built with React, TypeScript, and Tailwind CSS
- 🚀 **Real-time**: Instant query generation and execution
- 📊 **Data Visualization**: View results in formatted tables
- 🔒 **Security**: Read-only SQL queries for safety
- 📁 **File Upload**: Support for CSV data upload
- 🌐 **CORS Enabled**: Frontend-backend communication

## Setup & Running

### Prerequisites
- Python 3.12+
- Node.js 18+
- Gemini API Key

### 1. Backend Setup
```bash
# Navigate to project root
cd PlainQuery

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies (already done)
pip install -r requirements.txt

# Set your Gemini API key in .env
# GEMINI_API_KEY=your_actual_api_key_here

# Start Flask backend
python app/app.py
```
Backend runs at: http://localhost:5000

### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (already done)
npm install

# Start development server
npm run dev
```
Frontend runs at: http://localhost:8080

## API Endpoints

### Backend (Flask) - Port 5000
- `GET /` - Serve basic HTML (legacy)
- `GET /schema` - Get database schema information
- `POST /generate_sql` - Generate SQL from natural language
- `POST /upload_csv` - Upload CSV files

### Frontend (React) - Port 8080
- React development server with hot reload
- Modern component-based architecture
- Tailwind CSS for styling

## Usage

1. **Open the application**: http://localhost:8080
2. **Ask questions**: Type natural language queries like:
   - "Show me all customers"
   - "What are the total sales by region?"
   - "List products with price greater than 100"
3. **View results**: See the generated SQL and query results
4. **Upload data**: Drag and drop CSV files for analysis

## Project Structure

```
PlainQuery/
├── app/                    # Flask Backend
│   ├── app.py             # Main Flask application
│   ├── static/            # Static files (legacy)
│   └── templates/         # HTML templates (legacy)
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── lib/           # API utilities
│   │   └── hooks/         # Custom React hooks
│   ├── package.json       # Frontend dependencies
│   └── vite.config.ts     # Vite configuration
├── venv/                  # Python virtual environment
├── .env                   # Environment variables
├── database.db           # SQLite database
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Development

### Frontend Development
- Uses Vite for fast hot module replacement
- TypeScript for type safety
- Tailwind CSS for styling
- shadcn/ui components for modern UI

### Backend Development
- Flask with CORS enabled
- Gemini AI integration
- SQLite database support
- File upload capabilities

## Integration Details

The frontend and backend communicate via REST API:

1. **Query Flow**:
   - User enters question in frontend
   - Frontend sends POST to `/generate_sql`
   - Backend uses Gemini AI to generate SQL
   - Backend executes SQL on database
   - Results returned to frontend
   - Frontend displays results in table

2. **CORS Configuration**:
   - Flask-CORS enabled for all routes
   - Frontend can make requests to backend
   - Development servers on different ports

## Troubleshooting

### Common Issues

1. **API Key Invalid**: Check `.env` file has correct Gemini API key without quotes
2. **CORS Errors**: Ensure flask-cors is installed and enabled
3. **Port Conflicts**: Make sure ports 5000 and 8080 are available
4. **Dependencies**: Ensure all npm and pip packages are installed

### Logs
- Backend logs: Check Flask terminal output
- Frontend logs: Check browser developer console
- API errors: Network tab in browser dev tools

## Next Steps

- Add authentication
- Implement data visualization charts
- Add query history
- Support more database types
- Deploy to production
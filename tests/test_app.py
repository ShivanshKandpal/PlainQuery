import os
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock
import sys

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import app

class TestApp(unittest.TestCase):

    def setUp(self):
        """Set up a test client and other test variables."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Create a temporary directory for uploads
        self.upload_dir = tempfile.TemporaryDirectory()
        app.config['UPLOAD_FOLDER'] = self.upload_dir.name

        # Create a dummy CSV file for testing uploads
        self.csv_fd, self.csv_path = tempfile.mkstemp(suffix='.csv', dir=self.upload_dir.name)
        with os.fdopen(self.csv_fd, 'w') as f:
            f.write("id,name\n1,Alice\n2,Bob")

    def tearDown(self):
        """Clean up after each test."""
        self.upload_dir.cleanup()

    def test_upload_csv(self):
        """Test CSV file upload and processing."""
        with open(self.csv_path, 'rb') as f:
            data = {'file': (f, os.path.basename(self.csv_path))}
            response = self.app.post('/upload_csv', content_type='multipart/form-data', data=data)
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['message'], 'File processed successfully')
        
        # Check if the database and context files were created
        base_name = os.path.splitext(os.path.basename(self.csv_path))[0]
        db_path = os.path.join(self.upload_dir.name, f"{base_name}.db")
        context_path = os.path.join(self.upload_dir.name, f"{base_name}_context.json")
        self.assertTrue(os.path.exists(db_path))
        self.assertTrue(os.path.exists(context_path))

    @patch('app.app.genai.GenerativeModel')
    def test_generate_sql_valid(self, mock_generative_model):
        """Test SQL generation with a valid prompt."""
        # Mock the Gemini API response
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = "SELECT * FROM customers"
        mock_generative_model.return_value = mock_model_instance

        response = self.app.post('/generate_sql',
                                 data=json.dumps({'question': 'Show me all customers'}),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data['sql_query'], 'SELECT * FROM customers')

    @patch('app.app.genai.GenerativeModel')
    def test_generate_sql_invalid_prompt(self, mock_generative_model):
        """Test SQL generation with an invalid (nonsensical) prompt."""
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = "INVALID"
        mock_generative_model.return_value = mock_model_instance

        response = self.app.post('/generate_sql',
                                 data=json.dumps({'question': 'i am deaf'}),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.data)
        self.assertIn("I'm sorry", json_data['error'])

    @patch('app.app.genai.GenerativeModel')
    def test_generate_sql_malicious(self, mock_generative_model):
        """Test the enhanced safety check for malicious queries."""
        # Test 1: Non-SELECT statement
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = "DROP TABLE customers"
        mock_generative_model.return_value = mock_model_instance

        response = self.app.post('/generate_sql',
                                 data=json.dumps({'question': 'Delete the customers table'}),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 403)
        json_data = json.loads(response.data)
        self.assertIn('Security violation', json_data['error'])
        
        # Test 2: SELECT with dangerous keywords
        mock_model_instance.generate_content.return_value.text = "SELECT * FROM customers; DROP TABLE orders"
        
        response = self.app.post('/generate_sql',
                                 data=json.dumps({'question': 'Show customers and destroy orders'}),
                                 content_type='application/json')
        
        self.assertEqual(response.status_code, 403)
        json_data = json.loads(response.data)
        self.assertIn('Security violation', json_data['error'])
        self.assertIn('DROP', json_data['error'])

if __name__ == '__main__':
    unittest.main()

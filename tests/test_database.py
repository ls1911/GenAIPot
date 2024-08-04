import os
import sys
import pandas as pd
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src import database

class TestDatabase(unittest.TestCase):
    @patch('sqlite3.connect')
    def setUp(self, mock_connect):
        # Mock the database connection and cursor
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Mock the cursor methods to ensure they work as expected
        self.mock_cursor.execute.return_value = None
        self.mock_cursor.fetchall.return_value = []

        # Call the setup_database function to ensure the table is created
        database.conn = self.mock_conn
        database.c = self.mock_cursor
        database.setup_database()

    def test_setup_database(self):
        # Check that the correct SQL command was executed
        expected_call = '''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            timestamp TEXT,
            command TEXT,
            response TEXT
        )
        '''
        actual_call = self.mock_cursor.execute.call_args[0][0].strip()
        self.assertEqual(expected_call.strip(), actual_call)
        self.mock_conn.commit.assert_called_once()

    def test_log_interaction(self):
        # Define test data
        ip = '192.168.1.1'
        command = 'TEST COMMAND'
        response = 'TEST RESPONSE'
        test_time = datetime.now().isoformat()

        with patch('src.database.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime.fromisoformat(test_time)
            # Call the function to log the interaction
            database.log_interaction(ip, command, response)

        # Check that the correct SQL command was executed with the expected data
        expected_create_table_call = '''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            timestamp TEXT,
            command TEXT,
            response TEXT
        )
        '''.strip()

        expected_insert_call = 'INSERT INTO connections (ip, timestamp, command, response) VALUES (?, ?, ?, ?)'
        expected_insert_data = (ip, test_time, command, response)

        actual_create_table_call = self.mock_cursor.execute.call_args_list[0][0][0].strip()
        actual_insert_call = self.mock_cursor.execute.call_args_list[1][0][0]
        actual_insert_data = self.mock_cursor.execute.call_args_list[1][0][1]

        self.assertEqual(expected_create_table_call, actual_create_table_call)
        self.assertEqual(expected_insert_call, actual_insert_call)
        self.assertEqual(expected_insert_data, actual_insert_data)
        self.mock_conn.commit.assert_called()

    @patch('pandas.read_sql_query')
    def test_collect_honeypot_data(self, mock_read_sql):
        # Mock the pandas.read_sql_query function
        mock_df = MagicMock(spec=pd.DataFrame)
        mock_read_sql.return_value = mock_df

        # Call the function to collect data
        result = database.collect_honeypot_data()

        # Check that the correct SQL command was executed
        mock_read_sql.assert_called_once_with("SELECT * FROM connections", database.conn)

        # Check that the function returns the expected result
        self.assertEqual(result, mock_df)

if __name__ == '__main__':
    unittest.main()
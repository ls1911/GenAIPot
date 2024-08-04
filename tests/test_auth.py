import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.auth import hash_password, check_credentials

class TestAuth(unittest.TestCase):

    @patch('src.auth.config')
    def test_hash_password(self, mock_config):
        password = 'test_password'
        expected_hash = '10a6e6cc8311a3e2bcc09bf6c199adecd5dd59408c343e926b129c4914f3cb01'  # Correct hash of 'test_password'
        self.assertEqual(hash_password(password), expected_hash)

    @patch('src.auth.config')
    def test_check_credentials_success(self, mock_config):
        username = 'test_user'
        password = 'test_password'
        hashed_password = hash_password(password)

        mock_config.get.return_value = 'test_user'
        mock_config.get.side_effect = lambda section, option: {'username': 'test_user', 'password': hashed_password}.get(option)

        self.assertTrue(check_credentials(username, password))

    @patch('src.auth.config')
    def test_check_credentials_failure(self, mock_config):
        username = 'test_user'
        password = 'wrong_password'

        mock_config.get.return_value = 'test_user'
        mock_config.get.side_effect = lambda section, option: {'username': 'test_user', 'password': hash_password('test_password')}.get(option)

        self.assertFalse(check_credentials(username, password))

    @patch('src.auth.config')
    def test_check_credentials_logging(self, mock_config):
        username = 'test_user'
        password = 'test_password'
        hashed_password = hash_password(password)

        mock_config.get.return_value = 'test_user'
        mock_config.get.side_effect = lambda section, option: {'username': 'test_user', 'password': hashed_password, 'debug': 'true'}.get(option)

        with self.assertLogs('src.auth', level='DEBUG') as log:
            self.assertTrue(check_credentials(username, password))
            self.assertIn('DEBUG:src.auth:Checking credentials for user: test_user', log.output)
            self.assertIn(f'DEBUG:src.auth:Provided password (hashed): {hashed_password}', log.output)
            self.assertIn('DEBUG:src.auth:Stored username: test_user', log.output)
            self.assertIn(f'DEBUG:src.auth:Stored password (hashed): {hashed_password}', log.output)

if __name__ == '__main__':
    unittest.main()
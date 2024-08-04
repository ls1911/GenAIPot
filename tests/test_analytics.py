import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src import analytics

class TestAnalytics(unittest.TestCase):

    def setUp(self):
        # Sample data for testing
        self.df = pd.DataFrame({
            'timestamp': pd.date_range(start='2023-01-01', periods=5, freq='D'),
            'command': ['cmd1', 'cmd2', 'cmd3', 'cmd4', 'cmd5'],
            'ip': ['192.168.1.1', '192.168.1.2', '192.168.1.3', '192.168.1.1', '192.168.1.2']
        })

    @patch('src.analytics.Prophet')
    @patch('src.analytics.pd.DataFrame.to_csv')
    def test_perform_prediction(self, mock_to_csv, MockProphet):
        mock_model = MockProphet.return_value
        mock_model.fit.return_value = None
        mock_model.make_future_dataframe.return_value = pd.DataFrame({'ds': pd.date_range(start='2023-01-01', periods=35, freq='D')})
        mock_model.predict.return_value = pd.DataFrame({'ds': pd.date_range(start='2023-01-01', periods=35, freq='D'), 'yhat': [1] * 35})

        analytics.perform_prediction(self.df)

        mock_model.fit.assert_called_once()
        mock_model.make_future_dataframe.assert_called_once_with(periods=30, freq='S')
        mock_model.predict.assert_called_once()
        mock_to_csv.assert_called_once_with("future_forecast.csv", index=False)

    @patch('src.analytics.Prophet')
    @patch('src.analytics.pd.DataFrame.to_csv')
    def test_detect_anomalies(self, mock_to_csv, MockProphet):
        mock_model = MockProphet.return_value
        mock_model.fit.return_value = None
        mock_model.make_future_dataframe.return_value = pd.DataFrame({'ds': pd.date_range(start='2023-01-01', periods=35, freq='D')})
        mock_model.predict.return_value = pd.DataFrame({'ds': pd.date_range(start='2023-01-01', periods=35, freq='D'), 'yhat_upper': [1] * 35})

        analytics.detect_anomalies(self.df)

        self.assertEqual(mock_model.fit.call_count, 2)
        self.assertEqual(mock_model.make_future_dataframe.call_count, 2)
        self.assertEqual(mock_model.predict.call_count, 2)
        self.assertEqual(mock_to_csv.call_count, 4)

    @patch('src.analytics.plt.show')
    @patch('src.analytics.plt.savefig')
    def test_generate_graphs(self, mock_savefig, mock_show):
        # Modify the timestamp to include the last 24 hours for consistent results
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df.loc[self.df.shape[0] - 1, 'timestamp'] = pd.Timestamp.now()

        analytics.generate_graphs(self.df)

        self.assertEqual(mock_savefig.call_count, 2)
        self.assertEqual(mock_show.call_count, 2)

if __name__ == '__main__':
    unittest.main()
#!/usr/bin/env python3
"""
Test harness for marketdata.py module in the Crazy Stock Badges project.

This module contains unit tests for the MarketDataManager class, covering:
- Stock data fetching and caching
- Technical analysis
- Summary statistics
- Report generation
- Sentiment analysis methods
- Error handling

Usage:
    python test_marketdata.py

The tests use unittest framework and include mocking where appropriate to avoid
actual API calls during testing.
"""

import unittest
import os
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
from pathlib import Path

# Import the module to test
import marketdata
from marketdata import MarketDataManager

class TestMarketDataManager(unittest.TestCase):
    """Test cases for the MarketDataManager class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a test cache directory if it doesn't exist
        os.makedirs("./test_cache", exist_ok=True)
        
        # Store original cache dir and replace with test dir
        self.original_cache_dir = marketdata.CACHE_DIR
        marketdata.CACHE_DIR = Path("./test_cache")
        
        # Create a sample stock data DataFrame
        dates = pd.date_range(start='2024-01-01', periods=30)
        self.sample_data = pd.DataFrame({
            'Open': np.random.uniform(100, 200, 30),
            'High': np.random.uniform(110, 210, 30),
            'Low': np.random.uniform(90, 190, 30),
            'Close': np.random.uniform(100, 200, 30),
            'Volume': np.random.randint(1000000, 10000000, 30)
        }, index=dates)
        
        # Create a test instance with a mock API key
        self.mdm = MarketDataManager(ticker='AAPL', period='1y', api_key='test_api_key')
    
    def tearDown(self):
        """Clean up after each test method."""
        # Restore original cache dir
        marketdata.CACHE_DIR = self.original_cache_dir
        
        # Clean up test cache files
        for file in os.listdir("./test_cache"):
            os.remove(os.path.join("./test_cache", file))
        os.rmdir("./test_cache")
    
    def test_init(self):
        """Test initialization of MarketDataManager."""
        self.assertEqual(self.mdm.ticker, 'AAPL')
        self.assertEqual(self.mdm.period, '1y')
        self.assertEqual(self.mdm.api_key, 'test_api_key')
        self.assertIsNone(self.mdm.data)
        self.assertIsNone(self.mdm.report)
    
    @patch('yfinance.Ticker')
    def test_fetch_stock_data_success(self, mock_ticker):
        """Test successful stock data fetching."""
        # Configure the mock
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = {'regularMarketPrice': 150.0}
        mock_ticker_instance.history.return_value = self.sample_data
        mock_ticker.return_value = mock_ticker_instance
        
        # Call the method
        result = self.mdm.fetch_stock_data(ticker='TSLA', period='1mo', use_cache=False)
        
        # Assertions
        self.assertEqual(self.mdm.ticker, 'TSLA')
        self.assertEqual(self.mdm.period, '1mo')
        self.assertIs(result, self.mdm.data)
        self.assertEqual(len(result), 30)
        mock_ticker.assert_called_once_with('TSLA')
        mock_ticker_instance.history.assert_called_once_with(period='1mo')
    
    @patch('yfinance.Ticker')
    def test_fetch_stock_data_invalid_ticker(self, mock_ticker):
        """Test fetching data with invalid ticker."""
        # Configure the mock to simulate invalid ticker
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = {}  # Empty info indicates invalid ticker
        mock_ticker.return_value = mock_ticker_instance
        
        # Assert that ValueError is raised
        with self.assertRaises(ValueError):
            self.mdm.fetch_stock_data(ticker='INVALID', use_cache=False)
    
    @patch('yfinance.Ticker')
    def test_fetch_stock_data_empty_data(self, mock_ticker):
        """Test fetching data that returns empty DataFrame."""
        # Configure the mock to return empty DataFrame
        mock_ticker_instance = MagicMock()
        mock_ticker_instance.info = {'regularMarketPrice': 150.0}
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        
        # Assert that ValueError is raised
        with self.assertRaises(ValueError):
            self.mdm.fetch_stock_data(ticker='TSLA', use_cache=False)
    
    def test_fetch_stock_data_use_cache(self):
        """Test using cached data."""
        # Create a cache file
        cache_file = marketdata.CACHE_DIR / f"AAPL_1y_{datetime.now().strftime('%Y%m%d')}.csv"
        self.sample_data.to_csv(cache_file)
        
        # Call the method with use_cache=True
        result = self.mdm.fetch_stock_data(use_cache=True)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 30)
    
    def test_perform_technical_analysis(self):
        """Test technical analysis calculation."""
        # Set up data
        self.mdm.data = self.sample_data
        
        # Call the method
        result = self.mdm.perform_technical_analysis()
        
        # Assertions
        self.assertIn('SMA_20', result.columns)
        self.assertIn('SMA_50', result.columns)
        self.assertIn('EMA_20', result.columns)
        self.assertIn('RSI', result.columns)
        self.assertIn('MACD', result.columns)
        self.assertIn('MACD_Signal', result.columns)
        self.assertIn('MACD_Hist', result.columns)
        self.assertIn('BB_High', result.columns)
        self.assertIn('BB_Low', result.columns)
        self.assertIn('BB_Mid', result.columns)
        self.assertIn('ATR', result.columns)
    
    def test_perform_technical_analysis_no_data(self):
        """Test technical analysis with no data."""
        # Ensure data is None
        self.mdm.data = None
        
        # Assert that ValueError is raised
        with self.assertRaises(ValueError):
            self.mdm.perform_technical_analysis()
    
    def test_get_summary_stats(self):
        """Test getting summary statistics."""
        # Set up data with technical indicators
        self.mdm.data = self.sample_data
        self.mdm.perform_technical_analysis()
        
        # Call the method
        stats = self.mdm.get_summary_stats()
        
        # Assertions
        self.assertEqual(stats['ticker'], 'AAPL')
        self.assertIn('latest_price', stats)
        self.assertIn('high', stats)
        self.assertIn('low', stats)
        self.assertIn('price_change_pct', stats)
        self.assertIn('volatility_pct', stats)
        self.assertIn('macd', stats)
        self.assertIn('rsi', stats)
        self.assertIn('data_start', stats)
        self.assertIn('data_end', stats)
    
    def test_get_summary_stats_no_data(self):
        """Test getting summary stats with no data."""
        # Ensure data is None
        self.mdm.data = None
        
        # Assert that ValueError is raised
        with self.assertRaises(ValueError):
            self.mdm.get_summary_stats()
    
    @patch('requests.post')
    def test_generate_report(self, mock_post):
        """Test report generation."""
        # Set up data
        self.mdm.data = self.sample_data
        self.mdm.perform_technical_analysis()
        
        # Configure the mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'This is a test report for AAPL.'}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        # Call the method
        report = self.mdm.generate_report()
        
        # Assertions
        self.assertEqual(report, 'This is a test report for AAPL.')
        self.assertEqual(self.mdm.report, 'This is a test report for AAPL.')
        mock_post.assert_called_once()
        
        # Check that the report was saved to file
        self.assertTrue(os.path.exists("./stock_report"))
        with open("./stock_report", "r") as f:
            saved_report = f.read()
        self.assertEqual(saved_report, 'This is a test report for AAPL.')
        
        # Clean up
        os.remove("./stock_report")
    
    def test_generate_report_no_data(self):
        """Test report generation with no data."""
        # Ensure data is None
        self.mdm.data = None
        
        # Assert that ValueError is raised
        with self.assertRaises(ValueError):
            self.mdm.generate_report()
    
    def test_get_sentiment(self):
        """Test getting sentiment data."""
        # Create a test sentiment file
        sentiment_data = {
            'overall_sentiment': {
                'valence': 0.7,
                'arousal': 0.6,
                'dominance': 0.8,
                'confidence': 0.9,
                'financial_sentiment': 0.5
            }
        }
        os.makedirs("./cache", exist_ok=True)
        with open("./cache/sentiment_analysis.json", "w") as f:
            json.dump(sentiment_data, f)
        
        # Call the method
        sentiment = self.mdm.get_sentiment()
        
        # Assertions
        self.assertEqual(sentiment['valence'], 0.7)
        self.assertEqual(sentiment['arousal'], 0.6)
        self.assertEqual(sentiment['dominance'], 0.8)
        self.assertEqual(sentiment['confidence'], 0.9)
        self.assertEqual(sentiment['financial_sentiment'], 0.5)
        
        # Clean up
        os.remove("./cache/sentiment_analysis.json")
    
    def test_get_sentiment_no_file(self):
        """Test getting sentiment with no file."""
        # Ensure the file doesn't exist
        if os.path.exists("./cache/sentiment_analysis.json"):
            os.remove("./cache/sentiment_analysis.json")
        
        # Call the method
        sentiment = self.mdm.get_sentiment()
        
        # Assertions - should return default values
        self.assertEqual(sentiment['valence'], 0.5)
        self.assertEqual(sentiment['arousal'], 0.5)
        self.assertEqual(sentiment['dominance'], 0.5)
        self.assertEqual(sentiment['confidence'], 0.5)
        self.assertEqual(sentiment['financial_sentiment'], 0.0)
    
    def test_get_one_word_analysis(self):
        """Test getting one-word analysis."""
        # Create a test sentiment file
        sentiment_data = {
            'one_word_summary': 'BULLISH',
            'overall_sentiment': {
                'valence': 0.7,
                'arousal': 0.6,
                'dominance': 0.8
            }
        }
        os.makedirs("./cache", exist_ok=True)
        with open("./cache/sentiment_analysis.json", "w") as f:
            json.dump(sentiment_data, f)
        
        # Call the method with sentiment data
        sentiment = {'valence': 0.7, 'arousal': 0.6, 'dominance': 0.8}
        result = self.mdm.get_one_word_analysis(sentiment)
        
        # Assertions
        self.assertEqual(result, 'BULLISH')
        
        # Clean up
        os.remove("./cache/sentiment_analysis.json")
    
    def test_get_one_word_analysis_no_file(self):
        """Test getting one-word analysis with no file."""
        # Ensure the file doesn't exist
        if os.path.exists("./cache/sentiment_analysis.json"):
            os.remove("./cache/sentiment_analysis.json")
        
        # Call the method with different sentiment combinations
        high_valence = {'valence': 0.8, 'arousal': 0.8, 'dominance': 0.8}
        result_high = self.mdm.get_one_word_analysis(high_valence)
        
        low_valence = {'valence': 0.2, 'arousal': 0.2, 'dominance': 0.2}
        result_low = self.mdm.get_one_word_analysis(low_valence)
        
        neutral = {'valence': 0.5, 'arousal': 0.5, 'dominance': 0.5}
        result_neutral = self.mdm.get_one_word_analysis(neutral)
        
        # Assertions - should calculate based on VAD values
        self.assertIn(result_high, ['EXCITED', 'CONFIDENT'])
        self.assertIn(result_low, ['SAD', 'DISAPPOINTED'])
        self.assertEqual(result_neutral, 'NEUTRAL')
    
    def test_get_buy_sell_hold(self):
        """Test getting buy/sell/hold recommendation."""
        # Set up data with technical indicators
        self.mdm.data = self.sample_data
        self.mdm.perform_technical_analysis()
        
        # Test with different sentiment combinations
        bullish = {'financial_sentiment': 0.5, 'valence': 0.8}
        bearish = {'financial_sentiment': -0.5, 'valence': 0.2}
        neutral = {'financial_sentiment': 0.0, 'valence': 0.5}
        
        # Call the methods
        result_bullish = self.mdm.get_buy_sell_hold(bullish)
        result_bearish = self.mdm.get_buy_sell_hold(bearish)
        result_neutral = self.mdm.get_buy_sell_hold(neutral)
        
        # Assertions
        # Note: Exact results depend on the random data, but we can check they're valid
        self.assertIn(result_bullish, ['BUY', 'HOLD', 'SELL'])
        self.assertIn(result_bearish, ['BUY', 'HOLD', 'SELL'])
        self.assertIn(result_neutral, ['BUY', 'HOLD', 'SELL'])
    
    def test_get_buy_sell_hold_no_data(self):
        """Test getting buy/sell/hold with no data."""
        # Ensure data is None
        self.mdm.data = None
        
        # Call the method
        result = self.mdm.get_buy_sell_hold({})
        
        # Should return default HOLD
        self.assertEqual(result, 'HOLD')
    
    def test_get_latest_macd(self):
        """Test getting latest MACD."""
        # Set up data with technical indicators
        self.mdm.data = self.sample_data
        self.mdm.perform_technical_analysis()
        
        # Call the method
        result = self.mdm.get_latest_macd()
        
        # Assertions
        self.assertTrue(result.startswith('MACD:'))
    
    def test_get_latest_macd_no_data(self):
        """Test getting latest MACD with no data."""
        # Ensure data is None
        self.mdm.data = None
        
        # Call the method
        result = self.mdm.get_latest_macd()
        
        # Should return default message
        self.assertEqual(result, 'MACD: N/A')
    
    def test_get_high(self):
        """Test getting high price."""
        # Set up data
        self.mdm.data = self.sample_data
        
        # Call the method
        result = self.mdm.get_high()
        
        # Assertions
        self.assertTrue(result.startswith('Hi:'))
    
    def test_get_high_no_data(self):
        """Test getting high price with no data."""
        # Ensure data is None
        self.mdm.data = None
        
        # Call the method
        result = self.mdm.get_high()
        
        # Should return default message
        self.assertEqual(result, 'H/L: N/A')
    
    def test_get_low(self):
        """Test getting low price."""
        # Set up data
        self.mdm.data = self.sample_data
        
        # Call the method
        result = self.mdm.get_low()
        
        # Assertions
        self.assertTrue(result.startswith('Lo:'))
    
    def test_get_low_no_data(self):
        """Test getting low price with no data."""
        # Ensure data is None
        self.mdm.data = None
        
        # Call the method
        result = self.mdm.get_low()
        
        # Should return default message
        self.assertEqual(result, 'H/L: N/A')
    
    def test_get_market_outlook(self):
        """Test getting market outlook."""
        # Create a test sentiment file
        sentiment_data = {
            'emotional_summary': {
                'market_outlook': 'bullish'
            }
        }
        os.makedirs("./cache", exist_ok=True)
        with open("./cache/sentiment_analysis.json", "w") as f:
            json.dump(sentiment_data, f)
        
        # Set up data
        self.mdm.data = self.sample_data
        
        # Call the method
        result = self.mdm.get_market_outlook({})
        
        # Assertions
        self.assertEqual(result, 'bullish')
        
        # Clean up
        os.remove("./cache/sentiment_analysis.json")
    
    def test_get_market_outlook_no_file(self):
        """Test getting market outlook with no file."""
        # Ensure the file doesn't exist
        if os.path.exists("./cache/sentiment_analysis.json"):
            os.remove("./cache/sentiment_analysis.json")
        
        # Set up data
        self.mdm.data = self.sample_data
        
        # Call the method
        result = self.mdm.get_market_outlook({})
        
        # Should return default neutral
        self.assertEqual(result, 'neutral')
    
    def test_get_market_outlook_no_data(self):
        """Test getting market outlook with no data."""
        # Ensure data is None
        self.mdm.data = None
        
        # Call the method
        result = self.mdm.get_market_outlook({})
        
        # Should return default message
        self.assertEqual(result, 'Uncertain')


if __name__ == '__main__':
    unittest.main()

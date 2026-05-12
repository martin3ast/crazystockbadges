#!/usr/bin/env python3
"""
Market Data Module for Crazy Stock Badges Project

This module handles fetching stock data, performing technical analysis,
and generating stock reports using the OpenRouter API and GPT.

The prompt which generates the report is embedded here. 

Data structures for the finance data are held in pandas DataFrames.

The closing daily prices are used to calculate the following technical indicators:
- Moving Averages (SMA, EMA)   
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- ATR (Average True Range)
- Sentiment Analysis

Using this data it is also possible to plot 2-D graphs, this was tried, but later removed to focus on the 3-D models.

The sentiment analysis is done using the SentimentAnalyzer class, which uses the OpenRouter API to get sentiment data.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for market data fetching and analysis - Apr 13, 2025.
Version 1.1 - Martin East - Revew and tidy code, reduce complexity, remove graphing - Apr 14, 2025.
"""

import os
import re
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
import requests
import json
import time
from datetime import datetime
import logging
from pathlib import Path
import sys
from sentiment_analyser import SentimentAnalyzer
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get logger
logger = logging.getLogger('market_data')

# Cache directory for storing fetched data
CACHE_DIR = Path(os.getenv('CACHE_DIR', './cache'))
CACHE_DIR.mkdir(exist_ok=True) 

# Configuration from environment variables
DEFAULT_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = os.getenv('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions')


class MarketDataManager:
    """
    Manages fetching, analyzing, and reporting on stock market data.
    
    Version 1.0 - Cline implementation for Martin East - Implements data fetching, technical analysis, and report generation - Apr 13, 2025.
    """
    
    def __init__(self, ticker='AAPL', period='1y', api_key=None):
        """
        Initialize the MarketDataManager, use defaults if none given.
        
        Args:
            ticker (str): Stock ticker symbol (default: 'AAPL')
            period (str): Time period for data (default: '1y')
            api_key (str, optional): OpenRouter API key. If None, will try to get from
                                    environment variable or use default.
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY', DEFAULT_API_KEY)
        self.data = None
        self.ticker = ticker
        self.period = period
        self.report = None
    
    @staticmethod
    def validate_ticker(ticker):
        """
        Validate if a stock ticker symbol exists using yfinance.
        
        Args:
            ticker (str): Stock ticker symbol to validate
            
        Returns:
            dict: {'valid': bool, 'name': str or None, 'error': str or None}
        """
        if not ticker or not isinstance(ticker, str):
            return {'valid': False, 'name': None, 'error': 'Ticker must be a non-empty string'}
        
        # Clean ticker: remove whitespace and convert to uppercase
        ticker = ticker.strip().upper()
        
        # Length and character validation
        if len(ticker) == 0 or len(ticker) > 15:
            return {'valid': False, 'name': None, 'error': 'Ticker must be 1-15 characters long'}

        # Only allow alphanumeric, dots, and hyphens (covers tickers like BRK.B, BF-B)
        if not re.match(r'^[A-Z0-9.\-]+$', ticker):
            return {'valid': False, 'name': None, 'error': 'Ticker contains invalid characters'}
        
        try:
            # Try to get ticker info from yfinance
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if we got valid stock info
            if not info or len(info) < 3:  # yfinance returns minimal dict for invalid tickers
                return {'valid': False, 'name': None, 'error': f'Ticker "{ticker}" not found'}
            
            # Additional validation - check for common indicators of valid stock data
            has_price = any(key in info for key in ['regularMarketPrice', 'previousClose', 'currentPrice'])
            has_name = 'longName' in info or 'shortName' in info
            
            if not (has_price or has_name):
                return {'valid': False, 'name': None, 'error': f'Ticker "{ticker}" appears to be invalid or delisted'}
            
            # Get company name if available
            company_name = info.get('longName') or info.get('shortName') or ticker
            
            return {'valid': True, 'name': company_name, 'error': None}
            
        except Exception as e:
            logger.warning(f"Error validating ticker {ticker}: {e}")
            return {'valid': False, 'name': None, 'error': f'Unable to validate ticker "{ticker}": {str(e)}'}
    
    def fetch_stock_data(self, ticker=None, period=None, use_cache=True):
        """
        Fetch historical stock data for the given ticker.
        Cache results by default.
        
        Args:
            ticker (str): Stock ticker symbol (e.g., 'AAPL', 'TSLA')
            period (str): Time period for data (e.g., '1d', '1mo', '1y')
            use_cache (bool): Whether to use cached data if available
            
        Returns:
            pandas.DataFrame: Historical stock data
            
        Raises:
            ValueError: If ticker is invalid or no data is returned
        """
        # Set ticker if given, else use ones from class initialisation.
        if ticker is None:
            ticker = self.ticker
        else:
            self.ticker = ticker

        if period is None:
            period = self.period
        else:
            self.period = period

        # Check cache first if enabled
        cache_file = CACHE_DIR / f"{ticker}_{period}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if use_cache and cache_file.exists():
            logger.info(f"Loading cached data for {ticker} ({period})")
            try:
                self.data = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                # Verify the cached data is not empty
                if self.data.empty:
                    logger.warning(f"Cached data for {ticker} is empty, fetching fresh data")
                else:
                    return self.data
            except Exception as e:
                logger.warning(f"Error loading cached data: {e}")
                # Fall through to fetching fresh data
        
        # Fetch fresh data
        logger.info(f"Fetching data for {ticker} ({period})")
        try:
            stock = yf.Ticker(ticker)
            
            # Check if the ticker exists by trying to get info
            try:
                info = stock.info
                if not info or 'regularMarketPrice' not in info:
                    logger.error(f"Invalid ticker symbol: {ticker}")
                    raise ValueError(f"Invalid ticker symbol: {ticker}. The stock ticker does not exist or has no data.")
            except Exception as e:
                logger.error(f"Error retrieving ticker info: {e}")
                raise ValueError(f"Invalid ticker symbol: {ticker}. The stock ticker does not exist or has no data.")
            
            # Fetch historical data
            self.data = stock.history(period=period)
            
            # Check if data is empty
            if self.data.empty:
                logger.error(f"No data returned for ticker: {ticker}")
                raise ValueError(f"No data available for {ticker} in the specified period ({period}).")
            
            # Cache the data
            if use_cache:
                self.data.to_csv(cache_file)
                
            return self.data
        except ValueError as e:
            # Re-raise ValueError for invalid tickers
            logger.error(f"Error with ticker {ticker}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching stock data: {e}")
            raise RuntimeError(f"Failed to fetch data for {ticker}: {str(e)}")
    
    def perform_technical_analysis(self):
        """
        Calculate technical indicators and add them to the DataFrame.
        This includes moving average, RSI (Relative Strength Index), 
        MACD(Moving Average Convergence Divergence), and Bollinger Bands.
        Also calculates ATR (Average True Range) for volatility.

        These are used for creating the 3-D Models.

        Args:
            None
        Raises:
            ValueError: If no data is available
            RuntimeError: If technical analysis fails 

        Returns:
            pandas.DataFrame: Data with technical indicators
        """
        if self.data is None:
            raise ValueError("No data available. Call fetch_stock_data first.")
        
        logger.info("Performing technical analysis")
        
        try:
            # Moving Averages
            logger.info("Calculating moving averages...")
            self.data['SMA_20'] = ta.trend.sma_indicator(self.data['Close'], window=20)
            self.data['SMA_50'] = ta.trend.sma_indicator(self.data['Close'], window=50)
            self.data['EMA_20'] = ta.trend.ema_indicator(self.data['Close'], window=20)
            
            # RSI
            logger.info("Calculating RSI...")
            self.data['RSI'] = ta.momentum.rsi(self.data['Close'], window=14)
            
            # MACD
            logger.info("Calculating MACD...")
            self.data['MACD'] = ta.trend.macd(self.data['Close'])
            self.data['MACD_Signal'] = ta.trend.macd_signal(self.data['Close'])
            self.data['MACD_Hist'] = ta.trend.macd_diff(self.data['Close'])
            
            logger.info(f"Technical analysis completed. DataFrame columns: {list(self.data.columns)}")
            
            # Bollinger Bands
            self.data['BB_High'] = ta.volatility.bollinger_hband(self.data['Close'])
            self.data['BB_Low'] = ta.volatility.bollinger_lband(self.data['Close'])
            self.data['BB_Mid'] = ta.volatility.bollinger_mavg(self.data['Close'])
            
            # ATR - Average True Range (volatility indicator)
            self.data['ATR'] = ta.volatility.average_true_range(
                self.data['High'], self.data['Low'], self.data['Close']
            )
            return self.data
        except Exception as e:
            logger.error(f"Error performing technical analysis: {e}")
            raise RuntimeError(f"Failed to perform technical analysis: {str(e)}")
    
    def get_summary_stats(self):
        """
        Get comprehensive summary statistics and technical analysis for the stock data.
        
        Returns:
            dict: Comprehensive technical analysis and market statistics
        """
        if self.data is None:
            raise ValueError("No data available. Call fetch_stock_data first.")
        
        # Get the most recent data point
        latest = self.data.iloc[-1]
        
        # Basic price data
        latest_close = latest['Close']
        high = self.data['High'].max()
        low = self.data['Low'].min()
        
        # Calculate price change
        first_close = self.data['Close'].iloc[0]
        price_change = ((latest_close - first_close) / first_close) * 100
        
        # Calculate volatility (standard deviation of returns)
        returns = self.data['Close'].pct_change().dropna()
        volatility = returns.std() * 100
        
        # Technical indicators
        latest_rsi = latest.get('RSI', None)
        latest_macd = latest.get('MACD', None)
        latest_macd_signal = latest.get('MACD_Signal', None)
        latest_macd_hist = latest.get('MACD_Hist', None)
        
        # Moving averages
        latest_sma_20 = latest.get('SMA_20', None)
        latest_sma_50 = latest.get('SMA_50', None)
        latest_ema_20 = latest.get('EMA_20', None)
        
        # Bollinger Bands
        latest_bb_high = latest.get('BB_High', None)
        latest_bb_low = latest.get('BB_Low', None)
        latest_bb_mid = latest.get('BB_Mid', None)
        
        # ATR (Average True Range)
        latest_atr = latest.get('ATR', None)
        
        # Calculate additional metrics
        volume_avg = self.data['Volume'].mean() if 'Volume' in self.data.columns else None
        latest_volume = latest.get('Volume', None)
        
        # Price position relative to range
        price_position = ((latest_close - low) / (high - low)) * 100 if high != low else 50
        
        # RSI signal
        rsi_signal = "Neutral"
        if latest_rsi is not None:
            if latest_rsi > 70:
                rsi_signal = "Overbought"
            elif latest_rsi < 30:
                rsi_signal = "Oversold"
            elif latest_rsi > 60:
                rsi_signal = "Bullish"
            elif latest_rsi < 40:
                rsi_signal = "Bearish"
        
        # MACD signal
        macd_signal = "Neutral"
        if latest_macd is not None and latest_macd_signal is not None:
            if latest_macd > latest_macd_signal:
                macd_signal = "Bullish"
            else:
                macd_signal = "Bearish"
        
        # Moving average trend
        ma_trend = "Neutral"
        if latest_sma_20 is not None and latest_sma_50 is not None:
            if latest_sma_20 > latest_sma_50:
                ma_trend = "Bullish" if latest_close > latest_sma_20 else "Mixed"
            else:
                ma_trend = "Bearish" if latest_close < latest_sma_20 else "Mixed"
        
        # Overall trend based on price vs moving averages
        overall_trend = "Neutral"
        if latest_sma_20 is not None:
            if latest_close > latest_sma_20:
                overall_trend = "Bullish"
            else:
                overall_trend = "Bearish"
        
        # Support and resistance levels (simplified)
        recent_data = self.data.tail(20)  # Last 20 days
        support_level = recent_data['Low'].min()
        resistance_level = recent_data['High'].max()
        
        return {
            # Basic info
            'ticker': self.ticker,
            'data_start': str(self.data.index[0])[:10],
            'data_end': str(self.data.index[-1])[:10],
            
            # Price action
            'latest_price': latest_close,
            'high': high,
            'low': low,
            'price_change_pct': price_change,
            'price_position': price_position,
            'volatility_pct': volatility,
            'support_level': support_level,
            'resistance_level': resistance_level,
            
            # Volume
            'latest_volume': latest_volume,
            'volume_avg': volume_avg,
            
            # Technical indicators - raw values
            'rsi': latest_rsi,
            'macd': latest_macd,
            'macd_signal_line': latest_macd_signal,
            'macd_histogram': latest_macd_hist,
            'sma_20': latest_sma_20,
            'sma_50': latest_sma_50,
            'ema_20': latest_ema_20,
            'bb_upper': latest_bb_high,
            'bb_lower': latest_bb_low,
            'bb_middle': latest_bb_mid,
            'atr': latest_atr,
            
            # Signals and analysis
            'rsi_signal': rsi_signal,
            'macd_signal': macd_signal,
            'ma_trend': ma_trend,
            'overall_trend': overall_trend,
            
            # Trading levels
            'price_vs_sma20': ((latest_close / latest_sma_20 - 1) * 100) if latest_sma_20 else None,
            'price_vs_sma50': ((latest_close / latest_sma_50 - 1) * 100) if latest_sma_50 else None,
            'bb_position': None if not all([latest_bb_high, latest_bb_low]) else 
                          ((latest_close - latest_bb_low) / (latest_bb_high - latest_bb_low)) * 100
        }
      
    def generate_report(self, prompt_template=None, output_file=None):
        """
        Generate a stock report using OpenRouter.ai API and GPT model.
        
        Args:
            prompt_template (str, optional): Custom prompt template
            output_file (str, optional): Path to save report file. Defaults to "./stock_report"
            
        Returns:
            str: Generated report text
        """
        if self.data is None:
            raise ValueError("No data available. Call fetch_stock_data first.")
        
        logger.info(f"Generating report for {self.ticker}")
        
        # Get summary stats for the report
        stats = self.get_summary_stats()
        
        # Default prompt template
        if prompt_template is None:
            prompt_template = (
                "You are an investor personality and presenter. Your name is Crazy Badge, which is what you introduce yourself with excitably!"
                "You are knowledgeable about pricing,"
                "trends, and the market. Give an insightful report for {ticker} as if you "
                "really care about this company's past, present and future. Include some nugget of interesting information about the company."
                "Also include the current price is ${latest_price:.2f}."
                "The 52-week high is ${high:.2f} and the low is ${low:.2f}. "
                "The price has changed by {price_change_pct:.2f}% over the period. "
                "The latest MACD value is {macd} and RSI is {rsi}. "
                "Make it short, 300 words."
            )
        
        # Format the prompt with the stats
        prompt = prompt_template.format(**stats)
        
        # Set up the API request
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        
        json_data = {
            'model': 'openai/gpt-4.1-mini',
            'messages': [
                {'role': 'system', 'content': 'You are a financial news TV anchor.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 1000,
        }
        
        # Make the API request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    OPENROUTER_API_URL, 
                    headers=headers, 
                    json=json_data,
                    timeout=30
                )
                response.raise_for_status()
                
                # Extract the report text
                self.report = response.json()['choices'][0]['message']['content'].strip()
                
                # Save the report to a file
                report_file = output_file or "./stock_report"
                with open(report_file, "w") as f:
                    f.write(self.report)
                
                logger.info("Report generated and saved")
                return self.report
            
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Failed to generate report after multiple attempts")
                    raise RuntimeError(f"Failed to generate report: {str(e)}")
            
            except Exception as e:
                logger.error(f"Error generating report: {e}")
                raise RuntimeError(f"Failed to generate report: {str(e)}")
    
    def get_sentiment(self):
        """
        Get sentiment analysis data from sentiment_analysis.json file in the cache directory.
        
        Returns:
            dict: Sentiment analysis data or default values if file not found
        """
        # Look for sentiment analysis file in cache directory
        sentiment_file = Path("./cache/sentiment_analysis.json")
        
        try:
            with open(sentiment_file, "r") as f:
                sentiment_data = json.load(f)
                return sentiment_data.get('overall_sentiment', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading sentiment data: {e}")
            # Return default sentiment values
            return {
                'valence': 0.5,
                'arousal': 0.5,
                'dominance': 0.5,
                'confidence': 0.5,
                'financial_sentiment': 0.0
            }
    
    def get_one_word_analysis(self, sentiment):
        """
        Get a one-word summary of the sentiment analysis.
        
        Args:
            sentiment (dict): Sentiment data from get_sentiment()
            
        Returns:
            str: One-word summary of sentiment
        """
        # Look for sentiment analysis file in cache directory
        sentiment_file = Path("./cache/sentiment_analysis.json")
        
        try:
            with open(sentiment_file, "r") as f:
                sentiment_data = json.load(f)
                return sentiment_data.get('one_word_summary', 'NEUTRAL')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading sentiment data for one-word analysis: {e}")
            
            # Determine sentiment based on valence, arousal, and dominance
            valence = sentiment.get('valence', 0.5)
            arousal = sentiment.get('arousal', 0.5)
            dominance = sentiment.get('dominance', 0.5)
            
            # Simple mapping of sentiment values to emotions
            if valence > 0.67:
                if arousal > 0.67:
                    return "EXCITED" if dominance > 0.5 else "HAPPY"
                else:
                    return "CONFIDENT" if dominance > 0.5 else "CONTENT"
            elif valence < 0.33:
                if arousal > 0.67:
                    return "ANGRY" if dominance > 0.5 else "FEARFUL"
                else:
                    return "DISAPPOINTED" if dominance > 0.5 else "SAD"
            else:
                return "NEUTRAL"
    
    def get_buy_sell_hold(self, sentiment):
        """
        Get a buy/sell/hold recommendation based on sentiment and technical indicators.
        
        Args:
            sentiment (dict): Sentiment data from get_sentiment()
            
        Returns:
            str: Buy, Sell, or Hold recommendation
        """
        if self.data is None:
            return "HOLD"
        
        # Get latest technical indicators
        latest = self.data.iloc[-1]
        rsi = latest.get('RSI', 50)
        macd = latest.get('MACD', 0)
        macd_signal = latest.get('MACD_Signal', 0)
        
        # Get sentiment values
        financial_sentiment = sentiment.get('financial_sentiment', 0)
        valence = sentiment.get('valence', 0.5)
        
        # Combine technical and sentiment signals
        technical_signal = 0
        
        # RSI signals (oversold/overbought)
        if rsi < 30:
            technical_signal += 1  # Oversold, bullish
        elif rsi > 70:
            technical_signal -= 1  # Overbought, bearish
            
        # MACD signals (crossovers)
        if macd > macd_signal:
            technical_signal += 1  # Bullish
        elif macd < macd_signal:
            technical_signal -= 1  # Bearish
            
        # Combine with sentiment
        sentiment_signal = 0
        if financial_sentiment > 0.1:
            sentiment_signal += 1
        elif financial_sentiment < -0.1:
            sentiment_signal -= 1
            
        if valence > 0.67:
            sentiment_signal += 1
        elif valence < 0.33:
            sentiment_signal -= 1
            
        # Final recommendation
        combined_signal = technical_signal + sentiment_signal
        
        if combined_signal >= 2:
            return "BUY"
        elif combined_signal <= -2:
            return "SELL"
        else:
            return "HOLD"
    
    def get_latest_macd(self):
        """
        Get the latest MACD value as a formatted string.
        
        Returns:
            str: Formatted MACD value
        """
        if self.data is None:
            return "MACD: N/A"
        
        latest = self.data.iloc[-1]
        macd = latest.get('MACD', None)
        
        if macd is None:
            return "MACD: N/A"
        
        return f"MACD: {macd:.2f}"
    
    def get_high(self):
        """
        Get the high/low price information as a formatted string.
        
        Returns:
            str: Formatted high/low price information
        """
        if self.data is None:
            return "H/L: N/A"
        
        high = self.data['High'].max()
        
        return f"Hi: {high:.2f}"

    def get_low(self):
        """
        Get the high/low price information as a formatted string.
        
        Returns:
            str: Formatted high/low price information
        """
        if self.data is None:
            return "H/L: N/A"
        
        low = self.data['Low'].min()
        
        return f"Lo: {low:.2f}"
        
    def get_market_outlook(self, sentiment=None):
        """
        Get the market outlook as a formatted string based on sentiment analysis.
        Reads directly from sentiment_analysis.json file in the cache directory.
        
        Args:
            sentiment (dict, optional): Sentiment data from get_sentiment()
            
        Returns:
            str: Formatted market outlook information
        """
        if self.data is None:
            return "Uncertain"
        
        # Look for sentiment analysis file in cache directory
        sentiment_file = Path("./cache/sentiment_analysis.json")
        
        try:
            # Read directly from the sentiment analysis JSON file
            with open(sentiment_file, "r") as f:
                sentiment_data = json.load(f)
                # Get the market outlook from the emotional_summary section
                market_outlook = sentiment_data.get('emotional_summary', {}).get('market_outlook', 'neutral')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading sentiment data for market outlook: {e}")
            market_outlook = "neutral"
        
        return f"{market_outlook}"


def main():
    """
    Main function for testing the module.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch and analyze stock data')
    parser.add_argument('--ticker', type=str, default='TSLA', help='Stock ticker symbol')
    parser.add_argument('--period', type=str, default='1y', help='Time period for data')
    parser.add_argument('--no-cache', action='store_true', help='Disable data caching')
    parser.add_argument('--show-plot', action='store_true', help='Display the plot')
    args = parser.parse_args()
    
    try:
        # Create a market data manager
        mdm = MarketDataManager()
        
        # Fetch and analyze data
        mdm.fetch_stock_data(args.ticker, args.period, use_cache=not args.no_cache)
        mdm.perform_technical_analysis()
        
        # Get and print summary stats
        stats = mdm.get_summary_stats()
        print("\nSummary Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Generate and print report
        report = mdm.generate_report()
        print("\nGenerated Report:")
        print(report)
        
        # Get sentiment analysis
        sentiment = mdm.get_sentiment()
        one_word = mdm.get_one_word_analysis(sentiment)
        recommendation = mdm.get_buy_sell_hold(sentiment)
        market_outlook = mdm.get_market_outlook(sentiment)

        print(f"\nSentiment Analysis:")
        print(f"  One-word summary: {one_word}")
        print(f"  Recommendation: {recommendation}")
        print(f"  {mdm.get_latest_macd()}")
        print(f"  {mdm.get_high()}")
        print(f"  {mdm.get_low()}")
        print(f"  {market_outlook}")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

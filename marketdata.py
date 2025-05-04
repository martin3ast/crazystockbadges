#!/usr/bin/env python3
"""
Market Data Module for Crazy Stock Badges Project

This module handles fetching stock data, performing technical analysis,
and generating stock reports using the OpenRouter API ang GPT3.5.

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

# Get logger
logger = logging.getLogger('market_data')

# Cache directory for storing fetched data
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True) 

# **Fix this before pushing to GitHUB**
# Default OpenRouter API key - should be overridden with environment variable
DEFAULT_API_KEY = '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'
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class MarketDataManager:
    """
    Manages fetching, analyzing, and reporting on stock market data.
    
    Version 1.0 - Cline implementation for Martin East - Implements data fetching, technical analysis, and report generation - Apr 13, 2025.
    Version 1.1 - Martin East - Review and tidy code, reduce complexity, remove graphing - Apr 14, 2025.
    """
    
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
            self.data['SMA_20'] = ta.trend.sma_indicator(self.data['Close'], window=20)
            self.data['SMA_50'] = ta.trend.sma_indicator(self.data['Close'], window=50)
            self.data['EMA_20'] = ta.trend.ema_indicator(self.data['Close'], window=20)
            
            # RSI
            self.data['RSI'] = ta.momentum.rsi(self.data['Close'], window=14)
            
            # MACD
            self.data['MACD'] = ta.trend.macd(self.data['Close'])
            self.data['MACD_Signal'] = ta.trend.macd_signal(self.data['Close'])
            self.data['MACD_Hist'] = ta.trend.macd_diff(self.data['Close'])
            
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
        Get summary statistics for the stock data.
        
        Returns:
            dict: Summary statistics
        """
        if self.data is None:
            raise ValueError("No data available. Call fetch_stock_data first.")
        
        # Get the most recent data point
        latest = self.data.iloc[-1]
        
        # Calculate year high/low
        high = self.data['High'].max()
        low = self.data['Low'].min()
        
        # Get latest technical indicators
        latest_close = latest['Close']
        latest_macd = latest.get('MACD', 'N/A')
        latest_rsi = latest.get('RSI', 'N/A')
        
        # Calculate price change
        first_close = self.data['Close'].iloc[0]
        price_change = ((latest_close - first_close) / first_close) * 100
        
        # Calculate volatility (standard deviation of returns)
        returns = self.data['Close'].pct_change().dropna()
        volatility = returns.std() * 100
        
        return {
            'ticker': self.ticker,
            'latest_price': latest_close,
            'high': high,
            'low': low,
            'price_change_pct': price_change,
            'volatility_pct': volatility,
            'latest_macd': latest_macd,
            'latest_rsi': latest_rsi,
            'data_start': self.data.index[0].strftime('%Y-%m-%d'),
            'data_end': self.data.index[-1].strftime('%Y-%m-%d')
        }
      
    def generate_report(self, prompt_template=None):
        """
        Generate a stock report using OpenRouter.ai API and GPT 3.5 model.
        
        Args:
            prompt_template (str, optional): Custom prompt template
            
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
                "The latest MACD value is {latest_macd:.2f} and RSI is {latest_rsi:.2f}. "
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
            'model': 'openai/gpt-3.5-turbo',
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
                with open("./stock_report", "w") as f:
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

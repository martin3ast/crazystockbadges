#!env python
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
import os

# Replace with your OpenRouter API key
OPENROUTER_API_KEY = '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'
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import ta
import requests
import os

# Set your OpenRouter API key
#openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
openrouter_api_key = OPENROUTER_API_KEY

def fetch_stock_data(ticker, period='1y'):
    """Fetch historical stock data for the given ticker."""
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    return data

def perform_technical_analysis(data):
    """Calculate technical indicators and add them to the DataFrame."""
    # Calculate Moving Averages
    data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
    
    # Calculate RSI
    data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
    
    # Calculate MACD
    data['MACD'] = ta.trend.macd(data['Close'])
    
    return data

def plot_stock_data(data, ticker):
    """Plot stock closing price and technical indicators."""
    plt.figure(figsize=(14, 7))
    plt.plot(data['Close'], label='Close Price')
    plt.plot(data['SMA_20'], label='20-Day SMA')
    plt.plot(data['SMA_50'], label='50-Day SMA')
    plt.title(f'{ticker} Stock Price and Moving Averages')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid()
    plt.savefig(f'{ticker}_stock_report.png')
    plt.show()

def generate_report(data, ticker):
    """Generate a stock report using OpenRouter's API."""
    latest_data = data.iloc[-1]
    prompt = (
        f"You are a TV anchor in financial news. You are knowledgeable about pricing, trends, and the market. Give me an insightful report for {ticker} as if you really care about this company's past, present and future. Make it short, 200 words."
    )
    
    headers = {
        'Authorization': f'Bearer {openrouter_api_key}',
        'Content-Type': 'application/json',
    }
    
    json_data = {
        #'model': 'openai/gpt-4',  # Specify the model; adjust as needed
        'model' : 'openai/gpt-3.5-turbo-instruct',
        'prompt': prompt,
        'max_tokens': 1000,
    }
    
    response = requests.post('https://openrouter.ai/api/v1/completions', headers=headers, json=json_data)
    response.raise_for_status()
    report = response.json()['choices'][0]['text'].strip()
    return report

def main():
    ticker = 'TSLA'  # Example ticker symbol
    data = fetch_stock_data(ticker)
    data = perform_technical_analysis(data)
    plot_stock_data(data, ticker)
    report = generate_report(data, ticker)
    f = open('./stock_report','w')
    f.write(report)
    data.to_csv('./stock_data')

if __name__ == "__main__":
    main()
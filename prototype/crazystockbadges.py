import sys

# References
# Library review:
# https://medium.com/@alexeyyurasov/3d-modeling-with-python-c21296756db2

# Import libraries
import yfinance as yf
import numpy as np
import tensorflow as tf
from keras import layers
import trimesh
from openscad import *

# Step 1: Fetch stock data
def fetch_stock_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data['Close'].values  # Use closing prices

# Step 2: Preprocess data
def preprocess_data(prices):
    prices_normalized = (prices - np.min(prices)) / (np.max(prices) - np.min(prices))
    return prices_normalized


# Main workflow
if __name__ == "__main__":
    # Fetch and preprocess data
    stock_data = fetch_stock_data("AAPL", "2023-01-01", "2023-12-31")
    processed_data = preprocess_data(stock_data)
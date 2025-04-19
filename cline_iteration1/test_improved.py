#!/usr/bin/env python
"""
Test script for the improved Crazy Stock Badges components.

This script demonstrates how to use the improved components individually
and together to create a 3D badge from stock data.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for testing improved components - Apr 13, 2025.
"""

import os
import sys
import argparse
import logging

# Import improved modules
from improved_cli import CrazyStockBadgeCLI
from improved_market_data import MarketDataManager
from improved_sentiment import StockReportAnalyzer, SentimentAnalyzer
from improved_3d_models import BadgeFactory
from improved_crazystockbadges import CrazyStockBadges

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_improved')


def test_cli():
    """Test the improved CLI."""
    print("\n=== Testing Improved CLI ===")
    
    # Create CLI instance
    cli = CrazyStockBadgeCLI()
    
    # Parse arguments
    cli.parse_args(['--ticker', 'AAPL', '--non-interactive'])
    
    # Print parsed arguments
    print(f"Parsed arguments: {cli.args}")
    
    print("CLI test complete")


def test_market_data():
    """Test the improved market data module."""
    print("\n=== Testing Improved Market Data ===")
    
    # Create market data manager
    mdm = MarketDataManager()
    
    # Fetch data
    print("Fetching data for AAPL...")
    data = mdm.fetch_stock_data('AAPL', period='1mo', use_cache=True)
    print(f"Fetched {len(data)} data points")
    
    # Perform technical analysis
    print("Performing technical analysis...")
    data = mdm.perform_technical_analysis()
    
    # Get summary stats
    print("Getting summary statistics...")
    stats = mdm.get_summary_stats()
    print(f"Latest price: ${stats['latest_price']:.2f}")
    print(f"Year high/low: ${stats['year_high']:.2f}/${stats['year_low']:.2f}")
    print(f"Price change: {stats['price_change_pct']:.2f}%")
    
    # Plot data
    print("Creating plot...")
    plot_path = mdm.plot_stock_data(save_path='test_market_data.png')
    print(f"Plot saved to {plot_path}")
    
    print("Market data test complete")


def test_sentiment():
    """Test the improved sentiment analysis module."""
    print("\n=== Testing Improved Sentiment Analysis ===")
    
    # Create sentiment analyzer
    sentiment_analyzer = SentimentAnalyzer()
    
    # Create report analyzer
    report_analyzer = StockReportAnalyzer(sentiment_analyzer)
    
    # Sample report text
    report_text = """
    Welcome to the financial news segment, where we bring you the latest updates and insights on the world of business. Today, let's talk about one of the most talked about stocks in the market - Apple (AAPL).

    Apple has been making headlines since its inception, but it was the past year that truly put the company on the spotlight. Despite facing challenges such as supply chain issues and market volatility, Apple managed to maintain its position as one of the world's most valuable companies.

    What's impressive is Apple's vision for the future. The company has been innovating with its cutting-edge products and has expanded into services, which now represent a significant portion of its revenue. Not to mention, Apple's ecosystem continues to attract and retain customers.

    In terms of pricing, AAPL has had a steady journey. After hitting record highs, the stock experienced some volatility due to broader market conditions. However, with strong financial performance and a loyal customer base, Apple's stock has remained resilient.

    Looking ahead, Apple is poised for continued growth. The company is expanding its product lineup and services, with potential new markets on the horizon. Plus, with its focus on privacy and sustainability, Apple is well-positioned for the evolving tech landscape.

    In conclusion, Apple's past, present, and future are all intertwined with innovation, quality, and success. And as we continue to monitor this stock's performance, it's clear that AAPL is a company worth keeping an eye on. This concludes our report, thank you for tuning in.
    """
    
    # Analyze report
    print("Analyzing report...")
    analysis = report_analyzer.analyze_report(report_text=report_text)
    
    # Print summary
    report_analyzer.print_summary(analysis)
    
    # Save analysis
    report_analyzer.save_analysis(analysis, 'test_sentiment_analysis.json')
    
    print("Sentiment analysis test complete")


def test_3d_models():
    """Test the improved 3D models module."""
    print("\n=== Testing Improved 3D Models ===")
    
    # Check if stock data exists
    if not os.path.exists('./stock_data'):
        print("Stock data file not found. Run test_market_data() first.")
        return
    
    # Load stock data
    import pandas as pd
    stock_data = pd.read_csv('./stock_data')
    
    # Create badges of different types
    badge_types = ['disc', 'rectangular', 'triangular']
    
    for badge_type in badge_types:
        print(f"Creating {badge_type} badge...")
        
        # Get appropriate feature type for this badge type
        if badge_type == 'disc':
            feature_type = 'spiral'
        elif badge_type == 'rectangular':
            feature_type = 'bar_chart'
        else:
            feature_type = 'pyramid'
        
        # Create badge
        badge = BadgeFactory.create_badge(
            badge_type,
            stock_data,
            'TEST',
            {
                'feature_type': feature_type,
                'text_content': 'TEST',
                'text_position': 'bottom'
            }
        )
        
        # Generate model
        badge.generate_base()
        badge.generate_feature()
        badge.generate_text()
        badge.combine_models()
        
        # Calculate stats
        stats = badge.calculate_stats()
        print(f"  Stats: {stats}")
        
        # Save model
        output_file = f"test_{badge_type}_badge.scad"
        badge.save_to_file(output_file)
        print(f"  Saved to {output_file}")
    
    print("3D models test complete")


def test_full_application():
    """Test the full application."""
    print("\n=== Testing Full Application ===")
    
    # Create application
    app = CrazyStockBadges()
    
    # Run with arguments
    app.run(['--ticker', 'AAPL', '--period', '1y', '--output', 'test_full_app.scad', '--ga-generations', '10', '--non-interactive'])
    
    print("Full application test complete")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test improved Crazy Stock Badges components')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--cli', action='store_true', help='Test CLI')
    parser.add_argument('--market-data', action='store_true', help='Test market data')
    parser.add_argument('--sentiment', action='store_true', help='Test sentiment analysis')
    parser.add_argument('--3d-models', action='store_true', help='Test 3D models')
    parser.add_argument('--full-app', action='store_true', help='Test full application')
    
    args = parser.parse_args()
    
    # If no specific tests are requested, run all tests
    run_all = args.all or not (args.cli or args.market_data or args.sentiment or getattr(args, '3d_models') or args.full_app)
    
    try:
        if run_all or args.cli:
            test_cli()
        
        if run_all or args.market_data:
            test_market_data()
        
        if run_all or args.sentiment:
            test_sentiment()
        
        if run_all or getattr(args, '3d_models'):
            test_3d_models()
        
        if run_all or args.full_app:
            test_full_application()
        
        print("\nAll tests completed successfully!")
        return 0
    
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

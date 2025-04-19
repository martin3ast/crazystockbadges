#!/usr/bin/env python3
"""
Test Model Generator for Crazy Stock Badges

This script allows direct testing of the badge model generator without using the genetic algorithm.
You can specify all parameters manually and see the results immediately.

Version 1.0 - Cline implementation for Martin East - Test tool for model generation without genetic algorithm - Apr 16, 2025.
"""

import os
import sys
import argparse
import pandas as pd
import logging
from colorama import init, Fore, Style

# Import from existing modules
from badge_factory import BadgeFactory
import marketdata as md

# Initialize colorama
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_model_generator')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test badge model generator')
    
    # Basic parameters
    parser.add_argument('--ticker', type=str, default='TSLA', help='Stock ticker symbol')
    parser.add_argument('--period', type=str, default='1y', help='Time period for stock data')
    parser.add_argument('--output', type=str, default='test_badge.scad', help='Output file name')
    parser.add_argument('--skip-report', action='store_true', help='Skip generating stock report')
    
    # Badge type
    parser.add_argument('--badge-type', type=str, default='disc', 
                       choices=['disc', 'rectangular', 'triangular'], help='Badge type')
    
    # Feature type
    parser.add_argument('--feature-type', type=str, help='Feature type (depends on badge type)')
    
    # Text parameters
    parser.add_argument('--text-content', type=str, help='Text content (defaults to ticker symbol)')
    parser.add_argument('--text-position', type=str, default='bottom', 
                       choices=['bottom', 'top', 'front'], help='Text position')
    parser.add_argument('--text-size', type=float, default=10, help='Text size (5-15)')
    parser.add_argument('--text-depth', type=float, default=2, help='Text depth (1-3)')
    
    # Base parameters
    parser.add_argument('--base-height', type=float, default=3, help='Base height (2-5)')
    parser.add_argument('--feature-height', type=float, default=10, help='Feature height (5-20)')
    
    # Range parameters
    parser.add_argument('--height-range-max', type=float, default=15, help='Height range max (10-20)')
    parser.add_argument('--width-range-max', type=float, default=10, help='Width range max (5-15)')
    
    # Badge-specific parameters
    parser.add_argument('--base-radius', type=float, default=50, help='Base radius for disc (30-70)')
    parser.add_argument('--spiral-turns', type=int, default=7, help='Spiral turns for disc (3-10)')
    parser.add_argument('--base-width', type=float, default=100, help='Base width for rectangular (60-120)')
    parser.add_argument('--base-depth', type=float, default=60, help='Base depth for rectangular (40-80)')
    parser.add_argument('--side-length', type=float, default=80, help='Side length for triangular (60-100)')
    
    # Terrain type parameter for disc badge
    parser.add_argument('--terrain-type', type=str, default='spiral_chart', 
                       choices=['spiral_chart', 'bar_chart'], help='Terrain type for disc badge')
    
    return parser.parse_args()

def create_params_dict(args):
    """
    Create parameters dictionary from arguments.
    
    Version 1.0 - Cline implementation for Martin East - Parameter mapping function - Apr 16, 2025.
    """
    params = {
        'badge_type': args.badge_type,
        'text_position': args.text_position,
        'text_size': args.text_size,
        'text_depth': args.text_depth,
        'base_height': args.base_height,
        'feature_height': args.feature_height,
        'height_range': (0, args.height_range_max),
        'width_range': (0, args.width_range_max)
    }
    
    # Set text content
    if args.text_content:
        params['text_content'] = args.text_content
    
    # Set feature type based on badge type if provided
    if args.feature_type:
        params['feature_type'] = args.feature_type
    
    # Set terrain type for disc badge
    if args.badge_type == 'disc':
        params['spiral_chart'] = args.terrain_type
        params['base_radius'] = args.base_radius
        params['spiral_turns'] = args.spiral_turns
    
    # Set badge-specific parameters
    if args.badge_type == 'rectangular':
        params['base_width'] = args.base_width
        params['base_depth'] = args.base_depth
    elif args.badge_type == 'triangular':
        params['side_length'] = args.side_length
    
    return params

def fetch_market_data(ticker, period, skip_report=False):
    """
    Fetch and analyze market data.
    
    Args:
        ticker (str): Stock ticker symbol
        period (str): Time period for data
        skip_report (bool): Whether to skip generating the report
        
    Returns:
        pandas.DataFrame: Processed market data
        
    Version 1.0 - Cline implementation for Martin East - Market data fetching function - Apr 16, 2025.
    """
    print(f"\n{Fore.BLUE}... Retrieving Market Data from Yahoo Finance{Style.RESET_ALL}")
    
    # Create a market data manager
    mdm = md.MarketDataManager(ticker=ticker, period=period)
    
    # Fetch and analyze data
    mdm.fetch_stock_data(use_cache=True)
    
    print(f"{Fore.BLUE}... Running technical Analysis{Style.RESET_ALL}")
    mdm.perform_technical_analysis()
    
    # Get and print summary stats
    stats = mdm.get_summary_stats()
    print(f"{Fore.BLUE}...   High/Low = {stats['high']} / {stats['low']} {Style.RESET_ALL}")
    print(f"{Fore.BLUE}...   Latest MACD = {stats['latest_macd']} {Style.RESET_ALL}")
    
    # Generate report if needed
    if not skip_report:
        print(f"{Fore.BLUE}... Generating a market report{Style.RESET_ALL}")
        mdm.generate_report()
    
    # Return the processed data
    return mdm.data

def main():
    """
    Main function.
    
    Version 1.0 - Cline implementation for Martin East - Main execution function - Apr 16, 2025.
    """
    args = parse_args()
    
    try:
        # Fetch market data
        print(f"{Fore.CYAN}Fetching market data for {args.ticker}{Style.RESET_ALL}")
        stock_data = fetch_market_data(args.ticker, args.period, args.skip_report)
        
        # Create parameters dictionary
        params = create_params_dict(args)
        
        # Print parameters for reference
        print(f"\n{Fore.GREEN}Using the following parameters:{Style.RESET_ALL}")
        for key, value in params.items():
            print(f"  {key}: {value}")
        
        # Create the badge
        print(f"\n{Fore.CYAN}Creating {params['badge_type']} badge{Style.RESET_ALL}")
        badge = BadgeFactory.create_badge(args.badge_type, stock_data, args.ticker, params)
        
        # Generate the model
        print(f"{Fore.BLUE}... Generating base{Style.RESET_ALL}")
        badge.generate_base()
        
        print(f"{Fore.BLUE}... Generating terrain{Style.RESET_ALL}")
        badge.generate_terrain()
        
        print(f"{Fore.BLUE}... Generating text{Style.RESET_ALL}")
        badge.generate_text()
        
        print(f"{Fore.BLUE}... Combining models{Style.RESET_ALL}")
        badge.combine_models()
        
        # Calculate and print statistics
        try:
            stats = badge.calculate_stats()
            print(f"\n{Fore.GREEN}Model Statistics:{Style.RESET_ALL}")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        except Exception as e:
            logger.warning(f"Could not calculate stats: {e}")
        
        # Save the model
        output_file = args.output
        badge.save_to_file(output_file)
        print(f"\n{Fore.GREEN}✅ Model saved to: {output_file}{Style.RESET_ALL}")
        print(f"\nYou can now open {output_file} in OpenSCAD to view your badge or export it to STL for 3D printing.")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

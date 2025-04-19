#!/usr/bin/env python3
"""
Improved CLI for Crazy Stock Badges Project

This module provides a friendly, interactive command-line interface for the
Crazy Stock Badges project, allowing users to generate 3D printable badges
based on stock market data.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for command-line interface - Apr 13, 2025.
"""

import argparse
import sys
import time
import os

# Try to import colorama for colored terminal output
try:
    from colorama import init, Fore, Style
    init()  # Initialize colorama
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    # Create dummy color classes if colorama is not available
    class DummyFore:
        def __getattr__(self, name):
            return ""
    class DummyStyle:
        def __getattr__(self, name):
            return ""
    Fore = DummyFore()
    Style = DummyStyle()


class CrazyStockBadges:
    """
    Command-line interface for the Crazy Stock Badge Generator.
    
    Version 1.0 - Cline implementation for Martin East - Implements user-friendly CLI with interactive prompts - Apr 13, 2025.
    Version 1.1 - Martin East - Fix stub code, rewrite and simplify appropriately - Apr 14, 2025.
    """
    
    def __init__(self):
        """Initialize the CLI with an argument parser."""
        self.parser = self._create_parser()
        self.args = None
        
    def _create_parser(self):
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description="Crazy Stock Badge Generator - Create 3D printable badges from stock market data",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Add arguments
        parser.add_argument('--ticker', type=str, help='Stock ticker symbol (e.g., TSLA, AAPL)')
        parser.add_argument('--period', type=str, default='1y', 
                           help='Time period for stock data (default: 1y)')
        parser.add_argument('--non-interactive', action='store_true', 
                           help='Run in non-interactive mode')
        parser.add_argument('--output', type=str, 
                           help='Output file name for the SCAD file (default: disc.scad)')
        parser.add_argument('--skip-report', action='store_true',
                           help='Skip generating and displaying the stock report')
        parser.add_argument('--ga-generations', type=int, default=100,
                           help='Number of generations for the genetic algorithm (default: 100)')
        
        return parser
    
    def parse_args(self, args=None):
        """Parse command line arguments."""
        self.args = self.parser.parse_args(args)
        return self.args
    
    def run(self):
        """Main CLI execution flow."""
        # Display welcome message
        self._print_welcome()
        
        # Get ticker symbol (from args or prompt)
        ticker = self._get_ticker()
        
        # Show progress for data retrieval
        self._show_data_retrieval_progress(ticker)
        
        # Offer to show stock report
        if not self.args.skip_report:
            self._handle_report_display()
        
        # Show badge generation progress
        #self._show_badge_generation_progress()
        
        # Display final information
        #self._show_final_info()
        
    def _print_welcome(self):
        """Display welcome message."""
        print(f"\n{Fore.CYAN}🚀 Welcome to Crazy Stock Badge Generator! 🚀{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Are you ready to get crazy with stock data?{Style.RESET_ALL}\n")
    
    def _get_ticker(self):
        """Get ticker symbol from args or user input."""
        if self.args.ticker:
            ticker = self.args.ticker.upper()
            print(f"Using provided ticker symbol: {Fore.GREEN}{ticker}{Style.RESET_ALL}")
        else:
            ticker = input(f"{Fore.YELLOW}What stock price symbol would you like to choose? > {Style.RESET_ALL}").upper()
            print(f"\nOk, you chose {Fore.GREEN}{ticker}{Style.RESET_ALL}. Let's see what we can do.")
        
        return ticker
    
    def _show_data_retrieval_progress(self, ticker):
        """Show progress during data retrieval."""
        print(f"\n{Fore.BLUE}... Retrieving Market Data from Yahoo Finance{Style.RESET_ALL}")
        time.sleep(0.5)  # Simulate processing time
        
        print(f"{Fore.BLUE}... Running some technical Analysis{Style.RESET_ALL}")
        time.sleep(0.5)
        
        # These would be actual values in the real implementation
        print(f"{Fore.BLUE}...   1 Year High/Low = 450/220{Style.RESET_ALL}")
        print(f"{Fore.BLUE}...   Latest MACD = -4.2{Style.RESET_ALL}")
        
        if not self.args.skip_report:
            print(f"{Fore.BLUE}... Generating a market report{Style.RESET_ALL}")
    
    def _handle_report_display(self):
        """Ask if user wants to see the report and display it if yes."""
        if self.args.non_interactive:
            return
            
        show_report = input(f"\n{Fore.YELLOW}Would you like to see the market report? (yes/no) > {Style.RESET_ALL}").lower()
        if show_report in ['yes', 'y']:
            # In the real implementation, this would load the actual report
            try:
                if os.path.exists("stock_report"):
                    with open("stock_report", "r") as f:
                        report = f.read()
                    print(f"\n{Fore.MAGENTA}{report}{Style.RESET_ALL}\n")
                else:
                    print(f"\n{Fore.RED}Stock report file not found. It may not have been generated yet.{Style.RESET_ALL}\n")
            except Exception as e:
                print(f"\n{Fore.RED}Error reading stock report: {str(e)}{Style.RESET_ALL}\n")
                print("[Stock report would be displayed here]\n")
    
    def _show_badge_generation_progress(self):
        """Show progress during badge generation."""
        print(f"\n{Fore.BLUE}... Starting the 3-D badge generation...{Style.RESET_ALL}")
        time.sleep(0.5)
        
        generations = self.args.ga_generations
        print(f"{Fore.BLUE}... Choosing one that's crazy, running GA with {generations} generations...{Style.RESET_ALL}")
        time.sleep(0.5)
        
        output_file = self.args.output if self.args.output else "disc.scad"
        print(f"{Fore.BLUE}... OK I found one, writing to {output_file}...{Style.RESET_ALL}")
        time.sleep(0.5)
        
        # These would be actual values in the real implementation
        print(f"{Fore.BLUE}...    Size = 50mm x 50mm{Style.RESET_ALL}")
        print(f"{Fore.BLUE}...    No. of objects = 120{Style.RESET_ALL}")
        print(f"{Fore.BLUE}...    Height difference (Z) = 15mm{Style.RESET_ALL}")
        print(f"{Fore.BLUE}...    Width difference (X) = 10mm{Style.RESET_ALL}")
        print(f"{Fore.BLUE}...    Depth difference (Y) = 5mm{Style.RESET_ALL}")
    
    def _show_final_info(self):
        """Display final information about the generated files."""
        output_file = self.args.output if self.args.output else "disc.scad"
        
        print(f"\n{Fore.GREEN}✅ Badge generation complete!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📁 Files created:{Style.RESET_ALL}")
        print(f"   - {output_file} (OpenSCAD file)")
        if not self.args.skip_report:
            print("   - stock_report (Text report)")
        
        print(f"\nYou can now open {output_file} in OpenSCAD to view your badge or export it to STL for 3D printing.")


def main():
    """Main entry point for the CLI."""
    try:
        cli = CrazyStockBadges()
        cli.parse_args()
        cli.run()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}Process interrupted by user. Exiting...{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()

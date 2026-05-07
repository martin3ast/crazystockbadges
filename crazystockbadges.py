#!/usr/bin/env python3
"""
Main command line interface for Crazy Stock Badges Project.

Please see the individual code blocks for version changes over time.

This is an interactive command-line interface for the
Crazy Stock Badges project.

This file also includes the genetic algorithm for generating the 3D badge.

See Version history changes for individual functions below.

"""
import os
import argparse
import sys
import time
import re
import logging
import random
import statistics
import warnings
from collections import defaultdict
from colorama import init, Fore, Style
import matplotlib.pyplot as plt
import numpy as np

# Import required modules
import marketdata as md
from badge_factory import BadgeFactory
from complexity_analyser import ComplexityAnalyzer
from sentiment_analyser import StockReportAnalyzer
from solid import scad_render
import pygad
from pygad.visualize import plot
from ga_engine import BadgeGAEngine, GENE_SPACE


# Initialize colorama for Text color on terminal output.
init(autoreset=True)

class CrazyStockBadge:
    """
    Command-line interface for the Crazy Stock Badge Generator.
    
    Version 1.0 - Cline implementation for Martin East - Implements user-friendly CLI with interactive prompts - Apr 13, 2025.
    Version 1.1 - Martin East, review and tidy up, add complete code for stubs - Apr 14, 2025.
    Version 2.0 - Cline for Martin East, refactor logging to use log-levels - Apr 27, 2025.
    """
    
    def __init__(self):
        """Initialize the CLI with an argument parser."""
        self.parser = argparse.ArgumentParser(
            description="Crazy Stock Badge Generator - Create 3D printable badges from stock market data",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        self.parser.add_argument('--ticker', type=str, help='Stock ticker symbol (e.g., TSLA, AAPL)')
        self.parser.add_argument('--period', type=str, default='1y', 
                           help='Time period for stock data (default: 1y)')
        self.parser.add_argument('--non-interactive', action='store_true', 
                           help='Run in non-interactive mode')
        self.parser.add_argument('--output', type=str, 
                           help='Output file name for the SCAD file (default: disc.scad)')
        self.parser.add_argument('--skip-report', action='store_true',
                           help='Skip generating and displaying the stock report')
        self.parser.add_argument('--ga-generations', type=int, default=10,
                           help='Number of generations for the genetic algorithm (default: 10)')
        self.parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARN', 'ERROR'], 
                           default='WARN', help='Set logging level (default: WARN)')
        self.parser.add_argument('--visualise-ga', action='store_true',
                           help='Visualise genetic algorithm results')
        
        # Parse the arguments
        self.args = self.parser.parse_args()
        
        # Configure logging
        log_level = getattr(logging, self.args.log_level)
            
        # Get the root logger and clear any existing handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Set the root logger level
        logger.setLevel(log_level)
        
        # Set up handlers - always log to both file and stdout
        file_handler = logging.FileHandler("crazystockbadges.log", mode='w')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        # Add stdout handler - always log to stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(log_level)
        stdout_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(stdout_handler)
            
        self.logger = logging.getLogger('crazystockbadges')

        # Set default values or from command line arguments.
        self.ticker = self.args.ticker if hasattr(self, 'args') else 'APPL'
        self.period = self.args.period if hasattr(self, 'args') else '1y'  
        self.ga_generations = self.args.ga_generations if hasattr(self, 'args') else 10

        self.mdm = None # Placeholder for MarketDataManager instance   
        self.stock_report = None # Placeholder for stock report content
        
        # Initialize fitness statistics tracking
        self.fitness_stats = {
            'generation': [],
            'min': [],
            'mean': [],
            'max': [],
            'best': []  # Best solution fitness across all generations
        }
        
        # Track the best solution ourselves
        self.best_badge = None
        self.best_report = None
        self.best_fitness = float('-inf')  # Start with negative infinity so any fitness is better
        self.best_solution = None  # Store the genes of the best solution
    
    
    def run(self):
        """Main CLI execution flow. Used in the main function, after parse_args."""
                
        print(f"\n{Fore.CYAN}Welcome to Crazy Stock Badge Generator!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Are you ready to get crazy with stock data?... Let's make something of it!{Style.RESET_ALL}\n")
    
        #Get ticker symbol from args or user input.
        if self.args.ticker:
            self.ticker = self.args.ticker.upper()
            print(f"Using given ticker symbol: {Fore.GREEN}{self.ticker}{Style.RESET_ALL}")
        else:
            # Define example tickers with company names
            example_tickers = [
                ("AAPL", "Apple Inc."),
                ("MSFT", "Microsoft Corporation"),
                ("GOOGL", "Alphabet Inc. (Google)"),
                ("AMZN", "Amazon.com Inc."),
                ("TSLA", "Tesla Inc."),
                ("META", "Meta Platforms Inc. (Facebook)"),
                ("NVDA", "NVIDIA Corporation"),
                ("JPM", "JPMorgan Chase & Co."),
                ("V", "Visa Inc."),
                ("WMT", "Walmart Inc.")
            ]
            
            # Display example tickers
            print(f"{Fore.GREEN}Example stock tickers you can use:{Style.RESET_ALL}")
            for ticker, company in example_tickers:
                print(f"{Fore.GREEN}  {ticker:<6}{Style.RESET_ALL} - {company}")
            print()
            
            self.ticker = input(f"{Fore.YELLOW}What stock price symbol would you like to choose? > {Style.RESET_ALL}").upper()
            print(f"\nYou chose {Fore.GREEN}{self.ticker}{Style.RESET_ALL}. Let's see what we can do.")

        #
        # Get the marketData and create and print a stock market report.
        #
        print(f"\n{Fore.BLUE}... Retrieving Market Data from Yahoo Finance{Style.RESET_ALL}")
        self.mdm = md.MarketDataManager(ticker=self.ticker, period=self.period)
        
        try:
            self.mdm.fetch_stock_data(use_cache=True)
        except ValueError as e:
            print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please try again with a valid ticker symbol.{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{Fore.RED}Error fetching stock data: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)

        print(f"{Fore.BLUE}... Running some technical Analysis{Style.RESET_ALL}")
        self.mdm.perform_technical_analysis()

        stats = self.mdm.get_summary_stats()
        
        print(f"{Fore.BLUE}...   High/Low = {stats['high']} / {stats['low']} {Style.RESET_ALL}")
        print(f"{Fore.BLUE}...   Latest MACD = {stats['macd']} {Style.RESET_ALL}")
        
        if not self.args.skip_report:
            print(f"{Fore.BLUE}... Generating a market report, talking with GPT3.5 via OpenRouter.ai to do this ... {Style.RESET_ALL}")
            self.mdm.generate_report()

            show_report = input(f"\n{Fore.YELLOW}Would you like to see the market report? (yes/no) > {Style.RESET_ALL}").lower()
            if show_report in ['yes', 'y'] and os.path.exists("stock_report"):
                with open("stock_report", "r") as f:
                    report = f.read()
                print(f"\n{Fore.MAGENTA}{report}{Style.RESET_ALL}\n")
                
                # Create a StockReportAnalyzer instance
                print(f"{Fore.BLUE}... Analyzing sentiment in the stock report...{Style.RESET_ALL}")
                report_analyzer = StockReportAnalyzer()
                
                # Analyze the report
                analysis = report_analyzer.analyze_report()
                
                # Save the analysis to the cache directory
                cache_file = os.path.join("./cache", "sentiment_analysis.json")
                print(f"{Fore.BLUE}... Saving sentiment analysis to {cache_file}...{Style.RESET_ALL}")
                report_analyzer.save_analysis(analysis, cache_file)
                
                # Print the sentiment analysis summary
                print(f"\n{Fore.BLUE}=== SENTIMENT ANALYSIS SUMMARY ==={Style.RESET_ALL}")
                report_analyzer.print_summary(analysis)
        
        #
        # Badge Generation, using a genetic algorithm
        #
        print(f"\n{Fore.BLUE}... Starting the 3-D badge generation...{Style.RESET_ALL}")
        time.sleep(0.5)
        
        generations = self.args.ga_generations
        print(f"{Fore.BLUE}... Initialising the Genetic Algorithm with {generations} generations...{Style.RESET_ALL}")
        print(f"{Fore.BLUE}... Searching for the CRAZIEST design, what will it be? ...{Style.RESET_ALL}")
        
        # Generate the badge using the genetic algorithm
        self.generate_badge()

        # Closing information
        #
        output_file = self.args.output if self.args.output else f"./scad_models/{self.ticker}_badge.scad"
        print(f"{Fore.BLUE}... Writing SCAD object to {output_file}...{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}✅ Badge generation complete!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📁 Files created:{Style.RESET_ALL}")
        print(f"   - {output_file} (OpenSCAD file)")
        if not self.args.skip_report:
            print("   - stock_report (Text report)")
        
        print(f"\nYou can now open {output_file} in OpenSCAD to view your badge or export it to STL for 3D printing.")



    def generate_badge(self):
        """Generate 3D badge using shared GA engine."""
        self.logger.info("Generating 3D badge using shared GA engine")

        def on_generation(ga_instance, engine):
            best_solution, best_fitness, solution_idx = ga_instance.best_solution()
            fitness_values = [
                ga_instance.badges[i][2]
                for i in range(len(ga_instance.population))
                if i in ga_instance.badges
            ]
            self.fitness_stats['generation'].append(ga_instance.generations_completed)
            self.fitness_stats['min'].append(min(fitness_values))
            self.fitness_stats['mean'].append(statistics.mean(fitness_values))
            self.fitness_stats['max'].append(max(fitness_values))
            self.fitness_stats['best'].append(best_fitness)

            print(f"{Fore.BLUE}.oOo.{Style.RESET_ALL}", end="")
            if ga_instance.generations_completed % 5 == 0:
                self.logger.info(
                    f"Generation {ga_instance.generations_completed}: "
                    f"Best fitness = {best_fitness:.2f}"
                )
                print(
                    f"{Fore.BLUE} ... Best fitness: {best_fitness:.2f} "
                    f"{Style.RESET_ALL}"
                )

        engine = BadgeGAEngine(
            mdm=self.mdm,
            ticker=self.ticker,
            num_generations=self.ga_generations,
            on_generation=on_generation,
        )
        self.logger.info(f"Running GA for {self.ga_generations} generations")
        best_badge, best_fitness = engine.run()
        self.ga_instance = engine.ga_instance
        self.best_badge = best_badge
        self.best_fitness = best_fitness

        output_file = (
            self.args.output if self.args.output
            else f"./scad_models/{self.ticker}_badge.scad"
        )
        self.args.output = output_file
        os.makedirs("./scad_models", exist_ok=True)
        best_badge.save_to_file(output_file)

        self.badge = best_badge
        self.badge_params = best_badge.params
        self.badge_output_file = output_file
        self.logger.info(
            f"Best fitness: {best_fitness:.2f} — saved badge to {output_file}"
        )

        if self.args.visualise_ga:
            self.visualise_ga_results()


    def visualise_ga_results(self):
        """
        Create and display plots for the genetic algorithm results.
        
        Version 1.0: Cline implementation for Martin East - Visualisation of GA results - Apr 27, 2025
        Version 1.1: Cline bugfix for Martin East - Fixed visualisation implementation - Apr 27, 2025
        Version 1.2: Cline implementation for Martin East - Added fitness statistics plotting - Apr 28, 2025
        """
        self.logger.info("Generating visualisation of GA results")
        
        # Create plots directory if it doesn't exist
        plots_dir = "./plots"
        os.makedirs(plots_dir, exist_ok=True)
        
        # Plot fitness evolution directly from the GA instance
        # fitness_fig = self.ga_instance.plot_fitness(
        #     title=f"{self.ticker} Badge - Fitness Evolution",
        #     save_dir=plots_dir
        # )
        
        # # Plot new solution rate directly from the GA instance
        # solution_rate_fig = self.ga_instance.plot_new_solution_rate(
        #     title=f"{self.ticker} Badge - New Solution Rate",
        #     save_dir=plots_dir
        # )
        
        # Plot fitness statistics (min, mean, max)
        # if self.fitness_stats['generation']:
        self.plot_fitness_statistics(plots_dir)
        
        self.logger.info(f"GA plots saved to {plots_dir}")
        print(f"{Fore.GREEN}GA visualisation plots saved to {plots_dir}{Style.RESET_ALL}")
    
    def plot_fitness_statistics(self, plots_dir):
        """
        Plot min, mean, and max fitness statistics for each generation.
        
        Version 1.0: Cline implementation for Martin East - Fitness statistics plotting - Apr 28, 2025
        
        Args:
            plots_dir (str): Directory to save the plot
        """
        self.logger.info("Generating fitness statistics plot")
        
        # Create a new figure
        plt.figure(figsize=(10, 6))
        
        # Plot the statistics
        generations = self.fitness_stats['generation']
        plt.plot(generations, self.fitness_stats['min'], 'b-', label='Min Fitness')
        plt.plot(generations, self.fitness_stats['mean'], 'g-', label='Mean Fitness')
        plt.plot(generations, self.fitness_stats['max'], 'r-', label='Max Fitness')
        plt.plot(generations, self.fitness_stats['best'], 'm-', label='Best Solution')
        
        # Calculate and plot linear trend line for mean fitness
        z = np.polyfit(generations, self.fitness_stats['mean'], 1)
        p = np.poly1d(z)
        plt.plot(generations, p(generations), 'g--', label='Mean Trend')
        
        # Add labels and title
        plt.xlabel('Generation')
        plt.ylabel('Fitness')
        plt.title(f'{self.ticker} Badge - Fitness Statistics per Generation')
        plt.grid(True)
        plt.legend()
        
        # Save the plot
        plot_path = os.path.join(plots_dir, f"{self.ticker}_fitness_stats.png")
        plt.savefig(plot_path)
        plt.close()
        
        self.logger.info(f"Fitness statistics plot saved to {plot_path}")
        print(f"{Fore.GREEN}Fitness statistics plot saved to {plot_path}{Style.RESET_ALL}")
    
def main():
    """Main entry point for the CLI."""
    try:
        cli = CrazyStockBadge()
        cli.run()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.RED}Process interrupted by user. Exiting...{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()

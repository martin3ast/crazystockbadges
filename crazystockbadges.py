#!/usr/bin/env python3
"""
Main command line interface for Crazy Stock Badges Project

This module provides a friendly, interactive command-line interface for the
Crazy Stock Badges project, allowing users to generate 3D printable badges
based on stock market data.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for command-line interface - Apr 13, 2025.
Version 1.1 - Martin East - Strip unnecessary error checking and simplify -  Apr 14, 2025.
Version 2.0 - Martin East - Simplify, removed unecessary functions and added docstrings - Apr 14, 2025.
"""

import argparse
import sys
import time
import os
import re
import logging
import random
from collections import defaultdict
from colorama import init, Fore, Style

# Import Python debugger
import pdb

# Import required modules
import marketdata as md
from badge_factory import BadgeFactory
from complexity_analyser import ComplexityAnalyzer
from sentiment_analyser import StockReportAnalyzer
from solid import scad_render
import pygad


# Initialize colorama for Text color on terminal output.
init(autoreset=True)

class CrazyStockBadge:
    """
    Command-line interface for the Crazy Stock Badge Generator.
    
    Version 1.0 - Cline implementation for Martin East - Implements user-friendly CLI with interactive prompts - Apr 13, 2025.
    Version 1.1 - Martin East, review and tidy up, add complete code for stubs - Apr 14, 2025.
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
                           default='INFO', help='Set logging level (default: INFO)')
        
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
        self.ga_generations = self.args.ga_generations if hasattr(self, 'args') else 100

        self.mdm = None # Placeholder for MarketDataManager instance   
        self.stock_report = None # Placeholder for stock report content
        
    
    
    def run(self):
        """Main CLI execution flow. Used in the main function, after parse_args."""
                
        print(f"\n{Fore.CYAN}Welcome to Crazy Stock Badge Generator!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Are you ready to get crazy with stock data?... Let's make something of it!{Style.RESET_ALL}\n")
    
        #Get ticker symbol from args or user input.
        if self.args.ticker:
            self.ticker = self.args.ticker.upper()
            print(f"Using given ticker symbol: {Fore.GREEN}{self.ticker}{Style.RESET_ALL}")
        else:
            self.ticker = input(f"{Fore.YELLOW}What stock price symbol would you like to choose? > {Style.RESET_ALL}").upper()
            print(f"\nYou chose {Fore.GREEN}{self.ticker}{Style.RESET_ALL}. Let's see what we can do.")

        #
        # Get the marketData and create and print a stock market report.
        #
        print(f"\n{Fore.BLUE}... Retrieving Market Data from Yahoo Finance{Style.RESET_ALL}")
        self.mdm = md.MarketDataManager(ticker=self.ticker, period=self.period)
        self.mdm.fetch_stock_data(use_cache=True)

        print(f"{Fore.BLUE}... Running some technical Analysis{Style.RESET_ALL}")
        self.mdm.perform_technical_analysis()

        stats = self.mdm.get_summary_stats()
        
        print(f"{Fore.BLUE}...   High/Low = {stats['high']} / {stats['low']} {Style.RESET_ALL}")
        print(f"{Fore.BLUE}...   Latest MACD = {stats['latest_macd']} {Style.RESET_ALL}")
        
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
        print(f"{Fore.BLUE}... Badge generation complete!{Style.RESET_ALL}")

        # Get the badge complexity stats
        # Ensure the badge has its final_model generated
        if self.badge.final_model is None:
            self.badge.combine_models()
            
        # Create analyzer and get complexity report
        analyzer = ComplexityAnalyzer(self.badge.final_model)
        # Print the complexity report
        print(f"\n{Fore.LIGHTBLUE_EX}=== BADGE COMPLEXITY REPORT ==={Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLUE_EX}... Total nodes: {self.complexity_report['total_nodes']}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLUE_EX}... Max depth: {self.complexity_report['max_depth']}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLUE_EX}... Complexity score: {self.complexity_report['complexity_score']:.2f}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLUE_EX}... Operation counts: {', '.join([f'{k}: {v}' for k, v in self.complexity_report['operation_counts'].items()])}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLUE_EX}... Primitive counts: {', '.join([f'{k}: {v}' for k, v in self.complexity_report['primitive_counts'].items()])}{Style.RESET_ALL}")
        print(f"{Fore.LIGHTBLUE_EX}... Best fitness: {self.ga_instance.best_solution()[1]:.2f}{Style.RESET_ALL}")


        output_file = self.args.output 
        print(f"{Fore.BLUE}... Writing SCAD object to {output_file}...{Style.RESET_ALL}")

        
        # Closing information
        #
        output_file = self.args.output if self.args.output else f"./scad_models/{self.ticker}_badge.scad"
        
        print(f"\n{Fore.GREEN}✅ Badge generation complete!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📁 Files created:{Style.RESET_ALL}")
        print(f"   - {output_file} (OpenSCAD file)")
        if not self.args.skip_report:
            print("   - stock_report (Text report)")
        
        print(f"\nYou can now open {output_file} in OpenSCAD to view your badge or export it to STL for 3D printing.")



    def generate_badge(self):
        """
        Generate 3D badge using genetic algorithm with focus on complexity and craziness.
        
        Version 2.0: Cline refactor for Martin East - refactor this function after changes to badge_factory.py.
        Attribution: Cline implementation for Martin East - Complexity-focused badge generation - Apr 17, 2025
        """
        self.logger.info("Generating 3D badge using genetic algorithm with complexity metrics")
        
        # Define gene space
        gene_space = self._create_gene_space()
        
        # Create pyGAD instance
        self.ga_instance = pygad.GA(
            num_generations=self.ga_generations,
            num_parents_mating=2,
            fitness_func=self.fitness_function,
            sol_per_pop=50,
            num_genes=len(gene_space),
            gene_space=gene_space,
            parent_selection_type="tournament",
            K_tournament=3,
            crossover_type="uniform",
            mutation_type="random",
            mutation_percent_genes=20,
            keep_elitism=2,
            on_generation=self._on_generation
        )
        
        # Run the genetic algorithm
        self.logger.info(f"Running genetic algorithm for {self.ga_generations} generations")
        self.ga_instance.run()
        
        # Get the best solution according to PyGAD
        solution, solution_fitness, solution_idx = self.ga_instance.best_solution()
        self.logger.info(f"Best solution (individual {solution_idx}) found with fitness: {solution_fitness:.2f}")
        
        # Get the best badge and complexity report
        best_badge, complexity_report, _ = self.ga_instance.badges[solution_idx]
        
        # Instead of regenerating parameters from genes, use the actual parameters from the badge
        best_params = best_badge.params
        
        # Store the complexity report for display
        self.complexity_report = complexity_report
            
        # Save the best badge to scad_models directory
        if self.args.output:
            # If output file is specified, use it but ensure it's in scad_models directory
            if not self.args.output.startswith("./scad_models/"):
                output_file = f"./scad_models/{os.path.basename(self.args.output)}"
            else:
                output_file = self.args.output
        else:
            # Default output file in scad_models directory
            output_file = f"./scad_models/{self.args.ticker}_badge.scad"
        
        self.args.output = output_file
        self.logger.info(f"Saving badge to {output_file}")

        # Ensure scad_models directory exists
        os.makedirs("./scad_models", exist_ok=True)
        
        best_badge.save_to_file(output_file)
        
        # Store the results
        self.badge = best_badge
        self.badge_params = best_params
        self.badge_output_file = output_file

        # Log terrain types
        if 'terrain_types' in best_params:
            terrain_types = best_params['terrain_types']
            self.logger.info(f"Terrain types: {', '.join(terrain_types)}")
        else:
            self.logger.info(f"Terrain type: {best_params.get('terrain_type', 'N/A')}")
        
        # Log complexity metrics
        self.logger.info(f"Complexity score: {self.complexity_report['complexity_score']:.2f}")
        self.logger.info(f"Total nodes: {self.complexity_report['total_nodes']}")
        self.logger.info(f"Max depth: {self.complexity_report['max_depth']}")
                
        # Log badge details
        self.logger.info(f"Badge generation complete. Output file: {output_file}")
        self.logger.info(f"Badge type: {best_params['badge_type']}")
        

    def get_text_content(self, text_type, sentiment):
        """
        Get text content based on the text type and sentiment.
        
        Args:
            text_type (str): Type of text to display
            sentiment (float): Sentiment value for the stock
            
        Returns:
            str: Text content for the badge
        """
        if text_type == 'one_word_analysis':
            return self.mdm.get_one_word_analysis(sentiment)
        elif text_type == 'buy_sell_hold':
            return self.mdm.get_buy_sell_hold(sentiment)
        elif text_type == 'latest_macd':
            return self.mdm.get_latest_macd()
        elif text_type == 'high':
            return self.mdm.get_high()
        elif text_type == 'low':
            return self.mdm.get_low()
        elif text_type == 'market_outlook':
            return self.mdm.get_market_outlook(sentiment)
        else:
            return "Unknown"
        
            
    def genes_to_badge_params(self, genes):
        """
        Convert genes array to badge parameters dictionary.
        
        Version 3.0: Cline refactor for Martin East - Updated for simplified genotype - Apr 24, 2025.
        
        Args:
            genes (list): List of gene values
            
        Returns:
            dict: Badge parameters
        """
        # Define badge types and terrain types
        badge_types = ['disc', 'rectangular', 'triangular']
        all_terrain_types = ['spiral_chart', 'bar_chart', 'pyramid', 'surface_plot']
        # Text rotation held in continuous range 
        text_content_types = ['one_word_analysis', 'buy_sell_hold', 'latest_macd', 'high', 'low', 'market_outlook']
        
        # Get badge type
        badge_type_idx = int(genes[0])
        badge_type = badge_types[badge_type_idx]
        
        # Get number of terrain types to use
        num_terrain_types = int(genes[1])
        
        # Get terrain types (genes 2-7)
        terrain_types = []
        terrain_idx = int(genes[2])
        # Only use the first num_terrain_types terrain types
        for i in range(num_terrain_types):
            terrain_idx = int(genes[2 + i])   
            terrain_types.append(all_terrain_types[terrain_idx])
        
        # Get text position (continuous value between 0 and 360 degrees)
        text_position = genes[6]  # Direct value, no indexing needed
        
        # Get text type
        text_type_idx = int(genes[7])
        text_type = text_content_types[text_type_idx]
        sentiment = self.mdm.get_sentiment()
        text_content = self.ticker + " " + self.get_text_content(text_type, sentiment)
    
        # Get base height
        base_height = int(genes[8])
        
        # Get size parameter
        size_idx = int(genes[9])
        
        # Map size to badge-specific dimensions
        if badge_type == 'disc':
            # Small, medium, large disc sizes
            base_radius_map = [30, 50, 70]
            base_radius = base_radius_map[size_idx]
        elif badge_type == 'rectangular':
            # Small, medium, large rectangular sizes
            base_width_map = [60, 90, 120]
            base_depth_map = [40, 60, 80]
            base_width = base_width_map[size_idx]
            base_depth = base_depth_map[size_idx]
        elif badge_type == 'triangular':
            # Small, medium, large triangular sizes
            side_length_map = [60, 80, 100]
            side_length = side_length_map[size_idx]

        # Get spiral turn
        spiral_turns = int(genes[10])
        
        # Create parameters dictionary
        params = {
            'badge_type': badge_type,
            'text_position': text_position,
            'text_content': text_content,
            'base_height': base_height,
            'height_range': (0, 10),  # Default height range
            'width_range': (0, 10),   # Default width range
            'text_size': 10,  # Default text size
            'text_depth': 2,   # Default text depth
            'spiral_turns': spiral_turns
        }
        
        # Add terrain types if multiple
        params['terrain_types'] = terrain_types
        
        # Add badge-specific parameters
        if badge_type == 'disc':
            params['base_radius'] = base_radius
        elif badge_type == 'rectangular':
            params['base_width'] = base_width
            params['base_depth'] = base_depth
        elif badge_type == 'triangular':
            params['side_length'] = side_length
        
        return params

    
    
    def fitness_function(self, ga_instance, solution, solution_idx):
        """
        Fitness function using complexity metrics.
        
        Version 3.0: Cline refactor for Martin East - Updated to work with ComplexityAnalyzer - Apr 23, 2025.
        Version 3.1: Martin East - Fix issue with model generation - Apr 25, 2025.
        Version 3.2: Martin East - Modifying weights for fitness - Apr 25, 2025.
        Version 3.3: Cline - Fixed fitness function to return proper values for all solutions - Apr 26, 2025.
        Version 3.4: Cline - Modified to use raw metric values with weights instead of normalization - Apr 26, 2025.
        Version 3.5: Martin East - Added debug logging for fitness function, removed node vs complexity weighting (both 1 now) - Apr 27, 2025.
        """
        params = self.genes_to_badge_params(solution)

        # Create the badge using the parameters
        badge = BadgeFactory.create_badge(params['badge_type'], self.mdm.data, self.ticker, params)
        
        # Ensure the badge's model components are generated
        badge.generate_base()
        badge.generate_terrain()
        badge.generate_text()
        badge.combine_models()
            
        analyzer = ComplexityAnalyzer(badge.final_model)
        report = analyzer.get_complexity_report()
        self.logger.debug(f"Complexity report for solution {solution_idx}: {report}")

        # Initialize badges dictionary if it doesn't exist
        if not hasattr(ga_instance, 'badges'):
            ga_instance.badges = {}
        
        # Store the badge and report
        ga_instance.badges[solution_idx] = (badge, report, 0)  # Initial fitness placeholder
        
        # Define metrics to use for fitness calculation
        metrics = [
            'total_nodes', 
            'complexity_score'
        ]
        
        # Assign weights to the metrics, they are now even!
        weights = {
            'total_nodes': 1,
            'complexity_score': 1 
        }
        
        # Calculate fitness for this solution using raw metric values with weights
        fitness = (report['total_nodes'] * weights['total_nodes']) + (report['complexity_score'] * weights['complexity_score'])
        
        # Update the fitness value in badges
        ga_instance.badges[solution_idx] = (badge, report, fitness)
        
        # Print detailed information about this solution
        self.logger.debug(f"Solution {solution_idx}: Fitness = {fitness:.2f}, Total nodes = {report['total_nodes']}, Complexity score = {report['complexity_score']:.2f}")
        self.logger.debug(f"Parameters: {', '.join([f'{k}: {v}' for k, v in badge.params.items()])}")
    
        # Return the calculated fitness value
        return fitness
        
    def _on_generation(self, ga_instance):
        """
        Callback function called after each generation.
        
        Attribution: Cline implementation for Martin East - Generation callback - Apr 17, 2025
        Version 2.0: Cline implementation for Martin East - Added SCAD model generation for fittest individual - Apr 27, 2025
        Version 2.1: Martin East - Added debug logging for generation callback, write out interim fittest models for debug - Apr 27, 2025.
        Version 2.2: Cline - Added debug flag to control generation printing - Apr 27, 2025.
        Version 2.3: Cline - Added detailed debugging for fitness discrepancy - Apr 27, 2025.
        
        Args:
            ga_instance: The genetic algorithm instance
        """
        best_solution, best_fitness, solution_idx = ga_instance.best_solution()

        # Get the best badge from ga_instance.badges
        best_badge = ga_instance.badges[solution_idx][0]
        params = best_badge.params
        
        # Only print generation details if log level is DEBUG
        if self.args.log_level == 'DEBUG':
            # Get the best badge from ga_instance.badges
            best_badge = ga_instance.badges[solution_idx][0]
            
            # Ensure scad_models directory exists
            os.makedirs("./scad_models", exist_ok=True)
            self.logger.debug(f"Generation {ga_instance.generations_completed}: Best fitness = {best_fitness:.2f}")
            self.logger.debug(f"Parameters: Badge Type = {params['badge_type']}, Terrain Types = {params['terrain_types']}")
            self.logger.debug(f"Text Content = '{params['text_content']}', Text Position = {params['text_position']:.2f}°")
        
            # Create a SCAD model for the fittest individual in each generation
            generation_num = ga_instance.generations_completed
            output_file = f"./scad_models/{self.ticker}_gen{generation_num}_badge.scad"
        

            # Save the model to file
            best_badge.save_to_file(output_file)
            self.logger.info(f"Generation {generation_num}: Saved this generation's best model to {output_file}")
        
        if ga_instance.generations_completed % 10 == 0:
            # Log the best solution according to PyGAD
            self.logger.info(f"Generation {ga_instance.generations_completed}: Best fitness = {best_fitness:.2f}")


    def _create_gene_space(self):
        """
        Define simplified gene space for badge generation.
        
        Version 3.0: Cline refactor for Martin East - Simplified genotype - Apr 24, 2025.
        
        Returns:
            list: Gene space definition for pyGAD
        """

        
        gene_space = [
            # Gene 0: Badge type (disc, rectangular, triangular)
            [0, 1, 2],
            
            # Gene 1: Number of terrain types to use (1-6)
            [1, 2, 3, 4],
            
            # Genes 2-5: Terrain types (up to 6 different types)
            # Each can be spiral_chart, bar_chart, pyramid, surface_plot
                    # Define terrain types:
                    # 0: spiral_chart
                    # 1: bar_chart
                    # 2: pyramid
                    # 3: surface_plot
            [0, 1, 2, 3],  # Terrain type 1
            [0, 1, 2, 3],  # Terrain type 2
            [0, 1, 2, 3],  # Terrain type 3
            [0, 1, 2, 3],  # Terrain type 4
            
            # Gene 6: Text position (rotation in degrees)
            {'low': 0, 'high': 360},

            # Gene 7: Text type (one_word_analysis, buy_sell_hold, latest_macd, high, low, market_outlook)
            [0, 1, 2, 3, 4, 5],
            
            # Gene 8: Base height (1-3)
            [1, 2, 3],
            
            # Gene 9: Size (small, medium, large)
            [0, 1, 2],
            # Gene10: Spiral turns (1-3)
            {'low': 3, 'high': 10}
        
        ]
        
        return gene_space

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

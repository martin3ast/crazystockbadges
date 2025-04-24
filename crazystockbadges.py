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
from solid import scad_render
import pygad


# Configure logging
logging.basicConfig(
    level=logging.WARN,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crazystockbadges.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('crazystockbadges')

init(autoreset=True)  # Initialize colorama for Text color on terminal output.

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
        self.parser.add_argument('--ga-generations', type=int, default=100,
                           help='Number of generations for the genetic algorithm (default: 100)')
        
        # Parse the arguments
        self.args = self.parser.parse_args()

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
        self.complexity_report = self._get_complexity_report(self.badge)
        print(f"{Fore.BLUE}... Badge complexity analysis complete!{Style.RESET_ALL}")

        output_file = self.args.output if self.args.output else "disc.scad"
        print(f"{Fore.BLUE}... Writing SCAD object to {output_file}...{Style.RESET_ALL}")

        
        #
        # Closing information
        #
        output_file = self.args.output if self.args.output else "disc.scad"
        
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
        logger.info("Generating 3D badge using genetic algorithm with complexity metrics")
        
        # Define gene space
        gene_space = self._create_gene_space()
        
        # Create pyGAD instance
        self.ga_instance = pygad.GA(
            num_generations=self.ga_generations,
            num_parents_mating=4,
            fitness_func=self.fitness_function,
            sol_per_pop=20,
            num_genes=len(gene_space),
            gene_space=gene_space,
            parent_selection_type="tournament",
            K_tournament=3,
            crossover_type="uniform",
            mutation_type="random",
            mutation_percent_genes=15,
            keep_elitism=2,
            on_generation=self._on_generation
        )
        
        # Run the genetic algorithm
        logger.info(f"Running genetic algorithm for {self.ga_generations} generations")
        self.ga_instance.run()
        
        # Get the best solution
        solution, solution_fitness, solution_idx = self.ga_instance.best_solution()
        logger.info(f"Best solution found with fitness: {solution_fitness:.2f}")
        
        # Get the best badge and complexity report
        best_badge, complexity_report, _ = self.ga_instance.badges[solution_idx]
        best_params = self.genes_to_badge_params(solution)
        
        # Store the complexity report for display
        self.complexity_report = complexity_report
        
        # Set text content to one-word summary if available
        if hasattr(self, 'one_word_summary'):
            logger.info(f"Setting badge text to sentiment summary: {self.one_word_summary}")
            best_params['text_content'] = self.one_word_summary
            
            # Regenerate the badge with the new text
            best_badge = BadgeFactory.create_badge(
                best_params['badge_type'], 
                self.mdm.data, 
                self.ticker, 
                best_params
            )
            best_badge.generate_base()
            best_badge.generate_terrain()
            best_badge.generate_text()
            best_badge.combine_models()
            
            # Update complexity report for the new badge
            self.complexity_report = self._get_complexity_report(best_badge)
        
        # Save the best badge
        output_file = self.args.output or "disc.scad"
        best_badge.save_to_file(output_file)
        
        # Store the results
        self.badge = best_badge
        self.badge_params = best_params
        self.badge_output_file = output_file
        
        # Log badge details
        logger.info(f"Badge generation complete. Output file: {output_file}")
        logger.info(f"Badge type: {best_params['badge_type']}")
        
        # Log terrain types
        if 'terrain_types' in best_params:
            terrain_types = best_params['terrain_types']
            terrain_weights = best_params['terrain_weights']
            logger.info(f"Terrain types: {', '.join(terrain_types)}")
            logger.info(f"Terrain weights: {', '.join([f'{w:.2f}' for w in terrain_weights])}")
        else:
            logger.info(f"Terrain type: {best_params.get('terrain_type', 'N/A')}")
        
        # Log complexity metrics
        logger.info(f"Complexity score: {self.complexity_report['complexity_score']:.2f}")
        logger.info(f"Total nodes: {self.complexity_report['total_nodes']}")
        logger.info(f"Max depth: {self.complexity_report['max_depth']}")

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
        elif text_type == 'high_low':
            return self.mdm.get_high_low()
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
        text_positions = ['bottom', 'top']
        
        # Get badge type
        badge_type_idx = int(genes[0])
        badge_type = badge_types[badge_type_idx]
        
        # Get number of terrain types to use
        num_terrain_types = int(genes[1])
        
        # Get terrain types (genes 2-7)
        terrain_types = []
        terrain_weights = []
        
        # Only use the first num_terrain_types terrain types
        for i in range(num_terrain_types):
            terrain_idx = int(genes[2 + i])
            terrain_types.append(all_terrain_types[terrain_idx])
            # Equal weights for now
            terrain_weights.append(1.0 / num_terrain_types)
        
        # Get text position
        text_position_idx = int(genes[8])
        text_position = text_positions[text_position_idx]
        
        # Get base height
        base_height = int(genes[9])
        
        # Get size parameter
        size_idx = int(genes[10])
        
        # Map size to badge-specific dimensions
        if badge_type == 'disc':
            # Small, medium, large disc sizes
            base_radius_map = [30, 50, 70]
            base_radius = base_radius_map[size_idx]
            spiral_turns = 5  # Default value
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
        
        # Create parameters dictionary
        params = {
            'badge_type': badge_type,
            'text_position': text_position,
            'base_height': base_height,
            'height_range': (0, 10),  # Default height range
            'width_range': (0, 10),   # Default width range
            'text_content': self.ticker,  # Default to ticker symbol
            'text_size': 10,  # Default text size
            'text_depth': 2   # Default text depth
        }
        
        # Add terrain types if multiple
        if len(terrain_types) > 1:
            params['terrain_types'] = terrain_types
            params['terrain_weights'] = terrain_weights
        else:
            # Single terrain type
            params['terrain_type'] = terrain_types[0]
        
        # Add badge-specific parameters
        if badge_type == 'disc':
            params['base_radius'] = base_radius
            params['spiral_turns'] = spiral_turns
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
        """
        params = self.genes_to_badge_params(solution)
        badge = BadgeFactory.create_badge(params['badge_type'], self.mdm.data, self.ticker, params)
        report = self._get_complexity_report(badge)
        
        ga_instance.population_stats = getattr(ga_instance, 'population_stats', [])
        ga_instance.population_stats.append(report)
        
        ga_instance.badges = getattr(ga_instance, 'badges', {})
        ga_instance.badges[solution_idx] = (badge, report, 0)
        
        # Process all solutions when the last one is evaluated
        # Get the population size from the sol_per_pop attribute instead of pop_size
        if solution_idx == ga_instance.sol_per_pop - 1:
            metrics = [
                'max_depth', 
                'total_nodes', 
                'complexity_score'
            ]
            
            min_values = {metric: min(s[metric] for s in ga_instance.population_stats) for metric in metrics}
            max_values = {metric: max(s[metric] for s in ga_instance.population_stats) for metric in metrics}
            
            # Ensure no division by zero
            for metric in metrics:
                if max_values[metric] == min_values[metric]:
                    max_values[metric] = min_values[metric] + 1
            
            # Calculate fitness for all solutions
            for i, report in enumerate(ga_instance.population_stats):
                normalized_metrics = {
                    metric: (report[metric] - min_values[metric]) / (max_values[metric] - min_values[metric])
                    for metric in metrics
                }
                
                weights = {
                    'max_depth': 0.30,
                    'total_nodes': 0.30,
                    'complexity_score': 0.40
                }
                
                fitness = sum(normalized_metrics[m] * weights[m] for m in metrics)
                
                badge, _, _ = ga_instance.badges[i]
                ga_instance.badges[i] = (badge, report, fitness)
                
                # Store the fitness value directly in the solution's fitness
                # We'll skip updating last_generation_fitness as it might not be initialized yet
            
            ga_instance.population_stats = []
            return ga_instance.badges[solution_idx][2]
        
        return 0


    def _get_complexity_report(self, badge):
        """
        Analyze the complexity of a badge model.
        
        Version 2.0: Cline refactor for Martin East - Added to support the new ComplexityAnalyzer class.
        """
        if badge.final_model is None:
            badge.combine_models()
            
        analyzer = ComplexityAnalyzer(badge.final_model)
        return analyzer.get_complexity_report()
        
    def _on_generation(self, ga_instance):
        """
        Callback function called after each generation.
        
        Attribution: Cline implementation for Martin East - Generation callback - Apr 17, 2025
        
        Args:
            ga_instance: The genetic algorithm instance
        """
        if ga_instance.generations_completed % 10 == 0:
            best_solution, best_fitness, _ = ga_instance.best_solution()
            logger.info(f"Generation {ga_instance.generations_completed}: Best fitness = {best_fitness:.2f}")


    def _create_gene_space(self):
        """
        Define simplified gene space for badge generation.
        
        Version 3.0: Cline refactor for Martin East - Simplified genotype - Apr 24, 2025.
        
        Returns:
            list: Gene space definition for pyGAD
        """
        # Define terrain types:
        # 0: spiral_chart
        # 1: bar_chart
        # 2: pyramid
        # 3: surface_plot
        # -1: not used (for terrain slots that aren't active)
        
        gene_space = [
            # Gene 0: Badge type (disc, rectangular, triangular)
            [0, 1, 2],
            
            # Gene 1: Number of terrain types to use (1-6)
            [1, 2, 3, 4, 5, 6],
            
            # Genes 2-7: Terrain types (up to 6 different types)
            # Each can be spiral_chart, bar_chart, pyramid, surface_plot
            [0, 1, 2, 3],  # Terrain type 1
            [0, 1, 2, 3],  # Terrain type 2
            [0, 1, 2, 3],  # Terrain type 3
            [0, 1, 2, 3],  # Terrain type 4
            [0, 1, 2, 3],  # Terrain type 5
            [0, 1, 2, 3],  # Terrain type 6
            
            # Gene 8: Text position (bottom, top)
            [0, 1],
            
            # Gene 9: Base height (1-3)
            [1, 2, 3],
            
            # Gene 10: Size (small, medium, large)
            [0, 1, 2]
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

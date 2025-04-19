#!/usr/bin/env python3
"""
Improved Crazy Stock Badges Main Application with pyGAD

This is the main application for the Crazy Stock Badges project, which integrates
all components to create 3D printable badges based on stock market data.
This version uses pyGAD for the genetic algorithm implementation.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for pyGAD genetic algorithm implementation - Apr 13, 2025.
"""

import os
import sys
import argparse
import logging
import time
import random
import numpy as np
import pandas as pd
from pathlib import Path

# Import pyGAD for genetic algorithm
try:
    import pygad
except ImportError:
    print("pyGAD is not installed. Please install it using: pip install pygad or conda install pygad")
    sys.exit(1)

# Import improved modules
from improved_cli import CrazyStockBadgeCLI
from improved_market_data import MarketDataManager
from improved_sentiment import StockReportAnalyzer, SentimentAnalyzer
from improved_3d_models import BadgeFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crazystockbadges_pygad.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('crazystockbadges_pygad')


# Global variables for pyGAD fitness function
stock_data = None
ticker_symbol = None


def create_gene_space():
    """
    Define the valid ranges for each gene.
    
    Each gene corresponds to a specific parameter of the badge:
    0: Badge type (0=disc, 1=rectangular, 2=triangular)
    1: Feature type (depends on badge type)
       - 0-1 for disc (jagged_edge, spiral)
       - 0-1 for rectangular (bar_chart, surface_plot)
       - 0-1 for triangular (pyramid, terrain)
    2: Text position (0=bottom, 1=top, 2=front)
    3: Text size (5-15)
    4: Text depth (1-3)
    5: Base height (2-5)
    6: Feature height (5-20)
    7: Height range max (10-20)
    8: Width range max (5-15)
    9: Base radius for disc (30-70)
    10: Spiral turns for disc (3-10)
    11: Base width for rectangular (60-120)
    12: Base depth for rectangular (40-80)
    13: Side length for triangular (60-100)
    
    Returns:
        list: Gene space definition for pyGAD
    """
    gene_space = [
        # Gene 0: Badge type (0=disc, 1=rectangular, 2=triangular)
        [0, 1, 2],
        
        # Gene 1: Feature type (depends on badge type)
        # 0-1 for disc (jagged_edge, spiral)
        # 0-1 for rectangular (bar_chart, surface_plot)
        # 0-1 for triangular (pyramid, terrain)
        [0, 1],
        
        # Gene 2: Text position (0=bottom, 1=top, 2=front)
        [0, 1, 2],
        
        # Gene 3: Text size (5-15)
        {'low': 5, 'high': 15},
        
        # Gene 4: Text depth (1-3)
        {'low': 1, 'high': 3},
        
        # Gene 5: Base height (2-5)
        {'low': 2, 'high': 5},
        
        # Gene 6: Feature height (5-20)
        {'low': 5, 'high': 20},
        
        # Gene 7: Height range max (10-20)
        {'low': 10, 'high': 20},
        
        # Gene 8: Width range max (5-15)
        {'low': 5, 'high': 15},
        
        # Gene 9: Base radius for disc (30-70)
        {'low': 30, 'high': 70},
        
        # Gene 10: Spiral turns for disc (3-10)
        {'low': 3, 'high': 10},
        
        # Gene 11: Base width for rectangular (60-120)
        {'low': 60, 'high': 120},
        
        # Gene 12: Base depth for rectangular (40-80)
        {'low': 40, 'high': 80},
        
        # Gene 13: Side length for triangular (60-100)
        {'low': 60, 'high': 100}
    ]
    
    return gene_space


def genes_to_badge_params(genes):
    """
    Convert genes array to badge parameters dictionary.
    
    Args:
        genes (list): List of gene values
        
    Returns:
        dict: Badge parameters
    """
    # Define badge types and features
    badge_types = ['disc', 'rectangular', 'triangular']
    feature_types = {
        'disc': ['jagged_edge', 'spiral'],
        'rectangular': ['bar_chart', 'surface_plot'],
        'triangular': ['pyramid', 'terrain']
    }
    text_positions = ['bottom', 'top', 'front']
    
    # Get badge type
    badge_type_idx = int(genes[0])
    badge_type = badge_types[badge_type_idx]
    
    # Get feature type based on badge type
    feature_type_idx = int(genes[1])
    feature_type = feature_types[badge_type][feature_type_idx]
    
    # Get text position
    text_position_idx = int(genes[2])
    text_position = text_positions[text_position_idx]
    
    # Create parameters dictionary
    params = {
        'badge_type': badge_type,
        'feature_type': feature_type,
        'text_position': text_position,
        'text_content': ticker_symbol,
        'text_size': genes[3],
        'text_depth': genes[4],
        'base_height': genes[5],
        'feature_height': genes[6],
        'height_range': (0, genes[7]),
        'width_range': (0, genes[8])
    }
    
    # Add badge-specific parameters
    if badge_type == 'disc':
        params['base_radius'] = genes[9]
        params['spiral_turns'] = int(genes[10])
    elif badge_type == 'rectangular':
        params['base_width'] = genes[11]
        params['base_depth'] = genes[12]
    elif badge_type == 'triangular':
        params['side_length'] = genes[13]
    
    return params


def fitness_function(ga_instance, solution, solution_idx):
    """
    Fitness function for pyGAD with dynamic min-max normalization.
    
    Args:
        ga_instance: The genetic algorithm instance
        solution: The solution to calculate fitness for (gene array)
        solution_idx: The index of the solution in the population
        
    Returns:
        float: The fitness value
    """
    # Convert solution (genes) to badge parameters
    params = genes_to_badge_params(solution)
    
    # Create badge and calculate stats
    badge = BadgeFactory.create_badge(
        params['badge_type'], 
        stock_data,
        ticker_symbol,
        params
    )
    
    # Generate the model to calculate stats
    badge.generate_base()
    badge.generate_feature()
    badge.generate_text()
    badge.combine_models()
    
    # Calculate stats
    stats = badge.calculate_stats()
    
    # Get the scaling factor
    scaling_factor = params['height_range'][1]
    
    # Extract raw statistics
    num_objects = stats['num_objects']
    depth_diff = stats['depth_diff']
    width_diff = stats['width_diff']
    height_diff = stats['height_diff']
    
    # Store the badge and stats for later retrieval and normalization
    if not hasattr(ga_instance, 'population_stats'):
        ga_instance.population_stats = []
    
    # Add current stats to population stats
    current_stats = {
        'num_objects': num_objects,
        'depth_diff': depth_diff,
        'width_diff': width_diff,
        'height_diff': height_diff,
        'scaling_factor': scaling_factor
    }
    ga_instance.population_stats.append(current_stats)
    
    # Store the badge for later retrieval
    if not hasattr(ga_instance, 'badges'):
        ga_instance.badges = {}
    ga_instance.badges[solution_idx] = (badge, stats, 0)  # Placeholder fitness
    
    # If this is the last solution in the population, normalize and update all fitness values
    if solution_idx == ga_instance.pop_size - 1:
        # Calculate min-max values from the population
        min_objects = min(s['num_objects'] for s in ga_instance.population_stats)
        max_objects = max(s['num_objects'] for s in ga_instance.population_stats)
        min_depth = min(s['depth_diff'] for s in ga_instance.population_stats)
        max_depth = max(s['depth_diff'] for s in ga_instance.population_stats)
        min_width = min(s['width_diff'] for s in ga_instance.population_stats)
        max_width = max(s['width_diff'] for s in ga_instance.population_stats)
        min_height = min(s['height_diff'] for s in ga_instance.population_stats)
        max_height = max(s['height_diff'] for s in ga_instance.population_stats)
        
        # Ensure no division by zero
        max_objects = max(max_objects, min_objects + 1)
        max_depth = max(max_depth, min_depth + 1)
        max_width = max(max_width, min_width + 1)
        max_height = max(max_height, min_height + 1)
        
        # Calculate fitness for all solutions
        for i, stats in enumerate(ga_instance.population_stats):
            # Normalize each statistic to [0, 1]
            norm_objects = (stats['num_objects'] - min_objects) / (max_objects - min_objects)
            norm_depth = (stats['depth_diff'] - min_depth) / (max_depth - min_depth)
            norm_width = (stats['width_diff'] - min_width) / (max_width - min_width)
            norm_height = (stats['height_diff'] - min_height) / (max_height - min_height)
            
            # Sum the normalized values
            normalized_sum = norm_objects + norm_depth + norm_width + norm_height
            
            # Calculate final fitness by multiplying by scaling factor
            fitness = normalized_sum * stats['scaling_factor']
            
            # Update the fitness value in badges
            badge, badge_stats, _ = ga_instance.badges[i]
            ga_instance.badges[i] = (badge, badge_stats, fitness)
            
            # Update the solution's fitness in the GA instance
            ga_instance.pop_fitness[i] = fitness
        
        # Clear population stats for the next generation
        ga_instance.population_stats = []
        
        # Return the fitness for the current solution
        return ga_instance.badges[solution_idx][2]
    
    # For all but the last solution, return a placeholder
    # The actual fitness will be calculated when the last solution is evaluated
    return 0


def on_generation(ga_instance):
    """
    Callback function called after each generation.
    
    Args:
        ga_instance: The genetic algorithm instance
    """
    if ga_instance.generations_completed % 10 == 0:
        best_solution, best_fitness, _ = ga_instance.best_solution()
        logger.info(f"Generation {ga_instance.generations_completed}: Best fitness = {best_fitness:.2f}")


class CrazyStockBadges:
    """
    Main application class for Crazy Stock Badges.
    
    Version 1.0 - Cline implementation for Martin East - Integrates all components with pyGAD genetic algorithm - Apr 13, 2025.
    """
    
    def __init__(self):
        """Initialize the application."""
        self.cli = CrazyStockBadgeCLI()
        self.market_data_manager = MarketDataManager()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.report_analyzer = StockReportAnalyzer(self.sentiment_analyzer)
    
    def run(self, args=None):
        """
        Run the application.
        
        Args:
            args (list): Command-line arguments
        """
        # Parse arguments
        self.cli.parse_args(args)
        
        # Run the CLI
        self.cli.run()
        
        # Get ticker symbol from CLI
        ticker = self.cli.args.ticker
        
        # Fetch and analyze market data
        self._fetch_and_analyze_market_data(ticker)
        
        # Generate and analyze report
        if not self.cli.args.skip_report:
            self._generate_and_analyze_report()
        
        # Generate badge
        self._generate_badge()
    
    def _fetch_and_analyze_market_data(self, ticker):
        """
        Fetch and analyze market data.
        
        Args:
            ticker (str): Stock ticker symbol
        """
        logger.info(f"Fetching and analyzing market data for {ticker}")
        
        try:
            # Fetch data
            self.market_data = self.market_data_manager.fetch_stock_data(ticker, self.cli.args.period)
            
            # Perform technical analysis
            self.market_data = self.market_data_manager.perform_technical_analysis()
            
            # Get summary stats
            self.market_stats = self.market_data_manager.get_summary_stats()
            
            # Plot data
            self.plot_path = self.market_data_manager.plot_stock_data()
            
            logger.info("Market data analysis complete")
        except Exception as e:
            logger.error(f"Error fetching and analyzing market data: {e}")
            raise
    
    def _generate_and_analyze_report(self):
        """Generate and analyze stock report."""
        logger.info("Generating and analyzing stock report")
        
        try:
            # Generate report
            self.report = self.market_data_manager.generate_report()
            
            # Analyze report
            self.report_analysis = self.report_analyzer.analyze_report(report_text=self.report)
            
            # Save analysis
            self.report_analyzer.save_analysis(self.report_analysis)
            
            # Get one-word summary
            self.one_word_summary = self.report_analysis['one_word_summary']
            
            logger.info("Report generation and analysis complete")
        except Exception as e:
            logger.error(f"Error generating and analyzing report: {e}")
            raise
    
    def _generate_badge(self):
        """Generate 3D badge using pyGAD genetic algorithm."""
        logger.info("Generating 3D badge using pyGAD")
        
        try:
            # Set global variables for fitness function
            global stock_data, ticker_symbol
            stock_data = self.market_data
            ticker_symbol = self.cli.args.ticker
            
            # Define gene space
            gene_space = create_gene_space()
            
            # Create pyGAD instance
            ga_instance = pygad.GA(
                num_generations=self.cli.args.ga_generations,
                num_parents_mating=4,
                fitness_func=fitness_function,
                sol_per_pop=20,
                num_genes=len(gene_space),
                gene_space=gene_space,
                parent_selection_type="tournament",
                K_tournament=3,
                crossover_type="uniform",
                mutation_type="random",
                mutation_percent_genes=10,
                keep_elitism=1,
                on_generation=on_generation
            )
            
            # Run the genetic algorithm
            logger.info(f"Running genetic algorithm for {self.cli.args.ga_generations} generations")
            ga_instance.run()
            
            # Get the best solution
            solution, solution_fitness, solution_idx = ga_instance.best_solution()
            logger.info(f"Best solution found with fitness: {solution_fitness:.2f}")
            
            # Get the best badge and stats
            best_badge, best_stats, _ = ga_instance.badges[solution_idx]
            best_params = genes_to_badge_params(solution)
            
            # Set text content to one-word summary if available
            if hasattr(self, 'one_word_summary'):
                logger.info(f"Setting badge text to sentiment summary: {self.one_word_summary}")
                best_params['text_content'] = self.one_word_summary
                
                # Regenerate the badge with the new text
                best_badge = BadgeFactory.create_badge(
                    best_params['badge_type'], 
                    self.market_data, 
                    self.cli.args.ticker, 
                    best_params
                )
                best_badge.generate_base()
                best_badge.generate_feature()
                best_badge.generate_text()
                best_badge.combine_models()
            
            # Save the best badge
            output_file = self.cli.args.output or "disc.scad"
            best_badge.save_to_file(output_file)
            
            # Store the results
            self.badge_params = best_params
            self.badge_stats = best_stats
            self.badge_output_file = output_file
            
            # Log badge details
            logger.info(f"Badge generation complete. Output file: {output_file}")
            logger.info(f"Badge type: {best_params['badge_type']}")
            logger.info(f"Feature type: {best_params['feature_type']}")
            logger.info(f"Stats: {best_stats}")
        except Exception as e:
            logger.error(f"Error generating badge: {e}")
            raise


def main():
    """Main entry point for the application."""
    try:
        app = CrazyStockBadges()
        app.run()
        return 0
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

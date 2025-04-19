#!/usr/bin/env python3
"""
Improved Crazy Stock Badges Main Application

This is the main application for the Crazy Stock Badges project, which integrates
all components to create 3D printable badges based on stock market data.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for main application integration - Apr 13, 2025.
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
        logging.FileHandler("crazystockbadges.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('crazystockbadges')


class GeneticAlgorithm:
    """
    Genetic Algorithm implementation for optimizing badge designs.
    
    Version 1.0 - Cline implementation for Martin East - Implements genetic algorithm for badge optimization - Apr 13, 2025.
    """
    
    def __init__(self, stock_data, ticker_symbol, population_size=20, generations=100):
        """
        Initialize the genetic algorithm.
        
        Args:
            stock_data (pandas.DataFrame): Stock data
            ticker_symbol (str): Stock ticker symbol
            population_size (int): Size of the population
            generations (int): Number of generations to run
        """
        self.stock_data = stock_data
        self.ticker_symbol = ticker_symbol
        self.population_size = population_size
        self.generations = generations
        
        # Available badge types and features
        self.badge_types = ['disc', 'rectangular', 'triangular']
        self.feature_types = {
            'disc': ['jagged_edge', 'spiral'],
            'rectangular': ['bar_chart', 'surface_plot'],
            'triangular': ['pyramid', 'terrain']
        }
        self.text_positions = ['bottom', 'top', 'front']
        
        # Initialize population
        self.population = self._initialize_population()
        self.best_individual = None
        self.best_fitness = -float('inf')
    
    def _initialize_population(self):
        """
        Initialize a random population of badge designs.
        
        Returns:
            list: List of badge design parameters
        """
        population = []
        
        for _ in range(self.population_size):
            # Select random badge type
            badge_type = random.choice(self.badge_types)
            
            # Select random feature type for the badge type
            feature_type = random.choice(self.feature_types[badge_type])
            
            # Generate random parameters
            params = {
                'badge_type': badge_type,
                'feature_type': feature_type,
                'text_position': random.choice(self.text_positions),
                'text_content': self.ticker_symbol,
                'text_size': random.uniform(5, 15),
                'text_depth': random.uniform(1, 3),
                'base_height': random.uniform(2, 5),
                'feature_height': random.uniform(5, 20),
                'height_range': (0, random.uniform(10, 20)),
                'width_range': (0, random.uniform(5, 15))
            }
            
            # Add badge-specific parameters
            if badge_type == 'disc':
                params['base_radius'] = random.uniform(30, 70)
                params['spiral_turns'] = random.randint(3, 10)
            elif badge_type == 'rectangular':
                params['base_width'] = random.uniform(60, 120)
                params['base_depth'] = random.uniform(40, 80)
            elif badge_type == 'triangular':
                params['side_length'] = random.uniform(60, 100)
            
            population.append(params)
        
        return population
    
    def _calculate_fitness(self, params):
        """
        Calculate fitness for a set of badge parameters.
        
        Args:
            params (dict): Badge parameters
            
        Returns:
            float: Fitness score
        """
        # Create a badge with the parameters
        badge = BadgeFactory.create_badge(
            params['badge_type'], 
            self.stock_data, 
            self.ticker_symbol, 
            params
        )
        
        # Generate the model to calculate stats
        badge.generate_base()
        badge.generate_feature()
        badge.generate_text()
        badge.combine_models()
        
        # Calculate stats
        stats = badge.calculate_stats()
        
        # Calculate fitness based on the stats
        # The formula is: num_objects * scaling_factor + depth_diff + width_diff + height_diff
        # We'll use the height_range max as the scaling factor
        scaling_factor = params['height_range'][1]
        
        fitness = (
            stats['num_objects'] * scaling_factor + 
            stats['depth_diff'] + 
            stats['width_diff'] + 
            stats['height_diff']
        )
        
        return fitness, stats, badge
    
    def _select_parents(self, fitnesses):
        """
        Select parents for reproduction using tournament selection.
        
        Args:
            fitnesses (list): List of fitness scores
            
        Returns:
            tuple: Indices of selected parents
        """
        # Tournament selection
        tournament_size = 3
        
        # Select first parent
        tournament1 = random.sample(range(len(fitnesses)), tournament_size)
        parent1 = max(tournament1, key=lambda i: fitnesses[i])
        
        # Select second parent
        tournament2 = random.sample(range(len(fitnesses)), tournament_size)
        parent2 = max(tournament2, key=lambda i: fitnesses[i])
        
        return parent1, parent2
    
    def _crossover(self, parent1, parent2):
        """
        Perform crossover between two parents.
        
        Args:
            parent1 (dict): First parent parameters
            parent2 (dict): Second parent parameters
            
        Returns:
            dict: Child parameters
        """
        # Create a new child with parameters from both parents
        child = {}
        
        # Inherit badge type from one parent
        if random.random() < 0.5:
            child['badge_type'] = parent1['badge_type']
            # Inherit feature type compatible with badge type
            child['feature_type'] = parent1['feature_type']
        else:
            child['badge_type'] = parent2['badge_type']
            # Inherit feature type compatible with badge type
            child['feature_type'] = parent2['feature_type']
        
        # Inherit other parameters with random crossover
        for key in set(parent1.keys()) | set(parent2.keys()):
            if key in ['badge_type', 'feature_type']:
                continue  # Already handled
                
            # Skip parameters that don't apply to this badge type
            if (child['badge_type'] == 'disc' and key in ['base_width', 'base_depth', 'side_length']) or \
               (child['badge_type'] == 'rectangular' and key in ['base_radius', 'spiral_turns', 'side_length']) or \
               (child['badge_type'] == 'triangular' and key in ['base_radius', 'spiral_turns', 'base_width', 'base_depth']):
                continue
            
            # Inherit from one parent or the other
            if key in parent1 and key in parent2:
                if isinstance(parent1[key], (int, float)) and isinstance(parent2[key], (int, float)):
                    # For numeric values, use a weighted average
                    weight = random.random()
                    child[key] = weight * parent1[key] + (1 - weight) * parent2[key]
                elif isinstance(parent1[key], tuple) and isinstance(parent2[key], tuple):
                    # For tuples (like ranges), mix the values
                    child[key] = (
                        (parent1[key][0] + parent2[key][0]) / 2,
                        (parent1[key][1] + parent2[key][1]) / 2
                    )
                else:
                    # For other types, choose one parent
                    child[key] = parent1[key] if random.random() < 0.5 else parent2[key]
            elif key in parent1:
                child[key] = parent1[key]
            else:
                child[key] = parent2[key]
        
        # Add badge-specific parameters if missing
        if child['badge_type'] == 'disc' and 'base_radius' not in child:
            child['base_radius'] = random.uniform(30, 70)
            child['spiral_turns'] = random.randint(3, 10)
        elif child['badge_type'] == 'rectangular' and 'base_width' not in child:
            child['base_width'] = random.uniform(60, 120)
            child['base_depth'] = random.uniform(40, 80)
        elif child['badge_type'] == 'triangular' and 'side_length' not in child:
            child['side_length'] = random.uniform(60, 100)
        
        return child
    
    def _mutate(self, individual):
        """
        Mutate an individual.
        
        Args:
            individual (dict): Individual parameters
            
        Returns:
            dict: Mutated individual
        """
        # Clone the individual
        mutated = individual.copy()
        
        # Mutation probability
        mutation_prob = 0.2
        
        # Potentially mutate badge type
        if random.random() < mutation_prob:
            old_badge_type = mutated['badge_type']
            mutated['badge_type'] = random.choice(self.badge_types)
            
            # If badge type changed, update feature type and badge-specific parameters
            if mutated['badge_type'] != old_badge_type:
                mutated['feature_type'] = random.choice(self.feature_types[mutated['badge_type']])
                
                # Add badge-specific parameters
                if mutated['badge_type'] == 'disc':
                    mutated['base_radius'] = random.uniform(30, 70)
                    mutated['spiral_turns'] = random.randint(3, 10)
                    # Remove incompatible parameters
                    mutated.pop('base_width', None)
                    mutated.pop('base_depth', None)
                    mutated.pop('side_length', None)
                elif mutated['badge_type'] == 'rectangular':
                    mutated['base_width'] = random.uniform(60, 120)
                    mutated['base_depth'] = random.uniform(40, 80)
                    # Remove incompatible parameters
                    mutated.pop('base_radius', None)
                    mutated.pop('spiral_turns', None)
                    mutated.pop('side_length', None)
                elif mutated['badge_type'] == 'triangular':
                    mutated['side_length'] = random.uniform(60, 100)
                    # Remove incompatible parameters
                    mutated.pop('base_radius', None)
                    mutated.pop('spiral_turns', None)
                    mutated.pop('base_width', None)
                    mutated.pop('base_depth', None)
        
        # Potentially mutate feature type
        if random.random() < mutation_prob:
            mutated['feature_type'] = random.choice(self.feature_types[mutated['badge_type']])
        
        # Potentially mutate text position
        if random.random() < mutation_prob:
            mutated['text_position'] = random.choice(self.text_positions)
        
        # Potentially mutate numeric parameters
        for key, value in mutated.items():
            if isinstance(value, (int, float)) and random.random() < mutation_prob:
                # Mutate by adding or subtracting a random value
                if key == 'text_size':
                    mutated[key] = max(5, min(15, value + random.uniform(-2, 2)))
                elif key == 'text_depth':
                    mutated[key] = max(1, min(3, value + random.uniform(-0.5, 0.5)))
                elif key == 'base_height':
                    mutated[key] = max(2, min(5, value + random.uniform(-0.5, 0.5)))
                elif key == 'feature_height':
                    mutated[key] = max(5, min(20, value + random.uniform(-3, 3)))
                elif key == 'base_radius':
                    mutated[key] = max(30, min(70, value + random.uniform(-10, 10)))
                elif key == 'spiral_turns':
                    mutated[key] = max(3, min(10, int(value + random.randint(-2, 2))))
                elif key == 'base_width':
                    mutated[key] = max(60, min(120, value + random.uniform(-10, 10)))
                elif key == 'base_depth':
                    mutated[key] = max(40, min(80, value + random.uniform(-10, 10)))
                elif key == 'side_length':
                    mutated[key] = max(60, min(100, value + random.uniform(-10, 10)))
            elif isinstance(value, tuple) and random.random() < mutation_prob:
                # Mutate ranges
                if key == 'height_range':
                    mutated[key] = (0, max(10, min(20, value[1] + random.uniform(-3, 3))))
                elif key == 'width_range':
                    mutated[key] = (0, max(5, min(15, value[1] + random.uniform(-2, 2))))
        
        return mutated
    
    def run(self, callback=None):
        """
        Run the genetic algorithm.
        
        Args:
            callback (function): Optional callback function to report progress
            
        Returns:
            tuple: Best individual, fitness, stats, and badge
        """
        for generation in range(self.generations):
            # Calculate fitness for each individual
            fitnesses = []
            stats_list = []
            badges = []
            
            for i, individual in enumerate(self.population):
                fitness, stats, badge = self._calculate_fitness(individual)
                fitnesses.append(fitness)
                stats_list.append(stats)
                badges.append(badge)
                
                # Update best individual
                if fitness > self.best_fitness:
                    self.best_fitness = fitness
                    self.best_individual = individual.copy()
                    self.best_stats = stats
                    self.best_badge = badge
            
            # Report progress
            if callback:
                callback(generation, self.best_individual, self.best_fitness, self.best_stats)
            
            # Create new population
            new_population = []
            
            # Elitism: keep the best individual
            new_population.append(self.best_individual.copy())
            
            # Create the rest of the population through selection, crossover, and mutation
            while len(new_population) < self.population_size:
                # Select parents
                parent1_idx, parent2_idx = self._select_parents(fitnesses)
                parent1 = self.population[parent1_idx]
                parent2 = self.population[parent2_idx]
                
                # Crossover
                child = self._crossover(parent1, parent2)
                
                # Mutation
                child = self._mutate(child)
                
                # Add to new population
                new_population.append(child)
            
            # Replace old population
            self.population = new_population
        
        # Return the best individual
        return self.best_individual, self.best_fitness, self.best_stats, self.best_badge


class CrazyStockBadges:
    """
    Main application class for Crazy Stock Badges.
    
    Version 1.0 - Cline implementation for Martin East - Integrates all components into main application - Apr 13, 2025.
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
        """Generate 3D badge using genetic algorithm."""
        logger.info("Generating 3D badge")
        
        try:
            # Run genetic algorithm to find the best badge design
            ga = GeneticAlgorithm(
                self.market_data, 
                self.cli.args.ticker, 
                generations=self.cli.args.ga_generations
            )
            
            # Progress callback
            def progress_callback(generation, best_individual, best_fitness, best_stats):
                if generation % 10 == 0:
                    logger.info(f"Generation {generation}: Best fitness = {best_fitness:.2f}")
            
            # Run the genetic algorithm
            best_params, best_fitness, best_stats, best_badge = ga.run(callback=progress_callback)
            
            # Set text content to one-word summary if available
            if hasattr(self, 'one_word_summary'):
                best_params['text_content'] = self.one_word_summary
            
            # Save the best badge
            output_file = self.cli.args.output or "disc.scad"
            best_badge.save_to_file(output_file)
            
            # Store the results
            self.badge_params = best_params
            self.badge_stats = best_stats
            self.badge_output_file = output_file
            
            logger.info(f"Badge generation complete. Output file: {output_file}")
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

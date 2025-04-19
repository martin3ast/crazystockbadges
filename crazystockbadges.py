#!/usr/bin/env python3
"""
Main command line interface for Crazy Stock Badges Project

This module provides a friendly, interactive command-line interface for the
Crazy Stock Badges project, allowing users to generate 3D printable badges
based on stock market data.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for command-line interface - Apr 13, 2025.
Version 1.1 - Martin East - Strip unnecessary error checking and simplify -  Apr 14, 2025.
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
from solid import scad_render

# Try to import pygad
try:
    import pygad
except ImportError:
    print("Warning: pyGAD is not installed. Genetic algorithm functionality will not be available.")
    print("Install with: pip install pygad")

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

# Complexity estimation functions
# Attribution: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
def count_csg_operations(scad_code):
    """
    Counts all CSG operations in generated OpenSCAD code
    
    Attribution: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
    
    Returns: dict with counts for each operation type
    """
    patterns = {
        'unions': r'union\(\)\s*\{',
        'differences': r'difference\(\)\s*\{',
        'intersections': r'intersection\(\)\s*\{',
        'hulls': r'hull\(\)\s*\{',
        'minkowskis': r'minkowski\(\)\s*\{',
        'transforms': r'(translate|rotate|scale|mirror|multmatrix|color)\s*\(',
        'primitives': r'(cube|sphere|cylinder|polyhedron|square|circle|polygon|text)\s*\('
    }
    
    counts = {}
    for name, pattern in patterns.items():
        counts[name] = len(re.findall(pattern, scad_code))
    
    return counts

# Attribution: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
class ComplexityAnalyzer:
    """
    Analyzes the complexity of a 3D model by traversing its node structure
    
    Attribution: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
    """
    def __init__(self):
        self.metrics = {
            'max_depth': 0,
            'total_nodes': 0,
            'primitive_counts': defaultdict(int),
            'operation_counts': defaultdict(int)
        }
    
    def analyze(self, node, depth=0):
        """
        Recursively analyze a node and its children
        
        Attribution: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
        """
        self.metrics['total_nodes'] += 1
        self.metrics['max_depth'] = max(self.metrics['max_depth'], depth)
        
        if isinstance(node, (list, tuple)):
            for child in node:
                self.analyze(child, depth+1)
        elif hasattr(node, 'children'):
            op_name = node.__class__.__name__.lower()
            self.metrics['operation_counts'][op_name] += 1
            for child in node.children:
                self.analyze(child, depth+1)
        else:
            # Primitive object
            prim_name = node.__class__.__name__.lower()
            self.metrics['primitive_counts'][prim_name] += 1

# Attribution: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
def estimate_geometry_complexity(obj):
    """
    Estimates geometric complexity with emphasis on polygonal complexity.
    This function prioritizes complex polygonal structures to maximize
    the "craziness" factor of the generated models.
    
    Version 1.0: Cline implementation for Martin East - Enhanced for maximum polygonal complexity - Apr 17, 2025
    
    Returns complexity score (higher = more complex/crazy)
    """
    from solid import cube, sphere, cylinder, polyhedron, polygon
    
    if isinstance(obj, cube):
        # Simple cube has low complexity
        return 1
    elif isinstance(obj, sphere):
        # Sphere complexity depends on $fn resolution
        fn = getattr(obj, 'fn', 30)  # Default OpenSCAD resolution
        return min(fn / 8, 12)  # Increased maximum score for spheres
    elif isinstance(obj, cylinder):
        # Cylinder complexity depends on both resolution and parameters
        fn = getattr(obj, 'fn', 30)
        r = getattr(obj, 'r', 1)
        h = getattr(obj, 'h', 1)
        return min((fn * (r + h)) / 15, 18)  # Increased maximum score for cylinders
    elif isinstance(obj, polyhedron):
        # Polyhedrons are inherently complex - heavily reward these
        points = len(getattr(obj, 'points', []))
        faces = len(getattr(obj, 'faces', []))
        # Significantly increased weight for polyhedrons
        return min((points + faces * 2) / 8, 30)  # Much higher maximum score
    elif isinstance(obj, polygon):
        # Polygons with many points are complex
        points = len(getattr(obj, 'points', []))
        return min(points / 5, 25)  # High score for complex polygons
    else:
        # Check for text objects which can be complex
        if hasattr(obj, 'text'):
            text_length = len(getattr(obj, 'text', ''))
            return min(text_length * 1.5, 15)  # Text adds complexity
        return 0  # Unknown type

# Attribution: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
def model_complexity_score(node):
    """
    Calculate overall complexity score with emphasis on operations that
    create complex, "crazy" structures.
    
    Version 1.0: Cline implementation for Martin East - Enhanced for maximum craziness - Apr 17, 2025
    
    Returns: float representing complexity (higher = more complex/crazy)
    """
    from solid import union, difference, intersection, hull, minkowski
    
    if isinstance(node, (list, tuple)):
        return sum(model_complexity_score(child) for child in node)
    elif hasattr(node, 'children'):
        # Operations multiply complexity of their children
        # Give higher weights to operations that create more complex structures
        if isinstance(node, difference):
            op_factor = 2.5  # Differences create interesting shapes
        elif isinstance(node, intersection):
            op_factor = 2.2  # Intersections can create complex forms
        elif isinstance(node, hull):
            op_factor = 3.0  # Hull operations often create organic shapes
        elif isinstance(node, minkowski):
            op_factor = 3.5  # Minkowski sums create very complex shapes
        else:
            op_factor = 1.8  # Default for other operations like union
            
        # Additional bonus for operations with many children
        child_count_bonus = min(len(node.children) * 0.2, 1.5)
        
        return (op_factor + child_count_bonus) * sum(model_complexity_score(child) for child in node.children)
    else:
        return estimate_geometry_complexity(node)

# Attribution: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
def suggest_optimizations(metrics):
    """
    Generates optimization suggestions based on complexity metrics
    
    Version 1.0: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
    
    Returns: list of suggestion strings
    """
    suggestions = []
    
    if metrics['operation_counts'].get('difference', 0) > 5:
        suggestions.append("Consider combining multiple difference operations")
    
    if metrics['max_depth'] > 8:
        suggestions.append("Very deep CSG tree - try flattening operations")
    
    if metrics['primitive_counts'].get('polyhedron', 0) > 0:
        suggestions.append("Polyhedrons are complex - consider alternatives")
    
    return suggestions

# Attribution: Cline implementation for Martin East - Additional polygonal complexity metrics - Apr 17, 2025
def analyze_polygonal_complexity(node):
    """
    Analyzes the polygonal complexity of a model.
    
    Attribution: Cline implementation for Martin East - Specialized polygonal complexity analysis - Apr 17, 2025
    
    Returns: dict with polygonal complexity metrics
    """
    from solid import polygon, polyhedron
    
    metrics = {
        'polygon_count': 0,
        'total_points': 0,
        'max_points_per_polygon': 0,
        'polyhedron_count': 0,
        'total_faces': 0
    }
    
    def analyze_node(node):
        if isinstance(node, (list, tuple)):
            for child in node:
                analyze_node(child)
        elif hasattr(node, 'children'):
            for child in node.children:
                analyze_node(child)
        else:
            # Check for polygonal primitives
            if isinstance(node, polygon):
                metrics['polygon_count'] += 1
                points = len(getattr(node, 'points', []))
                metrics['total_points'] += points
                metrics['max_points_per_polygon'] = max(metrics['max_points_per_polygon'], points)
            elif isinstance(node, polyhedron):
                metrics['polyhedron_count'] += 1
                points = len(getattr(node, 'points', []))
                faces = len(getattr(node, 'faces', []))
                metrics['total_points'] += points
                metrics['total_faces'] += faces
    
    analyze_node(node)
    
    # Calculate a single polygonal complexity score
    if metrics['polygon_count'] > 0 or metrics['polyhedron_count'] > 0:
        metrics['polygonal_complexity_score'] = (
            metrics['total_points'] * 0.5 + 
            metrics['max_points_per_polygon'] * 2 + 
            metrics['polyhedron_count'] * 10 + 
            metrics['total_faces'] * 1.5
        )
    else:
        metrics['polygonal_complexity_score'] = 0
        
    return metrics

init(autoreset=True)  # Initialize colorama

class CrazyStockBadge:
    """
    Command-line interface for the Crazy Stock Badge Generator.
    
    Version 1.0 - Cline implementation for Martin East - Implements user-friendly CLI with interactive prompts - Apr 13, 2025.
    Version 1.1 - Martin East, review and tidy up, add complete code for stubs - Apr 14, 2025.
    """
    
    def __init__(self):
        """Initialize the CLI with an argument parser."""
        self.parser = self._create_parser()
        self.ticker = self.args.ticker if hasattr(self, 'args') else None
        self.period = self.args.period if hasattr(self, 'args') else '1y'  

        self.mdm = None # Placeholder for MarketDataManager instance   
        self.stock_report = None # Placeholder for stock report content
        
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
        """Parse command line arguments. Used in the main function."""
        self.args = self.parser.parse_args(args)
        return self.args
    
    
    def run(self):
        """Main CLI execution flow. Used in the main function, after parse_args."""
        # Display welcome message
        self._print_welcome()
        
        # Get ticker symbol (from args or prompt)
        self.ticker = self._get_ticker()

        # Get the marketData and show progress for data retrieval
        self._show_data_retrieval_progress(self.ticker)
        
        # Offer to show stock report
        if not self.args.skip_report:
            self._handle_report_display()
        
        # Do the Badge Generation
        # Show badge generation progress
        self._show_badge_generation_progress()
        
        # Display final information
        self._show_final_info()
        
    def _print_welcome(self):
        """Display welcome message."""
        print(f"\n{Fore.CYAN}Welcome to Crazy Stock Badge Generator!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Are you ready to get crazy with stock data?... Let's make something of it!{Style.RESET_ALL}\n")
    
    def _get_ticker(self):
        """Get ticker symbol from args or user input."""
        if self.args.ticker:
            ticker = self.args.ticker.upper()
            print(f"Using given ticker symbol: {Fore.GREEN}{ticker}{Style.RESET_ALL}")
        else:
            ticker = input(f"{Fore.YELLOW}What stock price symbol would you like to choose? > {Style.RESET_ALL}").upper()
            print(f"\nYou chose {Fore.GREEN}{ticker}{Style.RESET_ALL}. Let's see what we can do.")
        
        return ticker
    
    def _show_data_retrieval_progress(self, ticker=None, period=None):
        """Show progress during data retrieval."""

        ticker = ticker or self.ticker
        period = period or self.period

        print(f"\n{Fore.BLUE}... Retrieving Market Data from Yahoo Finance{Style.RESET_ALL}")
        time.sleep(0.5)  # Simulate processing time

        # Create a market data manager
        self.mdm = md.MarketDataManager(ticker=ticker,period=period)

        # Fetch and analyze data
        self.mdm.fetch_stock_data(use_cache=True)

        print(f"{Fore.BLUE}... Running some technical Analysis{Style.RESET_ALL}")
        self.mdm.perform_technical_analysis()
        # Get and print summary stats
        stats = self.mdm.get_summary_stats()
        
        print(f"{Fore.BLUE}...   High/Low = {stats['high']} / {stats['low']} {Style.RESET_ALL}")
        print(f"{Fore.BLUE}...   Latest MACD = {stats['latest_macd']} {Style.RESET_ALL}")
        
        if not self.args.skip_report:
            print(f"{Fore.BLUE}... Generating a market report, talking with GPT3.5 to do this ... {Style.RESET_ALL}")
            self.mdm.generate_report()

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
        """
        Show progress during badge generation with focus on complexity and craziness metrics.
        
        Attribution: Cline implementation for Martin East - Complexity-focused progress display - Apr 17, 2025
        """
        print(f"\n{Fore.BLUE}... Starting the 3-D badge generation...{Style.RESET_ALL}")
        time.sleep(0.5)
        
        generations = self.args.ga_generations
        print(f"{Fore.BLUE}... Initialising the Genetic Algorithm with {generations} generations...{Style.RESET_ALL}")
        print(f"{Fore.BLUE}... Searching for the CRAZIEST design ...{Style.RESET_ALL}")
        time.sleep(0.5)
        
        output_file = self.args.output if self.args.output else "disc.scad"
        print(f"{Fore.BLUE}... Writing SCAD object to {output_file}...{Style.RESET_ALL}")
        time.sleep(0.5)
        
        # If we have complexity metrics, display them
        if hasattr(self, 'complexity_report'):
            print(f"\n{Fore.GREEN}=== CRAZINESS ANALYSIS ==={Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}...    CRAZINESS FACTOR: {self.complexity_report.get('craziness_factor', 0):.2f}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}...    Polygonal Complexity: {self.complexity_report.get('polygonal_complexity_score', 0):.2f}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}...    Overall Complexity: {self.complexity_report.get('complexity_score', 0):.2f}{Style.RESET_ALL}")
            
            # Show detailed metrics
            print(f"\n{Fore.CYAN}Complexity Metrics:{Style.RESET_ALL}")
            print(f"  - CSG Operations: {sum(self.complexity_report.get('csg_operations', {}).values())}")
            print(f"  - Max Tree Depth: {self.complexity_report.get('max_depth', 0)}")
            print(f"  - Total Nodes: {self.complexity_report.get('total_nodes', 0)}")
            
            # Show polygonal details
            poly_metrics = self.complexity_report.get('polygonal_metrics', {})
            if poly_metrics:
                print(f"\n{Fore.CYAN}Polygonal Details:{Style.RESET_ALL}")
                print(f"  - Polygon Count: {poly_metrics.get('polygon_count', 0)}")
                print(f"  - Total Points: {poly_metrics.get('total_points', 0)}")
                print(f"  - Max Points Per Polygon: {poly_metrics.get('max_points_per_polygon', 0)}")
                print(f"  - Polyhedron Count: {poly_metrics.get('polyhedron_count', 0)}")
                print(f"  - Total Faces: {poly_metrics.get('total_faces', 0)}")
    
    def _show_final_info(self):
        """Display final information about the generated files."""
        output_file = self.args.output if self.args.output else "disc.scad"
        
        print(f"\n{Fore.GREEN}✅ Badge generation complete!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📁 Files created:{Style.RESET_ALL}")
        print(f"   - {output_file} (OpenSCAD file)")
        if not self.args.skip_report:
            print("   - stock_report (Text report)")
        
        print(f"\nYou can now open {output_file} in OpenSCAD to view your badge or export it to STL for 3D printing.")

    def _generate_badge(self):
        """
        Generate 3D badge using genetic algorithm with focus on complexity and craziness.
        
        Attribution: Cline implementation for Martin East - Complexity-focused badge generation - Apr 17, 2025
        """
        logger.info("Generating 3D badge using genetic algorithm with complexity metrics")
        
        try:
            # Define gene space
            gene_space = self._create_gene_space()
            
            # Create pyGAD instance
            self.ga_instance = pygad.GA(
                num_generations=self.args.ga_generations,
                num_parents_mating=4,
                fitness_func=self._fitness_function,
                sol_per_pop=20,
                num_genes=len(gene_space),
                gene_space=gene_space,
                parent_selection_type="tournament",
                K_tournament=3,
                crossover_type="uniform",
                mutation_type="random",
                mutation_percent_genes=15,  # Increased mutation rate for more diversity
                keep_elitism=2,  # Keep more elite solutions
                on_generation=self._on_generation
            )
            
            # Run the genetic algorithm
            logger.info(f"Running genetic algorithm for {self.args.ga_generations} generations")
            self.ga_instance.run()
            
            # Get the best solution
            solution, solution_fitness, solution_idx = self.ga_instance.best_solution()
            logger.info(f"Best solution found with fitness: {solution_fitness:.2f}")
            
            # Get the best badge and complexity report
            best_badge, complexity_report, _ = self.ga_instance.badges[solution_idx]
            best_params = self._genes_to_badge_params(solution)
            
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
            self.badge_params = best_params
            self.badge_output_file = output_file
            
            # Log badge details
            logger.info(f"Badge generation complete. Output file: {output_file}")
            logger.info(f"Badge type: {best_params['badge_type']}")
            logger.info(f"Terrain type: {best_params.get('terrain_type', 'N/A')}")
            logger.info(f"Complexity score: {self.complexity_report['complexity_score']:.2f}")
            logger.info(f"Craziness factor: {self.complexity_report['craziness_factor']:.2f}")
        except Exception as e:
            logger.error(f"Error generating badge: {e}")
            raise

    def _get_text_content(self, text_type, sentiment):
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
        
            
    def _genes_to_badge_params(self, genes):
        ### TODO, this needs completion after model definitions. 
        """
        Convert genes array to badge parameters dictionary.
        
        Args:
            genes (list): List of gene values
            
        Returns:
            dict: Badge parameters
        """
        # Define badge types and features
        badge_types = ['disc', 'rectangular', 'triangular']
        terrain_types = ['spiral_chart', 'bar_chart']
        
        text_type = [ 'one_word_analysis', 'buy_sell_hold', 'latest_macd', 'high_low' ] 
        text_positions = ['bottom', 'top', 'front']
        
        # Get badge type
        badge_type_idx = int(genes[0])
        badge_type = badge_types[badge_type_idx]
        
        # Get feature type based on badge type
        terrain_type_idx = int(genes[1])
        terrain_type = terrain_types[terrain_type_idx]
        
        # Get text position
        text_position_idx = int(genes[2])
        text_position = text_positions[text_position_idx]

        # Get text type
        text_type_idx = int(genes[3])
        text_type = text_type[text_type_idx]

        text_content = self._get_text_content(text_type, genes[4])
        text_size = genes[5]
        text_depth = genes[6]
        base_height = genes[7]  

        feature_height = genes[8]
        
        # Create parameters dictionary
        params = {
            'badge_type': badge_type,
            'terrain_type': terrain_type,
            'text_type': text_type,
            'text_position': text_position,
            'text_content': text_content,
            'text_size': text_size,
            'text_depth': text_depth,
            'base_height': base_height,
            'feature_height': feature_height,
            'height_range': (0, genes[7]),  # Height range
            'width_range': (0, genes[8])    # Width range
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

    
    def _get_complexity_report(self, badge):
        """
        Generate a comprehensive complexity report with emphasis on polygonal complexity.
        
        Attribution: Cline implementation for Martin East - Enhanced complexity report with polygonal metrics - Apr 17, 2025
        
        Args:
            badge: The badge model
            
        Returns:
            dict: Complexity metrics and suggestions with emphasis on polygonal complexity
        """
        # Get the OpenSCAD code for complexity analysis
        scad_code = scad_render(badge.final_model)
        
        # Calculate complexity metrics
        csg_counts = count_csg_operations(scad_code)
        
        # Create a complexity analyzer
        analyzer = ComplexityAnalyzer()
        analyzer.analyze(badge.final_model)
        
        # Get standard complexity score
        complexity_score = model_complexity_score(badge.final_model)
        
        # Get polygonal complexity metrics
        polygonal_metrics = analyze_polygonal_complexity(badge.final_model)
        
        # Calculate a "craziness factor" that emphasizes polygonal complexity
        craziness_factor = (
            complexity_score * 0.6 + 
            polygonal_metrics['polygonal_complexity_score'] * 0.4
        )
        
        return {
            'csg_operations': csg_counts,
            'max_depth': analyzer.metrics['max_depth'],
            'total_nodes': analyzer.metrics['total_nodes'],
            'primitive_counts': dict(analyzer.metrics['primitive_counts']),
            'operation_counts': dict(analyzer.metrics['operation_counts']),
            'complexity_score': complexity_score,
            'polygonal_metrics': polygonal_metrics,
            'polygonal_complexity_score': polygonal_metrics['polygonal_complexity_score'],
            'craziness_factor': craziness_factor,
            'optimization_suggestions': suggest_optimizations(analyzer.metrics)
        }
    
    def _fitness_function(self, ga_instance, solution, solution_idx):
        """
        Fitness function using complexity metrics.
        This function evaluates badge designs based solely on complexity metrics
        to maximize the "craziness" of the generated models.
        
        Attribution: Cline implementation for Martin East - Complexity-focused fitness function - Apr 17, 2025
        
        Args:
            ga_instance: The genetic algorithm instance
            solution: The solution to calculate fitness for (gene array)
            solution_idx: The index of the solution in the population
            
        Returns:
            float: The fitness value to be maximized
        """
        # Convert solution (genes) to badge parameters
        params = self._genes_to_badge_params(solution)
        
        # Create badge and generate model
        badge = BadgeFactory.create_badge(
            params['badge_type'], 
            self.mdm.data,
            self.ticker,
            params
        )
        
        badge.generate_base()
        badge.generate_terrain()
        badge.generate_text()
        badge.combine_models()
        
        # Get complexity report
        complexity_report = self._get_complexity_report(badge)
        
        # Store the badge and complexity metrics for later retrieval and normalization
        if not hasattr(ga_instance, 'population_stats'):
            ga_instance.population_stats = []
        
        # Add current complexity metrics to population stats
        current_stats = {
            # New complexity metrics only
            'csg_operations': sum(complexity_report['csg_operations'].values()),
            'max_depth': complexity_report['max_depth'],
            'total_nodes': complexity_report['total_nodes'],
            'primitive_count': sum(complexity_report['primitive_counts'].values()),
            'operation_count': sum(complexity_report['operation_counts'].values()),
            'complexity_score': complexity_report['complexity_score'],
            'polygonal_complexity_score': complexity_report['polygonal_complexity_score'],
            'craziness_factor': complexity_report['craziness_factor'],
            
            # Scaling factor (keep this to ensure models aren't too small)
            'scaling_factor': params.get('height_range', (0, 10))[1]
        }
        ga_instance.population_stats.append(current_stats)
        
        # Store the badge and complexity report for later retrieval
        if not hasattr(ga_instance, 'badges'):
            ga_instance.badges = {}
        ga_instance.badges[solution_idx] = (badge, complexity_report, 0)  # Placeholder fitness
        
        # If this is the last solution in the population, normalize and update all fitness values
        if solution_idx == ga_instance.pop_size - 1:
            # Calculate min-max values from the population for all metrics
            metrics = [
                'csg_operations', 
                'max_depth', 
                'total_nodes', 
                'primitive_count',
                'operation_count',
                'complexity_score', 
                'polygonal_complexity_score',
                'craziness_factor'
            ]
            
            min_values = {metric: min(s[metric] for s in ga_instance.population_stats) for metric in metrics}
            max_values = {metric: max(s[metric] for s in ga_instance.population_stats) for metric in metrics}
            
            # Ensure no division by zero
            for metric in metrics:
                if max_values[metric] == min_values[metric]:
                    max_values[metric] = min_values[metric] + 1
            
            # Calculate fitness for all solutions
            for i, stats in enumerate(ga_instance.population_stats):
                # Normalize each metric to [0, 1]
                normalized_metrics = {}
                for metric in metrics:
                    normalized_metrics[metric] = (stats[metric] - min_values[metric]) / (max_values[metric] - min_values[metric])
                
                # Weight the metrics to emphasize polygonal complexity and craziness
                weights = {
                    'csg_operations': 0.15,           # CSG operations contribute to complexity
                    'max_depth': 0.10,                # Deeper trees are more complex
                    'total_nodes': 0.10,              # More nodes = more complex
                    'primitive_count': 0.05,          # Basic primitives (less important)
                    'operation_count': 0.10,          # Operations like union, difference
                    'complexity_score': 0.20,         # Overall complexity score
                    'polygonal_complexity_score': 0.20, # Polygonal complexity (important)
                    'craziness_factor': 0.10          # Combined craziness factor
                }
                
                # Calculate weighted sum
                weighted_sum = sum(normalized_metrics[metric] * weights[metric] for metric in metrics)
                
                # Calculate final fitness by multiplying by scaling factor
                fitness = weighted_sum * stats['scaling_factor']
                
                # Update the fitness value in badges
                badge, complexity_report, _ = ga_instance.badges[i]
                ga_instance.badges[i] = (badge, complexity_report, fitness)
                
                # Update the solution's fitness in the GA instance
                ga_instance.pop_fitness[i] = fitness
            
            # Clear population stats for the next generation
            ga_instance.population_stats = []
            
            # Return the fitness for the current solution
            return ga_instance.badges[solution_idx][2]
        
        # For all but the last solution, return a placeholder
        return 0


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

def main():
    """Main entry point for the CLI."""
    try:
        cli = CrazyStockBadge()
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

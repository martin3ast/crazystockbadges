#!/usr/bin/env python3
"""
Badge Factory class, 3-D Model Generation Module for Crazy Stock Badges Project

This module provides classes and functions for generating 3D models from stock data
using SolidPython to create OpenSCAD files that can be rendered to STL for 3D printing.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for 3D badge generation - Apr 13, 2025.

"""

import os
import numpy as np
import pandas as pd
from solid import *
from solid.utils import *
import logging
from abc import ABC, abstractmethod
from pathlib import Path
import math
import random  # For craziness enhancement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('improved_3d_models')


class StockDataValidator:
    """
    Validates and preprocesses stock data for 3D model generation.
    
    Version 1.0 - Cline implementation for Martin East - Implements data validation and normalization - Apr 13, 2025.
    """
    
    @staticmethod
    def validate_data(data):
        """
        Validate that the data contains the required columns.
        
        Args:
            data (pandas.DataFrame): Stock data
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        required_columns = ['Close', 'Volume']
        
        if not isinstance(data, pd.DataFrame):
            logger.error("Data must be a pandas DataFrame")
            return False
        
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"Required column '{col}' not found in data")
                return False
        
        if len(data) < 5:
            logger.error("Data must contain at least 5 rows")
            return False
            
        return True
    
    @staticmethod
    def normalize_data(data, columns=None, new_min=0, new_max=10):
        """
        Normalize specified columns to a new range.
        
        Args:
            data (pandas.DataFrame): Stock data
            columns (list): List of columns to normalize
            new_min (float): Minimum value for normalized data
            new_max (float): Maximum value for normalized data
            
        Returns:
            pandas.DataFrame: Data with normalized columns added
        """
        if columns is None:
            columns = ['Close', 'Volume']
        
        result = data.copy()
        
        for col in columns:
            if col in data.columns:
                norm_col = f'{col}_Normalized'
                min_val = data[col].min()
                max_val = data[col].max()
                
                # Avoid division by zero
                if max_val == min_val:
                    result[norm_col] = new_min
                else:
                    result[norm_col] = (data[col] - min_val) / (max_val - min_val) * (new_max - new_min) + new_min
            else:
                logger.warning(f"Column '{col}' not found in data, skipping normalization")
        
        return result


class Badge3DModel(ABC):
    """
    Abstract base class for 3D badge models.
    
    Version 1.0 - Cline implementation for Martin East - Defines base structure for all badge types - Apr 13, 2025.
    Version 2.0 - Martin East - Read, tidy, reduce overall complexity, modify base model primitives to base, terrain and text, add stub code - Apr 15, 2025.
    """
    
    def __init__(self, stock_data, ticker_symbol, params=None):
        """
        Initialize the 3D model.
        
        Args:
            stock_data (pandas.DataFrame): Stock data
            ticker_symbol (str): Stock ticker symbol
            params (dict): Additional parameters for the model
        """
        self.ticker_symbol = ticker_symbol
        self.params = params or {}
        self.model_complexity = 0 # Placeholder for model complexity
        
        # Validate and normalize data
        validator = StockDataValidator()
        if not validator.validate_data(stock_data):
            raise ValueError("Invalid stock data")
        
        # Set default normalization ranges
        height_range = self.params.get('height_range', (0, 10))
        width_range = self.params.get('width_range', (0, 10))
        
        # Normalize data
        self.data = validator.normalize_data(
            stock_data, 
            columns=['Close', 'Volume', 'High', 'Low'],
            new_min=height_range[0],
            new_max=height_range[1]
        )
        
        # Normalize volume separately for width
        self.data['Volume_Width'] = validator.normalize_data(
            stock_data, 
            columns=['Volume'],
            new_min=width_range[0],
            new_max=width_range[1]
        )['Volume_Normalized']
        
        # Initialize model components
        self.base_model = None
        self.terrain_model = None
        self.text_model = None
        self.final_model = None
        
    
    @abstractmethod
    def generate_base(self):
        """Generate the base part of the model."""
        pass
    
    @abstractmethod
    def generate_terrain(self):
        """Generate the feature part of the model based on stock data."""
        pass
    
    def generate_text(self):
        """
        Generate text for the badge. Only limited amount of characters
         possible due to laptop compute and memory resource restrictions.
        
        Returns:
            solid.OpenSCADObject: Text 3D model
        """
        text_depth = self.params.get('text_depth', 2)
        text_size = self.params.get('text_size', 10)
        text_content = self.params.get('text_content', self.ticker_symbol)
        text_position = self.params.get('text_position', 'bottom')
        
        # We can only add limited text characters owing to 
        # Model complexity. modelling restrictions on laptop compute and memory.
        text_2d = text(text_content, size=text_size, halign='center', valign='center')
        self.text_model = linear_extrude(height=text_depth)(text_2d)
        
        # Position the text
        if text_position == 'bottom':
            # Position text on the bottom of the badge
            z_pos = text_depth
            self.text_model = translate([0, 0, z_pos])(self.text_model)
        elif text_position == 'top':
            # Position text on the top of the badge
            base_height = self.params.get('base_height', 3)
            feature_height = self.params.get('feature_height', 2)
            z_pos = base_height + feature_height
            self.text_model = translate([0, 0, z_pos])(self.text_model)
        
        return self.text_model


    
    def enhance_craziness(self, model):
        """
        Enhance the craziness of a model by adding random variations.
        
        Attribution: Cline implementation for Martin East - Model craziness enhancer - Apr 17, 2025
        
        Args:
            model: The model to enhance
            
        Returns:
            solid.OpenSCADObject: Enhanced model with increased craziness
        """
        # Add random rotations to parts of the model
        if random.random() > 0.5:
            angle = random.uniform(-15, 15)
            axis = [random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)]
            model = rotate(a=angle, v=axis)(model)
        
        # Occasionally add hull operations to create more organic shapes
        if random.random() > 0.7:
            # Create a small sphere at a random position
            x = random.uniform(-10, 10)
            y = random.uniform(-10, 10)
            z = random.uniform(0, 20)
            radius = random.uniform(2, 5)
            
            sphere_obj = translate([x, y, z])(sphere(r=radius))
            
            # Hull with the original model for an organic connection
            model = hull()(model, sphere_obj)
        
        return model
    
    def combine_models(self):
        """
        Combine base, feature, and text models into the final model.
        Occasionally enhances craziness for more complex designs.

        Run the base, terrain and text model generation if they are 'None'
        
        Attribution: Cline implementation for Martin East - Enhanced to occasionally increase craziness - Apr 17, 2025

        Returns:
            solid.OpenSCADObject: Combined 3D model
        """
        if self.base_model is None:
            self.generate_base()
        
        if self.terrain_model is None:
            self.generate_terrain()
        
        if self.text_model is None:
            self.generate_text()
        
        # Combine models
        combined = union()(
            self.base_model,
            self.terrain_model,
            self.text_model
        )
        
        # Occasionally enhance craziness (20% chance)
        if random.random() > 0.8:
            combined = self.enhance_craziness(combined)
        
        self.final_model = combined
        
        return self.final_model
    
    
    def generate_spiral_chart(self):
        """
        Generate a spiral landscape model based on stock data.
        
        Returns:
            solid.OpenSCADObject: Spiral landscape 3D model
        """
        radius = self.params.get('spiral_radius', 45)
        z_offset = self.params.get('base_height', 3)
        spiral_turns = self.params.get('spiral_turns', 7)
        
        # Generate points on a spiral
        num_points = len(self.data)
        angles = np.linspace(0, spiral_turns * 2 * np.pi, num_points)  # Spiral angles
        radii = np.linspace(0, radius, num_points)  # Gradually increase radius for spiral
        
        # Map normalized stock prices to heights and widths
        heights = self.data['Close_Normalized']*2
        widths = self.data['Volume_Width']
        
        # Calculate coordinates
        x = radii * np.cos(angles)  # X coordinates
        y = radii * np.sin(angles)  # Y coordinates
        
        # Create the landscape as a series of cylinders
        landscape = []
        for i in range(num_points):
            cylinder_height = heights.iloc[i]
            cylinder_radius = widths.iloc[i]

            # Make sure the cylinders are not too small... they break off easily otherwise (3mm)
            if cylinder_radius < 3:
                cylinder_radius = 3 

            landscape.append(
                translate([x[i], y[i], z_offset])(
                    cylinder(r=cylinder_radius, h=cylinder_height, center=False)
                )
            )
        
        # Combine the landscape into a single object
        return union()(landscape)
        
    def generate_bar_chart(self):
        """
        Generate a bar chart model based on stock prices.
        
        Returns:
            solid.OpenSCADObject: Bar chart 3D model
        """
        base_width = self.params.get('base_width', 100)
        base_depth = self.params.get('base_depth', 60)
        z_offset = self.params.get('base_height', 3)
        bar_width = base_width / len(self.data)

        print (f"z_offset =  {z_offset}")
        
        # Create bars for each data point, double the max height (normalized)
        # to make them more visible and look better

        bars = []
        for i in range(len(self.data)):
            bar_height = z_offset + self.data['Close_Normalized'].iloc[i]*2
            bar_depth = base_depth * 0.7  # Make bars slightly narrower than the base
            
            # Position each bar along the x-axis
            x_pos = i * bar_width
            y_pos = (base_depth - bar_depth) / 2  # Center bars on the y-axis
            
            bars.append(
                translate([x_pos, y_pos, z_offset])(
                    cube([bar_width * 0.9, bar_depth, bar_height])
                )
            )
        
        # Translate the finished bar model to zero point
        # and combine them into a single object
        for i in range(len(bars)):
            bars[i] = translate([-base_width/2, -base_depth/2, z_offset])(bars[i])
        
        return union()(bars)
    
    def generate_surface_plot(self):
        # TODO: Not in use
        """
        Generate a surface plot model based on stock data.
        
        Returns:
            solid.OpenSCADObject: Surface plot 3D model
        """
        base_width = self.params.get('base_width', 100)
        base_depth = self.params.get('base_depth', 60)
        z_offset = self.params.get('base_height', 3)
        
        # Create a grid of points
        grid_size = int(math.sqrt(len(self.data)))
        if grid_size < 2:
            grid_size = 2
        
        # Truncate data to fit grid
        data_points = min(grid_size * grid_size, len(self.data))
        heights = self.data['Close_Normalized'].iloc[:data_points].values
        
        # Reshape to grid
        try:
            height_grid = heights[:grid_size * grid_size].reshape(grid_size, grid_size)
        except ValueError:
            # If reshaping fails, pad with zeros
            padded = np.zeros(grid_size * grid_size)
            padded[:len(heights)] = heights
            height_grid = padded.reshape(grid_size, grid_size)
        
        # Calculate cell dimensions
        cell_width = base_width / grid_size
        cell_depth = base_depth / grid_size
        
        # Create cells for the surface
        cells = []
        for i in range(grid_size):
            for j in range(grid_size):
                cell_height = height_grid[i, j]
                
                x_pos = i * cell_width
                y_pos = j * cell_depth
                
                cells.append(
                    translate([x_pos, y_pos, z_offset])(
                        cube([cell_width * 0.95, cell_depth * 0.95, cell_height])
                    )
                )
        
        return union()(cells)
    
    def calculate_stats(self):
        """
        Calculate statistics about the model.
        
        Attribution: Cline implementation for Martin East - Enhanced stats calculation - Apr 17, 2025
        
        Returns:
            dict: Model statistics
        """
        # Initialize stats dictionary
        stats = {}
        
        # Basic stats
        stats['num_objects'] = len(self.data)
        stats['height_diff'] = self.params.get('height_range', (0, 15))[1]
        stats['width_diff'] = self.params.get('width_range', (0, 10))[1]
        stats['depth_diff'] = 5  # Example value
        stats['size'] = (100, 100, 20)  # Example values
        
        return stats
    
    def save_to_file(self, filename=None):
        """
        Save the model to an OpenSCAD file.
        
        Args:
            filename (str): Output filename
            
        Returns:
            str: Path to the saved file
        """
        if self.final_model is None:
            self.combine_models()
        
        if filename is None:
            filename = f"{self.ticker_symbol}_badge.scad"
        
        # Save the model
        scad_render_to_file(self.final_model, filename)
        logger.info(f"Model saved to {filename}")
        
        return filename


class DiscBadge(Badge3DModel):
    """
    Circular badge with stock data features.
    
    Version 1.0 - Cline implementation for Martin East - Implements circular badge with jagged edge and spiral features - Apr 13, 2025.
    Version 2.0 - Martin East - Simplify, move most methods to base class - Apr 15, 2025.
        """
    
    def generate_base(self):
        """
        Generate a circular base for the badge.
        
        Returns:
            solid.OpenSCADObject: Base 3D model
        """
        radius = self.params.get('base_radius', 50)
        height = self.params.get('base_height', 1)
    
        # Take the stock price and make the edge jagged.
        base_radius = self.params.get('base_radius', 50)
        z_offset = self.params.get('base_height', 3)
        
        # Parameters for the polygon
        num_points = len(self.data)  # Use all data points
        angles = np.linspace(0, 2 * np.pi, num_points)  # Angles around the circle
        
        # Map normalized stock prices to the polygon edge
        radii = self.data['Close_Normalized'] + base_radius
        
        # Create points for the polygon
        points = []
        for i in range(num_points):
            x = radii.iloc[i] * np.cos(angles[i])  # X coordinate
            y = radii.iloc[i] * np.sin(angles[i])  # Y coordinate
            points.append([x, y])
        
        # Create 2D polygon and extrude to 3D
        jagged_disc_2d = polygon(points)
        jagged_disc_3d = linear_extrude(height=height)(jagged_disc_2d)

        self.base_model = translate([0, 0, z_offset])(jagged_disc_3d)
        return self.base_model 

    
    def generate_terrain(self):
        """
        Generate terrain on the badge based on stock data.
        
        Returns:
            solid.OpenSCADObject: Feature 3D model
        """
        terrain_type = self.params.get('spiral_chart','bar_chart')
        
        if terrain_type == 'spiral_chart':
            self.terrain_model = self.generate_spiral_chart()
        elif terrain_type == 'bar_chart':
            self.terrain_model = self.generate_bar_chart()
        else:
            logger.warning(f"Unknown terrain type: {terrain_type}, using spiral_chart")
            self.terrain_model = self.generate_spiral_chart()
        
        return self.terrain_model
        

    
    
class RectangularBadge(Badge3DModel):
    """
    Rectangular badge with stock data features. Specialisation of Badge3DModel.
    
    Version 1.0 - Cline implementation for Martin East - Implements rectangular badge with bar chart and surface plot features - Apr 13, 2025.
    Version 2.0 - Martin East - move most methods to base class - Apr 15, 2025.
    """
    
    def generate_base(self):
        """
        Generate a rectangular base for the badge with jagged edges based on stock prices.
        
        Returns:
            solid.OpenSCADObject: Base 3D model
        """
        width = self.params.get('base_width', 100)
        depth = self.params.get('base_depth', 60)
        height = self.params.get('base_height', 1)
        z_offset = 0
        
        # Number of points to use on each side of the rectangle
        # We'll distribute the data points around the perimeter
        num_points = len(self.data)
        points_per_side = num_points // 4  # Distribute points across 4 sides
        
        # Create points for the polygon
        points = []
        
        # Calculate how much to vary the points based on stock data
        max_variation = min(width, depth) * 0.2  # 20% of the smaller dimension
        
        # Map normalized stock prices to variations
        variations = self.data['Close_Normalized'] * max_variation / self.data['Close_Normalized'].max()
        
        # Generate points for each side of the rectangle with variations
        # Bottom side (left to right)
        for i in range(points_per_side):
            data_idx = i % len(variations)
            x = (i / points_per_side) * width
            y = -variations.iloc[data_idx]  # Vary outside the base
            points.append([x, y])
        
        # Right side (bottom to top)
        for i in range(points_per_side):
            data_idx = (points_per_side + i) % len(variations)
            x = width + variations.iloc[data_idx]  # Vary outside the base
            y = (i / points_per_side) * depth
            points.append([x, y])
        
        # Top side (right to left)
        for i in range(points_per_side):
            data_idx = (2 * points_per_side + i) % len(variations)
            x = width - (i / points_per_side) * width
            y = depth + variations.iloc[data_idx]  # Vary outside the base
            points.append([x, y])
        
        # Left side (top to bottom)
        for i in range(points_per_side):
            data_idx = (3 * points_per_side + i) % len(variations)
            x = -variations.iloc[data_idx]  # Vary outside the base
            y = depth - (i / points_per_side) * depth
            points.append([x, y])
        
        # Create 2D polygon and extrude to 3D
        jagged_rect_2d = polygon(points)
        jagged_rect_3d = linear_extrude(height=height)(jagged_rect_2d)
        
        # Centre the rectangle over the zero point.
        self.base_model = translate([-depth, -width, z_offset])(jagged_rect_3d)
        return self.base_model
    
    def generate_terrain(self):
        """
        Generate terrain on the badge based on stock data.
        
        Returns:
            solid.OpenSCADObject: Feature 3D model
        """
        terrain_type = self.params.get('spiral_chart', 'bar_chart')
        terrain_model = None

        if terrain_type == 'spiral_chart':
            terrain_model = self.generate_bar_chart()
        elif terrain_type == 'bar_chart':
            terrain_model = self.generate_surface_plot()
        else:
            logger.warning(f"Unknown terrain type: {terrain_type}, using bar_chart")
            terrain_model = self.generate_bar_chart()

        # Centre the rectangle over the zero point.
        self.terrain_model = translate([-depth, -width, 0])(terrain.model)
        
        return self.terrain_model
   

class TriangularBadge(Badge3DModel):
    """
    TODO: Not in use, needs modification to work...
    

    Triangular badge with stock data features. Specialisation of Badge3DModel.
    
    Version 1.0 - Cline implementation for Martin East - Implements triangular badge with pyramid and terrain features - Apr 13, 2025.
    Version 2.0 - Martin East - move most methods to base class - Apr 15, 2025.
    """
    
    def generate_base(self):
        """
        Generate a triangular base for the badge.
        
        Returns:
            solid.OpenSCADObject: Base 3D model
        """
        side_length = self.params.get('side_length', 80)
        height = self.params.get('base_height', 3)
        
        # Create an equilateral triangle
        points = [
            [0, 0],
            [side_length, 0],
            [side_length / 2, side_length * math.sin(math.radians(60))]
        ]
        
        triangle_2d = polygon(points)
        self.base_model = linear_extrude(height=height)(triangle_2d)
        return self.base_model
    
    def generate_terrain(self):
        """
        Generate terrain on the badge based on stock data.
        
        Returns:
            solid.OpenSCADObject: Feature 3D model
        """
        feature_type = self.params.get('feature_type', 'pyramid')
        
        if feature_type == 'pyramid':
            self.feature_model = self._generate_pyramid()
        elif feature_type == 'terrain':
            self.feature_model = self._generate_terrain()
        else:
            logger.warning(f"Unknown feature type: {feature_type}, using pyramid")
            self.feature_model = self._generate_pyramid()
        
        return self.feature_model
    
    def _generate_pyramid(self):
        """
        Generate a pyramid feature with height based on stock data.
        
        Returns:
            solid.OpenSCADObject: Pyramid 3D model
        """
        side_length = self.params.get('side_length', 80)
        z_offset = self.params.get('base_height', 3)
        
        # Use the average of normalized close prices for the pyramid height
        pyramid_height = self.data['Close_Normalized'].mean() * 3
        
        # Create a pyramid (triangular prism)
        points = [
            [0, 0],
            [side_length, 0],
            [side_length / 2, side_length * math.sin(math.radians(60))]
        ]
        
        # Create the pyramid by scaling a series of triangles
        layers = 20  # Number of layers in the pyramid
        pyramid_parts = []
        
        for i in range(layers):
            # Calculate the scale factor for this layer
            scale_factor = 1.0 - (i / layers)
            layer_height = pyramid_height * (i / layers)
            
            # Scale the points for this layer
            scaled_points = [[p[0] * scale_factor, p[1] * scale_factor] for p in points]
            
            # Create the layer
            layer_2d = polygon(scaled_points)
            layer_3d = linear_extrude(height=pyramid_height/layers)(layer_2d)
            
            # Position the layer
            pyramid_parts.append(
                translate([
                    side_length * (1 - scale_factor) / 2,  # Center on x
                    side_length * (1 - scale_factor) / 4,  # Center on y
                    z_offset + layer_height
                ])(layer_3d)
            )
        
        return union()(pyramid_parts)
    
    def _generate_terrain(self):
        """
        Generate a terrain feature based on stock data.
        
        Returns:
            solid.OpenSCADObject: Terrain 3D model
        """
        side_length = self.params.get('side_length', 80)
        z_offset = self.params.get('base_height', 3)
        
        # Create a triangular grid
        grid_size = 10  # Number of divisions along each side
        
        # Calculate the height of the triangle
        triangle_height = side_length * math.sin(math.radians(60))
        
        # Calculate cell dimensions
        cell_width = side_length / grid_size
        cell_height = triangle_height / grid_size
        
        # Create cells for the terrain
        cells = []
        
        # Use stock data to determine cell heights
        # We'll cycle through the data if we need more points than we have
        data_len = len(self.data)
        
        cell_count = 0
        for i in range(grid_size):
            # Calculate the number of cells in this row
            row_cells = grid_size - i
            
            for j in range(row_cells):
                # Get the data index, cycling if necessary
                data_idx = cell_count % data_len
                cell_count += 1
                
                # Get the height for this cell
                terrain_height = self.data['Close_Normalized'].iloc[data_idx]
                
                # Calculate position
                x_pos = j * cell_width + (i * cell_width / 2)  # Offset each row
                y_pos = i * cell_height
                
                cells.append(
                    translate([x_pos, y_pos, z_offset])(
                        cube([cell_width * 0.95, cell_height * 0.95, terrain_height])
                    )
                )
        
        return union()(cells)
    



class BadgeFactory:
    """
    Factory class for creating different types of badges.
    
    Version 1.0 - Cline implementation for Martin East - Creates appropriate badge type based on parameters - Apr 13, 2025.
    """
    
    @staticmethod
    def create_badge(badge_type, stock_data, ticker_symbol, params=None):
        """
        Create a badge of the specified type.
        
        Args:
            badge_type (str): Type of badge to create
            stock_data (pandas.DataFrame): Stock data
            ticker_symbol (str): Stock ticker symbol
            params (dict): Additional parameters for the badge
            
        Returns:
            Badge3DModel: Badge model instance
        """
        if badge_type == 'disc':
            return DiscBadge(stock_data, ticker_symbol, params)
        elif badge_type == 'rectangular':
            return RectangularBadge(stock_data, ticker_symbol, params)
        elif badge_type == 'triangular':
            return TriangularBadge(stock_data, ticker_symbol, params)
        else:
            logger.warning(f"Unknown badge type: {badge_type}, using disc")
            return DiscBadge(stock_data, ticker_symbol, params)


def main():
    """
    Main function for testing the module.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate 3D badge models from stock data')
    parser.add_argument('--ticker', type=str, default='TSLA', help='Stock ticker symbol')
    parser.add_argument('--data-file', type=str, default='./stock_data', help='Stock data CSV file')
    parser.add_argument('--badge-type', type=str, default='disc', 
                       choices=['disc', 'rectangular', 'triangular'], help='Badge type')
    parser.add_argument('--feature-type', type=str, help='Feature type (depends on badge type)')
    parser.add_argument('--output', type=str, help='Output file name')
    args = parser.parse_args()
    
    try:
        # Load stock data
        if os.path.exists(args.data_file):
            stock_data = pd.read_csv(args.data_file)
            logger.info(f"Loaded stock data from {args.data_file}")
        else:
            logger.error(f"Data file not found: {args.data_file}")
            return 1
        
        # Set parameters based on badge type
        params = {}
        if args.feature_type:
            params['feature_type'] = args.feature_type
        
        # Create the badge
        badge = BadgeFactory.create_badge(args.badge_type, stock_data, args.ticker, params)
        
        # Generate the model
        badge.generate_base()
        badge.generate_terrain()
        badge.generate_text()
        badge.combine_models()
        
        #badge.enhance_craziness(badge.final_model)

        # Save the model
        output_file = args.output or f"{args.ticker}_{args.badge_type}_badge.scad"
        badge.save_to_file(output_file)
        print(f"\nModel saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

#!/usr/bin/env python3
"""
Badge Factory class, 3-D Model Generation Module for Crazy Stock Badges Project

This module provides classes and functions for generating 3D models from stock data
using SolidPython to create OpenSCAD files that can be rendered to STL for 3D printing.

There is a base class for all badge types, and each badge type (rectangular, triangular, disc)
inherits from this base class. The base class provides methods for generating the base, terrain,
and text components of the badge. The terrain can be a bar chart, spiral chart, or surface plot,
and the text can be positioned on the top or bottom of the badge.

Multiple terrain types can be combined into a single model, different arrangements of these are
defined, from side by side to circul for many objects.

Notes: Cline tends to produce rangey verbose code, and test cases, but it is helpful in conceptualising
The shape model building mathematics.


History
=======

Version 1.0 - Cline implementation for Martin East - Based on original requirements for 3D badge generation - Apr 13, 2025.
Version 2.0 - Martin East - Read, tidy, reduce overall complexity - Apr 15, 2025.
Version 3.0 - Cline - Enhanced with pyramid feature for all badge types - Apr 21, 2025.
Version 4.0 - Martin East - Remove unnecessary complexity, read and tidy - Apr 23, 2025
Version 5.0 - Martin East - Made combined terrain models much simpler and more interesting by overlaying them, also removed terrain-weights, too fiddly - Apr 25, 2025.
"""

# Standard library imports
import os
import math
import random
import logging
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

# Third-party imports
import numpy as np
import pandas as pd
from solid import *
from solid.utils import *
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENSCAD_PATH = os.getenv('OPENSCAD_PATH', 'openscad')
OPENSCAD_TIMEOUT = int(os.getenv('OPENSCAD_TIMEOUT', '600'))

# Get logger
logger = logging.getLogger('badge_factory')


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
    a
    Version 3.0 - Cline & Martin - Add the combine models feature, 
    Version 4.0 - Martin tidy up and reduce complexity - Apr 23, 2025.
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
        """Generate the feature part of 
        the model based on stock data."""
        pass
    
    def generate_combined_terrain(self, terrain_types):
        """
        Generate a combined terrain model from multiple terrain types.
        
        Args:
            terrain_types (list): List of terrain type names

        Returns:
            solid.OpenSCADObject: Combined terrain 3D model
        """
        # Maximum size constraint
        max_size = 100
        
        # Get the base height for proper z-positioning
        base_height = self.params.get('base_height', 1)
        
        # Generate terrain models for each type
        terrain_models = []
        
        # Generate each terrain model
        for terrain_type in terrain_types:
            
            # Set the current terrain type
            self.params['terrain_type'] = terrain_type
            
            # Generate the terrain model based on type
            if terrain_type == 'spiral_chart':
                terrain_model = self.generate_spiral_chart()
            elif terrain_type == 'bar_chart':
                terrain_model = self.generate_bar_chart()
            elif terrain_type == 'pyramid':
                terrain_model = self.generate_pyramid()
            elif terrain_type == 'surface_plot':
                terrain_model = self.generate_surface_plot()
            else:
                logger.warning(f"Unknown terrain type: {terrain_type}, skipping")
                continue
            
            terrain_models.append(terrain_model)
         
        combined_model = None
        
        # Determine how to arrange the terrain models based on the number of models
        num_models = len(terrain_models)

        combined_parts = []
        
        # arrange multiple models in a circle
        for i,model in enumerate(terrain_models):

            # Calculate position on the circle
            angle = 2 * math.pi * i / num_models
            radius = i/num_models * 0.3  # Position at 30% of max_dim from center
            
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            # Position the model
            positioned_model = translate([x, y, 0])(model)
            
            combined_parts.append(positioned_model)
        
        combined_model = union()(*combined_parts)
        
        return combined_model
    
    def generate_text(self):
        """
        Generate text for the badge. Only limited amount of characters
         possible due to laptop compute and memory resource restrictions.
        Text is placed on a small rectangular plate underneath the base.
        
        Returns:
            solid.OpenSCADObject: Text 3D model with supporting plate
        """
        text_depth = self.params.get('text_depth', 1)  # Reduced depth for better fit
        text_size = self.params.get('text_size', 8)    # Smaller text size to fit on plate
        text_content = self.params.get('text_content', self.ticker_symbol)
        text_position = self.params.get('text_position', 0)
        
        # We can only add limited text characters owing to 
        # Model complexity. modelling restrictions on laptop compute and memory.
        text_2d = text(text_content, size=text_size, halign='center', valign='center')
        
        # Calculate the approximate dimensions of the text for the plate
        # Add a small margin around the text
        text_margin = 2
        text_width = len(text_content) * (text_size*0.9) + text_margin * 2  # Approximate width based on character count
        text_height = text_size + text_margin * 2
        plate_thickness = 0.5  # Thin plate
        
        # Create a small rectangular plate for the text
        plate = cube([text_width, text_height, plate_thickness], center=True)
        
        # Create the text as a negative space (hole) in the plate
        # First, create the text as a 3D object
        text_3d = linear_extrude(height=text_depth)(text_2d)
        
        # Mirror the text so it appears correctly when viewed from below
        mirrored_text = mirror([0, 1, 0])(text_3d)
        
        # Position the text on the plate
        positioned_text = translate([0, 0, -text_depth])(mirrored_text)
        
        # Combine the plate and text
        # The text is positioned to be embedded in the plate
        text_with_plate = union()(
            plate,
            positioned_text
        )
        
        # Position the model underneath the base
        base_height = self.params.get('base_height', 1)
        z_pos = text_depth  # Position below the base
        
        # Rotate and position the text
        rotated_model = rotate([0, 0, text_position])(text_with_plate)
        self.text_model = translate([0,0, 0])(rotated_model)
        
        return self.text_model
    
    def combine_models(self):
        """
        Combine base, feature, and text models into the final model.
        
        Generates any missing model components before combining.
        
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
        
        self.final_model = combined
        
        return self.final_model
    
    
    def generate_pyramid(self):
        """
        Generate a pyramid feature with height based on stock data.
        The pyramid sides are varied and spikey based on the stock data.
        Adapts to the badge shape (circular, rectangular, or triangular).
        Ensures the model fits within 100x100 dimensions.
        
        Returns:
            solid.OpenSCADObject: Pyramid 3D model with varied and spikey sides
        """
        # Maximum size constraint
        max_size = 100
        
        # Determine badge type and set appropriate dimensions
        if isinstance(self, RectangularBadge):
            # For rectangular badges
            base_width = self.params.get('base_width', 100)
            base_depth = self.params.get('base_depth', 60)
            # Use smaller dimension for better proportions, ensure it's within bounds
            base_size = min(base_width, base_depth) * 0.7  # Reduced from 0.8 to ensure it fits
            # Create a square base for the pyramid
            base_points = [
                [-base_size/2, -base_size/2],
                [base_size/2, -base_size/2],
                [base_size/2, base_size/2],
                [-base_size/2, base_size/2]
            ]
            # Height multiplier for rectangular badges - moderate craziness
            height_multiplier = random.randint(2, 4)  # Reduced from 3-6
            # Add extra points to create more complex shapes, but with less extreme offsets
            if random.random() > 0.5:  # 50% chance to add extra points
                # Add midpoints with smaller random offsets for more complex shape
                extra_points = []
                for j in range(len(base_points)):
                    p1 = base_points[j]
                    p2 = base_points[(j+1) % len(base_points)]
                    mid_x = (p1[0] + p2[0]) / 2
                    mid_y = (p1[1] + p2[1]) / 2
                    # Add random offset to midpoint (reduced from 0.1 to 0.05)
                    offset = base_size * 0.05 * random.uniform(-1, 1)
                    if j % 2 == 0:  # Alternate between x and y offset
                        mid_x += offset
                    else:
                        mid_y += offset
                    extra_points.append([mid_x, mid_y])
                
                # Interleave the original points with the new midpoints
                new_points = []
                for j in range(len(base_points)):
                    new_points.append(base_points[j])
                    new_points.append(extra_points[j])
                base_points = new_points
            
            # Extra variation for rectangular badges (reduced from 0.25)
            extra_variation = 0.15
            
        elif isinstance(self, TriangularBadge):
            # For triangular badges
            side_length = self.params.get('side_length', 80)
            # Calculate the center of the triangle
            x_center = side_length / 2
            y_center = (side_length * math.sin(math.radians(60))) / 3
            # Create an equilateral triangle centered at (0,0)
            base_points = [
                [-x_center, -y_center],
                [side_length - x_center, -y_center],
                [side_length/2 - x_center, side_length * math.sin(math.radians(60)) - y_center]
            ]
            # Height multiplier for triangular badges - moderate craziness
            height_multiplier = random.randint(2, 5)  # Reduced from 3-6
            # Extra variation for triangular badges (reduced from 0.2)
            extra_variation = 0.15
            
        else:
            # For disc badges (or any other type)
            radius = min(self.params.get('base_radius', 50) * 0.7, max_size/2 * 0.7)  # Ensure radius fits within bounds
            # Create a regular polygon with more sides for more complex shape
            num_sides = random.randint(8, 12)  # Reduced from 8-16
            base_points = []
            for i in range(num_sides):
                angle = 2 * math.pi * i / num_sides
                # Add some randomness to the radius for each point (reduced from 0.1)
                point_radius = radius * (1 + 0.05 * random.uniform(-1, 1))
                x = point_radius * math.cos(angle)
                y = point_radius * math.sin(angle)
                base_points.append([x, y])
            # Height multiplier for disc badges - moderate craziness
            height_multiplier = random.randint(2, 4)  # Reduced from 3-6
            # Extra variation for disc badges (reduced from 0.25)
            extra_variation = 0.15
        
        # Use the average of normalized close prices for the pyramid height
        # Apply different height multipliers based on badge type
        pyramid_height = self.data['Close_Normalized'].mean() * height_multiplier
        
        # Ensure pyramid height doesn't exceed max_size/2 for better proportions
        if pyramid_height > max_size/2:
            pyramid_height = max_size/2
        
        # Create the pyramid with varied and spikey sides based on stock data
        layers = height_multiplier * 10  # (Reduced from 15)
        
        # Ensure minimum number of layers
        if layers < 15:
            layers = 15
        
        pyramid_parts = []
        
        # Cycle through the stock data for each layer
        for i in range(layers):
            # Get data points for this layer (cycling through the data if needed)
            data_idx = i % len(self.data)
            close_value = self.data['Close_Normalized'].iloc[data_idx]
            volume_value = self.data['Volume_Width'].iloc[data_idx]
            
            # Calculate the scale factor for this layer, varied by stock data
            # Base scale decreases as we go up the pyramid
            base_scale = 1.0 - (i / layers)
            
            # Vary the scale based on stock data to create spikes
            # Use close price to vary the scale, making it more spikey
            variation = (0.1 + extra_variation) * close_value
            scale_factor = base_scale * (1.0 + variation)
            
            # Calculate the height for this layer
            layer_height = pyramid_height * (i / layers)
            
            # Create varied points for this layer to make it spikey
            varied_points = []
            for j, point in enumerate(base_points):
                # Add variation to each point based on stock data
                # This creates the spikey effect
                point_variation = (0.1 + extra_variation) * volume_value  # (reduced from 0.15)
                
                # Different variation for each point to create asymmetry
                # Add more randomness to the variation
                phase_shift = i * 0.2 + random.uniform(0, 0.1)
                x_var = point_variation * math.sin(j * 2 * math.pi / len(base_points) + phase_shift)
                y_var = point_variation * math.cos(j * 2 * math.pi / len(base_points) + phase_shift)
                
                # Scale and vary the point
                varied_x = point[0] * scale_factor * (1 + x_var)
                varied_y = point[1] * scale_factor * (1 + y_var)
                
                # Ensure point stays within bounds
                max_coord = max_size/2 * 0.9  # 90% of half max_size
                varied_x = max(min(varied_x, max_coord), -max_coord)
                varied_y = max(min(varied_y, max_coord), -max_coord)
                
                varied_points.append([varied_x, varied_y])
            
            # Create the layer with varied points
            layer_2d = polygon(varied_points)
            
            # Vary the layer height based on stock data
            layer_thickness = pyramid_height/layers * (1 + (0.15 + extra_variation) * close_value)  # Reduced from 0.2
            
            # Occasionally create a thicker layer for dramatic effect (reduced frequency and magnitude)
            if random.random() > 0.95:  # 5% chance (reduced from 10%)
                layer_thickness *= random.uniform(1.2, 1.8)  # Reduced from 1.5-2.5
            
            layer_3d = linear_extrude(height=layer_thickness)(layer_2d)
            
            # Position the layer
            pyramid_parts.append(
                translate([0, 0, layer_height])(layer_3d)
            )
        
        return union()(pyramid_parts)
    
    def generate_spiral_chart(self):
        """
        Generate a spiral landscape model based on stock data.
        Adapts to fit within the base shape (circular or rectangular).
        Includes a thin disc at the bottom for stability.
        
        Returns:
            solid.OpenSCADObject: Spiral landscape 3D model
        """
        radius = self.params.get('spiral_radius', self.params.get('base_radius', 50) * 0.8)
        # Generate a random factor between 0 and 2.0 that affects the terrain
        # 0.0 = empty model, 1.0 = normal model, 2.0 = complex/exaggerated model
        random_factor = random.uniform(0.0, 2.0)
        spiral_turns = self.params.get('spiral_turns', 7)
        
        # Generate points on a spiral
        num_points = len(self.data)
        angles = np.linspace(0, spiral_turns * 2 * np.pi, num_points)  # Spiral angles
        radii = np.linspace(0, radius, num_points)  # Gradually increase radius for spiral
        
        # Map normalized stock prices to heights and widths, affected by random_factor
        # When random_factor is 0, heights will be minimal
        # When random_factor is 1, heights will be normal
        # When random_factor is 2, heights will be doubled
        heights = self.data['Close_Normalized'] * 2 * random_factor
        widths = self.data['Volume_Width'] * random_factor
        
        # Calculate coordinates
        x = radii * np.cos(angles)  # X coordinates
        y = radii * np.sin(angles)  # Y coordinates
        
        # Create the landscape as a series of cylinders
        landscape = []
        
        # Add a thin disc at the bottom for stability
        disc_thickness = 0.5  # Thin disc (0.5 units thick)
        disc_radius = radius * 1.1  # Slightly larger than the spiral radius
        
        # Create the thin disc and add it to the landscape
        bottom_disc = cylinder(r=disc_radius, h=disc_thickness, center=False)
        landscape.append(bottom_disc)
        
        # Add the spiral cylinders
        for i in range(num_points):
            cylinder_height = heights.iloc[i]
            cylinder_radius = widths.iloc[i]

            # Make sure the cylinders are not too small... they break off easily otherwise (3mm)
            if cylinder_radius < 3:
                cylinder_radius = 3 

            landscape.append(
                translate([x[i], y[i], disc_thickness])(  # Position cylinders on top of the disc
                    cylinder(r=cylinder_radius, h=cylinder_height, center=False)
                )
                )
        
        # Combine the landscape into a single object
        return union()(landscape)
        
    def generate_bar_chart(self):
        """
        Generate a bar chart model based on stock prices.
        Adapts to the badge shape (circular, rectangular, or triangular).
        Includes a thin plate at the bottom for stability that covers all bar chart extremities.
        
        Returns:
            solid.OpenSCADObject: Bar chart 3D model
        """
        # Generate a random factor between 0 and 2.0 that affects the terrain
        # 0.0 = empty model, 1.0 = normal model, 2.0 = complex/exaggerated model
        random_factor = random.uniform(0.0, 2.0)
        plate_thickness = 0.5  # Thin plate (0.5 units thick)
        
        # Determine badge type and set appropriate dimensions
        if isinstance(self, DiscBadge):
            # For disc badges, create a circular arrangement of bars
            radius = self.params.get('base_radius', 50) * 0.8
            num_points = len(self.data)
            angles = np.linspace(0, 2 * np.pi, num_points)
            
            # Create bars in a circular arrangement and track the maximum distance from center
            bars = []
            max_distance = 0
            
            for i in range(num_points):
                # Apply random_factor to bar height
                bar_height = self.data['Close_Normalized'].iloc[i] * 2 * random_factor
                # Apply random_factor to bar dimensions
                bar_width = 2 * np.pi * radius / num_points * 0.7 * max(0.2, random_factor)  # Width as a fraction of circumference
                bar_depth = radius * 0.3 * max(0.2, random_factor)  # Depth as a fraction of radius
                
                # Calculate position on the circle
                angle = angles[i]
                x_pos = radius * 0.7 * np.cos(angle)  # Position at 70% of radius
                y_pos = radius * 0.7 * np.sin(angle)
                
                # Calculate the distance from center to the furthest point of this bar
                # The furthest point is at the corner of the bar furthest from the center
                # We need to account for the bar's rotation and dimensions
                
                # Calculate the corners of the bar before rotation
                corners = [
                    [0, 0],  # Near corner
                    [bar_depth, 0],  # Far corner along depth
                    [0, bar_width],  # Far corner along width
                    [bar_depth, bar_width]  # Far corner diagonally
                ]
                
                # Rotate the corners and find the maximum distance
                for corner in corners:
                    # Rotate the corner
                    rotated_x = corner[0] * math.cos(angle) - corner[1] * math.sin(angle)
                    rotated_y = corner[0] * math.sin(angle) + corner[1] * math.cos(angle)
                    
                    # Add the position offset
                    corner_x = x_pos + rotated_x
                    corner_y = y_pos + rotated_y
                    
                    # Calculate distance from center
                    distance = math.sqrt(corner_x**2 + corner_y**2)
                    max_distance = max(max_distance, distance)
                
                # Rotate the bar to point outward from center
                bars.append(
                    translate([x_pos, y_pos, 0])(
                        rotate([0, 0, angle * 180 / np.pi])(
                            cube([bar_depth, bar_width, bar_height])
                        )
                    )
                )
            
            # Create the combined bars model
            bars_model = union()(bars)
            
            # Add a thin disc at the bottom for stability
            # Use the calculated maximum distance to ensure the plate covers all bars
            # Add a 10% margin to ensure complete coverage
            plate_radius = max_distance * 1.1
            bottom_plate = cylinder(r=plate_radius, h=plate_thickness, center=False)
            
            # Combine the plate and bars
            return union()([
                bottom_plate,
                translate([0, 0, plate_thickness])(bars_model)
            ])
        else:
            # For rectangular and triangular badges
            base_width = self.params.get('base_width', 100)
            base_depth = self.params.get('base_depth', 60)
            bar_width = base_width / len(self.data)
            
            # Create bars for each data point and track the actual dimensions
            bars = []
            min_x = float('inf')
            max_x = float('-inf')
            min_y = float('inf')
            max_y = float('-inf')
            
            for i in range(len(self.data)):
                # Apply random_factor to bar height
                bar_height = self.data['Close_Normalized'].iloc[i] * 2 * random_factor
                bar_depth = base_depth * 0.7 * max(0.2, random_factor)  # Make bars slightly narrower than the base
                
                # Position each bar along the x-axis
                x_pos = i * bar_width
                y_pos = (base_depth - bar_depth) / 2  # Center bars on the y-axis
                
                # Calculate the actual dimensions of this bar
                bar_min_x = x_pos
                bar_max_x = x_pos + bar_width * 0.9 * max(0.2, random_factor)
                bar_min_y = y_pos
                bar_max_y = y_pos + bar_depth
                
                # Update the overall min/max coordinates
                min_x = min(min_x, bar_min_x)
                max_x = max(max_x, bar_max_x)
                min_y = min(min_y, bar_min_y)
                max_y = max(max_y, bar_max_y)
                
                bars.append(
                    translate([x_pos, y_pos, 0])(
                        cube([bar_width * 0.9 * max(0.2, random_factor), bar_depth, bar_height])
                    )
                )
            
            # Calculate the actual width and depth of the bar chart
            actual_width = max_x - min_x
            actual_depth = max_y - min_y
            
            # Translate the bars to center them at the origin
            centered_bars = []
            for bar in bars:
                centered_bars.append(translate([-base_width/2, -base_depth/2, 0])(bar))
            
            # Create the combined bars model
            bars_model = union()(centered_bars)
            
            # Add a thin plate at the bottom for stability
            # Use the calculated actual dimensions to ensure the plate covers all bars
            # Add a 10% margin to ensure complete coverage
            plate_width = actual_width * 1.1
            plate_depth = actual_depth * 1.1
            
            # Create the thin plate centered at the origin
            # Adjust the position to account for the actual center of the bar chart
            plate_center_x = (min_x + max_x) / 2 - base_width / 2
            plate_center_y = (min_y + max_y) / 2 - base_depth / 2
            
            bottom_plate = translate([plate_center_x - plate_width/2, plate_center_y - plate_depth/2, 0])(
                cube([plate_width, plate_depth, plate_thickness])
            )
            
            # Combine the plate and bars
            return union()([
                bottom_plate,
                translate([0, 0, plate_thickness])(bars_model)
            ])
    
    def generate_surface_plot(self):
        """
        Generate a surface plot model based on stock data.
        Includes a thin plate at the bottom for stability.
        
        Returns:
            solid.OpenSCADObject: Surface plot 3D model
        """
        # Generate a random factor between 0 and 2.0 that affects the terrain
        # 0.0 = empty model, 1.0 = normal model, 2.0 = complex/exaggerated model
        random_factor = random.uniform(0.0, 2.0)
        
        base_width = self.params.get('base_width', 100)
        base_depth = self.params.get('base_depth', 60)
        
        # Create a grid of points
        # Apply random_factor to grid size for more/less complexity
        base_grid_size = int(math.sqrt(len(self.data)))
        if random_factor > 1.0:
            # More complex grid for higher random factors
            grid_size = max(2, int(base_grid_size * (1 + (random_factor - 1) * 0.5)))
        else:
            # Simpler grid for lower random factors
            grid_size = max(2, int(base_grid_size * random_factor))
        
        # Truncate data to fit grid
        data_points = min(grid_size * grid_size, len(self.data))
        # Apply random_factor to heights
        heights = self.data['Close_Normalized'].iloc[:data_points].values * random_factor
        
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
        
        # Calculate center offsets to center the surface plot at (0,0)
        x_center = base_width / 2
        y_center = base_depth / 2
        
        # Create cells for the surface
        cells = []
        
        # Add a thin plate at the bottom for stability
        plate_thickness = 0.5  # Thin plate (0.5 units thick)
        plate_width = base_width * 1.1  # Slightly larger than the surface width
        plate_depth = base_depth * 1.1  # Slightly larger than the surface depth
        
        # Create the thin plate and add it to the cells
        bottom_plate = translate([-plate_width/2, -plate_depth/2, 0])(
            cube([plate_width, plate_depth, plate_thickness])
        )
        cells.append(bottom_plate)
        for i in range(grid_size):
            for j in range(grid_size):
                cell_height = height_grid[i, j]
                
                # Calculate position, centered at (0,0)
                x_pos = i * cell_width - x_center
                y_pos = j * cell_depth - y_center
                
                # Apply random_factor to cell dimensions
                # When random_factor is close to 0, cells will be very small or non-existent
                # When random_factor is 1, cells will be normal size
                # When random_factor is 2, cells will be more varied and potentially larger
                cell_width_factor = max(0.1, random_factor * (0.8 + 0.4 * random.random()))
                cell_depth_factor = max(0.1, random_factor * (0.8 + 0.4 * random.random()))
                
                cells.append(
                    translate([x_pos, y_pos, 0])(
                        cube([cell_width * cell_width_factor, cell_depth * cell_depth_factor, cell_height])
                    )
                )
        
        return union()(cells)
    
    def save_to_file(self, filename=None):
        """
        Save the model to an OpenSCAD file in the scad_models directory.
        
        Args:
            filename (str): Output filename
            
        Returns:
            str: Path to the saved file
        """
        if self.final_model is None:
            self.combine_models()
        
        if filename is None:
            filename = f"{self.ticker_symbol}_badge.scad"
        
        # Ensure scad_models directory exists
        scad_models_dir = Path("./scad_models")
        scad_models_dir.mkdir(exist_ok=True)
        
        # Create full path to file in scad_models directory, stripping any directory components
        filepath = (scad_models_dir / Path(filename).name).resolve()

        # Ensure the resolved path stays within scad_models
        if not str(filepath).startswith(str(scad_models_dir.resolve())):
            raise ValueError(f"Invalid filename: path escapes scad_models directory")
        
        # Save the model
        scad_render_to_file(self.final_model, filepath)
        logger.info(f"Model saved to {filepath}")
        
        return str(filepath)
    
    @staticmethod
    def test_openscad():
        """Test if OpenSCAD is available and working."""
        try:
            result = subprocess.run([OPENSCAD_PATH, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"OpenSCAD found: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"OpenSCAD test failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"OpenSCAD test error: {e}")
            return False
    
    def save_to_stl_async(self, filename=None):
        """
        Start STL generation in background without blocking.
        Returns immediately, STL file will be available later.
        """
        import threading
        
        def generate_stl():
            try:
                result = self.save_to_stl(filename)
                if result:
                    logger.info(f"Async STL generation completed: {result}")
                else:
                    logger.warning("Async STL generation failed")
            except Exception as e:
                logger.error(f"Async STL generation error: {e}")
        
        thread = threading.Thread(target=generate_stl, daemon=True)
        thread.start()
        logger.info("STL generation started in background")
        return True
    
    def save_to_stl(self, filename=None):
        """
        Save the model to an STL file for 3D visualization.
        Requires OpenSCAD to be installed on the system.
        
        Args:
            filename (str): Output filename (without extension)
            
        Returns:
            str: Path to the saved STL file, or None if conversion failed
        """
        if self.final_model is None:
            self.combine_models()
        
        if filename is None:
            filename = f"{self.ticker_symbol}_badge"
        
        # Remove .stl extension if provided
        if filename.endswith('.stl'):
            filename = filename[:-4]
        
        # Ensure directories exist
        scad_models_dir = Path("./scad_models")
        stl_models_dir = Path("./stl_models")
        scad_models_dir.mkdir(exist_ok=True)
        stl_models_dir.mkdir(exist_ok=True)
        
        # File paths
        scad_path = scad_models_dir / f"{filename}.scad"
        stl_path = stl_models_dir / f"{filename}.stl"
        
        try:
            # Test OpenSCAD first
            if not self.test_openscad():
                logger.error("OpenSCAD test failed, skipping STL generation")
                return None
            
            # First save to SCAD
            scad_render_to_file(self.final_model, scad_path)
            logger.info(f"SCAD model saved to {scad_path}")
            
            # Convert SCAD to STL using OpenSCAD with optimization flags
            cmd = [
                OPENSCAD_PATH,
                '-o', str(stl_path),
                '--render',  # Force render mode
                '--quiet',   # Reduce output
                str(scad_path)
            ]
            logger.info(f"Running OpenSCAD command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=OPENSCAD_TIMEOUT)
            
            if result.returncode == 0:
                logger.info(f"STL model saved to {stl_path}")
                return str(stl_path)
            else:
                logger.error(f"OpenSCAD conversion failed with return code {result.returncode}")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"OpenSCAD conversion timed out after {OPENSCAD_TIMEOUT} seconds")
            logger.error(f"Command was: {' '.join(cmd)}")
            return None
        except FileNotFoundError:
            logger.error(f"OpenSCAD not found at path: {OPENSCAD_PATH}")
            logger.error("STL export requires OpenSCAD installation. Check OPENSCAD_PATH in .env file")
            return None
        except Exception as e:
            logger.error(f"Error during STL export: {e}")
            return None

class DiscBadge(Badge3DModel):
    """
    Circular badge with stock data features.
    
    Version 1.0 - Cline implementation for Martin East - Implements circular badge with jagged edge and spiral features - Apr 13, 2025.
    Version 2.0 - Martin East - Simplify, move most methods to base class - Apr 15, 2025.

    Class relies on a 'params' dictionary to set the parameters for the badge. It assumes defaults if no parameters given.
        """
    
    def generate_base(self):
        """
        Generate a circular base for the badge.
        
        Returns:
            solid.OpenSCADObject: Base 3D model
        """

        # Assume sensible defaults if no params given.
        radius = self.params.get('base_radius', 50)
        height = self.params.get('base_height', 1)
    
        base_radius = self.params.get('base_radius', 50)
        z_offset = 0  # Position the base at z=0, consistent with other badge types
        
        # For making a jagged edge:
        # Parameters for the polygon
        num_points = len(self.data)  # Use all data points
        angles = np.linspace(0, 2 * np.pi, num_points)  # Angles around the circle
        
        # Map normalized stock prices to the polygon edge to make it jagged.
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

        Each generate terrain is different for each badge type.
        
        Returns:
            solid.OpenSCADObject: Feature 3D model
        """
        # Get the base height for proper z-positioning
        base_height = self.params.get('base_height', 1)
        
        # Check if multiple terrain types are specified
        terrain_types = self.params['terrain_types']
            
        terrain_model = self.generate_combined_terrain(terrain_types)
        
        # Apply z-offset to the terrain model
        self.terrain_model = translate([0, 0, base_height])(terrain_model)
        
        return self.terrain_model
        
class RectangularBadge(Badge3DModel):
    """
    Rectangular badge with stock data features. Specialisation of Badge3DModel.
    
    Version 1.0 - Cline implementation for Martin East - Implements rectangular badge with bar chart and surface plot features - Apr 13, 2025.
    Version 2.0 - Martin East - move most methods to base class - Apr 15, 2025.
    Version 2.1 - Martin East - debug and fix depth issues - Apr 17, 2025.
    """
    
    def generate_base(self):
        """
        Generate a rectangular base for the badge with jagged edges based on stock prices.

        Assume defaults for params if not given.
        
        Returns:
            solid.OpenSCADObject: Base 3D model
        """
        width = self.params.get('base_width', 100)
        depth = self.params.get('base_depth', 60)
        height = self.params.get('base_height', 1)
        z_offset = 0

        # Number of points to use on each side of the rectangle
        # Distribute the data points around the perimeter
        num_points = len(self.data)

        points_per_side = num_points // 4  # Distribute points across 4 sides
        
        points = []
        
        # Make sure the badge edges don't get too big with the jaggedness
        max_variation = min(width, depth) * 0.2  # 20% of the smaller dimension
        
        # Create the edge variations from normalised stock data.
        variations = self.data['Close_Normalized'] * max_variation / self.data['Close_Normalized'].max()
        
        # Calculate center offsets to center the rectangle at (0,0)
        x_center = width / 2
        y_center = depth / 2
        
        # Generate points for each side of the rectangle with variations
        # Bottom side (left to right)
        for i in range(points_per_side):
            data_idx = i % len(variations)
            x = (i / points_per_side) * width - x_center
            y = -variations.iloc[data_idx] - y_center  # Vary outside the base
            points.append([x, y])
        
        # Right side (bottom to top)
        for i in range(points_per_side):
            data_idx = (points_per_side + i) % len(variations)
            x = width + variations.iloc[data_idx] - x_center  # Vary outside the base
            y = (i / points_per_side) * depth - y_center
            points.append([x, y])
        
        # Top side (right to left)
        for i in range(points_per_side):
            data_idx = (2 * points_per_side + i) % len(variations)
            x = width - (i / points_per_side) * width - x_center
            y = depth + variations.iloc[data_idx] - y_center  # Vary outside the base
            points.append([x, y])
        
        # Left side (top to bottom)
        for i in range(points_per_side):
            data_idx = (3 * points_per_side + i) % len(variations)
            x = -variations.iloc[data_idx] - x_center  # Vary outside the base
            y = depth - (i / points_per_side) * depth - y_center
            points.append([x, y])
        
        # Create 2D polygon and extrude to 3D
        jagged_rect_2d = polygon(points)
        jagged_rect_3d = linear_extrude(height=height)(jagged_rect_2d)
        
        # Apply z-offset
        self.base_model = translate([0, 0, z_offset])(jagged_rect_3d)
        return self.base_model
    
    def generate_terrain(self):
        """
        Generate terrain on the badge based on stock data.
        
        Returns:
            solid.OpenSCADObject: Feature 3D model
        """
        # Get the base height for proper z-positioning
        base_height = self.params.get('base_height', 1)
        
        # Store base dimensions for reference
        base_width = self.params.get('base_width', 100)
        base_depth = self.params.get('base_depth', 60)
        
        # Check if multiple terrain types are specified
        if 'terrain_types' in self.params:
            terrain_types = self.params['terrain_types']
            
            # Generate combined terrain model
            terrain_model = self.generate_combined_terrain(terrain_types)
        else:
            # Single terrain type
            terrain_type = self.params.get('terrain_type', 'bar_chart')
            
            if terrain_type == 'spiral_chart':
                # Pass base dimensions to ensure spiral fits within the base
                self.params['spiral_radius'] = min(base_width, base_depth) * 0.35
                terrain_model = self.generate_spiral_chart()
            elif terrain_type == 'bar_chart':
                terrain_model = self.generate_bar_chart()
            elif terrain_type == 'pyramid':
                terrain_model = self.generate_pyramid()
            elif terrain_type == 'surface_plot':
                terrain_model = self.generate_surface_plot()
            else:
                logger.warning(f"Unknown terrain type: {terrain_type}, using bar_chart")
                terrain_model = self.generate_bar_chart()
        
        # Centre the terrain over the zero point and at the correct height
        self.terrain_model = translate([0, 0, base_height])(terrain_model)
        
        return self.terrain_model
   
class TriangularBadge(Badge3DModel):
    """
    Triangular badge with stock data features. Specialisation of Badge3DModel.
    
    Version 1.0 - Cline implementation for Martin East - Implements triangular badge with pyramid and terrain features - Apr 13, 2025.
    Version 2.0 - Martin East - move most methods to base class - Apr 15, 2025.
    """
    
    def generate_base(self):
        """
        Generate a triangular base for the badge with jagged edges based on stock prices.
        
        Version 4.0: Cline implementation for Martin East - Added jagged edges to triangular badge - Apr 23, 2025.

        
        Returns:
            solid.OpenSCADObject: Base 3D model
        """
        side_length = self.params.get('side_length', 80)
        height = self.params.get('base_height', 3)
        z_offset = 0
        
        # Calculate the center of the triangle to center it at (0,0)
        x_center = side_length / 2
        y_center = (side_length * math.sin(math.radians(60))) / 3
        
        # Calculate the vertices of the equilateral triangle
        triangle_height = side_length * math.sin(math.radians(60))
        base_points = [
            [-x_center, -y_center],  # Bottom left
            [side_length - x_center, -y_center],  # Bottom right
            [side_length/2 - x_center, triangle_height - y_center]  # Top
        ]
        
        # Number of points to use on each side of the triangle
        # We'll distribute the data points around the perimeter
        num_points = len(self.data)
        points_per_side = num_points // 3  # Distribute points across 3 sides
        
        # Create points for the polygon
        points = []
        
        # Calculate how much to vary the points based on stock data
        max_variation = side_length * 0.15  # 15% of the side length
        
        # Map normalized stock prices to variations
        variations = self.data['Close_Normalized'] * max_variation / self.data['Close_Normalized'].max()
        
        # Generate points for each side of the triangle with variations
        # Side 1: Bottom (left to right)
        for i in range(points_per_side):
            data_idx = i % len(variations)
            # Interpolate between bottom left and bottom right vertices
            t = i / points_per_side
            x = base_points[0][0] * (1 - t) + base_points[1][0] * t
            y = base_points[0][1] * (1 - t) + base_points[1][1] * t
            
            # Calculate normal vector to the edge (perpendicular)
            # For bottom edge, normal points down
            normal_x = 0
            normal_y = -1
            
            # Vary the point along the normal vector
            x += normal_x * variations.iloc[data_idx]
            y += normal_y * variations.iloc[data_idx]
            
            points.append([x, y])
        
        # Side 2: Right side (bottom to top)
        for i in range(points_per_side):
            data_idx = (points_per_side + i) % len(variations)
            # Interpolate between bottom right and top vertices
            t = i / points_per_side
            x = base_points[1][0] * (1 - t) + base_points[2][0] * t
            y = base_points[1][1] * (1 - t) + base_points[2][1] * t
            
            # Calculate normal vector to the edge (perpendicular)
            # For right edge, normal points to the right and slightly up
            edge_dx = base_points[2][0] - base_points[1][0]
            edge_dy = base_points[2][1] - base_points[1][1]
            length = math.sqrt(edge_dx**2 + edge_dy**2)
            normal_x = edge_dy / length
            normal_y = -edge_dx / length
            
            # Vary the point along the normal vector
            x += normal_x * variations.iloc[data_idx]
            y += normal_y * variations.iloc[data_idx]
            
            points.append([x, y])
        
        # Side 3: Left side (top to bottom)
        for i in range(points_per_side):
            data_idx = (2 * points_per_side + i) % len(variations)
            # Interpolate between top and bottom left vertices
            t = i / points_per_side
            x = base_points[2][0] * (1 - t) + base_points[0][0] * t
            y = base_points[2][1] * (1 - t) + base_points[0][1] * t
            
            # Calculate normal vector to the edge (perpendicular)
            # For left edge, normal points to the left and slightly up
            edge_dx = base_points[0][0] - base_points[2][0]
            edge_dy = base_points[0][1] - base_points[2][1]
            length = math.sqrt(edge_dx**2 + edge_dy**2)
            normal_x = edge_dy / length
            normal_y = -edge_dx / length
            
            # Vary the point along the normal vector
            x += normal_x * variations.iloc[data_idx]
            y += normal_y * variations.iloc[data_idx]
            
            points.append([x, y])
        
        # Create 2D polygon and extrude to 3D
        jagged_triangle_2d = polygon(points)
        jagged_triangle_3d = linear_extrude(height=height)(jagged_triangle_2d)
        
        # Apply z-offset
        self.base_model = translate([0, 0, z_offset])(jagged_triangle_3d)
        return self.base_model
    
    def generate_terrain(self):
        """
        Generate terrain on the badge based on stock data.
        
        Returns:
            solid.OpenSCADObject: Feature 3D model
        """
        # Get the base height for proper z-positioning
        base_height = self.params.get('base_height', 3)
        
        # Check if multiple terrain types are specified
        if 'terrain_types' in self.params:
            terrain_types = self.params['terrain_types']
            
            # Generate combined terrain model
            terrain_model = self.generate_combined_terrain(terrain_types)
        else:
            # Single terrain type
            terrain_type = self.params.get('terrain_type', 'pyramid')
            terrain_model = None
            
            if terrain_type == 'pyramid':
                # Use the base class pyramid generator
                terrain_model = self.generate_pyramid()
            elif terrain_type == 'terrain' or terrain_type == 'spiral_chart':
                terrain_model = self._generate_terrain()
            elif terrain_type == 'bar_chart':
                terrain_model = self.generate_bar_chart()
            elif terrain_type == 'surface_plot':
                terrain_model = self.generate_surface_plot()
            else:
                logger.warning(f"Unknown terrain type: {terrain_type}, using pyramid")
                terrain_model = self.generate_pyramid()
        
        # Apply z-offset to the terrain model
        self.terrain_model = translate([0, 0, base_height])(terrain_model)
        
        return self.terrain_model
    
    # The _generate_pyramid method has been moved to the base class
    
    def _generate_terrain(self):
        """
        Generate a terrain feature based on stock data with varied and spikey features.
        
        Returns:
            solid.OpenSCADObject: Terrain 3D model with varied and spikey features
        """
        side_length = self.params.get('side_length', 80)
        
        # Create a triangular grid
        grid_size = 10  # Number of divisions along each side
        
        # Calculate the height of the triangle
        triangle_height = side_length * math.sin(math.radians(60))
        
        # Calculate cell dimensions
        cell_width = side_length / grid_size
        cell_height = triangle_height / grid_size
        
        # Calculate the center of the triangle to center it at (0,0)
        x_center = side_length / 2
        y_center = triangle_height / 3
        
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
                
                # Get the stock data values for this cell
                close_value = self.data['Close_Normalized'].iloc[data_idx]
                volume_value = self.data['Volume_Width'].iloc[data_idx]
                
                # Get the height for this cell, varied by stock data
                # Use close price to determine the base height
                base_height = close_value
                
                # Add variation to make it more spikey
                # Higher volume = more variation in height
                height_variation = 0.3 * volume_value * random.uniform(0.7, 1.3)
                terrain_height = base_height * (1 + height_variation)
                
                # Ensure minimum height
                if terrain_height < 0.5:
                    terrain_height = 0.5
                
                # Calculate position, centered at (0,0)
                # Add some variation to the position based on stock data
                pos_variation_x = 0.1 * cell_width * volume_value * random.uniform(-1, 1)
                pos_variation_y = 0.1 * cell_height * volume_value * random.uniform(-1, 1)
                
                x_pos = j * cell_width + (i * cell_width / 2) - x_center + pos_variation_x
                y_pos = i * cell_height - y_center + pos_variation_y
                
                # Vary the cell dimensions based on stock data
                width_variation = 0.2 * volume_value * random.uniform(0.8, 1.2)
                height_variation = 0.2 * close_value * random.uniform(0.8, 1.2)
                
                cell_width_varied = cell_width * 0.95 * (1 + width_variation)
                cell_height_varied = cell_height * 0.95 * (1 + height_variation)
                
                # Create a more interesting shape for each cell
                # Use cylinders for high volume, cubes for low volume
                if volume_value > 0.5:
                    # For high volume, use cylinders with varied radius
                    radius = min(cell_width_varied, cell_height_varied) / 2
                    cells.append(
                        translate([x_pos, y_pos, 0])(
                            cylinder(r=radius, h=terrain_height, center=False)
                        )
                    )
                else:
                    # For low volume, use cubes with varied dimensions
                    cells.append(
                        translate([x_pos, y_pos, 0])(
                            cube([cell_width_varied, cell_height_varied, terrain_height])
                        )
                    )
        
        return union()(cells)
    
class BadgeFactory:
    """
    Factory class for creating different types of badges.
    
    Version 1.0 - Cline implementation for Martin East - Creates appropriate badge type based on parameters - Apr 13, 2025.
    Version 2.0 - Martin East - Added verbose flag parameter - Apr 24, 2025.
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
    Main function for testing the module separate to the main program. Very useful!
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate 3D badge models from stock data')
    parser.add_argument('--ticker', type=str, default='TSLA', help='Stock ticker symbol')
    parser.add_argument('--data-file', type=str, default='./stock_data', help='Stock data CSV file')
    parser.add_argument('--badge-type', type=str, default='disc', 
                       choices=['disc', 'rectangular', 'triangular'], help='Badge type')
    parser.add_argument('--terrain-types', type=str, help='Comma-separated list of terrain types to combine (spiral_chart, bar_chart, pyramid)')
    parser.add_argument('--output', type=str, help='Output file name')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose (INFO) logging')
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
        
        # Handle multiple terrain types
        if args.terrain_types:
            terrain_types = [t.strip() for t in args.terrain_types.split(',')]
            params['terrain_types'] = terrain_types
       # elif args.terrain_type:
       #     # For backward compatibility
      #      params['terrain_type'] = args.terrain_type
        
        # Set logger level based on verbose flag
        log_level = logging.INFO if args.verbose else logging.WARN
        logger.setLevel(log_level)
        
        # Create the badge
        badge = BadgeFactory.create_badge(args.badge_type, stock_data, args.ticker, params)

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

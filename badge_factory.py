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
Version 4.0 - Martin East - Remove unnecessary complexity, read and tidy - Apr 23, 2025.

"""

# Standard library imports
import os
import math
import random
import logging
from abc import ABC, abstractmethod
from pathlib import Path

# Third-party imports
import numpy as np
import pandas as pd
from solid import *
from solid.utils import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        """Generate the feature part of the model based on stock data."""
        pass
    
    def generate_combined_terrain(self, terrain_types, weights):
        """
        Generate a combined terrain model from multiple terrain types.
        
        Args:
            terrain_types (list): List of terrain type names
            weights (list): List of weights for each terrain type
            
        Returns:
            solid.OpenSCADObject: Combined terrain 3D model
        """
        # Maximum size constraint
        max_size = 100
        
        # Get the base height for proper z-positioning
        base_height = self.params.get('base_height', 1)
        
        # Generate terrain models for each type
        terrain_models = []
        
        # Track the maximum dimensions of all terrain models
        max_width = 0
        max_depth = 0
        
        # Generate each terrain model
        for terrain_type in terrain_types:
            # Store the original terrain type
            original_terrain_type = self.params.get('terrain_type')
            
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
            
            # Restore the original terrain type
            if original_terrain_type:
                self.params['terrain_type'] = original_terrain_type
            else:
                self.params.pop('terrain_type', None)
        
        # If no valid terrain models were generated, return an empty model
        if not terrain_models:
            logger.warning("No valid terrain models were generated")
            return cube([0, 0, 0])
        
        # Determine badge dimensions based on badge type
        if isinstance(self, RectangularBadge):
            base_width = self.params.get('base_width', 100)
            base_depth = self.params.get('base_depth', 60)
            # Use smaller dimension for better proportions
            max_dim = min(base_width, base_depth) * 0.9
        elif isinstance(self, TriangularBadge):
            side_length = self.params.get('side_length', 80)
            max_dim = side_length * 0.9
        else:  # DiscBadge or other
            radius = self.params.get('base_radius', 50)
            max_dim = radius * 1.8  # Diameter * 0.9
        
        # Ensure max_dim doesn't exceed max_size
        max_dim = min(max_dim, max_size * 0.9)
        logger.info(f"Max dimension for terrain models: {max_dim}")
        
        # Calculate the size of each terrain section based on weights
        section_sizes = [max_dim * weight for weight in weights]
        logger.info(f"Section sizes for terrain models: {section_sizes}")
        
        # Combine the terrain models based on weights
        combined_model = None
        
        # Determine how to arrange the terrain models based on the number of models
        num_models = len(terrain_models)
        
        if num_models == 1:
            # Only one terrain model, use it directly
            combined_model = terrain_models[0]
        elif num_models == 2:
            # Two terrain models, split horizontally
            model1 = scale([section_sizes[0]/max_dim, 1, 1])(terrain_models[0])
            model2 = scale([section_sizes[1]/max_dim, 1, 1])(terrain_models[1])
            
            # Position the models side by side
            model1 = translate([-max_dim/2 + section_sizes[0]/2, 0, 0])(model1)
            model2 = translate([max_dim/2 - section_sizes[1]/2, 0, 0])(model2)
            
            combined_model = union()(model1, model2)
        elif num_models == 3:
            # Three terrain models, arrange in a triangle
            model1 = scale([section_sizes[0]/max_dim, section_sizes[0]/max_dim, 1])(terrain_models[0])
            model2 = scale([section_sizes[1]/max_dim, section_sizes[1]/max_dim, 1])(terrain_models[1])
            model3 = scale([section_sizes[2]/max_dim, section_sizes[2]/max_dim, 1])(terrain_models[2])
            
            # Position the models in a triangle
            model1 = translate([0, max_dim/3, 0])(model1)
            model2 = translate([-max_dim/3, -max_dim/6, 0])(model2)
            model3 = translate([max_dim/3, -max_dim/6, 0])(model3)
            
            combined_model = union()(model1, model2, model3)
        elif num_models == 4:
            # Four terrain models, arrange in a 2x2 grid
            model1 = scale([section_sizes[0]/max_dim, section_sizes[0]/max_dim, 1])(terrain_models[0])
            model2 = scale([section_sizes[1]/max_dim, section_sizes[1]/max_dim, 1])(terrain_models[1])
            model3 = scale([section_sizes[2]/max_dim, section_sizes[2]/max_dim, 1])(terrain_models[2])
            model4 = scale([section_sizes[3]/max_dim, section_sizes[3]/max_dim, 1])(terrain_models[3])
            
            # Position the models in a 2x2 grid
            model1 = translate([-max_dim/4, max_dim/4, 0])(model1)
            model2 = translate([max_dim/4, max_dim/4, 0])(model2)
            model3 = translate([-max_dim/4, -max_dim/4, 0])(model3)
            model4 = translate([max_dim/4, -max_dim/4, 0])(model4)
            
            combined_model = union()(model1, model2, model3, model4)
        else:
            # More than 4 terrain models, arrange in a circle
            combined_parts = []
            
            for i, (model, size) in enumerate(zip(terrain_models, section_sizes)):
                # Scale the model based on its weight
                scaled_model = scale([size/max_dim, size/max_dim, 1])(model)
                
                # Calculate position on the circle
                angle = 2 * math.pi * i / num_models
                radius = max_dim * 0.3  # Position at 30% of max_dim from center
                
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                
                # Position the model
                positioned_model = translate([x, y, 0])(scaled_model)
                
                combined_parts.append(positioned_model)
            
            combined_model = union()(*combined_parts)
        
        return combined_model
    
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
            # For bottom text, we need to position it below the base
            # The base is at z=0, so we position the text at a negative z value
            # to make it visible from below
            z_pos = -text_depth  # Position text below the base
            self.text_model = translate([0, 0, z_pos])(self.text_model)
        elif text_position == 'top':
            # Position text on the top of the badge
            base_height = self.params.get('base_height', 3)
            feature_height = self.params.get('feature_height', 2)
            z_pos = base_height + feature_height
            self.text_model = translate([0, 0, z_pos])(self.text_model)
        
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
        
        Returns:
            solid.OpenSCADObject: Spiral landscape 3D model
        """
        # Determine if this is a rectangular badge by checking for base_width and base_depth
        # and by checking the class name
        is_rectangular = isinstance(self, RectangularBadge) or (hasattr(self, 'generate_base') and 'base_width' in self.params and 'base_depth' in self.params)
        
        # Set radius based on badge type
        if is_rectangular:
            # For rectangular badges, use dimensions that fit within the rectangle
            base_width = self.params.get('base_width', 100)
            base_depth = self.params.get('base_depth', 60)
            
            # Use the smaller dimension (minus margin) to ensure spiral fits within the base
            # Reduce to 35% to ensure it fits better
            radius = min(base_width, base_depth) * 0.35
            
            # Override spiral_radius if provided
            radius = self.params.get('spiral_radius', radius)
        else:
            # For circular badges, use the default or provided radius
            radius = self.params.get('spiral_radius', 45)
        
        spiral_turns = self.params.get('spiral_turns', 7)
        
        # Generate points on a spiral
        num_points = len(self.data)
        angles = np.linspace(0, spiral_turns * 2 * np.pi, num_points)  # Spiral angles
        radii = np.linspace(0, radius, num_points)  # Gradually increase radius for spiral
        
        # Map normalized stock prices to heights and widths
        heights = self.data['Close_Normalized']*2
        widths = self.data['Volume_Width']
        
        # For rectangular badges, scale the cylinder widths to fit better
        if is_rectangular:
            # Scale down the cylinder widths for rectangular badges
            scale_factor = 0.5  # 50% of original width to ensure they fit
            widths = widths * scale_factor
        
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

            # For rectangular badges, ensure cylinders don't exceed the base dimensions
            if is_rectangular:
                # Ensure x and y coordinates are within the base dimensions
                max_x = base_width / 2 * 0.9  # 90% of half width to ensure margin
                max_y = base_depth / 2 * 0.9  # 90% of half depth to ensure margin
                
                # Clamp x and y coordinates to ensure they're within the base
                x_clamped = max(min(x[i], max_x), -max_x)
                y_clamped = max(min(y[i], max_y), -max_y)
                
                landscape.append(
                    translate([x_clamped, y_clamped, 0])(
                        cylinder(r=cylinder_radius, h=cylinder_height, center=False)
                    )
                )
            else:
                landscape.append(
                    translate([x[i], y[i], 0])(
                        cylinder(r=cylinder_radius, h=cylinder_height, center=False)
                    )
                )
        
        # Combine the landscape into a single object
        return union()(landscape)
        
    def generate_bar_chart(self):
        """
        Generate a bar chart model based on stock prices.
        Adapts to the badge shape (circular, rectangular, or triangular).
        
        Returns:
            solid.OpenSCADObject: Bar chart 3D model
        """
        # Determine badge type and set appropriate dimensions
        if isinstance(self, DiscBadge):
            # For disc badges, create a circular arrangement of bars
            radius = self.params.get('base_radius', 50) * 0.8
            num_points = len(self.data)
            angles = np.linspace(0, 2 * np.pi, num_points)
            
            # Create bars in a circular arrangement
            bars = []
            for i in range(num_points):
                bar_height = self.data['Close_Normalized'].iloc[i] * 2
                bar_width = 2 * np.pi * radius / num_points * 0.7  # Width as a fraction of circumference
                bar_depth = radius * 0.3  # Depth as a fraction of radius
                
                # Calculate position on the circle
                angle = angles[i]
                x_pos = radius * 0.7 * np.cos(angle)  # Position at 70% of radius
                y_pos = radius * 0.7 * np.sin(angle)
                
                # Rotate the bar to point outward from center
                bars.append(
                    translate([x_pos, y_pos, 0])(
                        rotate([0, 0, angle * 180 / np.pi])(
                            cube([bar_depth, bar_width, bar_height])
                        )
                    )
                )
            
            return union()(bars)
        else:
            # For rectangular and triangular badges
            base_width = self.params.get('base_width', 100)
            base_depth = self.params.get('base_depth', 60)
            bar_width = base_width / len(self.data)
            
            # Create bars for each data point, double the max height (normalized)
            # to make them more visible and look better
            bars = []
            for i in range(len(self.data)):
                # Bar height should be the normalized value
                bar_height = self.data['Close_Normalized'].iloc[i] * 2
                bar_depth = base_depth * 0.7  # Make bars slightly narrower than the base
                
                # Position each bar along the x-axis
                x_pos = i * bar_width
                y_pos = (base_depth - bar_depth) / 2  # Center bars on the y-axis
                
                bars.append(
                    translate([x_pos, y_pos, 0])(
                        cube([bar_width * 0.9, bar_depth, bar_height])
                    )
                )
            
            # Translate the finished bar model to zero point
            # and combine them into a single object
            for i in range(len(bars)):
                bars[i] = translate([-base_width/2, -base_depth/2, 0])(bars[i])
            
            return union()(bars)
    
    def generate_surface_plot(self):
        """
        Generate a surface plot model based on stock data.
        
        Returns:
            solid.OpenSCADObject: Surface plot 3D model
        """
        base_width = self.params.get('base_width', 100)
        base_depth = self.params.get('base_depth', 60)
        
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
        
        # Calculate center offsets to center the surface plot at (0,0)
        x_center = base_width / 2
        y_center = base_depth / 2
        
        # Create cells for the surface
        cells = []
        for i in range(grid_size):
            for j in range(grid_size):
                cell_height = height_grid[i, j]
                
                # Calculate position, centered at (0,0)
                x_pos = i * cell_width - x_center
                y_pos = j * cell_depth - y_center
                
                cells.append(
                    translate([x_pos, y_pos, 0])(
                        cube([cell_width * 0.95, cell_depth * 0.95, cell_height])
                    )
                )
        
        return union()(cells)
    
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
    
        # Take the stock price and make the edge jagged.
        base_radius = self.params.get('base_radius', 50)
        z_offset = 0  # Position the base at z=0, consistent with other badge types
        
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
        if 'terrain_types' in self.params and 'terrain_weights' in self.params:
            terrain_types = self.params['terrain_types']
            weights = self.params['terrain_weights']
            
            logger.info(f"Generating combined disc terrain with types: {terrain_types}")
            logger.info(f"Using weights: {weights}")
            
            terrain_model = self.generate_combined_terrain(terrain_types, weights)
        else:
            # Single terrain type
            terrain_type = self.params.get('terrain_type', 'spiral_chart')
            
            logger.info(f"Generating disc terrain with base height={base_height}")
            logger.info(f"Terrain type: {terrain_type}")
            
            if terrain_type == 'spiral_chart':
                terrain_model = self.generate_spiral_chart()
            elif terrain_type == 'bar_chart':
                terrain_model = self.generate_bar_chart()
            elif terrain_type == 'pyramid':
                terrain_model = self.generate_pyramid()
            elif terrain_type == 'surface_plot':
                terrain_model = self.generate_surface_plot()
            else:
                logger.warning(f"Unknown terrain type: {terrain_type}, using spiral_chart")
                terrain_model = self.generate_spiral_chart()
        
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
        
        logger.info(f"Base width: {width}, depth: {depth}, height: {height}")
        
        # Number of points to use on each side of the rectangle
        # Distribute the data points around the perimeter
        num_points = len(self.data)
        logger.info(f"Number of data points: {num_points}")
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
        
        # Log dimensions for debugging
        logger.info(f"Generating terrain with base dimensions: width={base_width}, depth={base_depth}, height={base_height}")
        
        # Check if multiple terrain types are specified
        if 'terrain_types' in self.params and 'terrain_weights' in self.params:
            terrain_types = self.params['terrain_types']
            weights = self.params['terrain_weights']
            
            logger.info(f"Generating combined rectangular terrain with types: {terrain_types}")
            logger.info(f"Using weights: {weights}")
            
            # Generate combined terrain model
            terrain_model = self.generate_combined_terrain(terrain_types, weights)
        else:
            # Single terrain type
            terrain_type = self.params.get('terrain_type', 'bar_chart')
            logger.info(f"Terrain type: {terrain_type}")
            
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
        if 'terrain_types' in self.params and 'terrain_weights' in self.params:
            terrain_types = self.params['terrain_types']
            weights = self.params['terrain_weights']
            
            logger.info(f"Generating combined triangular terrain with types: {terrain_types}")
            logger.info(f"Using weights: {weights}")
            
            # Generate combined terrain model
            terrain_model = self.generate_combined_terrain(terrain_types, weights)
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
    parser.add_argument('--terrain-weights', type=str, help='Optional comma-separated list of weights for each terrain type (e.g., 0.5,0.3,0.2)')
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
        
        # Handle multiple terrain types
        if args.terrain_types:
            terrain_types = [t.strip() for t in args.terrain_types.split(',')]
            params['terrain_types'] = terrain_types
            
            # Handle terrain weights if provided
            if args.terrain_weights:
                weights = [float(w.strip()) for w in args.terrain_weights.split(',')]
                
                # Ensure we have the same number of weights as terrain types
                if len(weights) != len(terrain_types):
                    logger.warning(f"Number of weights ({len(weights)}) doesn't match number of terrain types ({len(terrain_types)}). Using equal weights.")
                    weights = [1.0/len(terrain_types)] * len(terrain_types)
                else:
                    # Normalize weights to sum to 1
                    total = sum(weights)
                    weights = [w/total for w in weights]
                
                params['terrain_weights'] = weights
            else:
                # Equal weights if not specified
                params['terrain_weights'] = [1.0/len(terrain_types)] * len(terrain_types)
                
            logger.info(f"Using terrain types: {terrain_types} with weights: {params['terrain_weights']}")
        elif args.terrain_type:
            # For backward compatibility
            params['terrain_type'] = args.terrain_type
        
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

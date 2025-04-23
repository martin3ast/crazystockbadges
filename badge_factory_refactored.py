#!/usr/bin/env python3
"""
Badge Factory class, 3-D Model Generation Module for Crazy Stock Badges Project

This module provides classes and functions for generating 3D models from stock data
using SolidPython to create OpenSCAD files that can be rendered to STL for 3D printing.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for 3D badge generation - Apr 13, 2025.
Version 2.0 - Martin East - Read, tidy, reduce overall complexity - Apr 15, 2025.
Version 3.0 - Cline - Enhanced with pyramid feature for all badge types - Apr 21, 2025.
Version 4.0 - Cline - Refactored to improve structure and reduce redundancy - Apr 21, 2025.
"""

# Standard library imports
import os
import math
import random
import logging
import enum
from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Union, Any

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


# Enums and Constants
class BadgeType(enum.Enum):
    """Enum for badge types"""
    DISC = "disc"
    RECTANGULAR = "rectangular"
    TRIANGULAR = "triangular"


class TerrainType(enum.Enum):
    """Enum for terrain types"""
    SPIRAL_CHART = "spiral_chart"
    BAR_CHART = "bar_chart"
    PYRAMID = "pyramid"
    SURFACE_PLOT = "surface_plot"
    
    @classmethod
    def from_string(cls, value: str) -> 'TerrainType':
        """Convert string to TerrainType enum"""
        try:
            return cls(value.lower())
        except ValueError:
            logger.warning(f"Unknown terrain type: {value}, using spiral_chart")
            return cls.SPIRAL_CHART


# Data Classes for Parameters
@dataclass
class BadgeParams:
    """Base class for badge parameters"""
    base_height: float = 1.0
    text_depth: float = 2.0
    text_size: float = 10.0
    text_position: str = "bottom"
    height_range: Tuple[float, float] = (0.0, 10.0)
    width_range: Tuple[float, float] = (0.0, 10.0)
    terrain_types: List[TerrainType] = field(default_factory=list)
    terrain_weights: List[float] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, params_dict: Dict[str, Any]) -> 'BadgeParams':
        """Create BadgeParams from dictionary"""
        params = cls()
        
        # Copy basic parameters
        for key, value in params_dict.items():
            if hasattr(params, key):
                setattr(params, key, value)
        
        # Handle terrain types
        if 'terrain_types' in params_dict:
            params.terrain_types = [
                TerrainType.from_string(t) for t in params_dict['terrain_types']
            ]
        elif 'terrain_type' in params_dict:
            params.terrain_types = [TerrainType.from_string(params_dict['terrain_type'])]
            
        # Handle terrain weights
        if 'terrain_weights' in params_dict:
            params.terrain_weights = params_dict['terrain_weights']
        elif params.terrain_types:
            # Equal weights if not specified
            params.terrain_weights = [1.0/len(params.terrain_types)] * len(params.terrain_types)
            
        return params


@dataclass
class DiscBadgeParams(BadgeParams):
    """Parameters specific to disc badges"""
    base_radius: float = 50.0
    spiral_radius: float = 45.0
    spiral_turns: int = 7


@dataclass
class RectangularBadgeParams(BadgeParams):
    """Parameters specific to rectangular badges"""
    base_width: float = 100.0
    base_depth: float = 60.0
    spiral_radius: Optional[float] = None


@dataclass
class TriangularBadgeParams(BadgeParams):
    """Parameters specific to triangular badges"""
    side_length: float = 80.0
    base_height: float = 3.0  # Override base class default


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


# Terrain Generator class
class TerrainGenerator:
    """
    Class for generating different terrain types based on stock data.
    
    Version 1.0 - Cline implementation for Martin East - Refactored from Badge3DModel - Apr 21, 2025.
    """
    
    def __init__(self, data, params):
        """
        Initialize the terrain generator.
        
        Args:
            data (pandas.DataFrame): Normalized stock data
            params: Badge parameters
        """
        self.data = data
        self.params = params
        
    def generate_terrain(self, terrain_type: TerrainType, badge_type: BadgeType):
        """
        Generate terrain based on type.
        
        Args:
            terrain_type: Type of terrain to generate
            badge_type: Type of badge this terrain is for
            
        Returns:
            solid.OpenSCADObject: Terrain 3D model
        """
        if terrain_type == TerrainType.SPIRAL_CHART:
            return self.generate_spiral_chart(badge_type)
        elif terrain_type == TerrainType.BAR_CHART:
            return self.generate_bar_chart(badge_type)
        elif terrain_type == TerrainType.PYRAMID:
            return self.generate_pyramid(badge_type)
        elif terrain_type == TerrainType.SURFACE_PLOT:
            return self.generate_surface_plot(badge_type)
        else:
            logger.warning(f"Unknown terrain type: {terrain_type}, using spiral_chart")
            return self.generate_spiral_chart(badge_type)
    
    def generate_spiral_chart(self, badge_type: BadgeType):
        """
        Generate a spiral landscape model based on stock data.
        Adapts to fit within the base shape (circular or rectangular).
        
        Args:
            badge_type: Type of badge this terrain is for
            
        Returns:
            solid.OpenSCADObject: Spiral landscape 3D model
        """
        # Determine if this is a rectangular badge
        is_rectangular = badge_type == BadgeType.RECTANGULAR
        
        # Set radius based on badge type
        if is_rectangular:
            # For rectangular badges, use dimensions that fit within the rectangle
            if isinstance(self.params, RectangularBadgeParams):
                base_width = self.params.base_width
                base_depth = self.params.base_depth
            else:
                base_width = 100
                base_depth = 60
            
            # Use the smaller dimension (minus margin) to ensure spiral fits within the base
            # Reduce to 35% to ensure it fits better
            radius = min(base_width, base_depth) * 0.35
            
            # Override spiral_radius if provided
            if hasattr(self.params, 'spiral_radius') and self.params.spiral_radius is not None:
                radius = self.params.spiral_radius
        else:
            # For circular badges, use the default or provided radius
            if isinstance(self.params, DiscBadgeParams):
                radius = self.params.spiral_radius
            else:
                radius = 45
        
        # Get spiral turns
        if isinstance(self.params, DiscBadgeParams):
            spiral_turns = self.params.spiral_turns
        else:
            spiral_turns = 7
        
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
    
    def generate_bar_chart(self, badge_type: BadgeType):
        """
        Generate a bar chart model based on stock prices.
        Adapts to the badge shape (circular, rectangular, or triangular).
        
        Args:
            badge_type: Type of badge this terrain is for
            
        Returns:
            solid.OpenSCADObject: Bar chart 3D model
        """
        # Determine badge type and set appropriate dimensions
        if badge_type == BadgeType.DISC:
            # For disc badges, create a circular arrangement of bars
            if isinstance(self.params, DiscBadgeParams):
                radius = self.params.base_radius * 0.8
            else:
                radius = 50 * 0.8
                
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
            if isinstance(self.params, RectangularBadgeParams):
                base_width = self.params.base_width
                base_depth = self.params.base_depth
            else:
                base_width = 100
                base_depth = 60
                
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
    
    def generate_pyramid(self, badge_type: BadgeType):
        """
        Generate a pyramid feature with height based on stock data.
        The pyramid sides are varied and spikey based on the stock data.
        Adapts to the badge shape (circular, rectangular, or triangular).
        Ensures the model fits within 100x100 dimensions.
        
        Args:
            badge_type: Type of badge this terrain is for
            
        Returns:
            solid.OpenSCADObject: Pyramid 3D model with varied and spikey sides
        """
        # Maximum size constraint
        max_size = 100
        
        # Determine badge type and set appropriate dimensions
        if badge_type == BadgeType.RECTANGULAR:
            # For rectangular badges
            if isinstance(self.params, RectangularBadgeParams):
                base_width = self.params.base_width
                base_depth = self.params.base_depth
            else:
                base_width = 100
                base_depth = 60
                
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
            
        elif badge_type == BadgeType.TRIANGULAR:
            # For triangular badges
            if isinstance(self.params, TriangularBadgeParams):
                side_length = self.params.side_length
            else:
                side_length = 80
                
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
            
        else:  # DISC or other
            # For disc badges
            if isinstance(self.params, DiscBadgeParams):
                radius = min(self.params.base_radius * 0.7, max_size/2 * 0.7)  # Ensure radius fits within bounds
            else:
                radius = min(50 * 0.7, max_size/2 * 0.7)
                
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
        # Use more layers for all badge types to create more detailed spikes
        layers = height_multiplier * 10  # Reduced from 15
        
        # Add some randomness to the layer count for more variation (reduced range)
        layers += random.randint(-3, 3)
        
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
                point_variation = (0.1 + extra_variation) * volume_value  # Reduced from 0.15
                
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
            
            # Occasionally add a small sphere at a random position on this layer (reduced frequency)
            if random.random() > 0.97:  # 3% chance (reduced from 5%)
                # Pick a random point on the perimeter
                rand_idx = random.randint(0, len(varied_points) - 1)
                sphere_x = varied_points[rand_idx][0]
                sphere_y = varied_points[rand_idx][1]
                sphere_z = layer_height + layer_thickness / 2
                # Smaller sphere radius
                sphere_radius = layer_thickness * random.uniform(0.3, 0.8)  # Reduced from 0.5-1.5
                
                pyramid_parts.append(
                    translate([sphere_x, sphere_y, sphere_z])(
                        sphere(r=sphere_radius)
                    )
                )
        
        return union()(pyramid_parts)
    
    def generate_surface_plot(self, badge_type: BadgeType):
        """
        Generate a surface plot model based on stock data.
        
        Args:
            badge_type: Type of badge this terrain is for
            
        Returns:
            solid.OpenSCADObject: Surface plot 3D model
        """
        if isinstance(self.params, RectangularBadgeParams):
            base_width = self.params.base_width
            base_depth = self.params.base_depth
        else:
            base_width = 100
            base_depth = 60
        
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
    
    def combine_terrains(self, terrain_types: List[TerrainType], weights: List[float], badge_type: BadgeType):
        """
        Generate a combined terrain model from multiple terrain types.
        
        Args:
            terrain_types: List of terrain types to combine
            weights: List of weights for each terrain type
            badge_type: Type of badge this terrain is for
            
        Returns:
            solid.OpenSCADObject: Combined terrain 3D model
        """
        # Maximum size constraint
        max_size = 100
        
        # Generate terrain models for each type
        terrain_models = []
        
        # Generate each terrain model
        for terrain_type in terrain_types:
            terrain_model = self.generate_terrain(terrain_type, badge_type)
            terrain_models.append(terrain_model)
        
        # If no valid terrain models were generated, return an empty model
        if not terrain_models:
            logger.warning("No valid terrain models were generated")
            return cube([0, 0, 0])
        
        # Determine badge dimensions based on badge type
        if badge_type == BadgeType.RECTANGULAR:
            if isinstance(self.params, RectangularBadgeParams):
                base_width = self.params.base_width
                base_depth = self.params.base_depth
            else:
                base_width = 100
                base_depth = 60
            # Use smaller dimension for better proportions
            max_dim = min(base_width, base_depth) * 0.9
        elif badge_type == BadgeType.TRIANGULAR:
            if isinstance(self.params, TriangularBadgeParams):
                side_length = self.params.side_length
            else:
                side_length = 80
            max_dim = side_length * 0.9
        else:  # DISC or other
            if isinstance(self.params, DiscBadgeParams):
                radius = self.params.base_radius
            else:
                radius = 50
            max_dim = radius * 1.8  # Diameter * 0.9
        
        # Ensure max_dim doesn't exceed max_size
        max_dim = min(max_dim, max_size * 0.9)
        
        # Calculate the size of each terrain section based on weights
        section_sizes = [max_dim * weight for weight in weights]
        
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
            model2

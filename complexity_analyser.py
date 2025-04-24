'''
Complexity estimation functions

A set of functions (experiments) to estimate the model complexity, this is for the fitness function for our 
Genetic algorithm. The class takes in a Solid Python model , that is traversed node by node, counting metrics

Version 1.0: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
Version 2.0: Martin East - Moved to separate file for better organization, read and analysed - Apr 17, 2025
Version 3.0: Cline for Martin East - reworked from prototype, under instructiom to keep it simple - Apr 23, 2025
Version 3.1:  Martin East - minor renames and tidy, weighting factors reviews and documented - Apr 23, 2025

'''

import re
from collections import defaultdict
from solid import cube, sphere, cylinder, polyhedron, polygon
from solid import union, difference, intersection, hull, minkowski

class ComplexityAnalyzer:
    """
    Analyzes the complexity of a SolidPython node structure.
    Consolidates all complexity analysis into a single class.
    
    Version 3.0: Cline for Martin East - reworked from prototype - Apr 23, 2025
    """
    
    def __init__(self, node):
        """
        Initialize with a SolidPython node structure
        
        Args:
            node: A SolidPython node structure to analyze
        """
        self.node = node
        
        # Initialize metrics
        self.metrics = {
            'max_depth': 0,
            'total_nodes': 0,
            'primitive_counts': defaultdict(int),
            'operation_counts': defaultdict(int),
            'polygonal_metrics': {
                'polygon_count': 0,
                'polyhedron_count': 0,
                'total_points': 0,
                'total_faces': 0,
                'max_points_per_polygon': 0
            }
        }
        
        # Perform analysis
        self._analyze_structure()
        self.metrics['complexity_score'] = self._model_complexity_score(self.node)
    
    def _analyze_structure(self):
        """Analyze the node structure and collect metrics"""
        self._traverse_node(self.node)
    
    def _traverse_node(self, node, depth=0):
        """
        Unified node traversal that collects metrics
        """
        self.metrics['total_nodes'] += 1
        self.metrics['max_depth'] = max(self.metrics['max_depth'], depth)
        
        if isinstance(node, (list, tuple)):
            for child in node:
                self._traverse_node(child, depth+1)
        elif hasattr(node, 'children'):
            # Operation node
            op_name = node.__class__.__name__.lower()
            self.metrics['operation_counts'][op_name] += 1
            
            for child in node.children:
                self._traverse_node(child, depth+1)
        else:
            # Primitive node
            prim_name = node.__class__.__name__.lower()
            self.metrics['primitive_counts'][prim_name] += 1
            
            # Collect polygonal metrics
            if isinstance(node, polygon):
                self.metrics['polygonal_metrics']['polygon_count'] += 1
                points = len(getattr(node, 'points', []))
                self.metrics['polygonal_metrics']['total_points'] += points
                self.metrics['polygonal_metrics']['max_points_per_polygon'] = max(
                    self.metrics['polygonal_metrics']['max_points_per_polygon'], 
                    points
                )
            elif isinstance(node, polyhedron):
                self.metrics['polygonal_metrics']['polyhedron_count'] += 1
                points = len(getattr(node, 'points', []))
                faces = len(getattr(node, 'faces', []))
                self.metrics['polygonal_metrics']['total_points'] += points
                self.metrics['polygonal_metrics']['total_faces'] += faces
    
    def _model_complexity_score(self, node):
        """
        Calculate complexity score with emphasis on operations that
        create complex, "crazy" structures.
        
        Returns: float representing complexity (higher = more complex/crazy)
        """
        if isinstance(node, (list, tuple)):
            return sum(self._model_complexity_score(child) for child in node)
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
            
            return (op_factor + child_count_bonus) * sum(
                self._model_complexity_score(child) for child in node.children
            )
        else:
            return self._estimate_geometry_complexity(node)
    
    def _estimate_geometry_complexity(self, obj):
        """
        Estimate geometric complexity with emphasis on polygonal complexity.
        This function prioritizes complex polygonal structures to maximize
        the "craziness" factor of the generated models.
        
        Returns complexity score (higher = more complex/crazy)
        """
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
    
    def calculate_polygonal_complexity_score(self):
        """
        
        Calculate a single polygonal complexity score based on collected metrics
        
        Weighting rationale:
        - total_points (0.5): Base contribution of points
        - max_points_per_polygon (2.0): Rewards complex individual polygons
        - polyhedron_count (10.0): Heavily rewards polyhedrons as most complex primitives
        - total_faces (1.5): Rewards models with more faces for visual complexity
        
        Returns: float representing polygonal complexity
        
        """
        metrics = self.metrics['polygonal_metrics']
        if metrics['polygon_count'] > 0 or metrics['polyhedron_count'] > 0:
            return (
                metrics['total_points'] * 0.5 + 
                metrics['max_points_per_polygon'] * 2 + 
                metrics['polyhedron_count'] * 10 + 
                metrics['total_faces'] * 1.5
            )
        else:
            return 0
    
    def get_complexity_report(self):
        """
        Get a comprehensive report of all complexity metrics
        
        Returns: dict with all metrics and scores
        """
        # Calculate polygonal complexity score before returning
        self.metrics['polygonal_metrics']['polygonal_complexity_score'] = self.calculate_polygonal_complexity_score()
        return self.metrics

"""
Complexity estimation functions

A set of functions to estimate the model complexity for the fitness function in our 
Genetic algorithm. The class takes in a Solid Python model, traverses it node by node, 
and counts various metrics.

Version 1.0: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
Version 2.0: Martin East - Moved to separate file for better organization, read and analysed - Apr 17, 2025
Version 3.0: Cline for Martin East - reworked from prototype, under instructiom to keep it simple - Apr 23, 2025
Version 3.1: Martin East - minor renames and tidy, weighting factors reviews and documented - Apr 23, 2025
Version 3.2: Martin East - discard base coverage calculations - April 25, 2025
Version 3.3: Martin East - Fix and fill in logic gaps, some parts of the report are not running atall - April 25, 2025
Version 3.4: Cline for Martin East - Greatly simplified to focus on object counts - April 25, 2025
"""

from collections import defaultdict
from solid import polygon, polyhedron

class ComplexityAnalyzer:
    """
    Analyzes the complexity of a SolidPython node structure.
    Simplified to focus on counting objects rather than complex calculations.
    """
    
    def __init__(self, solidpython_node):
        """
        Initialize with a SolidPython node structure
        
        Args:
            node: A SolidPython node structure to analyze
        """
        self.node = solidpython_node
        
        # Initialize metrics with simple counters
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
        self._traverse_and_count_nodes(self.node)
        
        # Calculate simple complexity score based on counts
        self.metrics['complexity_score'] = self._calculate_simple_complexity_score()

    def print_metrics(self):
        """
        Print the collected metrics in a readable format
        """
        print("Complexity Analysis Metrics:")
        print(f"  Total Nodes: {self.metrics['total_nodes']}")
        print(f"  Max Depth: {self.metrics['max_depth']}")
        
        print("\nPrimitive Counts:")
        for prim, count in self.metrics['primitive_counts'].items():
            print(f"  {prim}: {count}")
        
        print("\nOperation Counts:")
        for op, count in self.metrics['operation_counts'].items():
            print(f"  {op}: {count}")
        
        print("\nPolygonal Metrics:")
        for key, value in self.metrics['polygonal_metrics'].items():
            print(f"  {key}: {value}")
        
        print(f"\nComplexity Score: {self.metrics['complexity_score']:.2f}")
    
    def _traverse_and_count_nodes(self, node, depth=0):
        """
        Simplified node traversal that just counts objects
        """
        if node is None:
            return

        self.metrics['total_nodes'] += 1
        self.metrics['max_depth'] = max(self.metrics['max_depth'], depth)

        if isinstance(node, (list, tuple)):
            for child in node:
                self._traverse_and_count_nodes(child, depth + 1)
        elif hasattr(node, 'children') and node.children:
            op_name = node.__class__.__name__.lower()
            self.metrics['operation_counts'][op_name] += 1
            for child in node.children:
                self._traverse_and_count_nodes(child, depth + 1)
        else:
            prim_name = node.__class__.__name__.lower()
            self.metrics['primitive_counts'][prim_name] += 1

            if isinstance(node, polygon):
                self.metrics['polygonal_metrics']['polygon_count'] += 1
                points_count = 0
                if hasattr(node, 'points') and node.points:
                    points_count = len(node.points)
                elif hasattr(node, 'params') and 'points' in node.params:
                    points_count = len(node.params['points'])
                elif hasattr(node, '_points'):
                    points_count = len(node._points)
                if points_count > 0:
                    self.metrics['polygonal_metrics']['total_points'] += points_count
                    self.metrics['polygonal_metrics']['max_points_per_polygon'] = max(
                        self.metrics['polygonal_metrics']['max_points_per_polygon'],
                        points_count,
                    )
            elif isinstance(node, polyhedron):
                self.metrics['polygonal_metrics']['polyhedron_count'] += 1
                points_count = 0
                faces_count = 0
                if hasattr(node, 'points') and node.points:
                    points_count = len(node.points)
                elif hasattr(node, 'params') and 'points' in node.params:
                    points_count = len(node.params['points'])
                elif hasattr(node, '_points'):
                    points_count = len(node._points)
                if hasattr(node, 'faces') and node.faces:
                    faces_count = len(node.faces)
                elif hasattr(node, 'params') and 'faces' in node.params:
                    faces_count = len(node.params['faces'])
                elif hasattr(node, '_faces'):
                    faces_count = len(node._faces)
                self.metrics['polygonal_metrics']['total_points'] += points_count
                self.metrics['polygonal_metrics']['total_faces'] += faces_count
    
    def _calculate_simple_complexity_score(self):
        """Compute a weighted complexity score from the collected counts.

        Note for callers: the genetic-algorithm fitness adds this score to
        `total_nodes`. Because every operation node is also counted in
        `total_nodes` (see `_traverse_and_count_nodes`), each operation
        contributes at least 1 (via total_nodes) plus 1.5 (via operation_sum)
        to the GA fitness — a net 2.5x weighting versus a primitive node.
        This bias is intentional today (operation-rich trees feel "crazier"),
        but reweighting is on the CC follow-up list; do not change it without
        re-tuning the GA hyperparameters.
        """
        primitive_sum = sum(self.metrics['primitive_counts'].values())
        operation_sum = sum(self.metrics['operation_counts'].values())

        polygonal_sum = (
            self.metrics['polygonal_metrics']['polygon_count']
            + self.metrics['polygonal_metrics']['polyhedron_count'] * 2
            + self.metrics['polygonal_metrics']['total_points'] * 0.1
            + self.metrics['polygonal_metrics']['total_faces'] * 0.2
        )

        return (
            primitive_sum
            + operation_sum * 1.5
            + polygonal_sum
            + self.metrics['max_depth'] * 0.5
        )
    
    def get_complexity_report(self):
        """
        Get a comprehensive report of all complexity metrics
        
        Returns: dict with all metrics and scores
        """
        return self.metrics

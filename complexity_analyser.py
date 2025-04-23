'''
Complexity estimation functions

A set of functions (experiments) to estimate the model complexity, this is for the fitness function for our 
Genetc algorithm. Deepseek and Cline were used to find the correct datastructures under instruction
from Martin East. The functions are designed to be used with OpenSCAD code and analyze the complexity
of the generated models. The functions count CSG operations, analyze the node structure, and suggest
optimizations based on the complexity metrics. The goal is to provide a comprehensive analysis of the
3D model's complexity, focusing on polygonal structures and the overall craziness factor of the generated models.

Version 1.0: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
Version 2.0: Martin East - Moved to separate file for better organization - Apr 17, 2025


'''



def count_csg_operations(scad_code):
    """
    Counts all CSG operations in generated OpenSCAD code, Openscad files are text and readable, describing
    the model in coordinates and primitives.
    
    Version 1.0: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
    Version 2.0 : Read and commented by Martin East - Apr 17, 2025
    
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

class ComplexityAnalyzer:
    """
    Analyzes the complexity of a 3D model by traversing its node structure
    
    Version 1.0: Cline implementation for Martin East - Adapted from complexity_estimation.py - Apr 17, 2025
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
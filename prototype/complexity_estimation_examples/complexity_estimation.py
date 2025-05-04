# Prototype complexity analysis Notes and Code, Deepseek output 21st April approx. 

from solid import *
import re
from collections import defaultdict

def count_csg_operations(scad_code):
    """
    Counts all CSG operations in generated OpenSCAD code
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

# Example usage:
model = union()(
    cube(10),
    difference()(
        sphere(5),
        cylinder(r=2, h=8)
    )
)

scad_code = scad_render(model)
print(count_csg_operations(scad_code))

class ComplexityAnalyzer:
    def __init__(self):
        self.metrics = {
            'max_depth': 0,
            'total_nodes': 0,
            'primitive_counts': defaultdict(int),
            'operation_counts': defaultdict(int)
        }
    
    def analyze(self, node, depth=0):
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

# Usage:
#analyzer = ComplexityAnalyzer()
#analyzer.analyze(model)
#print(analyzer.metrics)


def estimate_geometry_complexity(obj):
    """
    Estimates geometric complexity based on parameters
    Returns complexity score (higher = more complex)
    """
    if isinstance(obj, cube):
        # Simple cube has low complexity
        return 1
    elif isinstance(obj, sphere):
        # Sphere complexity depends on $fn resolution
        fn = getattr(obj, 'fn', 30)  # Default OpenSCAD resolution
        return min(fn / 10, 10)  # Normalize to 0-10 scale
    elif isinstance(obj, cylinder):
        # Cylinder complexity depends on both resolution and parameters
        fn = getattr(obj, 'fn', 30)
        r = getattr(obj, 'r', 1)
        h = getattr(obj, 'h', 1)
        return min((fn * (r + h)) / 20, 15)
    elif isinstance(obj, polyhedron):
        # Polyhedrons are inherently complex
        points = len(getattr(obj, 'points', []))
        faces = len(getattr(obj, 'faces', []))
        return min((points + faces) / 10, 20)
    else:
        return 0  # Unknown type

def model_complexity_score(node):
    if isinstance(node, (list, tuple)):
        return sum(model_complexity_score(child) for child in node)
    elif hasattr(node, 'children'):
        # Operations multiply complexity of their children
        op_factor = 1.5 if isinstance(node, union) else 2.0  # difference/intersection are more complex
        return op_factor * sum(model_complexity_score(child) for child in node.children)
    else:
        return estimate_geometry_complexity(node)

# Usage:
print(f"Model complexity score: {model_complexity_score(model)}")


def optimize_csg_tree(node):
    """
    Simplifies CSG tree through basic optimizations
    """
    if hasattr(node, 'children'):
        # Flatten nested unions
        if isinstance(node, union):
            new_children = []
            for child in node.children:
                if isinstance(child, union):
                    new_children.extend(optimize_csg_tree(child).children)
                else:
                    new_children.append(optimize_csg_tree(child))
            node.children = new_children
        # Similar optimizations for other operations...
    return node

def suggest_optimizations(metrics):
    """
    Generates optimization suggestions based on complexity metrics
    """
    suggestions = []
    
    if metrics['operation_counts'].get('difference', 0) > 5:
        suggestions.append("Consider combining multiple difference operations")
    
    if metrics['max_depth'] > 8:
        suggestions.append("Very deep CSG tree - try flattening operations")
    
    if metrics['primitive_counts'].get('polyhedron', 0) > 0:
        suggestions.append("Polyhedrons are complex - consider alternatives")
    
    return suggestions

# Usage:
optimized_model = optimize_csg_tree(model)
analyzer = ComplexityAnalyzer()
analyzer.analyze(optimized_model)
print("Optimization suggestions:", suggest_optimizations(analyzer.metrics))

def generate_complexity_report(model, filename=None):
    """
    Generates a comprehensive complexity analysis report
    """
    scad_code = scad_render(model)
    op_counts = count_csg_operations(scad_code)
    
    analyzer = ComplexityAnalyzer()
    analyzer.analyze(model)
    
    complexity_score = model_complexity_score(model)
    
    report = f"""
    ===== 3D MODEL COMPLEXITY REPORT =====
    
    Basic Metrics:
    - Total CSG nodes: {analyzer.metrics['total_nodes']}
    - Maximum tree depth: {analyzer.metrics['max_depth']}
    - Overall complexity score: {complexity_score:.2f}
    
    Operation Counts:
    {', '.join([f"{k}: {v}" for k, v in analyzer.metrics['operation_counts'].items()])}
    
    Primitive Counts:
    {', '.join([f"{k}: {v}" for k, v in analyzer.metrics['primitive_counts'].items()])}
    
    CSG Operations in Generated Code:
    {', '.join([f"{k}: {v}" for k, v in op_counts.items()])}
    
    Optimization Suggestions:
    {chr(10).join(['- ' + s for s in suggest_optimizations(analyzer.metrics)])}
    """
    
    if filename:
        with open(filename, 'w') as f:
            f.write(report)
    
    return report

# Example usage of the complete report generator
if __name__ == "__main__":
    # Create a more complex model for testing
    test_model = union()(
        translate([0, 0, 0])(cube(10)),
        translate([5, 5, 5])(sphere(3)),
        difference()(
            translate([10, 10, 0])(cylinder(r=5, h=10)),
            translate([10, 10, -1])(cylinder(r=3, h=12))
        ),
        hull()(
            translate([0, 20, 0])(cube(5)),
            translate([5, 25, 5])(sphere(2))
        )
    )
    
    # Generate and print the report
    print(generate_complexity_report(test_model))
    
    # Optionally save to file
    # generate_complexity_report(test_model, "complexity_report.txt")

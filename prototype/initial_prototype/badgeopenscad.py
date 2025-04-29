from solid import *
from solid.utils import *
import pandas as pd
import numpy as np

MAX_HEIGHT=15
MAX_WIDTH=10

def load_stock_data(fname):
    return pd.read_csv(fname)

# Normalize stock prices to a range of 0 to 5
def normalise_prices(prices, new_min=0, new_max=5):
    prices_normalised = (prices - np.min(prices)) / (np.max(prices) - np.min(prices)) * (new_max - new_min) + new_min
    return prices_normalised

stock_data=load_stock_data("./stock_data")
# Normalize the stock prices
stock_data['Close_Normalized'] = normalise_prices(stock_data['Close'],0,MAX_HEIGHT)
stock_data['Volume_Normalized'] = normalise_prices(stock_data['Volume'],0,MAX_WIDTH)

radius = 10  # Radius of the disc

def jagged_disc(stock_data, base_radius=3, height=2):

    # Parameters for the polygon
    num_points = len(stock_data)  # Use all data points
    angles = np.linspace(0, 2 * np.pi, num_points)  # Angles around the circle

    # Map normalized stock prices to the polygon edge
    radii = stock_data['Close_Normalized'] + base_radius

    # Create points for the polygon
    points = []
    for i in range(num_points):
        x = radii[i] * np.cos(angles[i] )  # X coordinate
        y = radii[i] * np.sin(angles[i] )  # Y coordinate
        points.append([x, y])

    jagged_disc_2d = polygon(points)

    # Extrude the 2D polygon into a 3D disc
    jagged_disc_3d = linear_extrude(height=height)(jagged_disc_2d)
    return jagged_disc_3d

    return jagged_disc_3d

# Parameters for the spiral
def spiral_landscape(stock_data, radius=100, height=50):

    spiral_turns = 7  # Number of spiral turns
    max_height = height  # Maximum height of the landscape
    num_points= len(stock_data['Close'])
    # Generate points on a spiral
    angles = np.linspace(0, spiral_turns * 2 * np.pi, num_points)  # Spiral angles
    radii = np.linspace(0, radius, num_points)  # Gradually increase radius for spiral

    # Map normalized stock prices to heights
    cyl_heights = stock_data['Close_Normalized']
    cyl_radii = stock_data['Volume_Normalized']

    x = radii * np.cos(angles)  # X coordinates
    y = radii * np.sin(angles)  # Y coordinates

    # Create the landscape as a series of stacked cylinders
    landscape = []
    for i in range(num_points):
        cylinder_height = cyl_heights[i]
        cylinder_radius = cyl_radii[i]  # Small radius for smooth landscape
        landscape.append(
            translate([x[i], y[i], 0])(
                cylinder(r=cylinder_radius, h=cylinder_height, center=False)
            )
        )
    landscape_combined = union()(landscape)
    # Combine the landscape into a single object
    return landscape_combined

def make_text_object(depth=5, size=3, mystring="text"):
    
    text_2d = text(mystring, size=size, halign='center', valign='center')
    text_3d = linear_extrude(height=depth)(text_2d)
    return text_3d

def make_multiline_text_object(depth=5, size=3, mystring="text", wrap_chars=10):
    # Split text into lines of max 10 characters
    lines = [mystring[i:i+wrap_chars] for i in range(0, len(mystring), 10)]
    num_lines = len(lines)
    
    # Generate 3D text objects for each line and center them
    text_objects = []
    line_spacing = size * 1.2  # Adjust spacing based on text size
    for i, line in enumerate(lines):
        y_offset = (num_lines - 1) / 2 - i  # Center the text block
        text_2d = text(line, size=size, halign='center', valign='center')
        text_3d = linear_extrude(height=depth)(text_2d)
        text_objects.append(translate([0, y_offset * line_spacing, 0])(text_3d))

    return text_objects


def engraved_text_bottom():
    # Add text on the back of the disc
    text_depth = 20  # Depth of the engraved text
    text_size = 40   # Size of the text
    text_to_engrave = "TSLA"
    engraved_text = translate([0, 0, 0 - text_depth])(make_multiline_text_object(depth=text_depth,size=text_size,mystring=text_to_engrave, wrap_chars=10))
    return engraved_text

disc_interim = union()(
    jagged_disc(stock_data,base_radius=50,height=3),
    translate([0,0,2])(spiral_landscape(stock_data,radius=50,height=20))
)

# Combine the disc, landscape, and engraved text
final_disc = difference()(
    disc_interim,  # The base disc
    engraved_text_bottom()  # The text to engrave
)

#final_disc = disc_interim

# Save as an OpenSCAD file
scad_render_to_file(final_disc, "disc.scad")
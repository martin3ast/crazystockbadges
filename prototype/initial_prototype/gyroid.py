from openscad import *
# Create a cube and a cylinder
cu = cube([3,3,5])
cy = cylinder(5)

# Create a third object that is a fusion of the cube and the cylinder
fusion = cu.union(cy)
# alternatively you can also write:
fusion = union([cu, cy])

# Display the new object
output(fusion)
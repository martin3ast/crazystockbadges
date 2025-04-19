#!/bin/bash
# Test Badge Examples
# Version 1.0 - Cline implementation for Martin East - Example script for test_model_generator.py - Apr 16, 2025.

# This script demonstrates various parameter combinations for test_model_generator.py
# It creates several example badges with different configurations

BASE="/Users/martineast/workspace/crazystockbadges/"
echo "=== Generating Example Badges ==="

# Example 1: Basic Disc Badge with AAPL data
#echo -e "\n\033[1;36mExample 1: Basic Disc Badge (AAPL)\033[0m"
#python $BASE/test_model_generator.py --ticker AAPL --base-height 1 --output example1_disc_basic.scad --skip-report

# Example 2: Disc Badge with Spiral Chart
echo -e "\n\033[1;36mExample 2: Disc Badge with Spiral Chart (TSLA)\033[0m"
python $BASE/test_model_generator.py --ticker TSLA --badge-type disc --base-height 0.7 --terrain-type bar_chart \
    --base-radius 50 --base-depth 70 --base-width 110 --spiral-turns 6 --text-position bottom --output example2_disc_spiral.scad --skip-report

# Example 3: Rectangular Badge with Bar Chart
#echo -e "\n\033[1;36mExample 3: Rectangular Badge with Bar Chart (MSFT)\033[0m"
#python $BASE/test_model_generator.py --ticker MSFT --badge-type rectangular --base-height 1 --feature-type bar_chart \
 #   --base-width 110 --base-depth 70 --text-content "MSFT" --output example3_rect_bar.scad --skip-report

# Example 4: Rectangular Badge with Surface Plot
#echo -e "\n\033[1;36mExample 4: Rectangular Badge with Surface Plot (GOOGL)\033[0m"
#python $BASE/test_model_generator.py --ticker GOOGL --badge-type rectangular --base-height 1 --feature-type surface_plot \
#    --base-width 100 --base-depth 60 --text-position top --output example4_rect_surface.scad --skip-report

# Example 5: Triangular Badge with Pyramid
#echo -e "\n\033[1;36mExample 5: Triangular Badge with Pyramid (AMZN)\033[0m"
#python $BASE/test_model_generator.py --ticker AMZN --badge-type triangular --base-height 1 --feature-type pyramid \
#    --side-length 90 --text-position front --text-size 15 --output example5_tri_pyramid.scad --skip-report

# Example 6: Custom Badge with Modified Parameters
#echo -e "\n\033[1;36mExample 6: Custom Badge with Modified Parameters (NFLX)\033[0m"
#python $BASE/test_model_generator.py --ticker NFLX --badge-type disc --terrain-type bar_chart \
#    --base-radius 45 --text-content "BULLISH" --text-size 12 --text-depth 2.5 \
#    --base-height 2 --feature-height 15 --height-range-max 18 --width-range-max 12 \
#    --output example6_custom.scad --skip-report

echo -e "\n\033[1;32m=== All Example Badges Generated ===\033[0m"
echo "Generated SCAD files:"
ls -l example*.scad

echo -e "\nYou can open these files in OpenSCAD to view the badges."
echo "For example: openscad example1_disc_basic.scad"

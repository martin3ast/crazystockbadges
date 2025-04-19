#!/usr/bin/env python3
"""
Test script for the improved Crazy Stock Badges with pyGAD.

This script demonstrates how to use the pyGAD implementation
of the genetic algorithm for badge generation.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for testing pyGAD implementation - Apr 13, 2025.
"""

import os
import sys
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_pygad')

# Try to import pyGAD
try:
    import pygad
    logger.info("pyGAD is installed")
except ImportError:
    logger.error("pyGAD is not installed. Please install it using: pip install pygad")
    print("pyGAD is not installed. Please install it using: pip install pygad")
    sys.exit(1)

# Import the improved modules
from improved_crazystockbadges_pygad import CrazyStockBadges


def test_pygad_implementation():
    """Test the pyGAD implementation of the genetic algorithm."""
    print("\n=== Testing Improved Crazy Stock Badges with pyGAD ===")
    
    # Create the application
    app = CrazyStockBadges()
    
    # Run with arguments
    app.run([
        '--ticker', 'AAPL',
        '--period', '1mo',
        '--output', 'test_pygad_badge.scad',
        '--ga-generations', '20',  # Use fewer generations for testing
        '--non-interactive'
    ])
    
    # Check if the output file was created
    if os.path.exists('test_pygad_badge.scad'):
        print(f"Success! Badge created: test_pygad_badge.scad")
    else:
        print("Error: Badge file was not created")
    
    print("pyGAD test complete")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test pyGAD implementation for Crazy Stock Badges')
    parser.add_argument('--install-pygad', action='store_true', help='Install pyGAD if not already installed')
    
    args = parser.parse_args()
    
    # Install pyGAD if requested
    if args.install_pygad:
        try:
            import pygad
            print("pyGAD is already installed")
        except ImportError:
            print("Installing pyGAD...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pygad"])
            print("pyGAD installed successfully")
    
    try:
        test_pygad_implementation()
        return 0
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

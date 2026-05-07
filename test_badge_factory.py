#!/usr/bin/env python3
"""
Smoke tests for badge_factory.py.

These tests exercise the public surface of BadgeFactory and Badge3DModel for each
badge type. They do not verify visual correctness — only that the construction
pipeline (generate_base -> generate_terrain -> generate_text -> combine_models)
runs without error and produces a non-None final model.
"""

import unittest
import numpy as np
import pandas as pd
from badge_factory import BadgeFactory


class TestBadgeFactorySmoke(unittest.TestCase):
    """Each badge type must build a final_model from synthetic stock data."""

    def setUp(self):
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=30)
        self.data = pd.DataFrame({
            'Open': np.random.uniform(100, 200, 30),
            'High': np.random.uniform(110, 210, 30),
            'Low': np.random.uniform(90, 190, 30),
            'Close': np.random.uniform(100, 200, 30),
            'Volume': np.random.randint(1_000_000, 10_000_000, 30),
        }, index=dates)
        self.ticker = 'TEST'
        self.base_params = {
            'text_position': 0,
            'text_content': 'TEST',
            'base_height': 2,
            'height_range': (0, 10),
            'width_range': (0, 10),
            'text_size': 8,
            'text_depth': 1,
            'spiral_turns': 5,
            'terrain_types': ['bar_chart'],
        }

    def _build(self, badge_type, extra_params):
        params = {**self.base_params, **extra_params, 'badge_type': badge_type}
        badge = BadgeFactory.create_badge(badge_type, self.data, self.ticker, params)
        badge.generate_base()
        badge.generate_terrain()
        badge.generate_text()
        badge.combine_models()
        return badge

    def test_disc_badge_builds(self):
        badge = self._build('disc', {'base_radius': 50})
        self.assertIsNotNone(badge.final_model)

    def test_rectangular_badge_builds(self):
        badge = self._build('rectangular', {'base_width': 90, 'base_depth': 60})
        self.assertIsNotNone(badge.final_model)

    def test_triangular_badge_builds(self):
        badge = self._build('triangular', {'side_length': 80})
        self.assertIsNotNone(badge.final_model)

    def test_combined_terrain_types_build(self):
        badge = self._build('disc', {
            'base_radius': 50,
            'terrain_types': ['spiral_chart', 'bar_chart', 'pyramid', 'surface_plot'],
        })
        self.assertIsNotNone(badge.final_model)


if __name__ == '__main__':
    unittest.main()

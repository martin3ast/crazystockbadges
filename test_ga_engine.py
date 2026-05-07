#!/usr/bin/env python3
"""Tests for the shared GA engine."""

import unittest
from unittest.mock import MagicMock
import numpy as np
import pandas as pd
from ga_engine import (
    GENE_SPACE,
    BADGE_TYPES,
    TERRAIN_TYPES,
    genes_to_badge_params,
    BadgeGAEngine,
)


class TestGeneSpace(unittest.TestCase):
    def test_gene_space_has_eleven_genes(self):
        self.assertEqual(len(GENE_SPACE), 11)


class TestGenesToBadgeParams(unittest.TestCase):
    def setUp(self):
        self.mdm = MagicMock()
        self.mdm.get_sentiment.return_value = 0.5
        self.mdm.get_one_word_analysis.return_value = "GROWTH"

    def test_disc_genes_produce_disc_params(self):
        # disc=0, num_terrains=1, terrain=bar_chart(1), pad, pad, pad,
        # text_pos=180.0, text_type=one_word(0), base_h=2, size=med(1), spiral=5
        genes = [0, 1, 1, 0, 0, 0, 180.0, 0, 2, 1, 5]
        params = genes_to_badge_params(genes, 'TST', self.mdm)
        self.assertEqual(params['badge_type'], 'disc')
        self.assertEqual(params['terrain_types'], ['bar_chart'])
        self.assertEqual(params['base_radius'], 50)  # medium disc
        self.assertIn('TST', params['text_content'])

    def test_rectangular_genes_set_width_and_depth(self):
        genes = [1, 1, 0, 0, 0, 0, 0.0, 0, 1, 0, 5]
        params = genes_to_badge_params(genes, 'TST', self.mdm)
        self.assertEqual(params['badge_type'], 'rectangular')
        self.assertEqual(params['base_width'], 60)  # small
        self.assertEqual(params['base_depth'], 40)


class TestBadgeGAEngineRun(unittest.TestCase):
    """Run a single-generation GA against synthetic data and verify the engine
    produces a non-None best badge and a finite fitness."""

    def test_one_generation_produces_best_badge(self):
        np.random.seed(0)
        dates = pd.date_range(start='2024-01-01', periods=30)
        data = pd.DataFrame({
            'Open': np.random.uniform(100, 200, 30),
            'High': np.random.uniform(110, 210, 30),
            'Low': np.random.uniform(90, 190, 30),
            'Close': np.random.uniform(100, 200, 30),
            'Volume': np.random.randint(1_000_000, 10_000_000, 30),
        }, index=dates)

        mdm = MagicMock()
        mdm.data = data
        mdm.get_sentiment.return_value = 0.5
        mdm.get_one_word_analysis.return_value = "FLAT"
        mdm.get_buy_sell_hold.return_value = "HOLD"
        mdm.get_latest_macd.return_value = "0.0"
        mdm.get_high.return_value = "200"
        mdm.get_low.return_value = "100"
        mdm.get_market_outlook.return_value = "STABLE"

        engine = BadgeGAEngine(mdm=mdm, ticker='TST', num_generations=1)
        best_badge, best_fitness = engine.run()
        self.assertIsNotNone(best_badge)
        self.assertGreater(best_fitness, 0)


if __name__ == '__main__':
    unittest.main()

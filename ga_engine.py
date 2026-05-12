#!/usr/bin/env python3
"""
Shared genetic algorithm engine for badge generation.

Consumed by both the CLI (crazystockbadges.py) and the Flask app (app.py) so that
gene space, fitness, and pyGAD setup live in exactly one place. Per-call-site
behavior (progress prints vs database updates) is plugged in via the
`on_generation` callback.
"""

import logging
import warnings

import pygad

from badge_factory import BadgeFactory
from complexity_analyser import ComplexityAnalyzer

logger = logging.getLogger('ga_engine')

GENE_SPACE = [
    [0, 1, 2],                      # 0: Badge type (disc/rectangular/triangular)
    [1, 2, 3, 4],                   # 1: Number of terrain types
    [0, 1, 2, 3],                   # 2: Terrain type 1
    [0, 1, 2, 3],                   # 3: Terrain type 2
    [0, 1, 2, 3],                   # 4: Terrain type 3
    [0, 1, 2, 3],                   # 5: Terrain type 4
    {'low': 0, 'high': 360},        # 6: Text rotation (degrees)
    [0, 1, 2, 3, 4, 5],             # 7: Text content type
    [1, 2, 3],                      # 8: Base height
    [0, 1, 2],                      # 9: Size (small/medium/large)
    {'low': 3, 'high': 10},         # 10: Spiral turns
]

BADGE_TYPES = ['disc', 'rectangular', 'triangular']
TERRAIN_TYPES = ['spiral_chart', 'bar_chart', 'pyramid', 'surface_plot']
TEXT_CONTENT_TYPES = [
    'one_word_analysis', 'buy_sell_hold', 'latest_macd',
    'high', 'low', 'market_outlook',
]
SIZE_MAPS = {
    'disc': {'base_radius': [30, 50, 70]},
    'rectangular': {'base_width': [60, 90, 120], 'base_depth': [40, 60, 80]},
    'triangular': {'side_length': [60, 80, 100]},
}


def _resolve_text_content(text_type, sentiment, mdm):
    dispatch = {
        'one_word_analysis': lambda: mdm.get_one_word_analysis(sentiment),
        'buy_sell_hold': lambda: mdm.get_buy_sell_hold(sentiment),
        'latest_macd': mdm.get_latest_macd,
        'high': mdm.get_high,
        'low': mdm.get_low,
        'market_outlook': lambda: mdm.get_market_outlook(sentiment),
    }
    return dispatch.get(text_type, lambda: "Unknown")()


def genes_to_badge_params(genes, ticker, mdm):
    """Decode a pyGAD gene vector into a badge parameter dict."""
    badge_type = BADGE_TYPES[int(genes[0])]
    num_terrain_types = int(genes[1])
    terrain_types = [TERRAIN_TYPES[int(genes[2 + i])] for i in range(num_terrain_types)]

    text_position = genes[6]
    text_type = TEXT_CONTENT_TYPES[int(genes[7])]
    base_height = int(genes[8])
    size_idx = int(genes[9])
    spiral_turns = int(genes[10])

    sentiment = mdm.get_sentiment()
    text_content = ticker + " " + _resolve_text_content(text_type, sentiment, mdm)

    params = {
        'badge_type': badge_type,
        'text_position': text_position,
        'text_content': text_content,
        'base_height': base_height,
        'height_range': (0, 10),
        'width_range': (0, 10),
        'text_size': 10,
        'text_depth': 2,
        'spiral_turns': spiral_turns,
        'terrain_types': terrain_types,
    }
    for key, values in SIZE_MAPS[badge_type].items():
        params[key] = values[size_idx]
    return params


class BadgeGAEngine:
    """Wraps pyGAD with badge-specific fitness, gene space, and progress hooks.

    The fitness is the sum of two raw counts from ComplexityAnalyzer:
    `total_nodes` (every node in the SolidPython tree) and `complexity_score`
    (a weighted sum of primitive, operation, and polygonal counts). See the
    docstring of `ComplexityAnalyzer._calculate_simple_complexity_score` for the
    intentional double-weighting of operation nodes.
    """

    def __init__(self, mdm, ticker, num_generations=10, on_generation=None):
        self.mdm = mdm
        self.ticker = ticker
        self.num_generations = num_generations
        self._on_generation_hook = on_generation

        self.best_badge = None
        self.best_fitness = float('-inf')
        self.best_solution = None
        self.ga_instance = None

    def fitness(self, ga_instance, solution, solution_idx):
        params = genes_to_badge_params(solution, self.ticker, self.mdm)
        badge = BadgeFactory.create_badge(
            params['badge_type'], self.mdm.data, self.ticker, params,
        )
        badge.generate_base()
        badge.generate_terrain()
        badge.generate_text()
        badge.combine_models()

        report = ComplexityAnalyzer(badge.final_model).get_complexity_report()

        if not hasattr(ga_instance, 'badges'):
            ga_instance.badges = {}

        fitness_value = report['total_nodes'] + report['complexity_score']
        ga_instance.badges[solution_idx] = (badge, report, fitness_value)

        if fitness_value > self.best_fitness:
            self.best_fitness = fitness_value
            self.best_badge = badge
            self.best_solution = list(solution)
            logger.debug(
                "New best: idx=%d fitness=%.2f", solution_idx, fitness_value,
            )
        return fitness_value

    def _on_generation(self, ga_instance):
        if self._on_generation_hook is not None:
            self._on_generation_hook(ga_instance, self)

    def run(self):
        warnings.filterwarnings(
            "ignore", message="Use the 'save_solutions' parameter with caution",
        )
        self.ga_instance = pygad.GA(
            num_generations=self.num_generations,
            num_parents_mating=2,
            fitness_func=self.fitness,
            sol_per_pop=20,
            num_genes=len(GENE_SPACE),
            gene_space=GENE_SPACE,
            parent_selection_type="tournament",
            K_tournament=2,
            crossover_type="two_points",
            crossover_probability=0.8,
            mutation_type="adaptive",
            mutation_num_genes=[3, 1],
            keep_elitism=1,
            mutation_probability=[0.3, 0.1],
            on_generation=self._on_generation,
            allow_duplicate_genes=True,
            save_solutions=True,
        )
        self.ga_instance.run()
        return self.best_badge, self.best_fitness

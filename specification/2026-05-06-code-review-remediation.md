# Code Review Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Address concrete code-review findings (stale documentation, duplicated code, dead code, fitness-function ambiguity) without changing the project's creative behavior.

**Architecture:** Three layers of work — (1) trivial fixes and documentation corrections done in place; (2) a smoke-test safety net added before any refactor; (3) shared GA engine extracted to `ga_engine.py` and consumed by both `crazystockbadges.py` (CLI) and `app.py` (Flask). Computational-creativity enhancements (sentiment→shape coupling, novelty-search fitness, MACD reinstatement) are explicitly out of scope and listed as follow-ups at the bottom of this plan — they need their own brainstorming pass.

**Tech Stack:** Python 3.12, `uv` for deps and execution, `unittest` (matching the existing `test_marketdata.py` style), pyGAD 3.4, SolidPython, Flask, SQLite.

**Conventions:**
- Run everything via `uv run` (project preference, see memory).
- Run a single test with `uv run python -m unittest <module>.<class>.<method> -v`.
- Each task ends with a focused commit. Use Conventional Commits style (`fix:`, `refactor:`, `docs:`, `test:`).

---

## Task 0: Fix `latest_macd` key mismatch (pre-existing baseline failure)

**Files:**
- Modify: `crazystockbadges.py:185`
- Modify: `test_marketdata.py:180`

Discovered while running the baseline test suite. `MarketDataManager.get_summary_stats()` returns the dict key `macd`, but `crazystockbadges.py:185` and `test_marketdata.py:180` both read `stats['latest_macd']`. Introduced in commit `2d5ce76` ("Cleanup and updates"); the test has been failing and the CLI would `KeyError` after technical analysis. Fix the consumers, not the producer — the surrounding dict already uses unprefixed keys (`rsi`, `sma_20`).

The prototype files under `prototype/cline_iteration1/` also reference the old key but are out of scope (preserved as historical artifacts).

- [ ] **Step 1: Confirm the bug is reproducible**

Run: `uv run python -m unittest test_marketdata.TestMarketDataManager.test_get_summary_stats -v`
Expected: FAIL with `'latest_macd' not found in {...}`.

- [ ] **Step 2: Fix the CLI consumer**

In `crazystockbadges.py:185`, change:
```python
print(f"{Fore.BLUE}...   Latest MACD = {stats['latest_macd']} {Style.RESET_ALL}")
```
to:
```python
print(f"{Fore.BLUE}...   Latest MACD = {stats['macd']} {Style.RESET_ALL}")
```

- [ ] **Step 3: Fix the test expectation**

In `test_marketdata.py:180`, change:
```python
self.assertIn('latest_macd', stats)
```
to:
```python
self.assertIn('macd', stats)
```

- [ ] **Step 4: Run the full marketdata suite**

Run: `uv run python -m unittest test_marketdata -v`
Expected: 26 tests pass, 0 failures.

- [ ] **Step 5: Commit**

```bash
git add crazystockbadges.py test_marketdata.py
git commit -m "fix: correct macd key reference in CLI and test"
```

---

## Task 1: Fix README inaccuracies

**Files:**
- Modify: `README.md`

The README currently tells readers to embed an API key in source, mentions a conda environment that the project no longer uses (it uses `uv`), states the wrong default log level, and lists a `badge_factory_refactored.py` file that doesn't exist.

- [ ] **Step 1: Read the current README**

Run: `cat README.md`

- [ ] **Step 2: Replace the API-key instructions**

Find the block that begins:
```markdown
The application uses a personal OpenRouter API for generating stock reports, which will expire in 3 months.

```python
# In marketdata.py
DEFAULT_API_KEY = 'your-api-key-here'
```

This can also be set with `OPENROUTER_API_KEY` environment variable.
```

Replace with:

```markdown
The application uses an OpenRouter API key for generating stock reports.

1. Copy `.env.example` to `.env`.
2. Set `OPENROUTER_API_KEY=<your-key>` in `.env`.

The key is loaded via `python-dotenv`; do not hard-code it in source files.
```

- [ ] **Step 3: Replace the conda block with a uv block**

Find:
```markdown
### Conda Environment Setup

The project uses a conda environment to manage dependencies. Set it up with:

```bash
# Create and activate the environment from environment.yml
conda env create -f environment.yml
conda activate crazystockbadges
```
```

Replace with:

```markdown
### Python Environment Setup

The project uses [uv](https://docs.astral.sh/uv/) to manage dependencies (see `pyproject.toml`). To set up:

```bash
uv sync
```

To run any script, prefix it with `uv run`, e.g. `uv run python crazystockbadges.py`.
```

- [ ] **Step 4: Fix the log-level default**

In the `--log-level` row of the command-line options table, replace `(default: INFO)` with `(default: WARN)`.

- [ ] **Step 5: Fix the directory listing**

Remove the line `├── badge_factory_refactored.py # Refactored badge factory` from the directory tree. The file doesn't exist.

- [ ] **Step 6: Verify the README renders**

Run: `head -100 README.md` and visually confirm the corrections are in place.

- [ ] **Step 7: Commit**

```bash
git add README.md
git commit -m "docs: correct README — uv (not conda), env-based API key, accurate defaults"
```

---

## Task 2: Remove duplicate `MarketDataManager` class declaration

**Files:**
- Modify: `marketdata.py:59-72`

`marketdata.py` defines an empty `class MarketDataManager:` immediately followed by a second `class MarketDataManager:` with the real implementation. Python silently keeps the second one, but this is copy-paste residue that confuses readers.

- [ ] **Step 1: Read the affected region**

Run: `uv run python -c "import marketdata; print(marketdata.MarketDataManager)"`
Expected: `<class 'marketdata.MarketDataManager'>` (proves the second definition wins).

- [ ] **Step 2: Remove the first stub**

In `marketdata.py`, delete lines 59 through 65 inclusive (the first empty `class MarketDataManager:` block, including its docstring). Verify line 67's `class MarketDataManager:` becomes the only declaration.

- [ ] **Step 3: Re-run the existing tests**

Run: `uv run python -m unittest test_marketdata -v`
Expected: All tests pass (no regressions from the deletion).

- [ ] **Step 4: Commit**

```bash
git add marketdata.py
git commit -m "fix: remove duplicate MarketDataManager class declaration"
```

---

## Task 3: Remove unused `pdb` import

**Files:**
- Modify: `crazystockbadges.py:30`

`import pdb` was left in for debugging; nothing references it.

- [ ] **Step 1: Confirm `pdb` is unused**

Run: `grep -n "pdb" crazystockbadges.py`
Expected: only the import line itself.

- [ ] **Step 2: Delete the import line**

Remove `import pdb` (and the preceding `# Import Python debugger` comment) from `crazystockbadges.py:29-30`.

- [ ] **Step 3: Verify the module still imports**

Run: `uv run python -c "import crazystockbadges"`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add crazystockbadges.py
git commit -m "chore: drop unused pdb import"
```

---

## Task 4: Fix CLI output filename print order

**Files:**
- Modify: `crazystockbadges.py:226-231`

When `--output` is omitted, the CLI prints `... Writing SCAD object to None` before the default filename is computed.

- [ ] **Step 1: Read the affected region**

```bash
sed -n '224,235p' crazystockbadges.py
```

You'll see:
```python
output_file = self.args.output 
print(f"{Fore.BLUE}... Writing SCAD object to {output_file}...{Style.RESET_ALL}")

# Closing information
#
output_file = self.args.output if self.args.output else f"./scad_models/{self.ticker}_badge.scad"
```

- [ ] **Step 2: Reorder so the default is computed before the print**

Replace the block above with:

```python
# Closing information
output_file = self.args.output if self.args.output else f"./scad_models/{self.ticker}_badge.scad"
print(f"{Fore.BLUE}... Writing SCAD object to {output_file}...{Style.RESET_ALL}")
```

- [ ] **Step 3: Smoke-check the CLI startup path**

Run: `uv run python crazystockbadges.py --help`
Expected: argparse help text prints without error.

(Full end-to-end run requires a network call to yfinance; we add a proper test in later tasks.)

- [ ] **Step 4: Commit**

```bash
git add crazystockbadges.py
git commit -m "fix: print SCAD output filename after default is resolved"
```

---

## Task 5: Add smoke tests for `BadgeFactory`

**Files:**
- Create: `test_badge_factory.py`

`badge_factory.py` is the largest module (1,496 lines) and is currently untested. Before refactoring anything that touches it (Tasks 7 and 9), we need a minimum safety net: each badge type must construct, generate, and combine without error.

- [ ] **Step 1: Write the failing test file**

Create `test_badge_factory.py`:

```python
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
```

- [ ] **Step 2: Run the test file and confirm it passes**

Run: `uv run python -m unittest test_badge_factory -v`
Expected: 4 tests, all PASS.

If a test fails, *do not* paper over it — the failure is real information. Investigate and either fix the underlying bug or update the test to match the contract you actually want.

- [ ] **Step 3: Commit**

```bash
git add test_badge_factory.py
git commit -m "test: add smoke tests for BadgeFactory across all badge types"
```

---

## Task 6: Add smoke tests for `ComplexityAnalyzer`

**Files:**
- Create: `test_complexity_analyser.py`

We're about to prune dead branches in `_traverse_and_count_nodes` (Task 9). We need tests that prove the surviving branches do their job before we delete anything.

- [ ] **Step 1: Write the test file**

Create `test_complexity_analyser.py`:

```python
#!/usr/bin/env python3
"""
Smoke tests for complexity_analyser.py.

Verify that ComplexityAnalyzer counts nodes, identifies primitives vs operations,
and produces a non-zero complexity score for representative SolidPython structures.
"""

import unittest
from solid import cube, sphere, union, translate
from complexity_analyser import ComplexityAnalyzer


class TestComplexityAnalyzer(unittest.TestCase):
    def test_single_primitive_counts_one_node(self):
        analyzer = ComplexityAnalyzer(cube([10, 10, 10]))
        report = analyzer.get_complexity_report()
        self.assertGreaterEqual(report['total_nodes'], 1)
        self.assertGreater(report['complexity_score'], 0)

    def test_union_increases_node_count(self):
        small = ComplexityAnalyzer(cube([1, 1, 1])).get_complexity_report()
        bigger = ComplexityAnalyzer(
            union()(cube([1, 1, 1]), sphere(1), translate([5, 0, 0])(cube([2, 2, 2])))
        ).get_complexity_report()
        self.assertGreater(bigger['total_nodes'], small['total_nodes'])
        self.assertGreater(bigger['complexity_score'], small['complexity_score'])

    def test_operation_node_recorded_in_operation_counts(self):
        report = ComplexityAnalyzer(union()(cube([1, 1, 1]), sphere(1))).get_complexity_report()
        op_total = sum(report['operation_counts'].values())
        self.assertGreaterEqual(op_total, 1, f"Expected ≥1 operation, got {dict(report['operation_counts'])}")


if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Run the tests**

Run: `uv run python -m unittest test_complexity_analyser -v`
Expected: 3 tests, all PASS.

- [ ] **Step 3: Commit**

```bash
git add test_complexity_analyser.py
git commit -m "test: add smoke tests for ComplexityAnalyzer"
```

---

## Task 7: Extract shared GA engine

**Files:**
- Create: `ga_engine.py`
- Create: `test_ga_engine.py`
- Modify: `crazystockbadges.py`
- Modify: `app.py`

The GA logic (gene space, gene-to-params decoding, fitness, pyGAD setup) is duplicated between CLI and web with minor drift. Extract it into a single module that both call sites consume via callbacks for progress reporting.

- [ ] **Step 1: Write the failing test for `ga_engine`**

Create `test_ga_engine.py`:

```python
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
```

- [ ] **Step 2: Run the new test (should fail because `ga_engine` doesn't exist yet)**

Run: `uv run python -m unittest test_ga_engine -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ga_engine'`.

- [ ] **Step 3: Create `ga_engine.py`**

Create `ga_engine.py`:

```python
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
```

- [ ] **Step 4: Run `test_ga_engine` and confirm it passes**

Run: `uv run python -m unittest test_ga_engine -v`
Expected: 4 tests, all PASS.

- [ ] **Step 5: Commit the engine and its tests**

```bash
git add ga_engine.py test_ga_engine.py
git commit -m "feat: extract shared BadgeGAEngine with gene-space and fitness"
```

- [ ] **Step 6: Migrate `crazystockbadges.py` (CLI) to use the engine**

In `crazystockbadges.py`:

1. At the top, replace the GA-specific imports and `BadgeFactory`/`ComplexityAnalyzer` imports as needed:

```python
from ga_engine import BadgeGAEngine, GENE_SPACE
```

2. Delete the methods `genes_to_badge_params`, `fitness_function`, `_create_gene_space` (they are now in `ga_engine`).

3. Replace the body of `generate_badge` (lines 243–328) with this version that delegates to the engine and keeps all the CLI-specific bookkeeping (progress prints, fitness-stats tracking for plotting, terminal output) in `_on_generation`:

```python
def generate_badge(self):
    """Generate 3D badge using shared GA engine."""
    self.logger.info("Generating 3D badge using shared GA engine")

    def on_generation(ga_instance, engine):
        # Track best fitness across generations on the CLI object so existing
        # visualise_ga_results() keeps working.
        best_solution, best_fitness, solution_idx = ga_instance.best_solution()
        fitness_values = [
            ga_instance.badges[i][2]
            for i in range(len(ga_instance.population))
            if i in ga_instance.badges
        ]
        self.fitness_stats['generation'].append(ga_instance.generations_completed)
        self.fitness_stats['min'].append(min(fitness_values))
        self.fitness_stats['mean'].append(statistics.mean(fitness_values))
        self.fitness_stats['max'].append(max(fitness_values))
        self.fitness_stats['best'].append(best_fitness)

        print(f"{Fore.BLUE}.oOo.{Style.RESET_ALL}", end="")
        if ga_instance.generations_completed % 5 == 0:
            self.logger.info(
                f"Generation {ga_instance.generations_completed}: "
                f"Best fitness = {best_fitness:.2f}"
            )
            print(
                f"{Fore.BLUE} ... Best fitness: {best_fitness:.2f} "
                f"{Style.RESET_ALL}"
            )

    engine = BadgeGAEngine(
        mdm=self.mdm,
        ticker=self.ticker,
        num_generations=self.ga_generations,
        on_generation=on_generation,
    )
    self.logger.info(f"Running GA for {self.ga_generations} generations")
    best_badge, best_fitness = engine.run()
    self.ga_instance = engine.ga_instance
    self.best_badge = best_badge
    self.best_fitness = best_fitness

    output_file = (
        self.args.output if self.args.output
        else f"./scad_models/{self.ticker}_badge.scad"
    )
    self.args.output = output_file
    os.makedirs("./scad_models", exist_ok=True)
    best_badge.save_to_file(output_file)

    self.badge = best_badge
    self.badge_params = best_badge.params
    self.badge_output_file = output_file
    self.logger.info(
        f"Best fitness: {best_fitness:.2f} — saved badge to {output_file}"
    )

    if self.args.visualise_ga:
        self.visualise_ga_results()
```

4. Also delete `_on_generation` (its responsibilities are now in the closure above).

- [ ] **Step 7: Verify CLI module still imports**

Run: `uv run python -c "import crazystockbadges; print('ok')"`
Expected: `ok`.

Run: `uv run python crazystockbadges.py --help`
Expected: argparse help text prints.

- [ ] **Step 8: Migrate `app.py` (Flask) to use the engine**

In `app.py`, replace the contents of class `WebBadgeGenerator` from `_run_genetic_algorithm` through `_create_gene_space` (lines 112–294) with this slimmer version that delegates to the engine:

```python
def _run_genetic_algorithm(self):
    """Run the genetic algorithm with progress tracking."""
    def on_generation(ga_instance, engine):
        current_generation = ga_instance.generations_completed
        progress_pct = 30 + (current_generation / self.ga_generations) * 70
        progress = min(99, int(progress_pct))

        db.update_session(
            self.session_id,
            current_generation=current_generation,
            progress=progress,
            best_fitness=engine.best_fitness,
        )

        if hasattr(ga_instance, 'badges'):
            fitness_values = [
                ga_instance.badges[i][2]
                for i in range(len(ga_instance.population))
                if i in ga_instance.badges
            ]
            if fitness_values:
                db.add_fitness_stat(
                    self.session_id,
                    current_generation,
                    min(fitness_values),
                    sum(fitness_values) / len(fitness_values),
                    max(fitness_values),
                    engine.best_fitness,
                )

    engine = BadgeGAEngine(
        mdm=self.mdm,
        ticker=self.ticker,
        num_generations=self.ga_generations,
        on_generation=on_generation,
    )
    self.ga_instance = engine.ga_instance
    self.best_badge, self.best_fitness = engine.run()
    self.ga_instance = engine.ga_instance

    if self.best_badge:
        session_filename = f"{self.session_id}_{self.ticker}_badge"
        scad_dir = '/tmp/scad_models' if os.getenv('VERCEL') else './scad_models'
        stl_dir = '/tmp/stl_models' if os.getenv('VERCEL') else './stl_models'
        output_file = f"{scad_dir}/{session_filename}.scad"
        os.makedirs(scad_dir, exist_ok=True)
        os.makedirs(stl_dir, exist_ok=True)

        self.best_badge.save_to_file(output_file)

        try:
            logger.info(
                f"Starting STL generation for session {self.session_id}, "
                f"filename: {session_filename}"
            )
            self.best_badge.save_to_stl_async(session_filename)
            logger.info("STL generation started in background")
        except Exception as e:
            logger.warning(
                f"STL generation failed to start: {e} — "
                "3D preview may not be available"
            )
```

Then remove `_fitness_function`, `_genes_to_badge_params`, `_get_text_content`, `_create_gene_space`, and the now-unused imports of `BadgeFactory`, `ComplexityAnalyzer`, `pygad`, `warnings` (only if no other code in `app.py` uses them — verify with grep).

Add at the top of `app.py`:
```python
from ga_engine import BadgeGAEngine
```

- [ ] **Step 9: Verify `app.py` still imports**

Run: `uv run python -c "import app; print('ok')"`
Expected: `ok`.

- [ ] **Step 10: Re-run all existing tests**

Run: `uv run python -m unittest discover -v`
Expected: every test passes (4 BadgeFactory + 3 ComplexityAnalyzer + 4 ga_engine + the existing test_marketdata suite).

- [ ] **Step 11: Commit**

```bash
git add crazystockbadges.py app.py
git commit -m "refactor: route CLI and Flask through shared BadgeGAEngine"
```

---

## Task 8: Document fitness double-counting in `ComplexityAnalyzer`

**Files:**
- Modify: `complexity_analyser.py:165-182`

The current scoring counts each operation node once via `total_nodes` and again via `operation_counts * 1.5` inside `complexity_score`, and the GA fitness is `total_nodes + complexity_score`. This is a real bias toward operation-heavy designs. We document it now so it can't be silently changed; reweighting is left to a separate CC-driven brainstorming session.

- [ ] **Step 1: Read the existing function**

```bash
sed -n '163,185p' complexity_analyser.py
```

- [ ] **Step 2: Update the docstring of `_calculate_simple_complexity_score`**

Replace the function with:

```python
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
```

- [ ] **Step 3: Confirm tests still pass**

Run: `uv run python -m unittest test_complexity_analyser -v`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add complexity_analyser.py
git commit -m "docs: explain operation-node double-weighting in fitness"
```

---

## Task 9: Prune dead branches in `_traverse_and_count_nodes`

**Files:**
- Modify: `complexity_analyser.py:78-115`

The traversal handles three different child-attribute patterns (`children`, `child`, `objects`). SolidPython 1.x consistently uses `children`. Any branch that's truly dead is noise.

- [ ] **Step 1: Verify SolidPython actually uses `children` only**

Run:
```bash
uv run python - <<'PY'
from solid import cube, sphere, union, translate
nodes = [cube(1), translate([1,0,0])(cube(1)), union()(cube(1), sphere(1))]
for n in nodes:
    print(type(n).__name__,
          'children:', hasattr(n, 'children'),
          'child:', hasattr(n, 'child'),
          'objects:', hasattr(n, 'objects'))
PY
```

If every node reports `children: True` and `child: False, objects: False`, the `.child` and `.objects` branches are dead in our SolidPython version.

- [ ] **Step 2: Decide based on the output above**

- If both `.child` and `.objects` branches are dead → proceed to Step 3.
- If either is live → leave the corresponding branch alone, prune only the dead one (or skip this task entirely and document the finding in the commit message of Task 8).

- [ ] **Step 3: Remove the dead branches**

Replace the body of `_traverse_and_count_nodes` (after the `if isinstance(node, (list, tuple))` branch) with the simpler form:

```python
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
```

- [ ] **Step 4: Re-run the test suite**

Run: `uv run python -m unittest discover -v`
Expected: all PASS — including the BadgeFactory smoke tests, which generate real SolidPython trees.

- [ ] **Step 5: Commit**

```bash
git add complexity_analyser.py
git commit -m "refactor: drop dead .child and .objects branches in node traversal"
```

---

## Task 10: Remove commented-out plot code in CLI

**Files:**
- Modify: `crazystockbadges.py:645-655`

The `visualise_ga_results` method has multi-line commented-out calls to `plot_fitness` / `plot_new_solution_rate`. Pick one path: restore them or delete them. We delete because `plot_fitness_statistics` already produces a useful plot.

- [ ] **Step 1: Open `visualise_ga_results`**

Run: `sed -n '631,665p' crazystockbadges.py`

- [ ] **Step 2: Delete the commented-out blocks**

Remove these blocks (they currently sit between the docstring and the call to `self.plot_fitness_statistics`):

```python
        # Plot fitness evolution directly from the GA instance
        # fitness_fig = self.ga_instance.plot_fitness(
        #     title=f"{self.ticker} Badge - Fitness Evolution",
        #     save_dir=plots_dir
        # )
        
        # # Plot new solution rate directly from the GA instance
        # solution_rate_fig = self.ga_instance.plot_new_solution_rate(
        #     title=f"{self.ticker} Badge - New Solution Rate",
        #     save_dir=plots_dir
        # )
        
        # Plot fitness statistics (min, mean, max)
        # if self.fitness_stats['generation']:
```

Replace with a single comment:

```python
        # plot_fitness_statistics writes the only plot we actually use today;
        # PyGAD's built-in plot_fitness/plot_new_solution_rate hooks were
        # removed because they duplicate that information.
```

- [ ] **Step 3: Verify the module still imports**

Run: `uv run python -c "import crazystockbadges"`
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add crazystockbadges.py
git commit -m "chore: drop commented-out PyGAD plot calls in visualise_ga_results"
```

---

## Task 11: Trim the NRC VAD lexicon to the files we actually use

**Files:**
- Delete: `NRC-VAD-Lexicon/OneFilePerLanguage/` (the whole directory)
- Delete: `NRC-VAD-Lexicon/NRC-VAD-Lexicon-ForVariousLanguages.txt`
- Delete: `NRC-VAD-Lexicon/BipolarScale/`
- Keep: `NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt`, `NRC-VAD-Lexicon/OneFilePerDimension/`, `NRC-VAD-Lexicon/README.txt`, `NRC-VAD-Lexicon/ListOfLanguages-For-Which-Lexicon-Availabale.txt`

The project only reads `NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt` (English). The 100+ per-language files inflate the repo and Docker image without ever being read.

- [ ] **Step 1: Confirm only the English file is referenced**

Run: `grep -rn "NRC-VAD-Lexicon" --include='*.py' .`
Expected: only paths matching `NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt` (or just `./NRC-VAD-Lexicon`).

If anything references the per-language directories, stop and update this task to keep those.

- [ ] **Step 2: Delete the unused subdirectories and files**

```bash
git rm -r NRC-VAD-Lexicon/OneFilePerLanguage
git rm NRC-VAD-Lexicon/NRC-VAD-Lexicon-ForVariousLanguages.txt
git rm -r NRC-VAD-Lexicon/BipolarScale
```

- [ ] **Step 3: Re-run tests to confirm nothing depended on them**

Run: `uv run python -m unittest discover -v`
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add -A NRC-VAD-Lexicon
git commit -m "chore: drop unused NRC VAD per-language and bipolar files"
```

---

## Out of scope — follow-up brainstorming items

These were surfaced in the review but require a creative-design pass (use the `superpowers:brainstorming` skill before opening a plan for any of them):

1. **Sentiment → shape coupling.** Use NRC VAD valence/arousal/dominance to bias terrain choice, spiral steepness, or text scale rather than only choosing a one-word label.
2. **Reinstate the MACD scaling factor.** The original spec had MACD multiplying the object count in fitness. The implementation dropped it. Decide whether to restore (and how to normalise it).
3. **Novelty-search fitness.** Penalise gene-space proximity to previously-saved best individuals so repeated generations diverge instead of converging to the same crazy point.
4. **Cross-session memory.** Persist past best individuals so each new badge can reference (or actively avoid) the corpus.
5. **Reweight `complexity_score`.** Once a CC writeup decides what "crazy" means, revisit the operation-node double-weighting documented in Task 8.

## Out of scope — minor cleanups left for later

- Redundant import-time `nltk.download` in `sentiment_analyser.py` (Dockerfile already pre-downloads).
- `.env.example` OpenSCAD path is Mac-flavoured; add a Linux/Docker hint comment.
- `app.py:_on_generation` callback retains `current_generation` calculation in two places after the refactor — review whether the inner-loop math can move into the engine.

---

## Verification at the end

After Task 11, run the full suite to confirm nothing regressed:

```bash
uv run python -m unittest discover -v
```

Then walk through the CLI smoke test:

```bash
uv run python crazystockbadges.py --ticker AAPL --ga-generations 2 --skip-report --non-interactive
```

(Network access required for the yfinance fetch.)

And the Flask smoke test (in another terminal):

```bash
uv run python app.py
# Then POST to http://localhost:5000/api/generate with {"ticker": "AAPL", "generations": 2}
```

If both smoke runs succeed and `git status` is clean, the remediation is complete.

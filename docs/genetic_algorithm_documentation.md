# Genetic Algorithm for Crazy Stock Badges

This document describes the genetic algorithm implementation used in the Crazy Stock Badges project, focusing on the fitness function, genotype structure, and parameter setup.

## 1. Introduction

The Crazy Stock Badges project uses a genetic algorithm to optimize 3D badge designs based on stock market data. The genetic algorithm evolves badge designs to maximize "craziness" and complexity, creating unique and interesting 3D printable badges that represent stock market data.

The genetic algorithm is implemented using the PyGAD library and is configured to evolve a population of badge designs over multiple generations. Each badge design is represented by a set of genes that encode various parameters such as badge type, terrain features, text position, and size.

## 2. Genotype Structure

The genotype (genetic representation) of a badge design consists of 11 genes, each controlling different aspects of the badge's appearance and features. The gene space is defined as follows:

| Gene Index | Description | Possible Values |
|------------|-------------|-----------------|
| 0 | Badge type | [0, 1, 2] (disc, rectangular, triangular) |
| 1 | Number of terrain types | [1, 2, 3, 4] |
| 2 | Terrain type 1 | [0, 1, 2, 3] (spiral_chart, bar_chart, pyramid, surface_plot) |
| 3 | Terrain type 2 | [0, 1, 2, 3] (spiral_chart, bar_chart, pyramid, surface_plot) |
| 4 | Terrain type 3 | [0, 1, 2, 3] (spiral_chart, bar_chart, pyramid, surface_plot) |
| 5 | Terrain type 4 | [0, 1, 2, 3] (spiral_chart, bar_chart, pyramid, surface_plot) |
| 6 | Text position | Continuous range [0, 360] (rotation in degrees) |
| 7 | Text type | [0, 1, 2, 3, 4, 5] (one_word_analysis, buy_sell_hold, latest_macd, high, low, market_outlook) |
| 8 | Base height | [1, 2, 3] |
| 9 | Size | [0, 1, 2] (small, medium, large) |
| 10 | Spiral turns | Continuous range [3, 10] |

This genotype structure allows for a wide variety of badge designs while constraining the search space to reasonable values. The combination of discrete and continuous genes enables both broad exploration of design types and fine-tuning of specific parameters.

## 3. Parameter Setup

The genes are converted to badge parameters through the `genes_to_badge_params` function. This function maps the abstract genetic representation to concrete parameters that can be used to generate the 3D model. The mapping process includes:

### Badge Type Mapping
- Gene 0 value 0 → disc badge
- Gene 0 value 1 → rectangular badge
- Gene 0 value 2 → triangular badge

### Terrain Type Mapping
- Gene 2-5 value 0 → spiral_chart
- Gene 2-5 value 1 → bar_chart
- Gene 2-5 value 2 → pyramid
- Gene 2-5 value 3 → surface_plot

### Text Type Mapping
- Gene 7 value 0 → one_word_analysis
- Gene 7 value 1 → buy_sell_hold
- Gene 7 value 2 → latest_macd
- Gene 7 value 3 → high
- Gene 7 value 4 → low
- Gene 7 value 5 → market_outlook

### Size Mapping
For disc badges:
- Gene 9 value 0 → base_radius = 30 (small)
- Gene 9 value 1 → base_radius = 50 (medium)
- Gene 9 value 2 → base_radius = 70 (large)

For rectangular badges:
- Gene 9 value 0 → base_width = 60, base_depth = 40 (small)
- Gene 9 value 1 → base_width = 90, base_depth = 60 (medium)
- Gene 9 value 2 → base_width = 120, base_depth = 80 (large)

For triangular badges:
- Gene 9 value 0 → side_length = 60 (small)
- Gene 9 value 1 → side_length = 80 (medium)
- Gene 9 value 2 → side_length = 100 (large)

The complete parameter dictionary includes additional parameters such as text content (derived from stock data and sentiment analysis), text position, base height, and spiral turns.

## 4. Fitness Function

The fitness function evaluates how "crazy" and complex a badge design is. It uses the ComplexityAnalyzer class to analyze the 3D model and calculate complexity metrics.

### Mathematical Representation

In LaTeX notation, the fitness function can be represented as:

$$F(s) = w_n \cdot N(s) + w_c \cdot C(s)$$

Where:
- $F(s)$ is the fitness of solution $s$
- $N(s)$ is the total number of nodes in the 3D model of solution $s$
- $C(s)$ is the complexity score of the 3D model of solution $s$
- $w_n$ is the weight for the total nodes metric (currently set to 1)
- $w_c$ is the weight for the complexity score metric (currently set to 1)

The complexity score $C(s)$ is calculated as:

$$C(s) = P + 1.5 \cdot O + P_s + 0.5 \cdot D$$

Where:
- $P$ is the sum of all primitive counts
- $O$ is the sum of all operation counts
- $P_s$ is the polygonal sum, calculated as:
  $$P_s = P_c + 2 \cdot P_h + 0.1 \cdot P_p + 0.2 \cdot P_f$$
  - $P_c$ is the polygon count
  - $P_h$ is the polyhedron count
  - $P_p$ is the total points count
  - $P_f$ is the total faces count
- $D$ is the maximum depth of the node tree

The fitness function rewards designs with more complex structures, more nodes, and deeper hierarchies, which generally correspond to more interesting and "crazy" badge designs.

## 5. Genetic Algorithm Configuration

The genetic algorithm is configured with the following parameters:

- Number of generations: Configurable via command-line argument (default: 10)
- Population size: 20 individuals per generation
- Number of genes: 11
- Parent selection: Tournament selection with K=2
- Crossover: Two-point crossover with probability 0.8
- Mutation: Adaptive mutation with probability ranging from 0.1 to 0.3
- Elitism: Keep the best solution from each generation
- Mutation genes: Between 1 and 3 genes are mutated per individual

## 6. Optimization Process

The genetic algorithm optimization process follows these steps:

1. **Initialization**: Create an initial population of 20 random badge designs.
2. **Evaluation**: Calculate the fitness of each design using the fitness function.
3. **Selection**: Select parents for reproduction using tournament selection.
4. **Crossover**: Create offspring by combining genes from parents using two-point crossover.
5. **Mutation**: Introduce random changes to some genes to maintain diversity.
6. **Elitism**: Preserve the best solution from the previous generation.
7. **Repeat**: Steps 2-6 are repeated for the specified number of generations.
8. **Final Solution**: The best solution from the final generation is used to generate the badge.

Throughout the process, statistics such as minimum, mean, and maximum fitness are tracked for each generation. These statistics can be visualized to show the evolution of the population over time.

## 7. Visualization

The genetic algorithm results can be visualized using matplotlib to show:

- Fitness evolution over generations
- Fitness statistics (min, mean, max) per generation
- Linear trend line for mean fitness

These visualizations help in understanding how the algorithm converges toward better solutions over time.

## 8. Conclusion

The genetic algorithm approach allows for the automatic generation of complex and interesting badge designs based on stock market data. By optimizing for complexity and "craziness," the algorithm produces unique badges that represent the stock's performance in a visually engaging way.

The combination of different badge types, terrain features, and text elements creates a vast design space, while the fitness function guides the search toward designs that are both complex and aesthetically interesting.

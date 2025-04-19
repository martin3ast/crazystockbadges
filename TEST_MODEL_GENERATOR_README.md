# Test Model Generator for Crazy Stock Badges

Version 1.0 - Cline implementation for Martin East - Documentation for test tool - Apr 16, 2025.

## Overview

This tool allows you to test the badge model generator without using the genetic algorithm. You can directly specify all parameters and see the results immediately, which is useful for:

1. Debugging the model generation process
2. Experimenting with different parameter combinations
3. Understanding how each parameter affects the final model
4. Quickly generating models with specific characteristics

## Usage

### Basic Usage

```bash
python test_model_generator.py --ticker AAPL
```

This will:
1. Fetch market data for Apple (AAPL)
2. Generate a stock report
3. Create a disc badge with default parameters
4. Save the model to `test_badge.scad`

### Specifying Badge Type

```bash
python test_model_generator.py --badge-type rectangular
```

Available badge types:
- `disc` (default)
- `rectangular`
- `triangular`

### Specifying Feature Type

```bash
python test_model_generator.py --feature-type surface_plot
```

Feature types depend on the badge type:
- For disc badges: `jagged_edge`, `spiral`
- For rectangular badges: `bar_chart`, `surface_plot`
- For triangular badges: `pyramid`, `terrain`

### Customizing Text

```bash
python test_model_generator.py --text-content "BULLISH" --text-position top --text-size 12 --text-depth 2.5
```

Text positions:
- `bottom` (default)
- `top`
- `front`

### Customizing Base Parameters

```bash
python test_model_generator.py --base-height 4 --feature-height 15
```

### Customizing Range Parameters

```bash
python test_model_generator.py --height-range-max 18 --width-range-max 12
```

### Badge-Specific Parameters

#### Disc Badge

```bash
python test_model_generator.py --badge-type disc --base-radius 60 --spiral-turns 8 --terrain-type spiral_chart
```

Terrain types for disc badge:
- `spiral_chart`
- `bar_chart`

#### Rectangular Badge

```bash
python test_model_generator.py --badge-type rectangular --base-width 110 --base-depth 70
```

#### Triangular Badge

```bash
python test_model_generator.py --badge-type triangular --side-length 90
```

### Other Options

```bash
python test_model_generator.py --period 6mo --output custom_badge.scad --skip-report
```

- `--period`: Time period for stock data (default: 1y)
- `--output`: Output file name (default: test_badge.scad)
- `--skip-report`: Skip generating stock report

## Example Combinations

### Disc Badge with Spiral Chart

```bash
python test_model_generator.py --ticker TSLA --badge-type disc --terrain-type spiral_chart --base-radius 60 --spiral-turns 8 --text-position top
```

### Rectangular Badge with Surface Plot

```bash
python test_model_generator.py --ticker AAPL --badge-type rectangular --feature-type surface_plot --base-width 110 --base-depth 70 --text-content "APPLE"
```

### Triangular Badge with Pyramid Feature

```bash
python test_model_generator.py --ticker MSFT --badge-type triangular --feature-type pyramid --side-length 90 --text-position front --text-size 15
```

## Viewing the Results

After generating a model, you can open the SCAD file in OpenSCAD to view it or export it to STL for 3D printing:

```bash
openscad test_badge.scad
```

## Troubleshooting

If you encounter any issues:

1. Check that the stock data file exists
2. Verify that all parameters are within valid ranges
3. Make sure the badge type and feature type are compatible
4. Check the log file for detailed error messages

## Parameter Ranges

- Text size: 5-15
- Text depth: 1-3
- Base height: 2-5
- Feature height: 5-20
- Height range max: 10-20
- Width range max: 5-15
- Base radius for disc: 30-70
- Spiral turns for disc: 3-10
- Base width for rectangular: 60-120
- Base depth for rectangular: 40-80
- Side length for triangular: 60-100

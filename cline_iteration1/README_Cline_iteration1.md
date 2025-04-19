# Improved Crazy Stock Badges

This directory contains improved versions of the Crazy Stock Badges project components. The original files have been left untouched, and new files have been created with enhanced functionality, better code organization, and additional features.

## Improvements Overview

The improved version includes:

1. **Better Code Organization**: Object-oriented design with clear separation of concerns
2. **Enhanced Error Handling**: Robust error handling throughout all components
3. **Improved Documentation**: Comprehensive docstrings and comments
4. **Genetic Algorithm Implementation**: For finding optimal badge designs
5. **Extended 3D Model Options**: More badge types and features
6. **Enhanced Sentiment Analysis**: More sophisticated analysis of stock reports
7. **Improved CLI**: User-friendly command-line interface with more options
8. **Data Caching**: To avoid repeated API calls for the same data
9. **Logging**: Comprehensive logging for better debugging

## File Structure

- `improved_cli.py`: Enhanced command-line interface
- `improved_market_data.py`: Improved market data fetching and analysis
- `improved_sentiment.py`: Enhanced sentiment analysis for stock reports
- `improved_3d_models.py`: Improved 3D model generation with more options
- `improved_crazystockbadges.py`: Main application integrating all components

## Requirements

The improved version requires the same dependencies as the original project, plus:

- `colorama`: For colored terminal output
- `numpy`: For numerical operations
- `pandas`: For data manipulation
- `matplotlib`: For plotting
- `nltk`: For natural language processing
- `solid`: For 3D modeling with OpenSCAD
- `requests`: For API calls

You can install these dependencies with:

```bash
pip install colorama numpy pandas matplotlib nltk solid requests
```

## Usage

### Basic Usage

```bash
python improved_crazystockbadges.py
```

This will run the application in interactive mode, prompting you for a stock ticker symbol and guiding you through the process.

### Command-Line Options

You can also provide command-line options:

```bash
python improved_crazystockbadges.py --ticker TSLA --period 1y --output tesla_badge.scad
```

For a full list of options:

```bash
python improved_cli.py --help
```

### Using Individual Components

Each component can also be used independently:

#### Market Data

```bash
python improved_market_data.py --ticker AAPL --period 1y --show-plot
```

#### Sentiment Analysis

```bash
python improved_sentiment.py --report ./stock_report
```

#### 3D Models

```bash
python improved_3d_models.py --ticker TSLA --data-file ./stock_data --badge-type disc --feature-type spiral
```

## Badge Types and Features

The improved version supports multiple badge types and features:

### Badge Types

1. **Disc**: Circular badge (default)
2. **Rectangular**: Rectangular badge
3. **Triangular**: Triangular badge

### Features

Each badge type supports different features:

- **Disc**: 
  - `jagged_edge`: Creates a jagged edge based on stock prices
  - `spiral`: Creates a spiral landscape based on stock data

- **Rectangular**:
  - `bar_chart`: Creates a bar chart based on stock prices
  - `surface_plot`: Creates a surface plot based on stock data

- **Triangular**:
  - `pyramid`: Creates a pyramid feature with height based on stock data
  - `terrain`: Creates a terrain feature based on stock data

## Genetic Algorithm

The improved version uses a genetic algorithm to find the optimal badge design. The algorithm:

1. Creates a population of random badge designs
2. Evaluates each design using a fitness function
3. Selects the best designs for reproduction
4. Creates new designs through crossover and mutation
5. Repeats for a specified number of generations

The fitness function maximizes:
- Number of objects * Scaling factor
- Height difference
- Width difference
- Depth difference

## Sentiment Analysis

The improved sentiment analysis:

1. Analyzes the stock report for emotional content
2. Calculates Valence, Arousal, and Dominance scores
3. Identifies key emotional terms
4. Provides a one-word emotional summary
5. Analyzes financial sentiment (bullish/bearish)

## Examples

### Example 1: Tesla Badge

```bash
python improved_crazystockbadges.py --ticker TSLA --period 1y --output tesla_badge.scad
```

This will:
1. Fetch Tesla stock data for the past year
2. Generate a stock report
3. Analyze the sentiment of the report
4. Create a 3D badge based on the data
5. Save the badge as `tesla_badge.scad`

### Example 2: Apple Badge with Custom Parameters

```bash
python improved_3d_models.py --ticker AAPL --data-file ./stock_data --badge-type rectangular --feature-type bar_chart --output apple_badge.scad
```

This will create a rectangular badge with a bar chart feature based on Apple stock data.

## Contributing

Feel free to contribute to this project by:

1. Adding new badge types and features
2. Improving the genetic algorithm
3. Enhancing the sentiment analysis
4. Adding new visualization options
5. Improving the user interface

## License

This project is licensed under the same license as the original project.

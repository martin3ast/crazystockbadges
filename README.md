# Crazy Stock Badges

A tool for generating 3D printable badges based on stock market data.

## Setup and Requirements

### External Applications

- **OpenSCAD**: Required to view and modify the generated SCAD files
  - Download: [https://openscad.org/downloads.html](https://openscad.org/downloads.html)

- **Prusa Slicer**: Recommended for preparing 3D models for printing
  - Download: [https://www.prusa3d.com/prusaslicer/](https://www.prusa3d.com/prusaslicer/)

### Conda Environment Setup

The project uses a conda environment to manage dependencies. Set it up with:

```bash
# Create and activate the environment from environment.yml
conda env create -f environment.yml
conda activate crazystockbadges
```

### API Key Configuration

The application uses a personal OpenRouter API for generating stock reports, which will expire in 3 months.

```python
# In marketdata.py
DEFAULT_API_KEY = 'your-api-key-here'
```

This can also be set with `OPENROUTER_API_KEY` environment variable.

## Running the Application

Basic interactive usage, the program will prompt for a stock ticker and ask if you want to see a market report.

```bash
python crazystockbadges.py --log-level=WARN
```

### Command Line Options

```
usage: crazystockbadges.py [-h] [--ticker TICKER] [--period PERIOD] [--non-interactive] [--output OUTPUT]
                           [--skip-report] [--ga-generations GA_GENERATIONS]
                           [--log-level {DEBUG,INFO,WARN,ERROR}] [--visualise-ga]

Crazy Stock Badge Generator - Create 3D printable badges from stock market data

options:
  -h, --help            show this help message and exit
  --ticker TICKER       Stock ticker symbol (e.g., TSLA, AAPL)
  --period PERIOD       Time period for stock data (default: 1y)
  --non-interactive     Run in non-interactive mode
  --output OUTPUT       Output file name for the SCAD file (default: disc.scad)
  --skip-report         Skip generating and displaying the stock report
  --ga-generations GA_GENERATIONS
                        Number of generations for the genetic algorithm (default: 10)
  --log-level {DEBUG,INFO,WARN,ERROR}
                        Set logging level (default: INFO)
  --visualise-ga        Visualise genetic algorithm results
```

## Directory Structure

```
.
├── badge_factory.py            # Badge creation factory
├── badge_factory_refactored.py # Refactored badge factory
├── complexity_analyser.py      # Analyzes model complexity
├── crazystockbadges.py         # Main application
├── environment.yml             # Conda environment definition
├── marketdata.py               # Stock market data handling
├── sentiment_analyser.py       # Sentiment analysis for reports
├── cache/                      # Cached data
├── docs/                       # Documentation
├── examples/                   # Example outputs
├── plots/                      # Generated plots
├── scad_models/                # Generated SCAD models
└── stl_models/                 # Generated STL models
```

## Contact

Martin East (mbe5)  
Email: mbe5@kent.ac.uk

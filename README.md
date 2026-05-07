# Crazy Stock Badges

A tool for generating 3D printable badges based on stock market data.

It uses a Genetic Algorithm to find the most crazy (complex) design out of a set of primitive building blocks. 

Each one is unique!

## Setup and Requirements

### External Applications

- **OpenSCAD**: Required to view and modify the generated SCAD files
  - Download: [https://openscad.org/downloads.html](https://openscad.org/downloads.html)

- **Prusa Slicer**: Recommended for preparing 3D models for printing
  - Download: [https://www.prusa3d.com/prusaslicer/](https://www.prusa3d.com/prusaslicer/)

### Python Environment Setup

The project uses [uv](https://docs.astral.sh/uv/) to manage dependencies (see `pyproject.toml`). To set up:

```bash
uv sync
```

To run any script, prefix it with `uv run`, e.g. `uv run python crazystockbadges.py`.

### API Key Configuration

The application uses an OpenRouter API key for generating stock reports.

1. Copy `.env.example` to `.env`.
2. Set `OPENROUTER_API_KEY=<your-key>` in `.env`.

The key is loaded via `python-dotenv`; do not hard-code it in source files.

## Running the Application

Basic interactive usage, the program will prompt for a stock ticker and ask if you want to see a market report.

```bash
python crazystockbadges.py 
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
                        Set logging level (default: WARN)
  --visualise-ga        Visualise genetic algorithm results
```

## Directory Structure

```
.
├── badge_factory.py            # Badge creation factory
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


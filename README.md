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

## Running Locally with Docker Compose

The fastest way to run the web app on your machine is via Docker. The provided `docker-compose.yml` reuses the same `Dockerfile` that `deploy.sh` ships to Cloud Run, so a local run mirrors production behaviour.

**Prerequisites:**

- [Docker](https://docs.docker.com/get-docker/) (Engine 20.10+ with the Compose plugin, or Docker Desktop)
- An OpenRouter API key (see [API Key Configuration](#api-key-configuration) above)

**Steps:**

1. Copy the example env file and add your API key:
   ```bash
   cp .env.example .env
   # then edit .env and set OPENROUTER_API_KEY=<your-key>
   ```

2. Start the app. Pick one of the two profiles:
   ```bash
   # Prod-parity: identical image to what deploy.sh ships. Artifacts persist in named volumes.
   docker compose --profile prod up --build

   # Development: source tree is bind-mounted into the container, FLASK_DEBUG=True hot-reloads
   # changes to .py/templates/static without rebuilding.
   docker compose --profile dev up --build
   ```

3. Open the app at [http://localhost:5000](http://localhost:5000).

4. Stop the stack with `Ctrl+C`, then tear it down:
   ```bash
   docker compose down
   ```

**Where outputs go:**

- `prod` profile: cached data, SCAD files, STL files, and the SQLite DB live in Docker-managed named volumes (`cache`, `scad_models`, `stl_models`, `data`). They survive `docker compose down` and are wiped with `docker compose down -v`.
- `dev` profile: the same directories are bind-mounted from the repo root, so generated artifacts land directly in your working tree.

## Directory Structure

```
.
├── badge_factory.py            # Badge creation factory
├── complexity_analyser.py      # Analyzes model complexity
├── crazystockbadges.py         # Main application
├── marketdata.py               # Stock market data handling
├── sentiment_analyser.py       # Sentiment analysis for reports
├── cache/                      # Cached data
├── docs/                       # Documentation
├── examples/                   # Example outputs
├── plots/                      # Generated plots
├── scad_models/                # Generated SCAD models
└── stl_models/                 # Generated STL models
```


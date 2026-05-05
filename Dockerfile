FROM python:3.12-slim

# Install OpenSCAD and clean up apt cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends openscad xvfb && \
    rm -rf /var/lib/apt/lists/*

# OpenSCAD needs a virtual framebuffer in headless environments
ENV DISPLAY=:99

WORKDIR /app

# Install Python dependencies with uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Download NLTK data
RUN uv run python -c "import nltk; nltk.download('punkt_tab', quiet=True); nltk.download('stopwords', quiet=True)"

# Copy application code
COPY . .

# Create writable directories
RUN mkdir -p cache scad_models stl_models data

EXPOSE 5000

# Start Xvfb and then the app
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 &>/dev/null & uv run python app.py"]

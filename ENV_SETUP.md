# Environment Configuration Setup

This application now supports environment variables through `.env` files for secure configuration management.

## Quick Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file with your actual values:**
   ```bash
   nano .env
   ```

3. **Set your OpenRouter API key:**
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
   ```

## Environment Variables

### Required
- `OPENROUTER_API_KEY` - Your OpenRouter API key for AI report generation

### Optional (with defaults)
- `OPENROUTER_API_URL` - API endpoint (default: https://openrouter.ai/api/v1/chat/completions)
- `OPENSCAD_PATH` - Path to OpenSCAD executable (default: openscad)
- `FLASK_HOST` - Flask server host (default: 0.0.0.0)
- `FLASK_PORT` - Flask server port (default: 5000)
- `FLASK_DEBUG` - Enable debug mode (default: True)
- `CACHE_DIR` - Cache directory path (default: ./cache)
- `DEFAULT_TICKER` - Default stock ticker (default: AAPL)
- `DEFAULT_PERIOD` - Default time period (default: 1y)
- `DEFAULT_GA_GENERATIONS` - Default GA generations (default: 10)
- `LOG_LEVEL` - Logging level (default: INFO)

## Getting an OpenRouter API Key

1. Visit https://openrouter.ai/
2. Sign up for an account
3. Navigate to the API section
4. Generate a new API key
5. Copy the key to your `.env` file

## OpenSCAD Configuration

For 3D model visualization, you need OpenSCAD installed:

### macOS Installation:
1. Download OpenSCAD from https://openscad.org/downloads.html
2. Install the application to `/Applications/`
3. The default path should work: `/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD`

### Linux Installation:
```bash
sudo apt-get install openscad  # Ubuntu/Debian
# or
sudo yum install openscad      # CentOS/RHEL
```
Set `OPENSCAD_PATH=openscad` in your .env file

### Windows Installation:
1. Download and install OpenSCAD
2. Set `OPENSCAD_PATH=C:\Program Files\OpenSCAD\openscad.exe` in your .env file

### Custom Installation:
If OpenSCAD is installed in a different location, update the `OPENSCAD_PATH` variable in your `.env` file.

## Security Notes

- The `.env` file is already in `.gitignore` and won't be committed
- Never share your API keys publicly
- Use different API keys for development and production
- The `.env.example` file shows the structure but contains no real credentials

## Running the Application

Once your `.env` file is configured:

```bash
python app.py
```

The application will automatically load your environment variables and use them for configuration.
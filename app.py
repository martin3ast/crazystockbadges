#!/usr/bin/env python3
"""
Flask Web Application for Crazy Stock Badges
Provides a web interface for generating 3D printable badges from stock market data.
"""

import os
import json
import logging
import secrets
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import threading
import time
from datetime import datetime
import marketdata as md
from sentiment_analyser import StockReportAnalyzer
from ga_engine import BadgeGAEngine
from pathlib import Path
from dotenv import load_dotenv
from database import DatabaseManager

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000').split(',')
CORS(app, origins=allowed_origins)

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger(__name__)

# Initialize database
db = DatabaseManager()

# Store active generation instances (in-memory for performance)
# Session data is persisted in SQLite, but WebBadgeGenerator instances are kept here
active_generators = {}

class WebBadgeGenerator:
    """Web interface for badge generation with progress tracking"""
    
    def __init__(self, session_id, ticker, period=None, ga_generations=None):
        # Use environment variables for defaults
        period = period or os.getenv('DEFAULT_PERIOD', '1y')
        ga_generations = ga_generations or int(os.getenv('DEFAULT_GA_GENERATIONS', '10'))
        self.session_id = session_id
        self.ticker = ticker
        self.period = period
        self.ga_generations = ga_generations
        self.mdm = None
        self.best_badge = None
        self.best_fitness = float('-inf')
        self.ga_instance = None
        
    def generate_badge_async(self):
        """Generate badge asynchronously with progress updates"""
        try:
            # Update session status in database
            db.update_session(self.session_id, status="fetching_data", progress=10)
            
            self.mdm = md.MarketDataManager(ticker=self.ticker, period=self.period)
            self.mdm.fetch_stock_data(use_cache=True)
            self.mdm.perform_technical_analysis()
            
            db.update_session(self.session_id, status="generating_report", progress=20)
            
            # Generate session-specific report file
            cache_dir = os.getenv('CACHE_DIR', '/tmp/cache' if os.getenv('VERCEL') else './cache')
            session_report_file = f"{cache_dir}/{self.session_id}_stock_report"
            self.mdm.generate_report(output_file=session_report_file)
            
            # Analyze sentiment with session-specific files
            if os.path.exists(session_report_file):
                report_analyzer = StockReportAnalyzer()
                analysis = report_analyzer.analyze_report(report_path=session_report_file)
                session_sentiment_file = f"{cache_dir}/{self.session_id}_sentiment_analysis.json"
                report_analyzer.save_analysis(analysis, session_sentiment_file)
                
                # Store analysis in database
                db.set_session_data(self.session_id, 'sentiment_analysis', analysis)
            
            db.update_session(self.session_id, status="running_genetic_algorithm", progress=30)
            
            # Run genetic algorithm
            self._run_genetic_algorithm()
            
            db.update_session(self.session_id, status="completed", progress=100)
            
            # Store final stats in database before completing
            if self.mdm:
                try:
                    final_stats = self.mdm.get_summary_stats()
                    db.set_session_data(self.session_id, 'market_stats', final_stats)
                    logger.info("Stored market stats in database")
                except Exception as e:
                    logger.warning(f"Failed to store market stats: {e}")
            
        except Exception as e:
            logger.error(f"Error in badge generation for session {self.session_id}: {e}")
            db.update_session(self.session_id, status="error", error_message=str(e))
        finally:
            # Remove from active generators when done
            if self.session_id in active_generators:
                del active_generators[self.session_id]
            
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

@app.route('/')
def landing():
    """Landing page"""
    return render_template('landing.html')

@app.route('/generate')
def index():
    """Main badge generation page"""
    return render_template('index.html')

@app.route('/api/validate-ticker', methods=['POST'])
def validate_ticker():
    """Validate stock ticker symbol"""
    data = request.json
    ticker = data.get('ticker', '').strip().upper()
    
    if not ticker:
        return jsonify({'valid': False, 'error': 'Ticker is required'}), 400
    
    # Use the marketdata validation function
    validation_result = md.MarketDataManager.validate_ticker(ticker)
    
    return jsonify(validation_result)

@app.route('/api/generate', methods=['POST'])
def generate_badge():
    """Start badge generation"""
    data = request.json
    ticker = data.get('ticker', 'AAPL').upper()
    period = data.get('period', '1y')
    generations = data.get('generations', 10)

    # Validate generations to prevent DoS
    try:
        generations = int(generations)
    except (TypeError, ValueError):
        return jsonify({'error': 'Generations must be a number'}), 400
    if generations < 1 or generations > 100:
        return jsonify({'error': 'Generations must be between 1 and 100'}), 400

    # Validate period against allowed values
    allowed_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
    if period not in allowed_periods:
        return jsonify({'error': f'Period must be one of: {", ".join(allowed_periods)}'}), 400
    
    # Get client info for rate limiting
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # Validate ticker before starting generation
    validation_result = md.MarketDataManager.validate_ticker(ticker)
    if not validation_result['valid']:
        return jsonify({'error': validation_result['error']}), 400
    
    # Check if user has too many active sessions (rate limiting)
    user_sessions = db.get_user_active_sessions(client_ip, limit_hours=1)
    if len(user_sessions) >= 3:  # Limit to 3 sessions per hour per IP
        return jsonify({'error': 'Too many active sessions. Please wait before starting a new generation.'}), 429
    
    # Check system load
    active_count = db.get_active_generation_count()
    if active_count >= 10:  # System-wide limit
        return jsonify({'error': 'System is at capacity. Please try again in a few minutes.'}), 503
    
    # Create session in database
    session_id = db.create_session(ticker, period, generations, client_ip, user_agent)
    
    # Create generator
    generator = WebBadgeGenerator(session_id, ticker, period, generations)
    active_generators[session_id] = generator
    
    # Start generation in background thread
    thread = threading.Thread(target=generator.generate_badge_async)
    thread.daemon = True
    thread.start()
    
    return jsonify({'session_id': session_id})

@app.route('/api/progress/<session_id>')
def get_progress(session_id):
    """Get generation progress"""
    # Get session from database
    session = db.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found or expired'}), 404
    
    # Get fitness stats from database
    fitness_stats = db.get_fitness_stats(session_id)
    
    response = {
        'progress': session['progress'],
        'status': session['status'],
        'current_generation': session['current_generation'],
        'total_generations': session['generations'],
        'fitness_stats': fitness_stats
    }
    
    if session['error_message']:
        response['error'] = session['error_message']
        
    return jsonify(response)

@app.route('/api/report/<session_id>')
def get_report(session_id):
    """Get stock report and sentiment analysis"""
    # Get session from database
    session = db.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found or expired'}), 404
    
    # Get stock report from session-specific file
    report_text = ""
    cache_dir = os.getenv('CACHE_DIR', '/tmp/cache' if os.getenv('VERCEL') else './cache')
    session_report_file = f"{cache_dir}/{session_id}_stock_report"
    if os.path.exists(session_report_file):
        with open(session_report_file, "r") as f:
            report_text = f.read()
    
    # Get sentiment analysis from database
    sentiment_data = db.get_session_data(session_id, 'sentiment_analysis', {})
    
    # Get summary stats from database or active generator
    stats = db.get_session_data(session_id, 'market_stats', {})
    
    # If not in database, try to get from active generator
    if not stats and session_id in active_generators and active_generators[session_id].mdm:
        try:
            stats = active_generators[session_id].mdm.get_summary_stats()
        except Exception as e:
            logger.warning(f"Failed to get stats from active generator: {e}")
            stats = {}
    
    return jsonify({
        'report': report_text,
        'sentiment': sentiment_data,
        'stats': stats
    })

@app.route('/api/download/<session_id>/<file_type>')
def download_file(session_id, file_type):
    """Download generated files"""
    # Get session from database
    session = db.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found or expired'}), 404

    # Validate file_type
    if file_type not in ('scad', 'stl', 'report'):
        return jsonify({'error': 'Invalid file type'}), 400

    ticker = session['ticker']

    if file_type == 'scad':
        base_dir = Path('/tmp/scad_models' if os.getenv('VERCEL') else './scad_models').resolve()
        filename = f"{session_id}_{ticker}_badge.scad"
        download_name = f"{ticker}_badge.scad"
    elif file_type == 'stl':
        base_dir = Path('/tmp/stl_models' if os.getenv('VERCEL') else './stl_models').resolve()
        filename = f"{session_id}_{ticker}_badge.stl"
        download_name = f"{ticker}_badge.stl"
    else:  # report
        base_dir = Path(os.getenv('CACHE_DIR', '/tmp/cache' if os.getenv('VERCEL') else './cache')).resolve()
        filename = f"{session_id}_stock_report"
        download_name = f"{ticker}_report.txt"

    # Resolve path and verify it stays within the base directory
    file_path = (base_dir / Path(filename).name).resolve()
    if not str(file_path).startswith(str(base_dir)):
        return jsonify({'error': 'Invalid file path'}), 403

    if file_path.exists():
        return send_file(file_path, as_attachment=True, download_name=download_name)

    return jsonify({'error': 'File not found'}), 404

@app.route('/api/stl-status/<session_id>')
def get_stl_status(session_id):
    """Check if STL file is ready for viewing"""
    # Get session from database
    session = db.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found or expired'}), 404
    
    ticker = session['ticker']
    session_filename = f"{session_id}_{ticker}_badge.stl"
    stl_dir = '/tmp/stl_models' if os.getenv('VERCEL') else './stl_models'
    stl_path = f"{stl_dir}/{session_filename}"
    
    logger.info(f"Checking STL file: {stl_path}")
    logger.info(f"File exists: {os.path.exists(stl_path)}")
    
    if os.path.exists(stl_path):
        file_size = os.path.getsize(stl_path)
        logger.info(f"STL file size: {file_size} bytes")
        return jsonify({'ready': True, 'size': file_size})
    else:
        # List files in stl_models directory for debugging
        try:
            files = os.listdir(stl_dir)
            matching_files = [f for f in files if session_id in f]
            logger.info(f"Files in stl_models: {files[:10]}...")  # Show first 10 files
            logger.info(f"Files matching session_id {session_id}: {matching_files}")
        except Exception as e:
            logger.error(f"Error listing stl_models directory: {e}")
        
        return jsonify({'ready': False, 'expected_file': session_filename})

@app.route('/api/model/<session_id>')
def get_model(session_id):
    """Get 3D model for visualization"""
    # Get session from database
    session = db.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found or expired'}), 404
    
    ticker = session['ticker']
    session_filename = f"{session_id}_{ticker}_badge.stl"
    stl_dir = '/tmp/stl_models' if os.getenv('VERCEL') else './stl_models'
    stl_path = f"{stl_dir}/{session_filename}"
    
    logger.info(f"Serving STL model: {stl_path}")
    
    if os.path.exists(stl_path):
        file_size = os.path.getsize(stl_path)
        logger.info(f"Serving STL file, size: {file_size} bytes")
        return send_file(stl_path, mimetype='application/octet-stream')
    else:
        logger.error(f"STL file not found: {stl_path}")
        return jsonify({'error': 'STL file not found'}), 404

@app.route('/api/admin/cleanup', methods=['POST'])
def cleanup_expired():
    """Manual cleanup of expired sessions (admin only)"""
    admin_token = os.getenv('ADMIN_TOKEN')
    if not admin_token:
        return jsonify({'error': 'Admin access not configured'}), 503

    auth_token = request.headers.get('Authorization', '')
    if not secrets.compare_digest(auth_token, f"Bearer {admin_token}"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        expired_sessions = db.cleanup_expired_sessions()
        
        # Clean up associated files
        files_deleted = 0
        for session_id in expired_sessions:
            # Clean up session files
            for pattern in ['scad_models', 'stl_models', 'cache']:
                for file_path in Path(f'./{pattern}').glob(f'{session_id}_*'):
                    try:
                        file_path.unlink()
                        files_deleted += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")
        
        return jsonify({
            'sessions_deleted': len(expired_sessions),
            'files_deleted': files_deleted
        })
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/stats')
def get_stats():
    """Get system statistics"""
    try:
        active_sessions = db.get_active_sessions()
        active_count = db.get_active_generation_count()
        
        stats = {
            'active_sessions': len(active_sessions),
            'active_generations': active_count,
            'recent_sessions': active_sessions[:10]  # Last 10 sessions
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

def cleanup_task():
    """Background task to clean up expired sessions"""
    import schedule
    import time
    
    def cleanup():
        try:
            expired_sessions = db.cleanup_expired_sessions()
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                
                # Clean up associated files
                for session_id in expired_sessions:
                    for pattern in ['scad_models', 'stl_models', 'cache']:
                        for file_path in Path(f'./{pattern}').glob(f'{session_id}_*'):
                            try:
                                file_path.unlink()
                            except Exception as e:
                                logger.warning(f"Failed to delete {file_path}: {e}")
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
    
    # Schedule cleanup every hour
    schedule.every().hour.do(cleanup)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# Initialize directories for Vercel deployment
def init_directories():
    """Initialize required directories for the application"""
    cache_dir = os.getenv('CACHE_DIR', '/tmp/cache')
    os.makedirs('/tmp/scad_models', exist_ok=True)
    os.makedirs('/tmp/stl_models', exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs('./static', exist_ok=True)
    os.makedirs('./templates', exist_ok=True)
    # Use in-memory or external database for Vercel
    if not os.getenv('VERCEL'):
        os.makedirs('./data', exist_ok=True)

# Initialize on module load for serverless
init_directories()

if __name__ == '__main__':
    # Start cleanup task in background thread (only for local development)
    if not os.getenv('VERCEL'):
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        logger.info("Started background cleanup task")
    
    # Get Flask configuration from environment variables
    flask_host = os.getenv('FLASK_HOST', '0.0.0.0')
    flask_port = int(os.getenv('PORT', os.getenv('FLASK_PORT', '5000')))
    flask_debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(debug=flask_debug, host=flask_host, port=flask_port)
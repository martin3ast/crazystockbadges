#!/usr/bin/env python3
"""
Flask Web Application for Crazy Stock Badges
Provides a web interface for generating 3D printable badges from stock market data.
"""

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import threading
import time
from datetime import datetime
import marketdata as md
from badge_factory import BadgeFactory
from complexity_analyser import ComplexityAnalyzer
from sentiment_analyser import StockReportAnalyzer
import pygad
import warnings
from pathlib import Path
from dotenv import load_dotenv
from database import DatabaseManager

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

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
            session_report_file = f"./cache/{self.session_id}_stock_report"
            self.mdm.generate_report(output_file=session_report_file)
            
            # Analyze sentiment with session-specific files
            if os.path.exists(session_report_file):
                report_analyzer = StockReportAnalyzer()
                analysis = report_analyzer.analyze_report(report_path=session_report_file)
                session_sentiment_file = f"./cache/{self.session_id}_sentiment_analysis.json"
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
        """Run the genetic algorithm with progress tracking"""
        gene_space = self._create_gene_space()
        
        warnings.filterwarnings("ignore", message="Use the 'save_solutions' parameter with caution")
        
        self.ga_instance = pygad.GA(
            num_generations=self.ga_generations,
            num_parents_mating=2,
            fitness_func=self._fitness_function,
            sol_per_pop=20,
            num_genes=len(gene_space),
            gene_space=gene_space,
            parent_selection_type="tournament",
            K_tournament=2,
            crossover_type="two_points",
            crossover_probability=0.8,
            mutation_type="adaptive",
            mutation_num_genes=[3,1],
            keep_elitism=1,
            mutation_probability=[0.3,0.1],
            on_generation=self._on_generation,
            allow_duplicate_genes=True,
            save_solutions=True
        )
        
        self.ga_instance.run()
        
        # Save the best badge
        if self.best_badge:
            # Use session-specific filename to avoid conflicts
            session_filename = f"{self.session_id}_{self.ticker}_badge"
            output_file = f"./scad_models/{session_filename}.scad"
            os.makedirs("./scad_models", exist_ok=True)
            os.makedirs("./stl_models", exist_ok=True)
            
            # Save SCAD file
            self.best_badge.save_to_file(output_file)
            
            # Save STL file for 3D visualization (async to avoid blocking)
            try:
                logger.info(f"Starting STL generation for session {self.session_id}, filename: {session_filename}")
                self.best_badge.save_to_stl_async(session_filename)
                logger.info("STL generation started in background")
            except Exception as e:
                logger.warning(f"STL generation failed to start: {e} - 3D preview may not be available")
            
    def _fitness_function(self, ga_instance, solution, solution_idx):
        """Fitness function for genetic algorithm"""
        params = self._genes_to_badge_params(solution)
        
        badge = BadgeFactory.create_badge(params['badge_type'], self.mdm.data, self.ticker, params)
        badge.generate_base()
        badge.generate_terrain()
        badge.generate_text()
        badge.combine_models()
        
        analyzer = ComplexityAnalyzer(badge.final_model)
        report = analyzer.get_complexity_report()
        
        if not hasattr(ga_instance, 'badges'):
            ga_instance.badges = {}
        
        fitness = report['total_nodes'] + report['complexity_score']
        ga_instance.badges[solution_idx] = (badge, report, fitness)
        
        if fitness > self.best_fitness:
            self.best_fitness = fitness
            self.best_badge = badge
            
        return fitness
        
    def _on_generation(self, ga_instance):
        """Callback for generation completion"""
        current_generation = ga_instance.generations_completed
        progress_pct = 30 + (current_generation / self.ga_generations) * 70
        progress = min(99, int(progress_pct))
        
        # Update session progress in database
        db.update_session(self.session_id, 
                         current_generation=current_generation, 
                         progress=progress,
                         best_fitness=self.best_fitness)
        
        # Calculate and store fitness statistics
        if hasattr(ga_instance, 'badges'):
            fitness_values = [ga_instance.badges[i][2] for i in range(len(ga_instance.population)) if i in ga_instance.badges]
            if fitness_values:
                min_fitness = min(fitness_values)
                mean_fitness = sum(fitness_values) / len(fitness_values)
                max_fitness = max(fitness_values)
                
                # Store fitness stats in database
                db.add_fitness_stat(self.session_id, current_generation, 
                                  min_fitness, mean_fitness, max_fitness, self.best_fitness)
        
    def _genes_to_badge_params(self, genes):
        """Convert genes to badge parameters"""
        badge_types = ['disc', 'rectangular', 'triangular']
        all_terrain_types = ['spiral_chart', 'bar_chart', 'pyramid', 'surface_plot']
        text_content_types = ['one_word_analysis', 'buy_sell_hold', 'latest_macd', 'high', 'low', 'market_outlook']
        
        badge_type_idx = int(genes[0])
        badge_type = badge_types[badge_type_idx]
        
        num_terrain_types = int(genes[1])
        terrain_types = []
        for i in range(num_terrain_types):
            terrain_idx = int(genes[2 + i])
            terrain_types.append(all_terrain_types[terrain_idx])
        
        text_position = genes[6]
        text_type_idx = int(genes[7])
        text_type = text_content_types[text_type_idx]
        
        sentiment = self.mdm.get_sentiment()
        text_content = self.ticker + " " + self._get_text_content(text_type, sentiment)
        
        base_height = int(genes[8])
        size_idx = int(genes[9])
        spiral_turns = int(genes[10])
        
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
            'terrain_types': terrain_types
        }
        
        if badge_type == 'disc':
            base_radius_map = [30, 50, 70]
            params['base_radius'] = base_radius_map[size_idx]
        elif badge_type == 'rectangular':
            base_width_map = [60, 90, 120]
            base_depth_map = [40, 60, 80]
            params['base_width'] = base_width_map[size_idx]
            params['base_depth'] = base_depth_map[size_idx]
        elif badge_type == 'triangular':
            side_length_map = [60, 80, 100]
            params['side_length'] = side_length_map[size_idx]
            
        return params
        
    def _get_text_content(self, text_type, sentiment):
        """Get text content based on type and sentiment"""
        if text_type == 'one_word_analysis':
            return self.mdm.get_one_word_analysis(sentiment)
        elif text_type == 'buy_sell_hold':
            return self.mdm.get_buy_sell_hold(sentiment)
        elif text_type == 'latest_macd':
            return self.mdm.get_latest_macd()
        elif text_type == 'high':
            return self.mdm.get_high()
        elif text_type == 'low':
            return self.mdm.get_low()
        elif text_type == 'market_outlook':
            return self.mdm.get_market_outlook(sentiment)
        else:
            return "Unknown"
            
    def _create_gene_space(self):
        """Create gene space for genetic algorithm"""
        return [
            [0, 1, 2],  # Badge type
            [1, 2, 3, 4],  # Number of terrain types
            [0, 1, 2, 3],  # Terrain type 1
            [0, 1, 2, 3],  # Terrain type 2
            [0, 1, 2, 3],  # Terrain type 3
            [0, 1, 2, 3],  # Terrain type 4
            {'low': 0, 'high': 360},  # Text position
            [0, 1, 2, 3, 4, 5],  # Text type
            [1, 2, 3],  # Base height
            [0, 1, 2],  # Size
            {'low': 3, 'high': 10}  # Spiral turns
        ]

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
    session_report_file = f"./cache/{session_id}_stock_report"
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
    
    ticker = session['ticker']
    
    if file_type == 'scad':
        session_filename = f"{session_id}_{ticker}_badge.scad"
        file_path = f"./scad_models/{session_filename}"
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=f"{ticker}_badge.scad")
    elif file_type == 'stl':
        session_filename = f"{session_id}_{ticker}_badge.stl"
        file_path = f"./stl_models/{session_filename}"
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=f"{ticker}_badge.stl")
    elif file_type == 'report':
        session_report_file = f"./cache/{session_id}_stock_report"
        if os.path.exists(session_report_file):
            return send_file(session_report_file, as_attachment=True, download_name=f"{ticker}_report.txt")
    
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
    stl_path = f"./stl_models/{session_filename}"
    
    logger.info(f"Checking STL file: {stl_path}")
    logger.info(f"File exists: {os.path.exists(stl_path)}")
    
    if os.path.exists(stl_path):
        file_size = os.path.getsize(stl_path)
        logger.info(f"STL file size: {file_size} bytes")
        return jsonify({'ready': True, 'path': stl_path, 'size': file_size})
    else:
        # List files in stl_models directory for debugging
        try:
            files = os.listdir('./stl_models')
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
    stl_path = f"./stl_models/{session_filename}"
    
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
    # Basic auth check (in production, use proper authentication)
    auth_token = request.headers.get('Authorization')
    if auth_token != f"Bearer {os.getenv('ADMIN_TOKEN', 'admin123')}":
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

if __name__ == '__main__':
    # Ensure required directories exist
    cache_dir = os.getenv('CACHE_DIR', './cache')
    os.makedirs('./scad_models', exist_ok=True)
    os.makedirs('./stl_models', exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs('./static', exist_ok=True)
    os.makedirs('./templates', exist_ok=True)
    os.makedirs('./data', exist_ok=True)  # For SQLite database
    
    # Start cleanup task in background thread
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("Started background cleanup task")
    
    # Get Flask configuration from environment variables
    flask_host = os.getenv('FLASK_HOST', '0.0.0.0')
    flask_port = int(os.getenv('FLASK_PORT', '5000'))
    flask_debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(debug=flask_debug, host=flask_host, port=flask_port)
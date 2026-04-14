#!/usr/bin/env python3
"""
Database Module for Crazy Stock Badges
Handles SQLite operations for multi-user session management.
"""

import sqlite3
import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
import uuid

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database for session persistence and multi-user support"""
    
    def __init__(self, db_path='./data/sessions.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Thread-safe database connection context manager"""
        with self._lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                yield conn
            finally:
                conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    period TEXT NOT NULL,
                    generations INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'initializing',
                    progress INTEGER DEFAULT 0,
                    current_generation INTEGER DEFAULT 0,
                    error_message TEXT,
                    best_fitness REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    client_ip TEXT,
                    user_agent TEXT
                );
                
                CREATE TABLE IF NOT EXISTS fitness_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    min_fitness REAL,
                    mean_fitness REAL,
                    max_fitness REAL,
                    best_fitness REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS session_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    original_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS session_data (
                    session_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_id, key),
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
                CREATE INDEX IF NOT EXISTS idx_sessions_created ON sessions(created_at);
                CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
                CREATE INDEX IF NOT EXISTS idx_fitness_session ON fitness_stats(session_id, generation);
                CREATE INDEX IF NOT EXISTS idx_files_session ON session_files(session_id, file_type);
            ''')
            conn.commit()
            logger.info("Database initialized successfully")
    
    def create_session(self, ticker, period, generations, client_ip=None, user_agent=None):
        """Create a new generation session"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=24)  # 24 hour expiry
        
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO sessions (id, ticker, period, generations, expires_at, client_ip, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, ticker, period, generations, expires_at, client_ip, user_agent))
            conn.commit()
        
        logger.info(f"Created session {session_id} for {ticker}")
        return session_id
    
    def get_session(self, session_id):
        """Get session by ID"""
        with self.get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM sessions WHERE id = ? AND expires_at > CURRENT_TIMESTAMP
            ''', (session_id,)).fetchone()
            
            if row:
                return dict(row)
            return None
    
    # Columns that may be updated via update_session
    ALLOWED_UPDATE_FIELDS = {
        'status', 'progress', 'current_generation', 'error_message',
        'best_fitness', 'updated_at'
    }

    def update_session(self, session_id, **kwargs):
        """Update session fields"""
        if not kwargs:
            return

        # Always update the updated_at timestamp
        kwargs['updated_at'] = datetime.now()

        # Validate column names against whitelist
        invalid_keys = set(kwargs.keys()) - self.ALLOWED_UPDATE_FIELDS
        if invalid_keys:
            raise ValueError(f"Invalid update fields: {invalid_keys}")

        fields = ', '.join(f"{key} = ?" for key in kwargs.keys())
        values = list(kwargs.values()) + [session_id]

        with self.get_connection() as conn:
            conn.execute(f'''
                UPDATE sessions SET {fields} WHERE id = ?
            ''', values)
            conn.commit()
    
    def get_active_sessions(self):
        """Get all active (non-expired) sessions"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM sessions 
                WHERE expires_at > CURRENT_TIMESTAMP 
                ORDER BY created_at DESC
            ''').fetchall()
            
            return [dict(row) for row in rows]
    
    def get_sessions_by_status(self, status):
        """Get sessions by status"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM sessions 
                WHERE status = ? AND expires_at > CURRENT_TIMESTAMP
                ORDER BY created_at DESC
            ''', (status,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions and their associated data"""
        with self.get_connection() as conn:
            # Get expired session IDs for file cleanup
            expired_sessions = conn.execute('''
                SELECT id FROM sessions WHERE expires_at <= CURRENT_TIMESTAMP
            ''').fetchall()
            
            # Delete expired sessions (cascades to related tables)
            result = conn.execute('''
                DELETE FROM sessions WHERE expires_at <= CURRENT_TIMESTAMP
            ''')
            conn.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired sessions")
            
            return [row[0] for row in expired_sessions]
    
    def add_fitness_stat(self, session_id, generation, min_fitness, mean_fitness, max_fitness, best_fitness):
        """Add fitness statistics for a generation"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO fitness_stats 
                (session_id, generation, min_fitness, mean_fitness, max_fitness, best_fitness)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, generation, min_fitness, mean_fitness, max_fitness, best_fitness))
            conn.commit()
    
    def get_fitness_stats(self, session_id):
        """Get fitness statistics for a session"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT generation, min_fitness, mean_fitness, max_fitness, best_fitness
                FROM fitness_stats 
                WHERE session_id = ? 
                ORDER BY generation
            ''', (session_id,)).fetchall()
            
            if not rows:
                return {
                    'generation': [],
                    'min': [],
                    'mean': [],
                    'max': [],
                    'best': []
                }
            
            return {
                'generation': [row[0] for row in rows],
                'min': [row[1] for row in rows],
                'mean': [row[2] for row in rows],
                'max': [row[3] for row in rows],
                'best': [row[4] for row in rows]
            }
    
    def add_session_file(self, session_id, file_type, file_path, original_name=None):
        """Register a file associated with a session"""
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO session_files (session_id, file_type, file_path, original_name)
                VALUES (?, ?, ?, ?)
            ''', (session_id, file_type, file_path, original_name))
            conn.commit()
    
    def get_session_files(self, session_id, file_type=None):
        """Get files associated with a session"""
        with self.get_connection() as conn:
            if file_type:
                rows = conn.execute('''
                    SELECT * FROM session_files 
                    WHERE session_id = ? AND file_type = ?
                    ORDER BY created_at DESC
                ''', (session_id, file_type)).fetchall()
            else:
                rows = conn.execute('''
                    SELECT * FROM session_files 
                    WHERE session_id = ?
                    ORDER BY created_at DESC
                ''', (session_id,)).fetchall()
            
            return [dict(row) for row in rows]
    
    def set_session_data(self, session_id, key, value):
        """Set session-specific data (JSON serializable)"""
        json_value = json.dumps(value) if value is not None else None
        
        with self.get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO session_data (session_id, key, value)
                VALUES (?, ?, ?)
            ''', (session_id, key, json_value))
            conn.commit()
    
    def get_session_data(self, session_id, key, default=None):
        """Get session-specific data"""
        with self.get_connection() as conn:
            row = conn.execute('''
                SELECT value FROM session_data WHERE session_id = ? AND key = ?
            ''', (session_id, key)).fetchone()
            
            if row and row[0] is not None:
                return json.loads(row[0])
            return default
    
    def get_active_generation_count(self):
        """Get count of currently running generations"""
        with self.get_connection() as conn:
            result = conn.execute('''
                SELECT COUNT(*) FROM sessions 
                WHERE status IN ('running_genetic_algorithm', 'fetching_data', 'generating_report')
                AND expires_at > CURRENT_TIMESTAMP
            ''').fetchone()
            
            return result[0] if result else 0
    
    def get_user_active_sessions(self, client_ip, limit_hours=1):
        """Get active sessions for a user (by IP) in the last N hours"""
        since = datetime.now() - timedelta(hours=limit_hours)
        
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM sessions
                WHERE client_ip = ?
                AND created_at > ?
                AND expires_at > CURRENT_TIMESTAMP
                AND status NOT IN ('completed', 'error')
                ORDER BY created_at DESC
            ''', (client_ip, since)).fetchall()
            
            return [dict(row) for row in rows]

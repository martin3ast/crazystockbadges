#!/usr/bin/env python3
"""
Simple Flask server to test STL viewing
"""

import os
from flask import Flask, send_from_directory, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def test_viewer():
    """Serve the test viewer HTML"""
    return send_file('test_viewer.html')

@app.route('/stl_models/<filename>')
def serve_stl(filename):
    """Serve STL files"""
    return send_from_directory('stl_models', filename)

@app.route('/test-stl')
def test_stl_exists():
    """Check if AAPL_badge.stl exists"""
    stl_path = './stl_models/AAPL_badge.stl'
    exists = os.path.exists(stl_path)
    if exists:
        size = os.path.getsize(stl_path)
        return f"STL file exists: {stl_path} (size: {size} bytes)"
    else:
        return f"STL file not found: {stl_path}"

if __name__ == '__main__':
    print("Starting simple STL viewer server...")
    print("Visit http://localhost:5001 to test the 3D viewer")
    print("Visit http://localhost:5001/test-stl to check if STL file exists")
    app.run(debug=True, host='0.0.0.0', port=5001)
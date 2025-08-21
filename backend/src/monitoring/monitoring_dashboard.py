#!/usr/bin/env python3
"""
Web-based Monitoring Dashboard for UsenetSync
Provides real-time metrics and system health visualization
"""

import os
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

try:
    from flask import Flask, render_template, jsonify, request
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask flask-socketio")

class MonitoringDashboard:
    """Web dashboard for monitoring"""
    
    def __init__(self, monitoring_system, host: str = '127.0.0.1', port: int = 5000):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for the monitoring dashboard")
            
        self.monitoring = monitoring_system
        self.host = host
        self.port = port
        
        # Create Flask app
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / 'templates'),
                        static_folder=str(Path(__file__).parent / 'static'))
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Setup routes
        self._setup_routes()
        
        # Background thread for updates
        self._update_thread = None
        self._running = False
        
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('dashboard.html')
            
        @self.app.route('/api/dashboard')
        def dashboard_data():
            return jsonify(self.monitoring.get_dashboard_data())
            
        @self.app.route('/api/metrics/<metric_name>')
        def get_metric(metric_name):
            window_minutes = request.args.get('window', 60, type=int)
            aggregate = self.monitoring.metrics.get_aggregate(metric_name, window_minutes)
            return jsonify(aggregate)
            
        @self.app.route('/api/operations')
        def get_operations():
            limit = request.args.get('limit', 100, type=int)
            op_type = request.args.get('type')
            operations = self.monitoring.operations.get_operation_history(op_type, limit)
            return jsonify(operations)
            
        @self.app.route('/api/performance/history')
        def performance_history():
            history = []
            for snapshot in self.monitoring.performance.snapshots:
                history.append({
                    'timestamp': snapshot.timestamp.isoformat(),
                    'cpu': snapshot.cpu_percent,
                    'memory': snapshot.memory_mb,
                    'threads': snapshot.active_threads
                })
            return jsonify(history)
            
        @self.socketio.on('connect')
        def handle_connect():
            emit('connected', {'data': 'Connected to monitoring dashboard'})
            
    def start(self):
        """Start dashboard server"""
        self._running = True
        
        # Start update thread
        self._update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self._update_thread.start()
        
        # Run Flask app
        self.socketio.run(self.app, host=self.host, port=self.port, debug=False)
        
    def stop(self):
        """Stop dashboard server"""
        self._running = False
        self.socketio.stop()
        
    def _update_loop(self):
        """Send updates to connected clients"""
        while self._running:
            try:
                # Get current data
                data = self.monitoring.get_dashboard_data()
                
                # Emit to all connected clients
                self.socketio.emit('update', data)
                
            except Exception as e:
                print(f"Dashboard update error: {e}")
                
            # Update every 2 seconds
            self.socketio.sleep(2)
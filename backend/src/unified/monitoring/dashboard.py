#!/usr/bin/env python3
"""
Unified Dashboard - System dashboard data
"""

class UnifiedDashboard:
    """Dashboard data provider"""
    
    def __init__(self, metrics_collector=None):
        self.metrics = metrics_collector
    
    def get_dashboard_data(self):
        """Get dashboard data"""
        return {'widgets': []}
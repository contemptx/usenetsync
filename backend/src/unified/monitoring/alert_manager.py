#!/usr/bin/env python3
"""
Unified Alert Manager - Manage system alerts
"""

class UnifiedAlertManager:
    """Manage alerts"""
    
    def __init__(self):
        self.alerts = []
    
    def trigger_alert(self, alert_type, message):
        """Trigger an alert"""
        self.alerts.append({'type': alert_type, 'message': message})
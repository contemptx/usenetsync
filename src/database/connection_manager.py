#!/usr/bin/env python3
"""
Improved connection manager for PostgreSQL
"""

import logging
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from threading import Lock

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self, config):
        self.config = config
        self.pool = None
        self.lock = Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            host=self.config.get('host', 'localhost'),
            port=self.config.get('port', 5432),
            database=self.config.get('database', 'usenet'),
            user=self.config.get('user', 'usenet'),
            password=self.config.get('password', 'usenetsync')
        )
    
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            with self.lock:
                conn = self.pool.getconn()
            yield conn
        finally:
            if conn:
                with self.lock:
                    self.pool.putconn(conn)

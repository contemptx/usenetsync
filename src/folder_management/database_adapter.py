#!/usr/bin/env python3
"""
Database adapter to make FolderManager work with both PostgreSQL and SQLite
"""

import sqlite3
import uuid
import json
from contextlib import contextmanager
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class SQLiteToPostgreSQLAdapter:
    """Adapter to make SQLite work with PostgreSQL-style queries in FolderManager"""
    
    def __init__(self, sqlite_manager):
        self.sqlite_manager = sqlite_manager
        self.logger = logger
        
    @contextmanager
    def get_connection(self):
        """Get a connection that works like PostgreSQL connection"""
        conn = self.sqlite_manager.get_connection()
        
        # Wrap the connection to handle PostgreSQL-specific syntax
        wrapped_conn = SQLiteConnectionWrapper(conn)
        
        try:
            yield wrapped_conn
        finally:
            conn.close()
    
    def get_user_config(self, user_id: str = 'default'):
        """Get user configuration - returns a default config for SQLite"""
        # For SQLite, we return a simple default configuration
        return {
            'user_id': user_id,
            'username': 'default_user',
            'settings': {},
            'created_at': None
        }
    
    def __getattr__(self, name):
        """Forward any other method calls to the underlying SQLite manager"""
        return getattr(self.sqlite_manager, name)


class SQLiteConnectionWrapper:
    """Wrapper for SQLite connection to handle PostgreSQL syntax"""
    
    def __init__(self, sqlite_conn):
        self.conn = sqlite_conn
        self.conn.row_factory = sqlite3.Row
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Register custom functions
        self.conn.create_function("gen_random_uuid", 0, lambda: str(uuid.uuid4()))
        
    def cursor(self):
        """Get a cursor that handles PostgreSQL syntax"""
        return SQLiteCursorWrapper(self.conn.cursor())
    
    def commit(self):
        """Commit the transaction"""
        self.conn.commit()
    
    def rollback(self):
        """Rollback the transaction"""
        self.conn.rollback()
    
    def close(self):
        """Close the connection"""
        self.conn.close()


class SQLiteCursorWrapper:
    """Wrapper for SQLite cursor to handle PostgreSQL syntax"""
    
    def __init__(self, sqlite_cursor):
        self.cursor = sqlite_cursor
        
    def execute(self, query, params=None):
        """Execute a query, converting PostgreSQL syntax to SQLite"""
        # Convert PostgreSQL placeholders (%s) to SQLite (?)
        converted_query = self._convert_query(query)
        
        # Convert params tuple to list if needed
        if params:
            if isinstance(params, tuple):
                params = list(params)
        
        try:
            # Check if this is multiple statements
            if ';' in converted_query and converted_query.count(';') > 1:
                # Split and execute each statement separately
                statements = [s.strip() for s in converted_query.split(';') if s.strip()]
                for statement in statements:
                    if statement:
                        self.cursor.execute(statement)
                return self.cursor
            else:
                if params:
                    return self.cursor.execute(converted_query, params)
                else:
                    return self.cursor.execute(converted_query)
        except Exception as e:
            logger.error(f"Query failed: {converted_query}")
            logger.error(f"Params: {params}")
            raise
    
    def fetchone(self):
        """Fetch one row"""
        return self.cursor.fetchone()
    
    def fetchall(self):
        """Fetch all rows"""
        return self.cursor.fetchall()
    
    def fetchmany(self, size=None):
        """Fetch many rows"""
        if size:
            return self.cursor.fetchmany(size)
        return self.cursor.fetchmany()
    
    @property
    def lastrowid(self):
        """Get last row ID"""
        return self.cursor.lastrowid
    
    @property
    def rowcount(self):
        """Get row count"""
        return self.cursor.rowcount
    
    def _convert_query(self, query):
        """Convert PostgreSQL query syntax to SQLite"""
        # Remove or replace PostgreSQL-specific syntax
        
        # Replace %s with ?
        import re
        query = re.sub(r'%s', '?', query)
        
        # Replace SERIAL with INTEGER PRIMARY KEY AUTOINCREMENT
        query = re.sub(r'SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', query, flags=re.IGNORECASE)
        query = re.sub(r'SERIAL', 'INTEGER', query, flags=re.IGNORECASE)
        
        # Replace UUID type with TEXT
        query = re.sub(r'\bUUID\b', 'TEXT', query, flags=re.IGNORECASE)
        
        # Replace BIGINT with INTEGER
        query = re.sub(r'\bBIGINT\b', 'INTEGER', query, flags=re.IGNORECASE)
        
        # Replace BOOLEAN with INTEGER
        query = re.sub(r'\bBOOLEAN\b', 'INTEGER', query, flags=re.IGNORECASE)
        
        # Replace JSONB with TEXT
        query = re.sub(r'\bJSONB\b', 'TEXT', query, flags=re.IGNORECASE)
        
        # Replace TIMESTAMP with DATETIME
        query = re.sub(r'\bTIMESTAMP\b', 'DATETIME', query, flags=re.IGNORECASE)
        
        # Replace DEFAULT gen_random_uuid() with nothing (will generate in app)
        query = re.sub(r'DEFAULT gen_random_uuid\(\)', '', query, flags=re.IGNORECASE)
        
        # Replace gen_random_uuid() in other contexts
        query = re.sub(r'gen_random_uuid\(\)', "'" + str(uuid.uuid4()) + "'", query, flags=re.IGNORECASE)
        
        # Replace RETURNING * with nothing (SQLite doesn't support it)
        query = re.sub(r'\s+RETURNING\s+\*', '', query, flags=re.IGNORECASE)
        
        # Replace '{}'::jsonb with '{}'
        query = re.sub(r"'(\{\})'::jsonb", r"'\1'", query)
        
        # Replace '{}'::TEXT with '{}'
        query = re.sub(r"'(\{\})'::TEXT", r"'\1'", query, flags=re.IGNORECASE)
        
        # Remove any remaining :: casts
        query = re.sub(r"::[A-Za-z]+", "", query)
        
        # Handle ON DELETE CASCADE (SQLite needs it in table creation, not ALTER)
        # This is a simplified approach - proper handling would need more context
        
        # Replace NOW() with CURRENT_TIMESTAMP
        query = re.sub(r'\bNOW\(\)', 'CURRENT_TIMESTAMP', query, flags=re.IGNORECASE)
        
        # Replace DECIMAL type with REAL
        query = re.sub(r'\bDECIMAL\([^)]+\)', 'REAL', query, flags=re.IGNORECASE)
        
        # Replace VARCHAR with TEXT
        query = re.sub(r'\bVARCHAR\([^)]+\)', 'TEXT', query, flags=re.IGNORECASE)
        
        return query
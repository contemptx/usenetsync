/**
 * Backend API integration for unified backend endpoints
 * Provides direct HTTP API access to the Python backend
 */

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

/**
 * Fetch logs from the backend
 */
export async function fetchLogs(limit = 100, level?: string) {
  try {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (level && level !== 'all') params.append('level', level);
    
    const response = await fetch(`${BACKEND_URL}/api/v1/logs?${params}`);
    if (response.ok) {
      const data = await response.json();
      // Transform backend logs to frontend format
      return (data.logs || []).map((log: any) => ({
        id: log.id || `${Date.now()}-${Math.random()}`,
        timestamp: new Date(log.timestamp || Date.now()),
        level: log.level || 'info',
        category: log.category || 'system',
        message: log.message || '',
        details: log.details,
        source: log.source || 'backend'
      }));
    }
  } catch (error) {
    console.error('Failed to fetch logs from backend:', error);
  }
  return [];
}

/**
 * Search files and folders
 */
export async function searchContent(query: string, type?: string) {
  try {
    const params = new URLSearchParams();
    params.append('query', query);
    if (type) params.append('type', type);
    params.append('limit', '50');
    
    const response = await fetch(`${BACKEND_URL}/api/v1/search?${params}`);
    if (response.ok) {
      const data = await response.json();
      return data.results || { files: [], folders: [] };
    }
  } catch (error) {
    console.error('Failed to search:', error);
  }
  return { files: [], folders: [] };
}

/**
 * Get connection pool statistics
 */
export async function getConnectionPoolStats() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/network/connection_pool`);
    if (response.ok) {
      const data = await response.json();
      return data.pool || { 
        active: 0, 
        idle: 0, 
        total: 0, 
        max: 10,
        connections: []
      };
    }
  } catch (error) {
    console.error('Failed to fetch connection pool stats:', error);
  }
  return { 
    active: 0, 
    idle: 0, 
    total: 0, 
    max: 10,
    connections: [] 
  };
}

/**
 * Get system statistics
 */
export async function getSystemStats() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/stats`);
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error('Failed to fetch system stats:', error);
  }
  return {
    total_files: 0,
    total_size: 0,
    total_shares: 0,
    total_users: 0,
    database_size: 0
  };
}

/**
 * Create a new user
 */
export async function createUser(username: string, email: string) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email }),
    });
    
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error('Failed to create user:', error);
  }
  return null;
}

/**
 * Get share details
 */
export async function getShareDetails(shareId: string) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/shares/${shareId}`);
    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error('Failed to fetch share details:', error);
  }
  return null;
}

/**
 * Check backend health
 */
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/health`);
    if (response.ok) {
      const data = await response.json();
      return data.status === 'healthy';
    }
  } catch (error) {
    console.error('Backend health check failed:', error);
  }
  return false;
}

// Export all functions
export default {
  fetchLogs,
  searchContent,
  getConnectionPoolStats,
  getSystemStats,
  createUser,
  getShareDetails,
  checkBackendHealth
};

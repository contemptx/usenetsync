/**
 * Backend API integration for new endpoints
 */

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export async function fetchLogs(limit = 100, level?: string) {
  try {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (level) params.append('level', level);
    
    const response = await fetch(`${BACKEND_URL}/api/v1/logs?${params}`);
    if (response.ok) {
      const data = await response.json();
      return data.logs || [];
    }
  } catch (error) {
    console.error('Failed to fetch logs:', error);
  }
  return [];
}

export async function searchContent(query: string, type?: string) {
  try {
    const params = new URLSearchParams();
    params.append('query', query);
    if (type) params.append('type', type);
    
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

export async function getConnectionPoolStats() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/network/connection_pool`);
    if (response.ok) {
      const data = await response.json();
      return data.pool || { active: 0, idle: 0, total: 0, max: 10 };
    }
  } catch (error) {
    console.error('Failed to fetch connection pool stats:', error);
  }
  return { active: 0, idle: 0, total: 0, max: 10 };
}
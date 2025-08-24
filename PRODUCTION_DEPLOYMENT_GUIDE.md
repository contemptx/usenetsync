# 🚀 UsenetSync Production Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Security Configuration](#security-configuration)
5. [API Deployment](#api-deployment)
6. [Frontend Deployment](#frontend-deployment)
7. [Docker Deployment](#docker-deployment)
8. [Monitoring & Logging](#monitoring--logging)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / Debian 11+ / RHEL 8+
- **Python**: 3.10+
- **Node.js**: 18+
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 50GB+ for application and data
- **CPU**: 2+ cores

### Required Software
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3.10 python3-pip python3-venv -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis (for caching)
sudo apt install redis-server -y

# Install Nginx
sudo apt install nginx -y

# Install Supervisor (for process management)
sudo apt install supervisor -y
```

---

## Environment Setup

### 1. Create Application User
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash usenetsync
sudo usermod -aG sudo usenetsync

# Switch to application user
sudo su - usenetsync
```

### 2. Clone Repository
```bash
# Clone the repository
git clone https://github.com/yourusername/usenetsync.git
cd usenetsync
```

### 3. Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Environment Variables
Create `.env` file:
```bash
# Application Settings
APP_NAME=UsenetSync
APP_ENV=production
APP_DEBUG=false
APP_URL=https://your-domain.com

# Database
DATABASE_URL=postgresql://usenetsync:password@localhost/usenetsync
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Usenet Configuration
USENET_SERVER=news.newshosting.com
USENET_PORT=563
USENET_SSL=true
USENET_USERNAME=your_username
USENET_PASSWORD=your_password

# API Settings
API_RATE_LIMIT=100
API_RATE_LIMIT_PERIOD=60
CORS_ORIGINS=https://your-domain.com

# Monitoring
SENTRY_DSN=your_sentry_dsn
LOG_LEVEL=INFO

# File Storage
UPLOAD_PATH=/var/lib/usenetsync/uploads
TEMP_PATH=/var/lib/usenetsync/temp
MAX_FILE_SIZE=5368709120  # 5GB
```

---

## Database Configuration

### 1. PostgreSQL Setup
```sql
-- Create database and user
sudo -u postgres psql

CREATE USER usenetsync WITH PASSWORD 'secure_password';
CREATE DATABASE usenetsync OWNER usenetsync;
GRANT ALL PRIVILEGES ON DATABASE usenetsync TO usenetsync;

-- Enable extensions
\c usenetsync
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
\q
```

### 2. Run Migrations
```bash
# Activate virtual environment
source venv/bin/activate

# Run database migrations
python manage.py migrate

# Create initial admin user
python manage.py createsuperuser
```

### 3. Database Backup Script
Create `/usr/local/bin/backup-usenetsync.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/var/backups/usenetsync"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="usenetsync"

mkdir -p $BACKUP_DIR
pg_dump -U usenetsync -h localhost $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

Add to crontab:
```bash
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup-usenetsync.sh
```

---

## Security Configuration

### 1. SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Generate certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 2. Firewall Configuration
```bash
# Install UFW
sudo apt install ufw -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Security Headers (Nginx)
Add to `/etc/nginx/sites-available/usenetsync`:
```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self' https:; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
```

---

## API Deployment

### 1. Gunicorn Configuration
Create `/etc/supervisor/conf.d/usenetsync-api.conf`:
```ini
[program:usenetsync-api]
command=/home/usenetsync/usenetsync/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 run_backend:app
directory=/home/usenetsync/usenetsync
user=usenetsync
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/usenetsync/api.log
environment=PATH="/home/usenetsync/usenetsync/venv/bin",HOME="/home/usenetsync"
```

### 2. Nginx Configuration
Create `/etc/nginx/sites-available/usenetsync`:
```nginx
upstream usenetsync_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    client_max_body_size 5G;
    
    # API endpoints
    location /api {
        proxy_pass http://usenetsync_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for large uploads
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
    
    # Static files
    location /static {
        alias /home/usenetsync/usenetsync/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Frontend
    location / {
        root /home/usenetsync/usenetsync/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/usenetsync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Frontend Deployment

### 1. Build Frontend
```bash
cd frontend
npm install
npm run build
```

### 2. Environment Configuration
Create `frontend/.env.production`:
```env
VITE_API_URL=https://your-domain.com/api
VITE_APP_NAME=UsenetSync
VITE_ENABLE_ANALYTICS=true
```

### 3. Optimize Build
```json
// vite.config.js additions
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@headlessui/react', '@heroicons/react'],
        }
      }
    },
    chunkSizeWarningLimit: 1000,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
})
```

---

## Docker Deployment

### 1. Dockerfile for API
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "run_backend:app"]
```

### 2. Docker Compose
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: usenetsync
      POSTGRES_USER: usenetsync
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - usenetsync_network

  redis:
    image: redis:7-alpine
    networks:
      - usenetsync_network

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://usenetsync:${DB_PASSWORD}@postgres/usenetsync
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - usenetsync_network
    volumes:
      - ./uploads:/app/uploads
      - ./temp:/app/temp

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    networks:
      - usenetsync_network

volumes:
  postgres_data:

networks:
  usenetsync_network:
```

---

## Monitoring & Logging

### 1. Application Monitoring (Prometheus + Grafana)
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'usenetsync'
    static_configs:
      - targets: ['localhost:8000']
```

### 2. Log Aggregation (ELK Stack)
```python
# Add to logging configuration
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

### 3. Health Checks
```python
# Add health check endpoint
@app.get("/health")
async def health_check():
    checks = {
        "database": check_database(),
        "redis": check_redis(),
        "usenet": check_usenet_connection(),
        "storage": check_storage_space()
    }
    
    status = "healthy" if all(checks.values()) else "unhealthy"
    return {"status": status, "checks": checks}
```

---

## Performance Optimization

### 1. Database Optimization
```sql
-- Add indexes
CREATE INDEX idx_folders_user_id ON folders(user_id);
CREATE INDEX idx_files_folder_id ON files(folder_id);
CREATE INDEX idx_shares_owner_id ON shares(owner_id);
CREATE INDEX idx_segments_file_id ON segments(file_id);

-- Analyze tables
ANALYZE folders;
ANALYZE files;
ANALYZE shares;
ANALYZE segments;
```

### 2. Redis Caching
```python
from functools import lru_cache
import redis

redis_client = redis.from_url(os.getenv("REDIS_URL"))

def cache_result(expiry=3600):
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiry, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 3. CDN Configuration
```nginx
# CloudFlare or similar CDN
location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -U usenetsync -h localhost -d usenetsync

# Check logs
tail -f /var/log/postgresql/postgresql-*.log
```

#### 2. API Not Responding
```bash
# Check supervisor status
sudo supervisorctl status

# Restart API
sudo supervisorctl restart usenetsync-api

# Check logs
tail -f /var/log/usenetsync/api.log
```

#### 3. High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Restart services
sudo systemctl restart postgresql
sudo supervisorctl restart all
```

#### 4. Slow Performance
```bash
# Check disk I/O
iostat -x 1

# Check network
netstat -tuln

# Check database queries
psql -U usenetsync -c "SELECT * FROM pg_stat_activity WHERE state != 'idle';"
```

---

## Maintenance

### Daily Tasks
- Check application logs for errors
- Monitor disk space
- Verify backup completion

### Weekly Tasks
- Review performance metrics
- Update dependencies
- Test disaster recovery

### Monthly Tasks
- Security updates
- Database optimization
- Certificate renewal check

---

## Support

For issues and questions:
- Documentation: https://docs.usenetsync.com
- GitHub Issues: https://github.com/yourusername/usenetsync/issues
- Email: support@usenetsync.com

---

*Last Updated: December 2024*
*Version: 2.1.0*
# Windows Database Setup Guide

## PostgreSQL Installation for Windows

### Method 1: Full PostgreSQL Installation

1. **Download PostgreSQL:**
   - Visit: https://www.postgresql.org/download/windows/
   - Download the latest installer (14.x or higher)

2. **Install PostgreSQL:**
   - Run the installer as Administrator
   - During installation:
     - Password: Set a strong password for 'postgres' user
     - Port: Keep default 5432
     - Locale: Default
   - Complete the installation

3. **Create Database and User:**
   Open Command Prompt as Administrator and run:
   ```cmd
   "C:\Program Files\PostgreSQL\14\bin\psql" -U postgres
   ```
   
   Then execute these SQL commands:
   ```sql
   CREATE USER usenet WITH PASSWORD 'usenetsync';
   CREATE DATABASE usenet OWNER usenet;
   GRANT ALL PRIVILEGES ON DATABASE usenet TO usenet;
   \q
   ```

4. **Verify Connection:**
   ```cmd
   "C:\Program Files\PostgreSQL\14\bin\psql" -U usenet -d usenet -h localhost
   ```

### Method 2: Use SQLite Instead (Simpler Alternative)

If you don't want to install PostgreSQL, we can modify the application to use SQLite for local development:

1. **Update Database Configuration:**
   The application should automatically fall back to SQLite if PostgreSQL is not available.

2. **Create a local configuration file** at `%USERPROFILE%\.usenetsync\config.json`:
   ```json
   {
     "database": {
       "type": "sqlite",
       "path": "%USERPROFILE%/.usenetsync/data.db"
     }
   }
   ```

### Method 3: Use Docker (If Docker Desktop is installed)

1. **Install Docker Desktop for Windows:**
   - Download from: https://www.docker.com/products/docker-desktop/

2. **Run PostgreSQL in Docker:**
   ```powershell
   docker run -d `
     --name postgres-usenet `
     -e POSTGRES_USER=usenet `
     -e POSTGRES_PASSWORD=usenetsync `
     -e POSTGRES_DB=usenet `
     -p 5432:5432 `
     postgres:14
   ```

## Troubleshooting

### Check if PostgreSQL is Running:

**Windows Services:**
1. Press `Win + R`, type `services.msc`
2. Look for "postgresql-x64-14" (or similar)
3. If stopped, right-click and select "Start"
4. Set to "Automatic" for auto-start

**Command Line Check:**
```cmd
netstat -an | findstr :5432
```
If PostgreSQL is running, you should see:
```
TCP    0.0.0.0:5432    0.0.0.0:0    LISTENING
```

### Common Issues:

1. **Port 5432 Already in Use:**
   - Another application might be using the port
   - Change PostgreSQL port in `postgresql.conf`

2. **Firewall Blocking Connection:**
   - Add exception for port 5432 in Windows Firewall
   - Or temporarily disable firewall for testing

3. **PostgreSQL Service Not Starting:**
   - Check Event Viewer for errors
   - Verify data directory permissions
   - Check `pg_log` folder for error logs

## Quick SQLite Fallback (Immediate Fix)

For immediate use without PostgreSQL, we can add SQLite fallback support to the application. The application will use SQLite when PostgreSQL is not available.

### Environment Variable Configuration:
Set in PowerShell:
```powershell
$env:USE_SQLITE = "true"
$env:SQLITE_PATH = "$env:USERPROFILE\.usenetsync\data.db"
```

Or in Command Prompt:
```cmd
set USE_SQLITE=true
set SQLITE_PATH=%USERPROFILE%\.usenetsync\data.db
```

## Recommended Approach for Windows Users

**For Development/Testing:** Use SQLite (no installation required)
**For Production:** Install PostgreSQL properly

The application should gracefully handle both database types.
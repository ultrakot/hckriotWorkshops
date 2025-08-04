# HackeriotServer - Flask REST API

A Flask-based REST API server with Google OAuth authentication via Supabase, workshop management, and user registration system.

## ✨ Recent Updates

- 🐳 **Full Docker Support** with production-ready configuration
- 🎯 **Azure SQL Database Integration** with smart driver selection (pymssql/pyodbc)
- 🔧 **Smart Environment Detection** - automatically uses optimal database drivers
- 📦 **GitHub Container Registry** - published as `ghcr.io/ultrakot/hckr-app`
- 🚀 **Production Optimized** - enhanced error handling and logging

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ 
- Git
- Supabase account

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd HackeriotServer
```

### 📝 Manual Setup

### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Windows PowerShell
New-Item .env -ItemType File

# macOS/Linux
touch .env
```

Add your credentials to `.env`:
```env
# Supabase Authentication
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here

# Database Configuration (choose one)
# For SQLite (Development):
DB_TYPE=sqlite
DB_FOLDER=./data
DB_NAME=hackeriot.db

# For Azure SQL (Production):
# DB_TYPE=azure
# AZURE_SQL_SERVER=your-server.database.windows.net
# AZURE_SQL_DATABASE=your-database-name
# AZURE_SQL_USERNAME=your-username
# AZURE_SQL_PASSWORD=your-password
```

**🔑 How to get Supabase credentials:**

1. Go to [supabase.com](https://supabase.com)
2. Sign in and select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_KEY`

### 5. Initialize Database
```bash
python init_sqlite.py
```

### 6. Run the Server
```bash
python app.py
```

The API will be available at: `http://localhost:8000`

## 🔧 Development Setup

### Alternative Installation (Minimal Dependencies)
For basic testing without development tools:
```bash
pip install -r requirements-minimal.txt
```

### Environment Variables Setup by OS

**Windows PowerShell:**
```powershell
$env:SUPABASE_URL="https://your-project-id.supabase.co"
$env:SUPABASE_KEY="your-anon-key-here"
```

**Windows Command Prompt:**
```cmd
set SUPABASE_URL=https://your-project-id.supabase.co
set SUPABASE_KEY=your-anon-key-here
```

**macOS/Linux/WSL:**
```bash
export SUPABASE_URL="https://your-project-id.supabase.co"
export SUPABASE_KEY="your-anon-key-here"
```

## 🧪 Testing the Setup

### 1. Test API Connection
```bash
curl http://localhost:8000/api
```

Expected response:
```json
{
  "message": "HackeriotServer REST API",
  "version": "1.0",
  "endpoints": {
    "authentication": [...],
    "workshops": [...],
    "users": [...]
  }
}
```

### 2. Test Supabase Connection
```bash
curl http://localhost:8000/auth/config
```

Expected response:
```json
{
  "supabase_configured": true,
  "supabase_url": "https://your-project-id.supabase.co"
}
```

### 3. Test OAuth URL Generation
```bash
curl http://localhost:8000/auth/google/url
```

Should return a Google OAuth URL.

## 🔐 Google OAuth Setup

### 1. Google Cloud Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create/select project
3. Enable **Google+ API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Set authorized redirect URIs:
   ```
   http://localhost:3000/auth/callback
   https://your-project-id.supabase.co/auth/v1/callback
   ```

### 2. Supabase Google OAuth Setup

1. In Supabase Dashboard → **Authentication** → **Providers**
2. Enable **Google**
3. Add your Google OAuth **Client ID** and **Client Secret**
4. Set redirect URL: `https://your-project-id.supabase.co/auth/v1/callback`

## 📡 API Usage

### Authentication Flow

1. **Get OAuth URL:**
   ```bash
   curl http://localhost:8000/auth/google/url
   ```

2. **User signs in** with Google via the returned URL

3. **Extract token** from callback:
   ```bash
   curl -X POST http://localhost:8000/auth/extract-token \
     -H "Content-Type: application/json" \
     -d '{"callback_url": "callback_url_with_token"}'
   ```

4. **Use token** in API requests:
   ```bash
   curl http://localhost:8000/user/profile \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

### Key Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/api` | API documentation | No |
| GET | `/auth/google/url` | Get OAuth URL | No |
| POST | `/auth/extract-token` | Extract token from callback | No |
| GET | `/user/profile` | Get user profile | Yes |
| GET | `/workshops` | List workshops | Yes |
| POST | `/workshops/{workshop_id}/register` | Register for workshop | Yes |
| DELETE | `/workshops/{workshop_id}/register` | Cancel registration for workshop | Yes |

## 🗃️ Database

The project supports both **SQLite (development)** and **Azure SQL Database (production)** with smart driver selection:

### Smart Driver Selection
- **Development**: Uses `pyodbc` with ODBC Driver 17 for SQL Server
- **Production**: Automatically uses `pymssql` (lightweight, fewer dependencies)
- **Manual Override**: Set `AZURE_SQL_DRIVER_TYPE=pymssql` or `pyodbc`

### Database Tables
- `Users` - User profiles
- `Workshop` - Workshop information  
- `Registration` - Workshop registrations
- `Skill` - Available skills
- `UserSkill` - User skill associations
- `WorkshopSkill` - Workshop skill requirements

### SQLite Setup (Development)
```bash
python init_sqlite.py
```

### Azure SQL Setup (Production)
- Configure environment variables in `.env`
- Database tables work with existing schema
- Automatic connection pooling and optimization

## 🧰 Troubleshooting

### Virtual Environment Issues
```bash
# If activation fails, try:
python -m pip install --upgrade pip
python -m pip install virtualenv
```

### Supabase Connection Issues
1. Check `.env` file exists and has correct values
2. Verify Supabase URL format: `https://your-id.supabase.co`
3. Test credentials:
   ```bash
   curl http://localhost:8000/auth/config
   ```

### Import Errors
```bash
# Ensure venv is activated and dependencies installed
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Kill process using port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Kill process using port 8000 (macOS/Linux)
lsof -ti:8000 | xargs kill
```

## 🚀 Deployment

### 🐳 Docker Deployment (Recommended)

The application includes a production-ready Docker setup with optimized Azure SQL support.

#### Quick Docker Setup

**1. Build Image:**
```bash
docker build -t flask-pymssql-app .
```

**2. Create Environment File:**
Create `.env` file with your production credentials:
```env
# Azure SQL Configuration
AZURE_SQL_SERVER=your-server.database.windows.net
AZURE_SQL_DATABASE=your-database-name
AZURE_SQL_USERNAME=your-username
AZURE_SQL_PASSWORD=your-password

# Supabase Authentication
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

**3. Run Container:**
```bash
docker run -d --name flask-app -p 8000:8000 --env-file .env flask-pymssql-app
```

#### Docker Features
- ✅ **Smart Driver Selection**: Automatically uses `pymssql` in production
- ✅ **Optimized Dependencies**: Includes SQL Server ODBC Driver 17 + tools
- ✅ **Production Ready**: Gunicorn WSGI server with proper configuration
- ✅ **Multi-Database Support**: SQLite for development, Azure SQL for production
- ✅ **Security**: Environment-based credential management

#### Published Image
The application is available on GitHub Container Registry:
```bash
# Pull and run published image
docker run -d --name flask-app -p 8000:8000 --env-file .env ghcr.io/ultrakot/hckr-app:latest
```

#### Docker Management Commands
```bash
# View logs
docker logs flask-app

# Stop container  
docker stop flask-app

# Remove container
docker rm flask-app

# Clean up
docker system prune -a
```

### Azure Functions
For serverless deployment, see deployment documentation.

### Environment Variables for Production
Set these in your production environment:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `FLASK_ENV=production` - Enables pymssql driver selection
- `DB_TYPE=azure` - Use Azure SQL Database
- `AZURE_SQL_SERVER` - Azure SQL server name
- `AZURE_SQL_DATABASE` - Database name
- `AZURE_SQL_USERNAME` - Database username
- `AZURE_SQL_PASSWORD` - Database password
- `AZURE_SQL_DRIVER_TYPE` - Optional: Force specific driver (pymssql/pyodbc)

## 🏗️ Technical Architecture

### Database Driver Selection
The application automatically selects the optimal database driver based on environment:

- **Development** (`FLASK_ENV=development`): Uses `pyodbc` with ODBC Driver 17
  - Full compatibility with SQL Server Management Studio
  - Comprehensive debugging capabilities
  - Windows-optimized performance

- **Production** (`FLASK_ENV=production`): Uses `pymssql` 
  - Lightweight, fewer system dependencies
  - Better Docker container compatibility
  - Direct TDS protocol connection
  - Optimal for cloud deployments

### Connection String Formats

**pymssql (Production):**
```
mssql+pymssql://username@server:password@server.database.windows.net/database?timeout=30&charset=utf8
```

**pyodbc (Development):**
```
mssql+pyodbc://username:password@server.database.windows.net/database?driver=ODBC+Driver+17+for+SQL+Server&timeout=30&Encrypt=yes&TrustServerCertificate=no
```

### Docker Architecture
- **Base Image**: `python:3.11-slim-bullseye`
- **Dependencies**: Optimized for both SQLite and Azure SQL
- **WSGI Server**: Gunicorn with sync workers
- **Port**: 8000 (configurable via `PORT` environment variable)
- **Health Monitoring**: Built-in connection testing and error handling

### Key Files
- `db_selector.py` - Smart database driver selection logic
- `Dockerfile` - Production-ready container configuration  
- `requirements.txt` - Full dependencies (includes both drivers)
- `requirements-docker.txt` - Docker-optimized dependencies

## 📚 Documentation

- `FRONTEND_INTEGRATION.md` - Frontend integration examples
- `TOKEN_GENERATION_GUIDE.md` - Detailed OAuth token guide
- `tests/` - Test files and documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 
# HackeriotServer - Flask REST API

A Flask-based REST API server with Google OAuth authentication via Supabase, workshop management, and user registration system.

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

Add your Supabase credentials to `.env`:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
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

The API will be available at: `http://localhost:5000`

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
curl http://localhost:5000/api
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
curl http://localhost:5000/auth/config
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
curl http://localhost:5000/auth/google/url
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
   curl http://localhost:5000/auth/google/url
   ```

2. **User signs in** with Google via the returned URL

3. **Extract token** from callback:
   ```bash
   curl -X POST http://localhost:5000/auth/extract-token \
     -H "Content-Type: application/json" \
     -d '{"callback_url": "callback_url_with_token"}'
   ```

4. **Use token** in API requests:
   ```bash
   curl http://localhost:5000/user/profile \
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
| POST | `/signup/{workshop_id}` | Register for workshop | Yes |

## 🗃️ Database

The project uses SQLite with the following tables:
- `Users` - User profiles
- `Workshop` - Workshop information
- `Registration` - Workshop registrations
- `Skill` - Available skills
- `UserSkill` - User skill associations
- `WorkshopSkill` - Workshop skill requirements

Database is automatically created when running `init_sqlite.py`.

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
   curl http://localhost:5000/auth/config
   ```

### Import Errors
```bash
# Ensure venv is activated and dependencies installed
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Kill process using port 5000 (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Kill process using port 5000 (macOS/Linux)
lsof -ti:5000 | xargs kill
```

## 🚀 Deployment

### Azure Functions
For serverless deployment, see deployment documentation.

### Environment Variables for Production
Set these in your production environment:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `FLASK_ENV=production`

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
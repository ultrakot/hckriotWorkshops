# Frontend Integration Guide

Your HackerIot API now includes OAuth endpoints that make frontend integration easy!

## 🚀 New API Endpoints for Frontend Developers

### **GET /auth/providers**
List available authentication providers:

```bash
curl http://localhost:5000/auth/providers
```

Response:
```json
{
  "providers": [
    {
      "name": "google",
      "display_name": "Google", 
      "type": "oauth",
      "endpoint": "/auth/google/url",
      "available": true
    }
  ],
  "count": 1,
  "default_redirect": "http://localhost:3000/auth/callback",
  "usage": {
    "get_oauth_url": "GET /auth/google/url?redirect_to=your_callback_url",
    "custom_redirect": "POST /auth/google/url with {\"redirect_to\": \"your_url\"}"
  }
}
```

### **GET /auth/google/url**
Generate Google OAuth URL:

```bash
# Default redirect (localhost:3000)
curl http://localhost:5000/auth/google/url

# Custom redirect URL
curl "http://localhost:5000/auth/google/url?redirect_to=https://yourapp.com/auth/callback"
```

Response:
```json
{
  "provider": "google",
  "oauth_url": "https://your-project.supabase.co/auth/v1/authorize?provider=google&redirect_to=...",
  "redirect_to": "http://localhost:3000/auth/callback",
  "instructions": {
    "step1": "Redirect user to oauth_url",
    "step2": "User signs in with Google", 
    "step3": "User redirected to redirect_to with access_token in URL fragment",
    "step4": "Extract access_token from URL: #access_token=jwt_token_here",
    "step5": "Use token in API calls: Authorization: Bearer <token>"
  }
}
```

### **POST /auth/google/url**
Generate OAuth URL with custom redirect:

```bash
curl -X POST http://localhost:5000/auth/google/url \
  -H "Content-Type: application/json" \
  -d '{"redirect_to": "https://yourapp.com/callback"}'
```

### **GET /auth/config**  
Get authentication configuration:

```bash
curl http://localhost:5000/auth/config
```

### **POST /auth/signout**
Sign out current user (requires authentication):

```bash
curl -X POST http://localhost:5000/auth/signout \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "status": "success",
  "message": "Successfully signed out",
  "instructions": {
    "client_cleanup": [
      "Remove token from localStorage/sessionStorage",
      "Clear any user state in your app",
      "Redirect to login page"
    ]
  }
}
```

### **POST /auth/extract-token**
Extract JWT token from OAuth callback URL (server-side utility):

```bash
curl -X POST http://localhost:5000/auth/extract-token \
  -H "Content-Type: application/json" \
  -d '{
    "callback_url": "http://localhost:3000/auth/callback#access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&expires_in=3600"
  }'
```

Response:
```json
{
  "success": true,
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "v1.M0KnH...",
    "token_type": "bearer",
    "expires_in": "3600",
    "expires_at": "2024-01-15T11:30:00Z"
  },
  "token_info": {
    "length": 856,
    "parts": 3,
    "valid_jwt_structure": true
  },
  "usage": {
    "authorization_header": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "example_api_call": "curl -H \"Authorization: Bearer eyJhbGciOi...\" http://localhost:5000/user/profile"
  }
}
```

### **GET /auth/verify**
Verify token validity and get user info:

```bash
curl http://localhost:5000/auth/verify \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "name": "John Doe", 
    "email": "john@example.com",
    "created_date": "2024-01-15 10:30:00",
    "avatar_url": "https://lh3.googleusercontent.com/..."
  },
  "message": "Token is valid"
}
```

### **Server-Side Token Extraction Example**

For backend applications that want to handle OAuth callbacks server-side:

```javascript
// Node.js/Express example
app.post('/handle-oauth-callback', async (req, res) => {
  const callbackUrl = req.body.callback_url;
  
  try {
    // Use your API to extract the token
    const response = await fetch('http://localhost:5000/auth/extract-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ callback_url: callbackUrl })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Token extracted successfully
      const { access_token, expires_in } = data.tokens;
      
      // Store token securely (database, session, etc.)
      req.session.auth_token = access_token;
      
      res.json({
        success: true,
        message: 'Authentication successful',
        token: access_token,
        expires_in: expires_in
      });
    } else {
      res.status(400).json({
        error: 'Token extraction failed',
        details: data.error
      });
    }
  } catch (error) {
    res.status(500).json({
      error: 'Server error during token extraction'
    });
  }
});
```

## 📱 Frontend Implementation Examples

### **React Example**

```javascript
// AuthService.js
class AuthService {
  constructor() {
    this.API_BASE = 'http://localhost:5000';
  }

  // Get Google OAuth URL
  async getGoogleOAuthUrl(redirectUrl = null) {
    const url = redirectUrl 
      ? `${this.API_BASE}/auth/google/url?redirect_to=${encodeURIComponent(redirectUrl)}`
      : `${this.API_BASE}/auth/google/url`;
    
    const response = await fetch(url);
    return response.json();
  }

  // Redirect to Google OAuth
  async signInWithGoogle(redirectUrl = null) {
    const { oauth_url } = await this.getGoogleOAuthUrl(redirectUrl);
    window.location.href = oauth_url;
  }

  // Extract token from callback URL
  extractTokenFromCallback() {
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    return params.get('access_token');
  }

  // Make authenticated API calls
  async apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('auth_token');
    
    return fetch(`${this.API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
  },

  // Verify token is still valid
  async verifyToken() {
    const response = await this.apiCall('/auth/verify');
    if (response.ok) {
      return response.json();
    }
    return null;
  },

  // Sign out user
  async signOut() {
    try {
      await this.apiCall('/auth/signout', { method: 'POST' });
    } catch (error) {
      console.log('Signout API call failed:', error);
    } finally {
      // Always clean up locally regardless of API response
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      // Redirect to login or update app state
    }
  }
}

// Usage in React component
function AuthButtons() {
  const authService = new AuthService();
  const [user, setUser] = useState(null);

  const handleGoogleLogin = async () => {
    await authService.signInWithGoogle('http://localhost:3000/dashboard');
  };

  const handleSignOut = async () => {
    await authService.signOut();
    setUser(null);
    // Redirect or update app state
    window.location.href = '/login';
  };

  const checkAuth = async () => {
    const userInfo = await authService.verifyToken();
    if (userInfo && userInfo.valid) {
      setUser(userInfo.user);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  if (user) {
    return (
      <div>
        <span>Welcome, {user.name}!</span>
        <button onClick={handleSignOut}>Sign Out</button>
      </div>
    );
  }

  return <button onClick={handleGoogleLogin}>Sign in with Google</button>;
}

// In your callback page component
function AuthCallback() {
  useEffect(() => {
    const authService = new AuthService();
    const token = authService.extractTokenFromCallback();
    
    if (token) {
      localStorage.setItem('auth_token', token);
      // Redirect to dashboard or update app state
      navigate('/dashboard');
    }
  }, []);

  return <div>Processing authentication...</div>;
}
```

### **Vue.js Example**

```javascript
// auth.js
export const authService = {
  API_BASE: 'http://localhost:5000',

  async getGoogleOAuthUrl(redirectUrl) {
    const url = redirectUrl 
      ? `${this.API_BASE}/auth/google/url?redirect_to=${encodeURIComponent(redirectUrl)}`
      : `${this.API_BASE}/auth/google/url`;
    
    const response = await fetch(url);
    return response.json();
  },

  async signInWithGoogle() {
    const { oauth_url } = await this.getGoogleOAuthUrl(window.location.origin + '/auth/callback');
    window.location.href = oauth_url;
  },

  extractTokenFromCallback() {
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    return params.get('access_token');
  }
};

// In your Vue component
export default {
  methods: {
    async login() {
      await authService.signInWithGoogle();
    }
  }
}
```

### **Vanilla JavaScript Example**

```javascript
// Simple vanilla JS implementation
const Auth = {
  API_BASE: 'http://localhost:5000',

  async getGoogleOAuthUrl() {
    const response = await fetch(`${this.API_BASE}/auth/google/url`);
    return response.json();
  },

  async signInWithGoogle() {
    const { oauth_url } = await this.getGoogleOAuthUrl();
    window.location.href = oauth_url;
  },

  extractToken() {
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    return params.get('access_token');
  },

  async testAPI(token) {
    const response = await fetch(`${this.API_BASE}/user/profile`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.json();
  }
};

// Usage
document.getElementById('login-btn').addEventListener('click', () => {
  Auth.signInWithGoogle();
});

// On callback page
const token = Auth.extractToken();
if (token) {
  localStorage.setItem('token', token);
  // Test API call
  Auth.testAPI(token).then(user => {
    console.log('User:', user);
  });
}
```

## 🧪 Testing the Integration

1. **Start your API server**:
   ```bash
   python app.py
   ```

2. **Test the endpoints**:
   ```bash
   # List providers
   curl http://localhost:5000/auth/providers
   
   # Get OAuth URL
   curl http://localhost:5000/auth/google/url
   
   # Get auth config
   curl http://localhost:5000/auth/config
   ```

3. **Frontend testing workflow**:
   - Call `/auth/google/url` to get OAuth URL
   - Redirect user to the OAuth URL
   - User signs in with Google
   - Extract token from callback URL fragment
   - Use token for authenticated API calls

## 🔧 Configuration

Make sure your environment variables are set:

```bash
$env:SUPABASE_URL="https://your-project-id.supabase.co"
$env:SUPABASE_KEY="your-anon-key-here"
```

## 📋 API Endpoints Summary

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/auth/providers` | List auth providers | No |
| GET | `/auth/config` | Get auth configuration | No |
| GET | `/auth/google/url` | Get Google OAuth URL | No |
| POST | `/auth/google/url` | Custom OAuth URL | No |
| POST | `/auth/extract-token` | Extract token from callback URL | No |
| POST | `/auth/signout` | Sign out current user | Yes |
| GET | `/auth/verify` | Verify token & get user info | Yes |
| GET | `/user/profile` | Get user profile | Yes |
| GET | `/workshops` | List workshops | Yes |
| POST | `/signup/{id}` | Sign up for workshop | Yes |
| POST | `/cancel/{id}` | Cancel workshop registration | Yes |
| GET | `/registration_status/{id}` | Check registration status | Yes |

Your API is now **frontend-ready**! 🎉 
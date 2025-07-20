# How to Generate New JWT Tokens Using OAuth API

This guide shows you exactly how to generate new JWT tokens for authentication using your HackerIot API endpoints.

## 🚀 Complete Token Generation Flow

### **Step 1: Get Google OAuth URL from API**

**API Call:**
```bash
curl http://localhost:5000/auth/google/url
```

**Response:**
```json
{
  "provider": "google",
  "oauth_url": "https://gkbjmwfkyvsjyoolxrld.supabase.co/auth/v1/authorize?provider=google&redirect_to=http%3A//localhost%3A3000/auth/callback",
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

### **Step 2: Redirect User to OAuth URL**

Take the `oauth_url` from the response and redirect the user to it:

```javascript
// JavaScript example
const response = await fetch('http://localhost:5000/auth/google/url');
const data = await response.json();

// Redirect user to Google OAuth
window.location.href = data.oauth_url;
```

### **Step 3: User Signs In with Google**

The user will:
1. See Google's sign-in page
2. Sign in with their Google account
3. Grant permissions to your app
4. Get redirected back to your callback URL

### **Step 4: Extract JWT Token from Callback**

After Google OAuth, the user is redirected to your callback URL with the token in the URL fragment:

```
http://localhost:3000/auth/callback#access_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&expires_in=3600&refresh_token=...&token_type=bearer
```

**Extract the token:**
```javascript
// JavaScript to extract token from URL fragment
function extractTokenFromCallback() {
    const hash = window.location.hash.substring(1); // Remove #
    const params = new URLSearchParams(hash);
    const accessToken = params.get('access_token');
    const expiresIn = params.get('expires_in');
    const refreshToken = params.get('refresh_token');
    
    return {
        accessToken,
        expiresIn,
        refreshToken
    };
}

// Usage
const tokens = extractTokenFromCallback();
console.log('JWT Token:', tokens.accessToken);

// Save token for API calls
localStorage.setItem('auth_token', tokens.accessToken);
```

### **Step 5: Use Token for API Calls**

Now you can use the JWT token for authenticated requests:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     http://localhost:5000/user/profile
```

## 🔧 Custom Redirect URL

If you need a different callback URL:

```bash
# Custom redirect URL
curl "http://localhost:5000/auth/google/url?redirect_to=https://yourapp.com/callback"

# Or POST with JSON body
curl -X POST http://localhost:5000/auth/google/url \
  -H "Content-Type: application/json" \
  -d '{"redirect_to": "https://yourapp.com/callback"}'
```

## 📱 Complete Frontend Implementation

### **React Example**

```javascript
import React, { useState, useEffect } from 'react';

function AuthComponent() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const API_BASE = 'http://localhost:5000';

  // Check if we're on the callback page with a token
  useEffect(() => {
    const hash = window.location.hash.substring(1);
    if (hash.includes('access_token')) {
      const params = new URLSearchParams(hash);
      const accessToken = params.get('access_token');
      
      if (accessToken) {
        setToken(accessToken);
        localStorage.setItem('auth_token', accessToken);
        
        // Clear the URL hash
        window.location.hash = '';
        
        // Get user info
        fetchUserProfile(accessToken);
      }
    } else {
      // Check if we have a stored token
      const storedToken = localStorage.getItem('auth_token');
      if (storedToken) {
        setToken(storedToken);
        fetchUserProfile(storedToken);
      }
    }
  }, []);

  const startGoogleSignIn = async () => {
    try {
      // Get OAuth URL from your API
      const response = await fetch(`${API_BASE}/auth/google/url?redirect_to=${encodeURIComponent(window.location.origin + '/auth/callback')}`);
      const data = await response.json();
      
      // Redirect to Google OAuth
      window.location.href = data.oauth_url;
    } catch (error) {
      console.error('Error starting sign-in:', error);
    }
  };

  const fetchUserProfile = async (authToken) => {
    try {
      const response = await fetch(`${API_BASE}/user/profile`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        console.error('Failed to fetch user profile');
        // Token might be invalid
        localStorage.removeItem('auth_token');
        setToken(null);
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    }
  };

  const signOut = async () => {
    try {
      // Call signout API
      await fetch(`${API_BASE}/auth/signout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
    } catch (error) {
      console.error('Signout API failed:', error);
    } finally {
      // Always clean up locally
      localStorage.removeItem('auth_token');
      setToken(null);
      setUser(null);
    }
  };

  if (user) {
    return (
      <div>
        <h2>Welcome, {user.Name}!</h2>
        <p>Email: {user.Email}</p>
        <button onClick={signOut}>Sign Out</button>
        
        <div>
          <h3>Your JWT Token:</h3>
          <textarea value={token} readOnly rows={4} cols={60} />
          <p>Use this token in Postman: <code>Authorization: Bearer {token.substring(0, 30)}...</code></p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2>Sign In Required</h2>
      <button onClick={startGoogleSignIn}>Sign In with Google</button>
    </div>
  );
}

export default AuthComponent;
```

### **Vanilla JavaScript Example**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Token Generation Test</title>
</head>
<body>
    <div id="app">
        <button id="signin-btn">Generate New Token (Sign In)</button>
        <div id="result" style="display: none;">
            <h3>Token Generated!</h3>
            <p><strong>JWT Token:</strong></p>
            <textarea id="token-display" rows="4" cols="80" readonly></textarea>
            <br><br>
            <button id="test-api-btn">Test API with Token</button>
            <button id="signout-btn">Sign Out</button>
            <div id="api-result"></div>
        </div>
    </div>

    <script>
        const API_BASE = 'http://localhost:5000';
        let currentToken = null;

        // Check if we're on callback page
        window.addEventListener('load', () => {
            const hash = window.location.hash.substring(1);
            if (hash.includes('access_token')) {
                handleCallback();
            } else {
                // Check for stored token
                const storedToken = localStorage.getItem('auth_token');
                if (storedToken) {
                    showTokenResult(storedToken);
                }
            }
        });

        // Handle OAuth callback
        function handleCallback() {
            const hash = window.location.hash.substring(1);
            const params = new URLSearchParams(hash);
            const token = params.get('access_token');
            
            if (token) {
                localStorage.setItem('auth_token', token);
                showTokenResult(token);
                
                // Clean URL
                window.location.hash = '';
            }
        }

        // Start OAuth flow
        document.getElementById('signin-btn').addEventListener('click', async () => {
            try {
                // Get OAuth URL from API
                const response = await fetch(`${API_BASE}/auth/google/url?redirect_to=${encodeURIComponent(window.location.href)}`);
                const data = await response.json();
                
                // Redirect to Google
                window.location.href = data.oauth_url;
            } catch (error) {
                alert('Error: ' + error.message);
            }
        });

        // Show token result
        function showTokenResult(token) {
            currentToken = token;
            document.getElementById('token-display').value = token;
            document.getElementById('result').style.display = 'block';
            document.getElementById('signin-btn').style.display = 'none';
        }

        // Test API with token
        document.getElementById('test-api-btn').addEventListener('click', async () => {
            try {
                const response = await fetch(`${API_BASE}/user/profile`, {
                    headers: {
                        'Authorization': `Bearer ${currentToken}`
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    document.getElementById('api-result').innerHTML = 
                        `<div style="color: green;">
                            <h4>API Test Successful!</h4>
                            <p>User: ${data.Name}</p>
                            <p>Email: ${data.Email}</p>
                        </div>`;
                } else {
                    document.getElementById('api-result').innerHTML = 
                        `<div style="color: red;">API Error: ${data.error}</div>`;
                }
            } catch (error) {
                document.getElementById('api-result').innerHTML = 
                    `<div style="color: red;">Network Error: ${error.message}</div>`;
            }
        });

        // Sign out
        document.getElementById('signout-btn').addEventListener('click', async () => {
            try {
                await fetch(`${API_BASE}/auth/signout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${currentToken}`
                    }
                });
            } catch (error) {
                console.error('Signout failed:', error);
            } finally {
                localStorage.removeItem('auth_token');
                currentToken = null;
                document.getElementById('result').style.display = 'none';
                document.getElementById('signin-btn').style.display = 'block';
                document.getElementById('api-result').innerHTML = '';
            }
        });
    </script>
</body>
</html>
```

## 🧪 Testing with Postman

1. **Get OAuth URL:**
   ```
   GET http://localhost:5000/auth/google/url
   ```

2. **Copy the `oauth_url` from response**

3. **Open the OAuth URL in browser:**
   - Sign in with Google
   - Get redirected to callback URL

4. **Extract token from callback URL:**
   ```
   http://localhost:3000/auth/callback#access_token=YOUR_TOKEN_HERE&...
   ```

5. **Use token in Postman:**
   ```
   Authorization: Bearer YOUR_TOKEN_HERE
   ```

## 🔄 Token Refresh

JWT tokens expire (usually 1 hour). When your token expires:

1. **Check token validity:**
   ```bash
   curl http://localhost:5000/auth/verify \
     -H "Authorization: Bearer your-token"
   ```

2. **If expired (401 error), generate new token:**
   - Repeat the OAuth flow above
   - Or use the refresh token if available

## **🔧 Alternative: Server-Side Token Extraction**

For server-side applications, you can extract tokens using the API instead of JavaScript:

```bash
# Extract token from callback URL using the API
curl -X POST http://localhost:5000/auth/extract-token \
  -H "Content-Type: application/json" \
  -d '{
    "callback_url": "http://localhost:3000/auth/callback#access_token=eyJhbGciOi...&expires_in=3600"
  }'
```

**Response:**
```json
{
  "success": true,
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": "3600"
  },
  "usage": {
    "authorization_header": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Perfect for:**
- **Backend applications** that handle OAuth callbacks
- **Testing tools** and automation scripts  
- **Mobile apps** that might have difficulty with URL fragments
- **Server-to-server** authentication flows

## ✅ Quick Summary

**Client-Side Method:**
1. **Call API:** `GET /auth/google/url`
2. **Redirect user:** To the returned `oauth_url`
3. **User signs in:** With Google
4. **Extract token:** From callback URL fragment with JavaScript
5. **Use token:** `Authorization: Bearer <token>`

**Server-Side Method:**
1. **Call API:** `GET /auth/google/url`
2. **Redirect user:** To the returned `oauth_url`  
3. **User signs in:** With Google
4. **POST callback URL:** To `/auth/extract-token` endpoint
5. **Get token:** From JSON response
6. **Use token:** `Authorization: Bearer <token>`

**Your token is ready for all API calls!** 🎉 
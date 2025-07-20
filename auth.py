from functools import wraps
from flask import request, abort
from supabase import create_client, Client
from config import Config
from models import db, Users

# Initialize Supabase client with error handling
def get_supabase_client():
    """Get Supabase client with proper error handling."""
    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        raise ValueError(
            "Missing Supabase credentials! Set environment variables:\n"
            "  SUPABASE_URL=https://your-project-id.supabase.co\n"
            "  SUPABASE_KEY=your-anon-key-here"
        )
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Create client when first needed (lazy loading)
_supabase_client = None

def get_supabase():
    """Get cached Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            print("❌ Missing or invalid Authorization header")
            abort(401)
        
        token = auth_header.replace('Bearer ', '').strip()
        if not token:
            print("❌ Empty token")
            abort(401)
        
        # Basic JWT format validation
        if token.count('.') != 2:
            print(f"❌ Invalid JWT format - token has {token.count('.')} dots, expected 2")
            print(f"Token preview: {token[:50]}...")
            abort(401)
        
        try:
            supabase = get_supabase()
        except ValueError as e:
            print(f"Supabase configuration error: {e}")
            abort(500)
        
        try:
            # Try to get user with JWT token
            from gotrue import User
            user_data = supabase.auth.get_user(token)
        except Exception as e:
            print(f"❌ Token validation failed: {e}")
            print(f"Token preview: {token[:30]}...")
            print(f"Full error: {str(e)}")
            abort(401)
        if not user_data.user:
            abort(401)
        request.user = user_data.user
        
        # Find user by email (since we use integer autoincrement primary key)
        existing_user = Users.query.filter_by(Email=request.user.email).first()
        if not existing_user:
            # Create new user with Google profile information
            user_meta = request.user.user_metadata or {}
            google_name = user_meta.get('full_name') or user_meta.get('name') or request.user.email.split('@')[0]
            
            new_user = Users(
                Name=google_name,
                Email=request.user.email,
                SupabaseId=request.user.id,
                AvatarUrl=user_meta.get('avatar_url') or user_meta.get('picture')
            )
            db.session.add(new_user)
            db.session.commit()
            
            # Attach the local user to the request for easy access
            request.local_user = new_user
        else:
            # Update Supabase ID if not set and update profile info if changed
            if not existing_user.SupabaseId:
                existing_user.SupabaseId = request.user.id
            
            # Optionally update user info from Google (if profile changed)
            user_meta = request.user.user_metadata or {}
            if user_meta.get('full_name') or user_meta.get('name'):
                google_name = user_meta.get('full_name') or user_meta.get('name')
                if existing_user.Name != google_name:
                    existing_user.Name = google_name
            
            if user_meta.get('avatar_url') or user_meta.get('picture'):
                new_avatar = user_meta.get('avatar_url') or user_meta.get('picture')
                if existing_user.AvatarUrl != new_avatar:
                    existing_user.AvatarUrl = new_avatar
            
            db.session.commit()
            request.local_user = existing_user
            
        return f(*args, **kwargs)
    return decorated 
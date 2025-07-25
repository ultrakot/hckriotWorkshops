from flask import Flask, request, jsonify, abort
from models import db, Workshop, Users, Registration, WorkshopSkill, Skill, UserSkill
from auth import require_auth
from urllib.parse import urlencode, urlparse, parse_qs
import os
import re

def init_routes(app: Flask):
    
    @app.route('/')
    def health_check():
        """API health check endpoint."""
        return jsonify({
            'status': 'ok',
            'message': 'HackerIot API is running',
            'version': '1.0',
            'endpoints': {
                'authentication': [
                    'GET  /auth/providers - List auth providers',
                    'GET  /auth/config - Get auth configuration', 
                    'GET  /auth/google/url - Generate Google OAuth URL',
                    'POST /auth/google/url - Generate OAuth URL with custom redirect',
                    'POST /auth/extract-token - Extract token from OAuth callback URL',
                    'POST /auth/signout - Sign out current user',
                    'GET  /auth/verify - Verify token and get user info'
                ],
                'user': [
                    'GET  /user/profile - Get authenticated user profile'
                ],
                'workshops': [
                    'GET  /workshops - List all workshops',
                    'GET  /workshops/{id} - Get workshop details',
                    'POST /signup/{id} - Sign up for workshop',
                    'POST /cancel/{id} - Cancel registration',
                    'GET  /registration_status/{id} - Check registration status'
                ],
                'debug': [
                    'POST /debug/token - Debug JWT token format'
                ]
            }
        })
    
    @app.route('/debug/token', methods=['POST'])
    def debug_token():
        """Debug endpoint to check JWT token format."""
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing or invalid Authorization header',
                'received': auth_header[:50] if auth_header else 'None'
            }), 400
        
        token = auth_header.replace('Bearer ', '').strip()
        
        # Analyze token structure
        parts = token.split('.')
        
        return jsonify({
            'token_length': len(token),
            'token_parts': len(parts),
            'token_preview': token[:50] + '...' if len(token) > 50 else token,
            'parts_lengths': [len(part) for part in parts],
            'valid_jwt_structure': len(parts) == 3,
            'first_part_preview': parts[0][:20] if len(parts) > 0 else 'None'
                 })
    
    @app.route('/auth/google/url', methods=['GET', 'POST'])
    def get_google_oauth_url():
        """Generate Google OAuth URL for frontend authentication."""
        
        # Get Supabase URL from environment
        supabase_url = os.environ.get("SUPABASE_URL")
        if not supabase_url:
            return jsonify({
                'error': 'Authentication service not configured',
                'message': 'SUPABASE_URL not set'
            }), 500
        
        # Get redirect URL from request (POST) or query params (GET)
        if request.method == 'POST':
            data = request.get_json() or {}
            redirect_to = data.get('redirect_to')
        else:
            redirect_to = request.args.get('redirect_to')
        
        # Default redirect URL for frontend
        if not redirect_to:
            redirect_to = request.args.get('default_redirect', 'http://localhost:3000/auth/callback')
        
        # Build OAuth URL
        oauth_endpoint = f"{supabase_url}/auth/v1/authorize"
        params = {
            'provider': 'google',
            'redirect_to': redirect_to
        }
        oauth_url = f"{oauth_endpoint}?{urlencode(params)}"
        
        return jsonify({
            'provider': 'google',
            'oauth_url': oauth_url,
            'redirect_to': redirect_to,
            'instructions': {
                'step1': 'Redirect user to oauth_url',
                'step2': 'User signs in with Google',
                'step3': 'User redirected to redirect_to with access_token in URL fragment',
                'step4': 'Extract access_token from URL: #access_token=jwt_token_here',
                'step5': 'Use token in API calls: Authorization: Bearer <token>'
            }
        })
    
    @app.route('/auth/providers', methods=['GET'])
    def get_auth_providers():
        """List available authentication providers."""
        
        supabase_url = os.environ.get("SUPABASE_URL")
        
        providers = []
        
        if supabase_url:
            providers.append({
                'name': 'google',
                'display_name': 'Google',
                'type': 'oauth',
                'endpoint': '/auth/google/url',
                'available': True
            })
        
        return jsonify({
            'providers': providers,
            'count': len(providers),
            'default_redirect': 'http://localhost:3000/auth/callback',
            'usage': {
                'get_oauth_url': 'GET /auth/google/url?redirect_to=your_callback_url',
                'custom_redirect': 'POST /auth/google/url with {"redirect_to": "your_url"}'
            }
        })
    
    @app.route('/auth/config', methods=['GET'])
    def get_auth_config():
        """Get authentication configuration for frontend."""
        
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        return jsonify({
            'supabase_configured': bool(supabase_url and supabase_key),
            'supabase_url': supabase_url if supabase_url else None,
            'google_oauth_available': bool(supabase_url),
            'supported_providers': ['google'] if supabase_url else [],
            'endpoints': {
                'oauth_url': '/auth/google/url',
                'providers': '/auth/providers',
                'user_profile': '/user/profile',
                'workshops': '/workshops'
            }
                 })
    
    @app.route('/auth/signout', methods=['POST'])
    @require_auth
    def signout():
        """Sign out the current user and invalidate their session."""
        
        try:
            # Get the Supabase client
            from auth import get_supabase
            supabase = get_supabase()
            
            # Sign out from Supabase (invalidates the JWT token)
            supabase.auth.sign_out()
            
            return jsonify({
                'status': 'success',
                'message': 'Successfully signed out',
                'instructions': {
                    'client_cleanup': [
                        'Remove token from localStorage/sessionStorage',
                        'Clear any user state in your app',
                        'Redirect to login page'
                    ]
                }
            })
            
        except Exception as e:
            # Even if Supabase signout fails, we should tell the client to clean up
            return jsonify({
                'status': 'warning',
                'message': 'Signed out locally (server signout failed)',
                'error': str(e),
                'instructions': {
                    'client_cleanup': [
                        'Remove token from localStorage/sessionStorage',
                        'Clear any user state in your app', 
                        'Redirect to login page'
                    ]
                }
            })
    
    @app.route('/auth/verify', methods=['GET'])
    @require_auth 
    def verify_token():
        """Verify if the current token is valid and return user info."""
        
        user = request.local_user
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({
            'valid': True,
            'user': {
                'id': user.UserId,
                'name': user.Name,
                'email': user.Email,
                'created_date': user.CreatedDate,
                'avatar_url': user.AvatarUrl
            },
            'message': 'Token is valid'
                 })
    
    @app.route('/auth/extract-token', methods=['POST'])
    def extract_token_from_url():
        """Extract JWT token from OAuth callback URL."""
        
        data = request.get_json()
        if not data or 'callback_url' not in data:
            return jsonify({
                'error': 'Missing callback_url in request body',
                'example': {
                    'callback_url': 'http://localhost:3000/auth/callback#access_token=eyJ...&expires_in=3600'
                }
            }), 400
        
        callback_url = data['callback_url']
        
        try:
            # Parse the URL
            parsed_url = urlparse(callback_url)
            
            # Extract fragment (everything after #)
            fragment = parsed_url.fragment
            if not fragment:
                return jsonify({
                    'error': 'No URL fragment found',
                    'message': 'OAuth callback URLs should contain #access_token=... in the fragment',
                    'received_url': callback_url
                }), 400
            
            # Parse fragment parameters
            fragment_params = {}
            for param in fragment.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    fragment_params[key] = value
            
            # Extract tokens and metadata
            access_token = fragment_params.get('access_token')
            refresh_token = fragment_params.get('refresh_token')
            expires_in = fragment_params.get('expires_in')
            token_type = fragment_params.get('token_type', 'bearer')
            
            if not access_token:
                return jsonify({
                    'error': 'No access_token found in URL fragment',
                    'fragment_found': fragment,
                    'parsed_params': list(fragment_params.keys())
                }), 400
            
            # Validate token format (basic JWT structure check)
            if access_token.count('.') != 2:
                return jsonify({
                    'error': 'Invalid JWT token format',
                    'message': 'JWT tokens should have 3 parts separated by dots',
                    'token_parts': access_token.count('.') + 1
                }), 400
            
            # Calculate expiration time (if expires_in provided)
            expires_at = None
            if expires_in:
                try:
                    from datetime import datetime, timedelta
                    expires_at = (datetime.utcnow() + timedelta(seconds=int(expires_in))).isoformat() + 'Z'
                except (ValueError, TypeError):
                    pass
            
            return jsonify({
                'success': True,
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': token_type,
                    'expires_in': expires_in,
                    'expires_at': expires_at
                },
                'token_info': {
                    'length': len(access_token),
                    'parts': access_token.count('.') + 1,
                    'valid_jwt_structure': True
                },
                'usage': {
                    'authorization_header': f'Bearer {access_token}',
                    'example_api_call': f'curl -H "Authorization: Bearer {access_token[:30]}..." http://localhost:5000/user/profile'
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': 'Failed to parse callback URL',
                'message': str(e),
                'callback_url': callback_url
            }), 500
    
    @app.route('/user/profile', methods=['GET'])
    @require_auth
    def get_user_profile():
        user = request.local_user
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({
            'UserId': user.UserId,
            'Name': user.Name,
            'Email': user.Email,
            'CreatedDate': user.CreatedDate,
            'AvatarUrl': user.AvatarUrl
        })
    
    @app.route('/workshops', methods=['GET'])
    @require_auth
    def list_workshops():
        skills = request.args.getlist('skill')
        if skills:
            # Filter by skills - join Workshop -> WorkshopSkill -> Skill
            workshops = Workshop.query.join(WorkshopSkill).join(Skill).filter(Skill.Name.in_(skills)).all()
        else:
            workshops = Workshop.query.all()
        
        result = []
        for w in workshops:
            # Count registered users (not waitlisted or cancelled)
            registered_count = Registration.query.filter_by(
                WorkshopId=w.WorkshopId, 
                Status='Registered'
            ).count()
            vacant = w.MaxCapacity - registered_count
            
            result.append({
                'id': w.WorkshopId,
                'title': w.Title,
                'vacant': vacant
            })
        return jsonify(result)

    @app.route('/workshops/<int:w_id>', methods=['GET'])
    @require_auth
    def get_workshop(w_id):
        w = Workshop.query.get_or_404(w_id)
        
        # Count registered users
        registered_count = Registration.query.filter_by(
            WorkshopId=w.WorkshopId, 
            Status='Registered'
        ).count()
        vacant = w.MaxCapacity - registered_count
        
        return jsonify({
            'id': w.WorkshopId,
            'title': w.Title,
            'description': w.Description,
            'date': w.SessionDate,
            'time': w.StartTime,
            'duration_mins': w.DurationMin,
            'capacity': w.MaxCapacity,
            'vacant': vacant
        })

    @app.route('/signup/<int:w_id>', methods=['POST'])
    @require_auth
    def signup(w_id):
        w = Workshop.query.get_or_404(w_id)
        user_id = request.local_user.UserId
        
        # Check for any existing registration (any status)
        existing_registration = Registration.query.filter_by(
            UserId=user_id, 
            WorkshopId=w_id
        ).first()
        
        # If user is already registered or waitlisted, prevent duplicate signup
        if existing_registration and existing_registration.Status in ['Registered', 'Waitlisted']:
            return jsonify({
                'error': 'Already signed up',
                'current_status': existing_registration.Status,
                'registered_at': existing_registration.RegisteredAt
            }), 400
        
        # Count current active registrations
        registered_count = Registration.query.filter_by(
            WorkshopId=w_id, 
            Status='Registered'
        ).count()
        
        # Determine new status based on capacity
        if registered_count >= w.MaxCapacity:
            new_status = 'Waitlisted'
            message = 'Added to waitlist'
        else:
            new_status = 'Registered'
            message = 'Signed up successfully'
        
        if existing_registration:
            # Reuse existing cancelled registration
            existing_registration.Status = new_status
            existing_registration.RegisteredAt = db.text("datetime('now')")  # Update timestamp
            action = "Re-registered"
        else:
            # Create new registration
            existing_registration = Registration(
                UserId=user_id, 
                WorkshopId=w_id,
                Status=new_status
            )
            db.session.add(existing_registration)
            action = "Registered"
        
        db.session.commit()
        return jsonify({
            'status': message,
            'action': action,
            'workshop_status': new_status
        })

    @app.route('/cancel/<int:w_id>', methods=['POST'])
    @require_auth
    def cancel(w_id):
        registration = Registration.query.filter_by(
            UserId=request.local_user.UserId, 
            WorkshopId=w_id
        ).filter(Registration.Status.in_(['Registered', 'Waitlisted'])).first_or_404()
        
        old_status = registration.Status
        registration.Status = 'Cancelled'
        db.session.commit()
        
        return jsonify({
            'status': 'Cancelled',
            'previous_status': old_status,
            'cancelled_at': registration.RegisteredAt  # This gets updated when cancelled
        })
    
    @app.route('/registration_status/<int:w_id>', methods=['GET'])
    @require_auth
    def get_registration_status(w_id):
        """Get user's current registration status for a workshop."""
        user_id = request.local_user.UserId
        
        registration = Registration.query.filter_by(
            UserId=user_id,
            WorkshopId=w_id
        ).first()
        
        if not registration:
            return jsonify({
                'registered': False,
                'status': 'Not registered'
            })
        
        return jsonify({
            'registered': True,
            'status': registration.Status,
            'registered_at': registration.RegisteredAt,
            'can_cancel': registration.Status in ['Registered', 'Waitlisted'],
            'can_signup': registration.Status == 'Cancelled'
        })

    @app.route('/vacant/<int:w_id>', methods=['GET'])
    @require_auth
    def vacant(w_id):
        w = Workshop.query.get_or_404(w_id)
        registered_count = Registration.query.filter_by(
            WorkshopId=w_id, 
            Status='Registered'
        ).count()
        vacant = w.MaxCapacity - registered_count
        return jsonify({'vacant': vacant})

    @app.route('/by_skill', methods=['GET'])
    @require_auth
    def by_skill():
        skill_name = request.args.get('skill') or abort(400)
        workshops = Workshop.query.join(WorkshopSkill).join(Skill).filter(Skill.Name == skill_name).all()
        return jsonify([{'id': w.WorkshopId, 'title': w.Title} for w in workshops])

    @app.route('/by_user_skills', methods=['GET'])
    @require_auth
    def by_user_skills():
        user_id = request.local_user.UserId
        
        # Find workshops where user has all required skills
        # Get user's skills
        user_skills = db.session.query(UserSkill.SkillId).filter(UserSkill.UserId == user_id).subquery()
        
        # Get workshops where all required skills are in user's skills
        workshop_ids = db.session.query(Workshop.WorkshopId).outerjoin(
            WorkshopSkill, Workshop.WorkshopId == WorkshopSkill.WorkshopId
        ).outerjoin(
            user_skills, WorkshopSkill.SkillId == user_skills.c.SkillId
        ).group_by(Workshop.WorkshopId).having(
            db.func.count(WorkshopSkill.SkillId) == db.func.count(user_skills.c.SkillId)
        ).subquery()
        
        workshops = Workshop.query.filter(Workshop.WorkshopId.in_(workshop_ids)).all()
        return jsonify([{'id': w.WorkshopId, 'title': w.Title} for w in workshops]) 
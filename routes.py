import os
from datetime import datetime
from urllib.parse import urlencode, urlparse

from flask import Flask, request, jsonify, abort

from auth import require_auth
from models import db, Workshop, Registration, WorkshopSkill, Skill, UserSkill, RegistrationStatus


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
                    'POST /workshops - Create a new workshop',
                    'GET  /workshops - List all workshops',
                    'GET  /workshops/{id} - Get workshop details',
                    'PATCH /workshops/{id} - Edit workshop (leader/admin)',

                    # user registration
                    'POST   /workshops/{id}/register  - Register (sign up) for a workshop',
                    'DELETE /workshops/{id}/register  - Cancel registration',
                    'GET    /workshops/{id}/registration_status  - Get current user registration status'
                ],
                'debug': [
                    'POST /debug/token - Debug JWT token format'
                ]
            }
        })

    #########################  auth
    #########################################################################

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

    #########################  user profile
    #########################################################################

    @app.route('/user/profile', methods=['GET'])
    @require_auth
    def get_user_profile():
        user = request.local_user
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # workshops
        registered_workshop_ids = []
        waitlisted_workshop_ids = []
        for reg in user.registrations:
            if reg.Status == RegistrationStatus.REGISTERED:
                registered_workshop_ids.append(reg.WorkshopId)
            elif reg.Status == RegistrationStatus.WAITLISTED:
                waitlisted_workshop_ids.append(reg.WorkshopId)

        # skills
        skills_data = [
            {
                'id': user_skill.skill.SkillId,
                'name': user_skill.skill.Name,
                'grade': user_skill.Grade
            }
            for user_skill in user.skills
        ]

        return jsonify({
            'UserId': user.UserId,
            'Name': user.Name,
            'Email': user.Email,
            'CreatedDate': user.CreatedDate,
            'AvatarUrl': user.AvatarUrl,
            'workshops': {
                'registered': registered_workshop_ids,
                'waitlisted': waitlisted_workshop_ids
            },
            'skills': skills_data
        })

    #########################  workshops
    #########################################################################

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
                Status=RegistrationStatus.REGISTERED
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
            Status=RegistrationStatus.REGISTERED
        ).count()
        vacant = w.MaxCapacity - registered_count

        return jsonify({
            'id': w.WorkshopId,
            'title': w.Title,
            'description': w.Description,
            'date': w.SessionDate.isoformat(),
            'time': w.StartTime,
            'duration_mins': w.DurationMin,
            'capacity': w.MaxCapacity,
            'vacant': vacant
        })

    @app.route('/workshops', methods=['POST'])
    @require_auth
    def create_workshop():
        """Create new workshop. Requires ADMIN role."""
        user = request.local_user
        if not user.is_admin():
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to create a workshop.'
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Bad Request', 'message': 'No JSON data provided.'}), 400

        # --- Data Validation ---
        required_fields = ['title', 'start_time', 'session_date', 'duration_min', 'capacity']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Bad Request',
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        title = data.get('title')
        description = data.get('description','')  # Optional in model
        session_date_str = data.get('session_date')
        start_time_str = data.get('start_time')
        duration_min = data.get('duration_min')
        capacity = data.get('capacity')

        # Validate
        if not isinstance(title, str) or not title.strip():
            return jsonify({'error': 'Bad Request', 'message': 'Title must be a non-empty string.'}), 400
        if description and not isinstance(description, str):
            return jsonify({'error': 'Bad Request', 'message': 'Description must be a string.'}), 400
        if not isinstance(duration_min, int) or duration_min <= 0:
            return jsonify({'error': 'Bad Request', 'message': 'Duration must be a positive integer.'}), 400
        if not isinstance(capacity, int) or capacity <= 0:
            return jsonify({'error': 'Bad Request', 'message': 'Capacity must be a non-negative integer.'}), 400

        try:
            session_date = datetime.strptime(session_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return jsonify({'error': 'Bad Request', 'message': 'session_date must be in YYYY-MM-DD format.'}), 400
        try:
            datetime.strptime(start_time_str, '%H:%M:%S')
        except (ValueError, TypeError):
            return jsonify({'error': 'Bad Request', 'message': 'start_time must be in HH:MM:SS format.'}), 400

        # --- Create Workshop ---
        new_workshop = Workshop(
            Title=title.strip(),
            Description=description,
            SessionDate=session_date,
            StartTime=start_time_str,
            DurationMin=duration_min,
            MaxCapacity=capacity
        )
        db.session.add(new_workshop)
        db.session.commit()

        return jsonify({
            'message': 'Workshop created successfully.',
            'workshop': {
                'id': new_workshop.WorkshopId,
                'title': new_workshop.Title,
                'description': new_workshop.Description,
                'session_date': new_workshop.SessionDate.isoformat(),
                'start_time': new_workshop.StartTime,
                'duration_min': new_workshop.DurationMin,
                'capacity': new_workshop.MaxCapacity
            }
        }), 201

    @app.route('/workshops/<int:w_id>', methods=['PATCH'])
    @require_auth
    def update_workshop(w_id):
        """Partially update a workshop: title, description, maxCapacity.
        Requires workshop_leader role."""
        workshop = Workshop.query.get_or_404(w_id)
        user = request.local_user

        if not user.can_manage_workshop(w_id):
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to edit this workshop.'
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Bad Request', 'message': 'No data provided.'}), 400

        updated_fields = []

        if 'title' in data:
            if not isinstance(data['title'], str) or not data['title'].strip():
                return jsonify({'error': 'Bad Request', 'message': 'Title must be a non-empty string.'}), 400
            workshop.Title = data['title'].strip()
            updated_fields.append('title')

        if 'description' in data:
            if not isinstance(data.get('description'), str):
                return jsonify({'error': 'Bad Request', 'message': 'Description must be a string.'}), 400
            workshop.Description = data['description']
            updated_fields.append('description')

        if 'capacity' in data:
            curr_capacity = workshop.MaxCapacity
            new_capacity = data['capacity']
            if not isinstance(new_capacity, int) or (new_capacity < 0):
                return jsonify({'error': 'Bad Request', 'message': 'Capacity must be a non-negative integer.'}), 400

            registered_count = _get_registered_count(w_id)

            # case: new capacity < current registrations
            if new_capacity < registered_count:
                diff = registered_count - new_capacity
                canceled_user_ids = _remove_participants_from_workshop(w_id=w_id, num_participants=diff)
                if not canceled_user_ids:
                    return jsonify({
                        'error': 'Internal Server Error',
                        'message': 'New capacity is lower than current registrations. Failed to remove participants.'
                    }), 500

                _update_removed_participants(w_id, canceled_user_ids)

            if new_capacity > curr_capacity:
                _update_waitlisted_participants(w_id)

            workshop.MaxCapacity = new_capacity
            updated_fields.append('capacity')

        if not updated_fields:
            return jsonify({
                'error': 'Bad Request',
                'message': 'No updatable fields provided ("title", "description", "capacity").'
            }), 400

        db.session.commit()

        return jsonify({
            'message': 'Workshop updated successfully.',
            'updated_fields': updated_fields,
            'workshop': {
                'id': workshop.WorkshopId,
                'title': workshop.Title,
                'description': workshop.Description,
                'capacity': workshop.MaxCapacity
            }
        })

    @app.route('/workshops/<int:w_id>/register', methods=['POST'])
    @require_auth
    def register_to_workshop(w_id):
        w = Workshop.query.get_or_404(w_id)
        user_id = request.local_user.UserId

        # Check for any existing registration (any status)
        existing_registration = Registration.query.filter_by(
            UserId=user_id,
            WorkshopId=w_id
        ).first()

        # If user is already registered or waitlisted, prevent duplicate signup
        if existing_registration and existing_registration.Status in [RegistrationStatus.REGISTERED,
                                                                      RegistrationStatus.WAITLISTED]:
            return jsonify({
                'error': 'Already signed up',
                'current_status': existing_registration.Status,
                'registered_at': existing_registration.RegisteredAt
            }), 400

        # Count current active registrations
        registered_count = _get_registered_count(w_id)

        # Determine new status based on capacity
        if registered_count >= w.MaxCapacity:
            new_status = RegistrationStatus.WAITLISTED
            message = 'Added to waitlist'
        else:
            new_status = RegistrationStatus.REGISTERED
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

    @app.route('/workshops/<int:w_id>/register', methods=['DELETE'])
    @require_auth
    def unregister_to_workshop(w_id):
        registration = Registration.query.filter_by(
            UserId=request.local_user.UserId,
            WorkshopId=w_id
        ).filter(Registration.Status.in_([RegistrationStatus.REGISTERED, RegistrationStatus.WAITLISTED])).first_or_404()

        old_status = registration.Status
        registration.Status = RegistrationStatus.CANCELLED
        db.session.commit()

        return jsonify({
            'status': 'Cancelled',
            'previous_status': old_status,
            'cancelled_at': registration.RegisteredAt  # This gets updated when cancelled
        })

    @app.route('/workshops/<int:w_id>/registration_status', methods=['GET'])
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
            'status': registration.Status,
            'is_registered': registration.Status == RegistrationStatus.REGISTERED,
            'registered_at': registration.RegisteredAt
        })

    @app.route('/vacant/<int:w_id>', methods=['GET'])
    @require_auth
    def vacant(w_id):
        w = Workshop.query.get_or_404(w_id)
        registered_count = _get_registered_count(w_id)
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


######## helper functions

def _get_registered_count(w_id):
    """get number of registered users for a workshop"""
    registered_count = Registration.query.filter_by(
        WorkshopId=w_id,
        Status=RegistrationStatus.REGISTERED
    ).count()
    return registered_count


def _remove_participants_from_workshop(w_id, num_participants):
    """remove participants due to capacity limit, lifo.
    returns user_ids of cancelled registrations
    """
    cancelled_registrations = Registration.query.filter_by(
        WorkshopId=w_id,
        Status=RegistrationStatus.REGISTERED
    ).order_by(Registration.RegisteredAt.desc()).limit(num_participants).all()

    for reg in cancelled_registrations:
        reg.Status = RegistrationStatus.CANCELLED

    # note: email is sent to participant in another function
    user_ids = [reg.UserId for reg in cancelled_registrations]

    db.session.commit()

    return user_ids


def _update_waitlisted_participants(w_id):
    """email waitlisted participants of workshop (if any):
      capacity+, can now register"""
    # TODO
    pass


def _update_removed_participants(w_id, canceled_user_ids):
    """email removed participants of workshop:
    capacity-, registration canceled"""
    # TODO
    pass

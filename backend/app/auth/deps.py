from functools import wraps
from flask import request, jsonify
from app.auth.utils import decode_access_token

def get_current_user(f):
    """
    Flask decorator to protect endpoints and inject the current user's payload.
    Other team members (M2, M3, M4, M6) will use this on their routes.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        # Extract the token from the "Bearer <token>" header
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
        if not token:
            return jsonify({
                "success": False, 
                "message": "Token is missing", 
                "error_code": "UNAUTHORIZED"
            }), 401
            
        # Decode the token using M5's existing utility
        payload = decode_access_token(token)
        if not payload:
            return jsonify({
                "success": False, 
                "message": "Invalid or expired token", 
                "error_code": "INVALID_TOKEN"
            }), 401
            
        # Pass the decoded payload to the protected route
        return f(payload, *args, **kwargs)
        
    return decorated
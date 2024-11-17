from functools import wraps
from flask import request, abort, jsonify

roles = {"owner":4,"admin":3,"operator":2,"guest":1}

def role_decorator(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_role = request.cookies.get('role')                
            try:
                if roles[current_role] < roles[required_role]:
                   abort(403)
            except Exception as e:
                   abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator
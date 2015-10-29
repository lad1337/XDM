import traceback
from functools import wraps
from flask import jsonify

def as_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            data = f(*args, **kwargs)
            return jsonify({'data': data})
        except Exception as e:

            tb = traceback.format_exc()

            return jsonify({'errors': [
                {'message': str(e), 'traceback': str(tb)}
            ]})
    return decorated_function

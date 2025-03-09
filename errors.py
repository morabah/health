from flask import render_template, jsonify

class ErrorHandler:
    ERROR_MESSAGES = {
        'login_failed': 'Your email or password is incorrect. Please try again.',
        'user_not_found': 'This account does not exist. Please check your email or register.',
        'invalid_input': 'The information you provided is invalid. Please check and try again.',
        'server_error': 'Something went wrong on our end. Please try again later.',
        'unauthorized': 'You need to be logged in to access this page.',
        'password_mismatch': 'Passwords do not match. Please try again.',
    }
    
    @staticmethod
    def get_message(error_code):
        return ErrorHandler.ERROR_MESSAGES.get(error_code, 'An unknown error occurred')
    
    @staticmethod
    def handle_api_error(error_code, status_code=400, details=None):
        return jsonify({
            'error': error_code,
            'message': ErrorHandler.get_message(error_code),
            'details': details
        }), status_code
    
    @staticmethod
    def handle_web_error(error_code, template='error.html'):
        return render_template(template, 
                              error_message=ErrorHandler.get_message(error_code))

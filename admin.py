from flask import Blueprint, render_template, flash, redirect, url_for
import os
import signal
import sys
import subprocess
from functools import wraps
from flask_login import current_user, login_required

admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type.value != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/restart')
@login_required
@admin_required
def restart_page():
    """Display the restart server page"""
    return render_template('admin/restart.html')

@admin.route('/restart-server', methods=['POST'])
@login_required
@admin_required
def restart_server():
    """Restart the Flask server"""
    try:
        # Get the current process ID
        pid = os.getpid()
        
        # Start a new process that will restart the server
        # This uses a separate Python process to avoid killing the current request
        restart_command = f"""
import os
import time
import signal
import subprocess

# Wait a moment to allow the current request to complete
time.sleep(1)

# Kill the Flask process
try:
    os.kill({pid}, signal.SIGTERM)
except:
    pass

# Start the server again
subprocess.Popen(['python3', 'app.py'], 
                 cwd='{os.getcwd()}', 
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE)
"""
        
        # Execute the restart command in a separate process
        subprocess.Popen([sys.executable, '-c', restart_command],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
        
        flash('Server restart initiated. Please wait a moment...', 'info')
        return redirect(url_for('main.index'))
    except Exception as e:
        flash(f'Error restarting server: {str(e)}', 'danger')
        return redirect(url_for('admin.restart_page'))

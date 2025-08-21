from flask import Blueprint, send_from_directory, current_app
import os

frontend_bp = Blueprint('frontend', __name__)

@frontend_bp.route('/')
def serve_index():
    """Serve the main React app"""
    return send_from_directory(current_app.static_folder, 'index.html')

@frontend_bp.route('/<path:path>')
def serve_static_or_spa(path):
    """Serve static files or fallback to React app for SPA routing"""
    static_file_path = os.path.join(current_app.static_folder, path)
    
    # If it's a static file that exists, serve it
    if os.path.isfile(static_file_path):
        return send_from_directory(current_app.static_folder, path)
    
    # Otherwise, serve the React app (for client-side routing)
    return send_from_directory(current_app.static_folder, 'index.html')


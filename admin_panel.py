from flask import Blueprint, send_from_directory, send_file
import os

admin_panel_bp = Blueprint('admin_panel', __name__)

@admin_panel_bp.route('/admin')
@admin_panel_bp.route('/admin/')
def serve_admin_index():
    """Servir o index.html do painel administrativo"""
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'admin')
    index_path = os.path.join(static_folder, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    else:
        return "Admin panel not found", 404

@admin_panel_bp.route('/admin/<path:path>')
def serve_admin_assets(path):
    """Servir assets do painel administrativo"""
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'admin')
    
    if os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    else:
        # Se o arquivo não existir, retornar o index.html (para SPA routing)
        index_path = os.path.join(static_folder, 'index.html')
        if os.path.exists(index_path):
            return send_file(index_path)
        else:
            return "File not found", 404


import json as _json
from flask import Flask, send_from_directory, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    data_dir = os.environ.get('RENDER_DATA_DIR', os.path.join(app.root_path, '..', 'instance'))
    os.makedirs(data_dir, exist_ok=True)
    
    db_path = os.path.join(data_dir, 'lost_found.db')
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    upload_dir = os.environ.get('UPLOAD_DIR', os.path.join(app.root_path, 'static/uploads'))
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(os.path.join(upload_dir, 'lost'), exist_ok=True)
    os.makedirs(os.path.join(upload_dir, 'found'), exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_dir
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    
    @app.template_filter('from_json')
    def from_json_filter(value):
        if not value:
            return []
        try:
            result = _json.loads(value)
            if isinstance(result, list):
                return result
            return [result]
        except (ValueError, TypeError):
            if isinstance(value, str):
                return [v.strip() for v in value.split(',') if v.strip()]
            return [value] if value else []
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    csrf.init_app(app)
    
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.lost import lost_bp
    from app.routes.found import found_bp
    from app.routes.match import match_bp
    from app.routes.admin import admin_bp
    from app.routes.forum import forum_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(lost_bp, url_prefix='/lost')
    app.register_blueprint(found_bp, url_prefix='/found')
    app.register_blueprint(match_bp, url_prefix='/match')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(forum_bp, url_prefix='/forum')
    
    try:
        from app.routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    except:
        pass
    
    try:
        from app.routes.comment import comment_bp
        app.register_blueprint(comment_bp, url_prefix='/comment')
    except:
        pass
    
    try:
        from app.routes.favorite import favorite_bp
        app.register_blueprint(favorite_bp, url_prefix='/favorite')
    except:
        pass
    
    try:
        from app.routes.report import report_bp
        app.register_blueprint(report_bp, url_prefix='/report')
    except:
        pass
    
    try:
        from app.routes.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
    except:
        pass
    
    try:
        from app.routes.chat import chat_bp
        app.register_blueprint(chat_bp, url_prefix='/chat')
    except:
        pass
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        upload_dir = app.config['UPLOAD_FOLDER']
        file_path = os.path.normpath(os.path.join(upload_dir, filename))
        if not os.path.isfile(file_path):
            file_path = os.path.normpath(os.path.join(app.root_path, 'static', 'uploads', filename))
        if not os.path.isfile(file_path):
            abort(404)
        return send_file(file_path)
    
    return app

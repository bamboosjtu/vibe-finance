from flask import Flask
from config import Config
from database import init_db


def create_app(config_class=Config):
    """Flask 应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化数据库
    init_db()
    
    # 注册蓝图
    from api.v1 import bp as v1_bp
    app.register_blueprint(v1_bp, url_prefix='/api')
    
    return app

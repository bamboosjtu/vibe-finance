from flask import Blueprint

bp = Blueprint('v1', __name__)

# 导入路由模块
from . import health

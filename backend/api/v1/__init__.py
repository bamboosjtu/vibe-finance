from flask import Blueprint

bp = Blueprint('v1', __name__)

# 导入路由模块
from . import health
from . import institutions
from . import accounts
from . import products
from . import snapshots
from . import valuations


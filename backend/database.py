from sqlmodel import create_engine, SQLModel, Session
from config import Config
from models.base import BaseModel
from models.institution import Institution
from models.account import Account
from models.product import Product
from models.lot import Lot


def init_db():
    """初始化数据库"""
    engine = create_engine(Config.DATABASE_URL)
    
    # 创建所有表
    SQLModel.metadata.create_all(engine)
    print("数据库表创建完成")
    
    return engine


def get_session():
    """获取数据库会话"""
    engine = create_engine(Config.DATABASE_URL)
    return Session(engine)

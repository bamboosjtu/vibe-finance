from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy import text
from config import Config
from models.base import BaseModel
from models.institution import Institution
from models.account import Account
from models.product import Product


def _sqlite_column_names(engine, table_name: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
        return {r[1] for r in rows}


def _sqlite_table_info(engine, table_name: str):
    with engine.connect() as conn:
        return conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()


def _sqlite_add_column_if_missing(engine, table_name: str, column_name: str, ddl: str) -> None:
    cols = _sqlite_column_names(engine, table_name)
    if column_name in cols:
        return
    with engine.connect() as conn:
        conn.execute(text(ddl))
        conn.commit()


def _sqlite_migrate_accounts_nullable_institution(engine) -> None:
    info = _sqlite_table_info(engine, 'accounts')
    if not info:
        return

    # PRAGMA table_info columns: cid, name, type, notnull, dflt_value, pk
    institution_row = next((r for r in info if r[1] == 'institution_id'), None)
    if not institution_row:
        return

    institution_notnull = bool(institution_row[3])
    if not institution_notnull:
        return

    cols = {r[1] for r in info}
    currency_expr = 'currency' if 'currency' in cols else "'CNY' AS currency"

    with engine.connect() as conn:
        conn.execute(text('PRAGMA foreign_keys=OFF'))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS accounts__migrated (
                  id INTEGER PRIMARY KEY,
                  created_at TEXT,
                  updated_at TEXT,
                  name TEXT NOT NULL,
                  institution_id INTEGER,
                  type TEXT NOT NULL,
                  currency TEXT NOT NULL DEFAULT 'CNY',
                  is_liquid BOOLEAN NOT NULL DEFAULT 1,
                  FOREIGN KEY(institution_id) REFERENCES institutions(id)
                )
                """
            )
        )

        conn.execute(
            text(
                f"""
                INSERT INTO accounts__migrated (id, created_at, updated_at, name, institution_id, type, currency, is_liquid)
                SELECT id, created_at, updated_at, name, institution_id, type, {currency_expr}, is_liquid
                FROM accounts
                """
            )
        )

        conn.execute(text('DROP TABLE accounts'))
        conn.execute(text('ALTER TABLE accounts__migrated RENAME TO accounts'))
        conn.execute(text('PRAGMA foreign_keys=ON'))
        conn.commit()


def _sqlite_migrate_products_nullable_fields(engine) -> None:
    info = _sqlite_table_info(engine, 'products')
    if not info:
        return

    # PRAGMA table_info columns: cid, name, type, notnull, dflt_value, pk
    notnull_by_name = {r[1]: bool(r[3]) for r in info}

    needs_migration = False
    for col in ['institution_id', 'product_code', 'risk_level', 'term_days', 'note']:
        if notnull_by_name.get(col, False):
            needs_migration = True
            break

    if not needs_migration:
        return

    cols = {r[1] for r in info}
    product_code_expr = 'product_code' if 'product_code' in cols else 'NULL AS product_code'
    risk_level_expr = 'risk_level' if 'risk_level' in cols else 'NULL AS risk_level'
    term_days_expr = 'term_days' if 'term_days' in cols else 'NULL AS term_days'
    note_expr = 'note' if 'note' in cols else 'NULL AS note'
    settle_days_expr = 'settle_days' if 'settle_days' in cols else '1 AS settle_days'

    with engine.connect() as conn:
        conn.execute(text('PRAGMA foreign_keys=OFF'))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS products__migrated (
                  id INTEGER PRIMARY KEY,
                  created_at TEXT,
                  updated_at TEXT,
                  name TEXT NOT NULL,
                  institution_id INTEGER,
                  product_code TEXT,
                  product_type TEXT NOT NULL,
                  risk_level TEXT,
                  term_days INTEGER,
                  liquidity_rule TEXT NOT NULL,
                  settle_days INTEGER NOT NULL DEFAULT 1,
                  note TEXT,
                  FOREIGN KEY(institution_id) REFERENCES institutions(id)
                )
                """
            )
        )

        conn.execute(
            text(
                f"""
                INSERT INTO products__migrated (
                  id, created_at, updated_at, name, institution_id, product_code, product_type,
                  risk_level, term_days, liquidity_rule, settle_days, note
                )
                SELECT
                  id, created_at, updated_at, name, institution_id, {product_code_expr}, product_type,
                  {risk_level_expr}, {term_days_expr}, liquidity_rule, {settle_days_expr}, {note_expr}
                FROM products
                """
            )
        )

        conn.execute(text('DROP TABLE products'))
        conn.execute(text('ALTER TABLE products__migrated RENAME TO products'))
        conn.execute(text('PRAGMA foreign_keys=ON'))
        conn.commit()


def init_db():
    """初始化数据库"""
    engine = create_engine(Config.DATABASE_URL)
    
    # 创建所有表
    SQLModel.metadata.create_all(engine)

    if engine.dialect.name == 'sqlite':
        _sqlite_migrate_accounts_nullable_institution(engine)
        _sqlite_migrate_products_nullable_fields(engine)
        _sqlite_add_column_if_missing(
            engine,
            table_name='accounts',
            column_name='currency',
            ddl="ALTER TABLE accounts ADD COLUMN currency TEXT DEFAULT 'CNY'",
        )
        _sqlite_add_column_if_missing(
            engine,
            table_name='products',
            column_name='product_code',
            ddl="ALTER TABLE products ADD COLUMN product_code TEXT",
        )

    print("数据库表创建完成")
    
    return engine


def get_session():
    """获取数据库会话"""
    engine = create_engine(Config.DATABASE_URL)
    return Session(engine)

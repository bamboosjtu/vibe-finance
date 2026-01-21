from sqlmodel import Session, select, create_engine
from models.account import Account
from models.snapshot import Snapshot

# 连接数据库
engine = create_engine("sqlite:///db/construction.db")

with Session(engine) as session:
    # 查询 Accounts
    accounts = session.exec(select(Account)).all()
    print(f"Accounts count: {len(accounts)}")
    for acc in accounts:
        print(f" - ID: {acc.id}, Name: {acc.name}, Type: {acc.type}")

    # 查询 Snapshots
    snapshots = session.exec(select(Snapshot)).all()
    print(f"Snapshots count: {len(snapshots)}")
    for snap in snapshots:
        print(f" - Date: {snap.date}, AccountID: {snap.account_id}, Balance: {snap.balance}")

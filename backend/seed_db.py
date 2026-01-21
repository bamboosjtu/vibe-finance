from sqlmodel import Session
from database import get_session, init_db
from models.institution import Institution
from models.account import Account, AccountType
from models.snapshot import Snapshot
from datetime import date

def seed_data():
    # Ensure tables exist
    init_db()
    
    session = get_session()
    
    # 1. Create Institutions
    inst_cmb = Institution(name="招商银行")
    inst_alipay = Institution(name="支付宝")
    inst_ibkr = Institution(name="Interactive Brokers")
    
    session.add(inst_cmb)
    session.add(inst_alipay)
    session.add(inst_ibkr)
    session.commit()
    
    session.refresh(inst_cmb)
    session.refresh(inst_alipay)
    session.refresh(inst_ibkr)
    
    print(f"Created Institutions: {inst_cmb.id}, {inst_alipay.id}, {inst_ibkr.id}")
    
    # 2. Create Accounts
    acc_cmb_checking = Account(
        name="招行一卡通",
        institution_id=inst_cmb.id,
        type=AccountType.DEBIT,
        currency="CNY",
        is_liquid=True
    )
    
    acc_alipay_yuebao = Account(
        name="余额宝",
        institution_id=inst_alipay.id,
        type=AccountType.CASH, # Or INVESTMENT_CASH
        currency="CNY",
        is_liquid=True
    )
    
    acc_ibkr_usd = Account(
        name="IBKR USD",
        institution_id=inst_ibkr.id,
        type=AccountType.INVESTMENT_CASH,
        currency="USD",
        is_liquid=True
    )
    
    acc_cmb_credit = Account(
        name="招行信用卡",
        institution_id=inst_cmb.id,
        type=AccountType.CREDIT,
        currency="CNY",
        is_liquid=True
    )
    
    session.add(acc_cmb_checking)
    session.add(acc_alipay_yuebao)
    session.add(acc_ibkr_usd)
    session.add(acc_cmb_credit)
    session.commit()
    
    session.refresh(acc_cmb_checking)
    session.refresh(acc_alipay_yuebao)
    session.refresh(acc_ibkr_usd)
    session.refresh(acc_cmb_credit)
    
    print(f"Created Accounts: {acc_cmb_checking.id}, {acc_alipay_yuebao.id}, {acc_ibkr_usd.id}, {acc_cmb_credit.id}")

    # 3. Create some Snapshots for today
    today = date.today()
    
    snap1 = Snapshot(date=today, account_id=acc_cmb_checking.id, balance=50000.0)
    snap2 = Snapshot(date=today, account_id=acc_alipay_yuebao.id, balance=12345.67)
    snap3 = Snapshot(date=today, account_id=acc_ibkr_usd.id, balance=10000.0) # USD handled as raw value for now
    snap4 = Snapshot(date=today, account_id=acc_cmb_credit.id, balance=-2500.0)
    
    session.add(snap1)
    session.add(snap2)
    session.add(snap3)
    session.add(snap4)
    session.commit()
    
    print("Created Snapshots for today")
    
    session.close()

if __name__ == "__main__":
    seed_data()

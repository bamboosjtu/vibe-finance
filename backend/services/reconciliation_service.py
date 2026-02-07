"""
对账服务 - Sprint 6
提供账户对账、赎回一致性检查、估值断档检测等功能
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from sqlmodel import Session, select, func

from models.snapshot import Snapshot
from models.transaction import Transaction, TransactionCategory
from models.product import Product
from models.valuation import ProductValuation
from models.account import Account
from models.warning import ReconciliationWarningRecord, WarningStatus


class AccountDiffItem:
    """账户对账差异项"""
    def __init__(
        self,
        account_id: int,
        account_name: str,
        check_date: date,
        snapshot_balance: float,
        derived_balance: float,
        diff: float,
        severity: str,  # 'info' | 'warn'
        hint: str
    ):
        self.account_id = account_id
        self.account_name = account_name
        self.check_date = check_date
        self.snapshot_balance = snapshot_balance
        self.derived_balance = derived_balance
        self.diff = diff
        self.severity = severity
        self.hint = hint

    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "check_date": self.check_date.isoformat(),
            "snapshot_balance": self.snapshot_balance,
            "derived_balance": self.derived_balance,
            "diff": self.diff,
            "severity": self.severity,
            "hint": self.hint
        }


class RedeemCheckItem:
    """赎回检查项"""
    def __init__(
        self,
        product_id: int,
        product_name: str,
        pending_amount: float,
        status: str,  # 'normal' | 'negative' | 'overdue'
        latest_request_date: Optional[date],
        expected_settle_date: Optional[date],
        days_pending: Optional[int],
        hint: str
    ):
        self.product_id = product_id
        self.product_name = product_name
        self.pending_amount = pending_amount
        self.status = status
        self.latest_request_date = latest_request_date
        self.expected_settle_date = expected_settle_date
        self.days_pending = days_pending
        self.hint = hint

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "pending_amount": self.pending_amount,
            "status": self.status,
            "latest_request_date": self.latest_request_date.isoformat() if self.latest_request_date else None,
            "expected_settle_date": self.expected_settle_date.isoformat() if self.expected_settle_date else None,
            "days_pending": self.days_pending,
            "hint": self.hint
        }


class ValuationGapItem:
    """估值断档项"""
    def __init__(
        self,
        product_id: int,
        product_name: str,
        last_valuation_date: Optional[date],
        days_since: int,
        has_recent_trade: bool,
        severity: str,  # 'info' | 'warn'
        hint: str,
        last_trade_date: Optional[date] = None,  # Sprint 6 可选：最近一次交易日期
        days_since_trade: Optional[int] = None   # Sprint 6 可选：距离上次交易的天数
    ):
        self.product_id = product_id
        self.product_name = product_name
        self.last_valuation_date = last_valuation_date
        self.days_since = days_since
        self.has_recent_trade = has_recent_trade
        self.severity = severity
        self.hint = hint
        self.last_trade_date = last_trade_date
        self.days_since_trade = days_since_trade

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "last_valuation_date": self.last_valuation_date.isoformat() if self.last_valuation_date else None,
            "days_since": self.days_since,
            "has_recent_trade": self.has_recent_trade,
            "severity": self.severity,
            "hint": self.hint,
            "last_trade_date": self.last_trade_date.isoformat() if self.last_trade_date else None,
            "days_since_trade": self.days_since_trade
        }


class ReconciliationWarning:
    """统一对账警告"""
    def __init__(
        self,
        id: str,
        level: str,  # 'info' | 'warn'
        type: str,   # 'account_diff' | 'redeem_anomaly' | 'valuation_gap'
        title: str,
        description: str,
        object_type: str,  # 'account' | 'product'
        object_id: int,
        object_name: str,
        date: Optional[date],
        diff_value: Optional[float],
        suggested_action: str,
        link_to: str,
        status: str = 'open',  # 'open' | 'acknowledged' | 'muted'
        mute_reason: Optional[str] = None
    ):
        self.id = id
        self.level = level
        self.type = type
        self.title = title
        self.description = description
        self.object_type = object_type
        self.object_id = object_id
        self.object_name = object_name
        self.date = date
        self.diff_value = diff_value
        self.suggested_action = suggested_action
        self.link_to = link_to
        self.status = status
        self.mute_reason = mute_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "level": self.level,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "object_name": self.object_name,
            "date": self.date.isoformat() if self.date else None,
            "diff_value": self.diff_value,
            "suggested_action": self.suggested_action,
            "link_to": self.link_to,
            "status": self.status,
            "mute_reason": self.mute_reason
        }


def calculate_account_derived_balance(
    session: Session,
    account_id: int,
    target_date: date
) -> float:
    """
    计算账户的推导余额（基于 Transaction 现金流累计）
    
    逻辑：
    - 找到 target_date 之前最新的 Snapshot 作为期初
    - 累计从期初日期+1 到 target_date 的所有现金流
    """
    # 1. 找到期初 Snapshot（target_date 之前最新的）
    opening_snapshot = session.exec(
        select(Snapshot)
        .where(Snapshot.account_id == account_id)
        .where(Snapshot.date <= target_date)
        .order_by(Snapshot.date.desc())
        .limit(1)
    ).first()

    if not opening_snapshot:
        # 没有期初快照，无法计算
        return 0.0

    opening_balance = float(opening_snapshot.balance)
    opening_date = opening_snapshot.date

    # 2. 如果 target_date 就是 opening_date，直接返回
    if opening_date == target_date:
        return opening_balance

    # 3. 累计 (opening_date, target_date] 期间的现金流
    # 影响账户余额的交易类型：
    # - transfer_in: +amount
    # - transfer_out: -amount
    # - income: +amount
    # - expense: -amount
    # - buy: -amount（从账户扣款）
    # - redeem_settle: +amount（到账）
    # - fee: -amount

    transactions = session.exec(
        select(Transaction)
        .where(Transaction.account_id == account_id)
        .where(Transaction.settle_date > opening_date)
        .where(Transaction.settle_date <= target_date)
    ).all()

    cash_flow = 0.0
    for tx in transactions:
        amount = float(tx.amount)
        if tx.category in [
            TransactionCategory.TRANSFER_IN,
            TransactionCategory.INCOME,
            TransactionCategory.REDEEM_SETTLE
        ]:
            cash_flow += amount
        elif tx.category in [
            TransactionCategory.TRANSFER_OUT,
            TransactionCategory.EXPENSE,
            TransactionCategory.BUY,
            TransactionCategory.FEE
        ]:
            cash_flow -= amount
        # redeem_request 不影响账户余额（只是申请）

    return opening_balance + cash_flow


def check_account_diffs(
    session: Session,
    target_date: Optional[date] = None,
    threshold: float = 1.0
) -> List[AccountDiffItem]:
    """
    检查账户对账差异（S6-2）
    
    Args:
        target_date: 检查日期，默认今天
        threshold: 差异阈值，默认 1 元
    """
    if target_date is None:
        target_date = date.today()

    results = []

    # 获取所有账户
    accounts = session.exec(select(Account)).all()

    for account in accounts:
        # 获取 target_date 的 Snapshot
        snapshot = session.exec(
            select(Snapshot)
            .where(Snapshot.account_id == account.id)
            .where(Snapshot.date == target_date)
        ).first()

        if not snapshot:
            # 该日期没有快照，跳过（或生成缺失提示）
            continue

        # 计算推导余额
        derived = calculate_account_derived_balance(session, account.id, target_date)
        snapshot_balance = float(snapshot.balance)
        diff = snapshot_balance - derived

        # 判断差异
        if abs(diff) > threshold:
            severity = 'warn'
            hint = _generate_account_diff_hint(diff)
        else:
            severity = 'info'
            hint = "余额一致"

        results.append(AccountDiffItem(
            account_id=account.id,
            account_name=account.name,
            check_date=target_date,
            snapshot_balance=snapshot_balance,
            derived_balance=derived,
            diff=diff,
            severity=severity,
            hint=hint
        ))

    return results


def _generate_account_diff_hint(diff: float) -> str:
    """生成账户差异提示"""
    if diff > 0:
        return f"Snapshot 余额比推导多 {diff:.2f}，可能原因：漏录支出/买入交易、交易 settle_date 填错、或 Snapshot 录错"
    else:
        return f"Snapshot 余额比推导少 {abs(diff):.2f}，可能原因：漏录收入/赎回到账交易、交易 settle_date 填错、或 Snapshot 录错"


def check_redeem_consistency(
    session: Session,
    buffer_days: int = 3
) -> List[RedeemCheckItem]:
    """
    检查赎回在途一致性（S6-3）
    
    Args:
        buffer_days: 缓冲天数，默认 3 天
    """
    results = []
    today = date.today()

    # 获取所有产品
    products = session.exec(select(Product)).all()

    for product in products:
        # 计算在途金额
        requests = session.exec(
            select(Transaction)
            .where(Transaction.product_id == product.id)
            .where(Transaction.category == TransactionCategory.REDEEM_REQUEST)
        ).all()

        settles = session.exec(
            select(Transaction)
            .where(Transaction.product_id == product.id)
            .where(Transaction.category == TransactionCategory.REDEEM_SETTLE)
        ).all()

        total_request = sum(float(r.amount) for r in requests)
        total_settle = sum(float(s.amount) for s in settles)
        pending = total_request - total_settle

        # 获取最新申请日期
        latest_request = max(
            (r.trade_date for r in requests),
            default=None
        )

        # 判断状态
        if pending < -0.01:  # 允许小数误差
            status = 'negative'
            hint = f"到账金额({total_settle:.2f})大于申请金额({total_request:.2f})，请检查 redeem_settle 是否录错"
            expected_settle = None
            days_pending = None
        elif pending > 0.01:
            # 检查是否长期未结
            if latest_request:
                expected_settle = latest_request + timedelta(days=product.settle_days)
                days_pending = (today - latest_request).days
                overdue_threshold = product.settle_days + buffer_days

                if days_pending > overdue_threshold:
                    status = 'overdue'
                    hint = f"赎回申请已 {days_pending} 天未到账，超过 T+{product.settle_days} 预期到账时间，可能漏记到账或规则不同"
                else:
                    status = 'normal'
                    hint = f"在途赎回正常，预计 {expected_settle.isoformat()} 前到账"
            else:
                status = 'normal'
                hint = "在途赎回正常"
                expected_settle = None
                days_pending = None
        else:
            # pending ≈ 0，无在途
            continue

        results.append(RedeemCheckItem(
            product_id=product.id,
            product_name=product.name,
            pending_amount=pending,
            status=status,
            latest_request_date=latest_request,
            expected_settle_date=expected_settle,
            days_pending=days_pending,
            hint=hint
        ))

    return results


def check_valuation_gaps(
    session: Session,
    gap_threshold_days: int = 14
) -> List[ValuationGapItem]:
    """
    检查估值断档（S6-4）
    
    Args:
        gap_threshold_days: 断档阈值天数，默认 14 天
    """
    results = []
    today = date.today()

    # 获取所有产品
    products = session.exec(select(Product)).all()

    for product in products:
        # 获取最新估值日期
        latest_valuation = session.exec(
            select(ProductValuation)
            .where(ProductValuation.product_id == product.id)
            .order_by(ProductValuation.date.desc())
            .limit(1)
        ).first()

        # Sprint 6 可选：获取最近一次交易日期（用于提示优先级）
        latest_trade = session.exec(
            select(Transaction)
            .where(Transaction.product_id == product.id)
            .where(Transaction.category.in_([
                TransactionCategory.BUY,
                TransactionCategory.REDEEM_REQUEST,
                TransactionCategory.REDEEM_SETTLE
            ]))
            .order_by(Transaction.trade_date.desc())
            .limit(1)
        ).first()
        
        last_trade_date = latest_trade.trade_date if latest_trade else None
        days_since_trade = (today - last_trade_date).days if last_trade_date else None

        if not latest_valuation:
            # 从未录过估值
            days_since = 9999
            last_date = None
            severity = 'warn'
            if last_trade_date:
                hint = f"该产品从未录入估值，但最近 {days_since_trade} 天前有交易发生，请尽快补录"
            else:
                hint = "该产品从未录入估值，请尽快补录"
        else:
            last_date = latest_valuation.date
            days_since = (today - last_date).days

            if days_since <= gap_threshold_days:
                # 未超过阈值，正常
                continue

            # 判断是否期间有交易
            recent_trades = session.exec(
                select(Transaction)
                .where(Transaction.product_id == product.id)
                .where(Transaction.trade_date > last_date)
                .where(Transaction.trade_date <= today)
                .where(Transaction.category.in_([
                    TransactionCategory.BUY,
                    TransactionCategory.REDEEM_REQUEST,
                    TransactionCategory.REDEEM_SETTLE
                ]))
            ).all()

            has_recent_trade = len(recent_trades) > 0

            # Sprint 6 可选：根据最近一次交易日期提升提示优先级
            if has_recent_trade:
                severity = 'warn'
                if last_trade_date and days_since_trade is not None:
                    hint = f"已 {days_since} 天未录估值，最近交易发生在 {days_since_trade} 天前，建议尽快补录以保持数据连续性"
                else:
                    hint = f"已 {days_since} 天未录估值，且期间有交易发生，建议尽快补录以保持数据连续性"
            else:
                severity = 'info'
                hint = f"已 {days_since} 天未录估值，期间无交易，建议补录"

        results.append(ValuationGapItem(
            product_id=product.id,
            product_name=product.name,
            last_valuation_date=last_date,
            days_since=days_since,
            has_recent_trade=has_recent_trade if latest_valuation else False,
            severity=severity,
            hint=hint,
            last_trade_date=last_trade_date,
            days_since_trade=days_since_trade
        ))

    return results


def get_all_warnings(
    session: Session,
    target_date: Optional[date] = None,
    account_diff_threshold: float = 1.0,
    valuation_gap_days: int = 14,
    redeem_buffer_days: int = 3
) -> List[ReconciliationWarning]:
    """
    获取所有对账警告（聚合接口）
    """
    warnings = []

    # 1. 账户对账差异
    account_diffs = check_account_diffs(session, target_date, account_diff_threshold)
    for diff in account_diffs:
        if diff.severity == 'warn':
            warnings.append(ReconciliationWarning(
                id=f"account_diff_{diff.account_id}_{diff.check_date}",
                level='warn',
                type='account_diff',
                title=f"账户 [{diff.account_name}] 余额不一致",
                description=diff.hint,
                object_type='account',
                object_id=diff.account_id,
                object_name=diff.account_name,
                date=diff.check_date,
                diff_value=diff.diff,
                suggested_action="核对 Snapshot 与交易记录",
                link_to=f"/master/snapshots?date={diff.check_date.isoformat()}"
            ))

    # 2. 赎回异常
    redeem_checks = check_redeem_consistency(session, redeem_buffer_days)
    for check in redeem_checks:
        if check.status in ['negative', 'overdue']:
            warnings.append(ReconciliationWarning(
                id=f"redeem_{check.product_id}_{check.status}",
                level='warn',
                type='redeem_anomaly',
                title=f"产品 [{check.product_name}] 赎回异常",
                description=check.hint,
                object_type='product',
                object_id=check.product_id,
                object_name=check.product_name,
                date=check.latest_request_date,
                diff_value=check.pending_amount,
                suggested_action="核对赎回申请与到账记录",
                link_to=f"/master/products/{check.product_id}"
            ))

    # 3. 估值断档
    valuation_gaps = check_valuation_gaps(session, valuation_gap_days)
    for gap in valuation_gaps:
        warnings.append(ReconciliationWarning(
            id=f"valuation_gap_{gap.product_id}",
            level=gap.severity,
            type='valuation_gap',
            title=f"产品 [{gap.product_name}] 估值断档",
            description=gap.hint,
            object_type='product',
            object_id=gap.product_id,
            object_name=gap.product_name,
            date=gap.last_valuation_date,
            diff_value=None,
            suggested_action="补录产品估值",
            link_to=f"/master/products/{gap.product_id}"
        ))

    # 查询数据库中的状态记录
    warning_ids = [w.id for w in warnings]
    status_records = session.exec(
        select(ReconciliationWarningRecord)
        .where(ReconciliationWarningRecord.warning_id.in_(warning_ids))
    ).all()
    
    # 构建状态映射
    status_map = {r.warning_id: r for r in status_records}
    
    # 应用状态到警告
    for warning in warnings:
        if warning.id in status_map:
            record = status_map[warning.id]
            warning.status = record.status
            warning.mute_reason = record.mute_reason
    
    # 按级别排序（warn 在前）
    warnings.sort(key=lambda w: (0 if w.level == 'warn' else 1, w.object_name))

    return warnings


def update_warning_status(
    session: Session,
    warning_id: str,
    status: str,
    mute_reason: Optional[str] = None
) -> ReconciliationWarningRecord:
    """
    更新警告状态（S6-5）
    
    Args:
        session: 数据库会话
        warning_id: 警告ID
        status: 新状态 (open/acknowledged/muted)
        mute_reason: 静音原因（当 status=muted 时）
    
    Returns:
        更新后的记录
    """
    from datetime import datetime
    
    # 查找现有记录
    record = session.exec(
        select(ReconciliationWarningRecord)
        .where(ReconciliationWarningRecord.warning_id == warning_id)
    ).first()
    
    if record:
        # 更新现有记录
        record.status = status
        if status == WarningStatus.MUTED:
            record.mute_reason = mute_reason
        else:
            record.mute_reason = None
        record.updated_at = datetime.utcnow()
    else:
        # 创建新记录
        record = ReconciliationWarningRecord(
            warning_id=warning_id,
            warning_type=warning_id.split('_')[0] if '_' in warning_id else 'unknown',
            object_type='unknown',  # 会在后续查询中更新
            object_id=0,
            status=status,
            mute_reason=mute_reason if status == WarningStatus.MUTED else None
        )
        session.add(record)
    
    session.commit()
    session.refresh(record)
    return record


def get_warning_status(
    session: Session,
    warning_id: str
) -> Optional[ReconciliationWarningRecord]:
    """
    获取警告状态记录
    
    Args:
        session: 数据库会话
        warning_id: 警告ID
    
    Returns:
        状态记录，如果不存在返回 None
    """
    return session.exec(
        select(ReconciliationWarningRecord)
        .where(ReconciliationWarningRecord.warning_id == warning_id)
    ).first()


def restore_warning_to_open(
    session: Session,
    warning_id: str
) -> Optional[ReconciliationWarningRecord]:
    """
    将警告恢复为 open 状态
    
    Args:
        session: 数据库会话
        warning_id: 警告ID
    
    Returns:
        更新后的记录，如果不存在返回 None
    """
    record = session.exec(
        select(ReconciliationWarningRecord)
        .where(ReconciliationWarningRecord.warning_id == warning_id)
    ).first()
    
    if record:
        from datetime import datetime
        record.status = WarningStatus.OPEN
        record.mute_reason = None
        record.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(record)
    
    return record

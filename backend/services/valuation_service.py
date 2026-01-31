from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from sqlmodel import Session, select, delete
from sqlalchemy.dialects.sqlite import insert

from models.valuation import ProductValuation


def delete_valuation(session: Session, product_id: int, valuation_date: date) -> bool:
    """
    删除指定产品在指定日期的估值
    """
    statement = delete(ProductValuation).where(
        ProductValuation.product_id == product_id,
        ProductValuation.date == valuation_date
    )
    result = session.exec(statement)
    session.commit()
    return result.rowcount > 0


def batch_upsert_valuations(session: Session, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    批量插入或更新产品估值数据
    """
    if not rows:
        return {"inserted": 0, "updated": 0, "warnings": []}

    # 预处理数据
    data_to_insert = []
    for row in rows:
        # 确保 date 是 date 对象
        d = row['date']
        if isinstance(d, str):
            d = date.fromisoformat(d)
        
        # 确保 market_value 是 float
        mv = row['market_value']
        if isinstance(mv, str):
            mv = float(mv)
            
        data_to_insert.append({
            "product_id": row['product_id'],
            "date": d,
            "market_value": mv
        })

    # 使用 SQLite 的 ON CONFLICT DO UPDATE
    stmt = insert(ProductValuation.__table__).values(data_to_insert)
    
    stmt = stmt.on_conflict_do_update(
        index_elements=['product_id', 'date'],
        set_={"market_value": stmt.excluded.market_value}
    )
    
    result = session.exec(stmt)
    session.commit()
    
    total_rows = len(rows)
    return {"inserted": total_rows, "updated": 0, "warnings": []}


def list_valuations(session: Session, product_id: int, start_date: date, end_date: date) -> List[ProductValuation]:
    """
    查询指定产品在日期范围内的估值
    """
    statement = select(ProductValuation).where(
        ProductValuation.product_id == product_id,
        ProductValuation.date >= start_date,
        ProductValuation.date <= end_date
    ).order_by(ProductValuation.date)
    
    return session.exec(statement).all()


def get_valuation_series(
    session: Session,
    product_id: int,
    start_date: date,
    end_date: date,
    interpolate: bool = True
) -> List[Dict[str, Any]]:
    """
    获取连续的估值序列，支持插值
    只在两个 manual 点之间插值，之外使用外推（extrapolated）
    返回格式: [{"date": date, "value": float, "source": "manual"|"interpolated"|"extrapolated"}, ...]
    - manual: 用户录入的真实估值点
    - interpolated: 在两个 manual 点之间线性插值
    - extrapolated: 在最后一个 manual 点之后外推（保持最后一个值）
    """
    # 1. 获取范围内的所有 manual 点
    raw_points = list_valuations(session, product_id, start_date, end_date)
    
    if not interpolate:
        return [{"date": p.date, "value": p.market_value, "source": "manual"} for p in raw_points]
    
    # 2. 如果没有 manual 点，返回空
    if not raw_points:
        return []
        
    # 3. 只在 manual 点之间插值，之外断线
    # 获取范围前的最近一个点（用于插值边界）
    prev_point = session.exec(
        select(ProductValuation)
        .where(ProductValuation.product_id == product_id, ProductValuation.date < start_date)
        .order_by(ProductValuation.date.desc())
        .limit(1)
    ).first()
    
    # 获取范围后的最近一个点（用于插值边界）
    next_point = session.exec(
        select(ProductValuation)
        .where(ProductValuation.product_id == product_id, ProductValuation.date > end_date)
        .order_by(ProductValuation.date.asc())
        .limit(1)
    ).first()
    
    # 构建完整的 manual 点列表（包含边界点）
    all_manual_points = []
    if prev_point:
        all_manual_points.append(prev_point)
    all_manual_points.extend(raw_points)
    if next_point:
        all_manual_points.append(next_point)
    
    # 4. 只在相邻 manual 点之间插值
    result = []
    
    # 处理只有一个点的情况
    if len(all_manual_points) == 1:
        single_point = all_manual_points[0]
        if start_date <= single_point.date <= end_date:
            result.append({
                "date": single_point.date,
                "value": float(single_point.market_value),
                "source": "manual"
            })
        # 外推到 end_date（使用 extrapolated 标记）
        if single_point.date < end_date:
            curr = single_point.date + timedelta(days=1)
            while curr <= end_date:
                result.append({
                    "date": curr,
                    "value": float(single_point.market_value),
                    "source": "extrapolated"
                })
                curr += timedelta(days=1)
        return result
    
    for i in range(len(all_manual_points) - 1):
        left_point = all_manual_points[i]
        right_point = all_manual_points[i + 1]
        
        # 确定当前区间的有效范围（与请求范围交集）
        interval_start = max(left_point.date, start_date)
        interval_end = min(right_point.date, end_date)
        
        if interval_start > interval_end:
            continue
        
        # 生成区间内的所有日期
        curr = interval_start
        while curr <= interval_end:
            if curr == left_point.date:
                # manual 点 - 只在范围内添加（避免与上一个区间的right_point重复）
                if curr >= start_date:
                    result.append({
                        "date": curr,
                        "value": float(left_point.market_value),
                        "source": "manual"
                    })
            elif curr == right_point.date:
                # manual 点 - 只在范围内添加
                # 如果是最后一个区间，需要添加right_point；否则跳过（会在下一个区间作为left_point添加）
                is_last_interval = (i == len(all_manual_points) - 2)
                if curr <= end_date and curr >= start_date and is_last_interval:
                    result.append({
                        "date": curr,
                        "value": float(right_point.market_value),
                        "source": "manual"
                    })
            else:
                # 插值点
                total_days = (right_point.date - left_point.date).days
                curr_days = (curr - left_point.date).days
                
                left_val = float(left_point.market_value)
                right_val = float(right_point.market_value)
                val = left_val + (right_val - left_val) * (curr_days / total_days)
                result.append({
                    "date": curr,
                    "value": val,
                    "source": "interpolated"
                })
            
            curr += timedelta(days=1)
    
    # 5. 最后一个 manual 点之后到 end_date 进行外推（extrapolated）
    last_manual_point = all_manual_points[-1]
    if last_manual_point.date < end_date:
        # 使用0斜率外推：保持最后一个manual点的值
        # 明确标记为 extrapolated，与 interpolated 区分，避免误导
        curr = last_manual_point.date + timedelta(days=1)
        while curr <= end_date:
            result.append({
                "date": curr,
                "value": float(last_manual_point.market_value),
                "source": "extrapolated"
            })
            curr += timedelta(days=1)

    return result

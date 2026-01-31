from typing import List, Dict, Any, Optional
from datetime import date
import math

def calculate_metrics(series: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
    """
    计算收益与风险指标
    """
    if len(series) < 2:
        return None
        
    values = [p['value'] for p in series]
    dates = [p['date'] for p in series]
    
    # 1. TWR (累计收益率)
    start_val = values[0]
    end_val = values[-1]
    if start_val == 0:
        return None
    twr = (end_val / start_val) - 1
    
    # 2. Annualized (年化收益率)
    days_total = (dates[-1] - dates[0]).days
    if days_total > 0:
        # (1 + r)^(365/d) - 1
        # 防止负数底数（虽然市值通常为正）
        if end_val / start_val > 0:
            annualized = (end_val / start_val) ** (365 / days_total) - 1
        else:
            annualized = -1.0 # 亏光了
    else:
        annualized = 0.0
        
    # 3. Volatility (年化波动率)
    # 计算日收益率序列
    returns = []
    for i in range(1, len(values)):
        v_prev = values[i-1]
        v_curr = values[i]
        if v_prev > 0:
            r = (v_curr / v_prev) - 1
            returns.append(r)
        else:
            returns.append(0.0)
            
    if len(returns) > 1:
        mean_r = sum(returns) / len(returns)
        variance = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance)
        volatility = std_dev * math.sqrt(365)
    else:
        volatility = 0.0
        
    # 4. Max Drawdown (最大回撤) & Recovery Days
    max_dd = 0.0
    recovery_days = 0
    
    current_peak_val = values[0]
    current_peak_date = dates[0]
    
    # 记录最大回撤时的信息
    worst_dd_val = 0.0
    worst_peak_date = dates[0]
    
    for i, val in enumerate(values):
        date = dates[i]
        if val > current_peak_val:
            current_peak_val = val
            current_peak_date = date
        else:
            dd = 1.0 - (val / current_peak_val)
            if dd > max_dd:
                max_dd = dd
                worst_peak_date = current_peak_date
                
    # 5. Recovery Days (针对最大回撤)
    # 寻找从 worst_peak_date 开始，第一次回到 peak_val 的时间
    if max_dd > 0:
        # 找到 worst_peak_date 对应的 value
        peak_val = 0
        start_search_idx = 0
        for i, d in enumerate(dates):
            if d == worst_peak_date:
                peak_val = values[i]
                start_search_idx = i
                break
        
        recover_date = None
        for i in range(start_search_idx + 1, len(values)):
            if values[i] >= peak_val:
                recover_date = dates[i]
                break
                
        if recover_date:
            recovery_days = (recover_date - worst_peak_date).days
        else:
            # 尚未修复，使用当前天数作为下限
            recovery_days = (dates[-1] - worst_peak_date).days
            
    return {
        "twr": twr * 100,  # 转换为百分比
        "annualized": annualized * 100,  # 转换为百分比
        "volatility": volatility * 100,  # 转换为百分比
        "max_drawdown": max_dd * 100,  # 转换为百分比
        "drawdown_recovery_days": recovery_days
    }

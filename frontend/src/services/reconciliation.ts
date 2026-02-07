import { apiGet, apiPut, apiPost } from './api';

// Sprint 6: 统一对账警告类型
export interface ReconciliationWarning {
  id: string;
  level: 'warn' | 'info';
  type: 'account_diff' | 'redeem_anomaly' | 'valuation_gap';
  title: string;
  description: string;
  object_type: 'account' | 'product';
  object_id: number;
  object_name: string;
  date: string | null;
  diff_value: number | null;
  suggested_action: string;
  link_to: string;
  status: 'open' | 'acknowledged' | 'muted';
  mute_reason: string | null;
}

// S6-5: 警告状态更新响应
export interface WarningStatusResp {
  id: number;
  warning_id: string;
  status: 'open' | 'acknowledged' | 'muted';
  mute_reason: string | null;
  updated_at: string;
}

export interface ReconciliationSummary {
  total: number;
  warn: number;
  info: number;
}

export interface ReconciliationWarningsResp {
  items: ReconciliationWarning[];
  summary: ReconciliationSummary;
}

// 账户对账差异
export interface AccountDiffItem {
  account_id: number;
  account_name: string;
  check_date: string;
  snapshot_balance: number;
  derived_balance: number;
  diff: number;
  severity: 'info' | 'warn';
  hint: string;
}

export interface AccountDiffsResp {
  items: AccountDiffItem[];
  check_date: string;
  threshold: number;
}

// 赎回一致性检查
export interface RedeemCheckItem {
  product_id: number;
  product_name: string;
  pending_amount: number;
  status: 'normal' | 'negative' | 'overdue';
  latest_request_date: string | null;
  expected_settle_date: string | null;
  days_pending: number | null;
  hint: string;
}

export interface RedeemCheckResp {
  items: RedeemCheckItem[];
  buffer_days: number;
}

// 估值断档
export interface ValuationGapItem {
  product_id: number;
  product_name: string;
  last_valuation_date: string | null;
  days_since: number;
  has_recent_trade: boolean;
  severity: 'info' | 'warn';
  hint: string;
  // Sprint 6 可选：最近一次交易日期信息
  last_trade_date: string | null;
  days_since_trade: number | null;
}

export interface ValuationGapsResp {
  items: ValuationGapItem[];
  gap_threshold_days: number;
}

// API 函数

/**
 * 获取所有对账警告（聚合接口）
 */
export async function getReconciliationWarnings(
  date?: string,
  accountThreshold?: number,
  gapDays?: number,
  redeemBuffer?: number
) {
  return apiGet<ReconciliationWarningsResp>('/api/reconciliation/warnings', {
    date,
    account_threshold: accountThreshold,
    gap_days: gapDays,
    redeem_buffer: redeemBuffer,
  });
}

/**
 * 获取账户对账差异
 */
export async function getAccountDiffs(date?: string, threshold?: number) {
  return apiGet<AccountDiffsResp>('/api/reconciliation/account_diffs', {
    date,
    threshold,
  });
}

/**
 * 获取赎回在途一致性检查
 */
export async function getRedeemCheck(bufferDays?: number) {
  return apiGet<RedeemCheckResp>('/api/reconciliation/redeem_check', {
    buffer_days: bufferDays,
  });
}

/**
 * 获取估值断档产品列表
 */
export async function getValuationGaps(gapDays?: number) {
  return apiGet<ValuationGapsResp>('/api/reconciliation/valuation_gaps', {
    gap_days: gapDays,
  });
}

// S6-5: 警告状态管理 API

/**
 * 更新警告状态
 */
export async function updateWarningStatus(
  warningId: string,
  status: 'open' | 'acknowledged' | 'muted',
  muteReason?: string
) {
  return apiPut<WarningStatusResp>(`/api/reconciliation/warnings/${warningId}/status`, {
    status,
    mute_reason: muteReason,
  });
}

/**
 * 将警告恢复为 open 状态
 */
export async function restoreWarning(warningId: string) {
  return apiPost<WarningStatusResp>(`/api/reconciliation/warnings/${warningId}/restore`);
}

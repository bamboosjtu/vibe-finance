import { apiGet } from './api';

export interface DashboardSummary {
  date: string;
  total_assets: number;
  liquid_assets: number;
  liabilities: number;
  available_cash: number;
  // Sprint 4 新增字段
  real_available_cash: number;  // 实际可用现金（扣除在途赎回）
  pending_redeems: number;      // 在途赎回金额
  future_7d: number;            // 未来7天预计到账
  future_30d: number;           // 未来30天预计到账
  by_type: {
    cash: number;
    debit: number;
    credit: number;
    investment_cash: number;
    other: number;
  };
}

export interface LatestDateResp {
  date: string | null;
}

export interface AvailableDatesResp {
  dates: string[];
}

// Sprint 4: 在途赎回明细
export interface PendingRedeemItem {
  product_id: number;
  product_name: string;
  pending_amount: number;
  latest_request_date: string | null;
  estimated_settle_date: string | null;
}

export interface PendingRedeemsResp {
  total_pending: number;
  items: PendingRedeemItem[];
}

// Sprint 4: 未来现金流
export interface FutureCashFlowItem {
  date: string;
  amount: number;
  source: 'redeem' | 'maturity';
  description: string;
  product_id?: number;
}

export interface FutureCashFlowResp {
  items: FutureCashFlowItem[];
  total_7d: number;
  total_30d: number;
  by_date: Record<string, FutureCashFlowItem[]>;
}

// Sprint 4: 现金详情
export interface LiquidAccountDetail {
  account_id: number;
  account_name: string;
  account_type: string;
  balance: number;
}

export interface CashDetailResp {
  date: string;
  base_available: number;
  pending_redeems: number;
  real_available: number;
  details: {
    liquid_accounts: LiquidAccountDetail[];
    pending_details: PendingRedeemItem[];
  };
}

export async function getDashboardSummary(date: string) {
  return apiGet<DashboardSummary>('/api/dashboard/summary', { date });
}

export async function getLatestSnapshotDate() {
  return apiGet<LatestDateResp>('/api/dashboard/latest_date');
}

export async function getAvailableDates() {
  return apiGet<AvailableDatesResp>('/api/dashboard/available_dates');
}

// Sprint 4: 在途赎回接口
export async function getPendingRedeems(productId?: number) {
  return apiGet<PendingRedeemsResp>('/api/dashboard/pending_redeems', 
    productId ? { product_id: productId } : undefined
  );
}

// Sprint 4: 未来现金流接口
export async function getFutureCashFlow(days?: number) {
  return apiGet<FutureCashFlowResp>('/api/dashboard/future_cash_flow', 
    days ? { days } : undefined
  );
}

// Sprint 4: 现金详情接口
export async function getCashDetail(date?: string) {
  return apiGet<CashDetailResp>('/api/dashboard/cash_detail', 
    date ? { date } : undefined
  );
}

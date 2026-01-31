import { apiGet, apiPatch, apiPost, apiDelete } from './api';

export type ProductType =
  | 'bank_wmp'
  | 'money_market'
  | 'term_deposit'
  | 'fund'
  | 'stock'
  | 'other';

export type LiquidityRule = 'open' | 'closed' | 'periodic_open';

export type ValuationMode = 'product_value' | 'lot_value';

export interface Product {
  id: number;
  name: string;
  institution_id: number | null;
  product_code: string | null;
  product_type: ProductType;
  risk_level: string | null;
  term_days: number | null;
  liquidity_rule: LiquidityRule;
  settle_days: number;
  note: string | null;
  valuation_mode: ValuationMode;
}

export interface ProductWithMetrics extends Product {
  metrics?: ProductMetrics | null;
  total_holding_amount?: number | null;
  metrics_by_window?: Record<string, ProductMetrics | null>;
}

export interface ListProductsResp {
  items: ProductWithMetrics[];
}

export interface CreateProductReq {
  name: string;
  institution_id?: number | null;
  product_code?: string | null;
  product_type: ProductType;
  risk_level?: string | null;
  term_days?: number | null;
  liquidity_rule: LiquidityRule;
  settle_days?: number;
  note?: string | null;
  valuation_mode?: ValuationMode;
}

export interface PatchProductReq {
  name?: string;
  institution_id?: number | null;
  product_code?: string | null;
  product_type?: ProductType;
  risk_level?: string | null;
  term_days?: number | null;
  liquidity_rule?: LiquidityRule;
  settle_days?: number;
  note?: string | null;
  valuation_mode?: ValuationMode;
}

export interface ProductMetrics {
  twr: number;
  annualized: number;
  volatility: number;
  max_drawdown: number;
  drawdown_recovery_days: number;
}

export interface GetMetricsResp {
  product_id: number;
  valuation_mode: ValuationMode;
  window: string;
  status: 'ok' | 'insufficient_data' | 'degraded';
  metrics: ProductMetrics | null;
  reason?: string;
  degraded_reason?: string;
  degraded_fields?: string[];
}

export interface ChartPoint {
  date: string;
  market_value: number;
  source: 'manual' | 'interpolated';
}

export interface GetChartResp {
  product_id: number;
  valuation_mode: ValuationMode;
  points: ChartPoint[];
}

export async function listProducts(includeMetrics: boolean = false) {
  return apiGet<ListProductsResp>('/api/products', { include_metrics: includeMetrics });
}

export async function createProduct(body: CreateProductReq) {
  return apiPost<Product>('/api/products', body);
}

export async function patchProduct(id: number, body: PatchProductReq) {
  return apiPatch<Product>(`/api/products/${id}`, body);
}

export async function getProductMetrics(productId: number, window: string = '8w') {
  return apiGet<GetMetricsResp>(`/api/products/${productId}/metrics`, { window });
}

export async function getProductChart(productId: number, window: string = '8w') {
  return apiGet<GetChartResp>(`/api/products/${productId}/chart`, { window });
}

export async function deleteProduct(id: number) {
  return apiDelete<{ message: string }>(`/api/products/${id}`);
}

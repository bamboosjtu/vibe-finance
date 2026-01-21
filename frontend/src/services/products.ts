import { apiGet, apiPatch, apiPost, apiDelete } from './api';

export type ProductType =
  | 'bank_wmp'
  | 'money_market'
  | 'term_deposit'
  | 'fund'
  | 'stock'
  | 'other';

export type LiquidityRule = 'open' | 'closed' | 'periodic_open';

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
}

export interface ProductWithMetrics extends Product {
  metrics?: ProductMetrics | null;
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
  window: string;
  status: 'ok' | 'insufficient_data';
  metrics: ProductMetrics | null;
}

export async function listProducts(includeMetrics: boolean = false, window: string = '8w') {
  return apiGet<ListProductsResp>('/api/products', { include_metrics: includeMetrics, window });
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

export async function deleteProduct(id: number) {
  return apiDelete<{ message: string }>(`/api/products/${id}`);
}

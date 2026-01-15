import { apiGet, apiPatch, apiPost } from './api';

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

export interface ListProductsResp {
  items: Product[];
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

export async function listProducts() {
  return apiGet<ListProductsResp>('/api/products');
}

export async function createProduct(body: CreateProductReq) {
  return apiPost<Product>('/api/products', body);
}

export async function patchProduct(id: number, body: PatchProductReq) {
  return apiPatch<Product>(`/api/products/${id}`, body);
}

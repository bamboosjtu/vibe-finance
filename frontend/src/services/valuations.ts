import { apiGet, apiPost, apiDelete } from './api';

export interface ProductValuation {
  product_id: number;
  date: string;
  market_value: number;
}

export interface BatchUpsertReq {
  source: string;
  rows: ProductValuation[];
}

export interface BatchUpsertResp {
  inserted: number;
  updated: number;
  warnings: string[];
}

export interface GetValuationsResp {
  product_id: number;
  points: ProductValuation[];
}

export async function batchUpsertValuations(data: BatchUpsertReq) {
  return apiPost<BatchUpsertResp>('/api/valuations/batch_upsert', data);
}

export async function getProductValuations(productId: number, from: string, to: string) {
  return apiGet<GetValuationsResp>(`/api/products/${productId}/valuations`, { from, to });
}

export async function deleteProductValuation(productId: number, date: string) {
  return apiDelete<{ message: string }>(`/api/products/${productId}/valuations`, { date });
}

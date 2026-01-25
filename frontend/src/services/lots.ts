import { apiGet, apiPost, apiPatch, apiDelete } from './api';

export type LotStatus = 'holding' | 'redeeming' | 'settled';

export interface Lot {
  id: number;
  product_id: number;
  open_date: string;
  principal: number;
  status: LotStatus;
  note: string | null;
}

export interface CreateLotReq {
  product_id: number;
  open_date: string;
  principal: number;
  note?: string | null;
}

export interface PatchLotReq {
  principal?: number;
  note?: string | null;
}

export interface ListLotsResp {
  product_id: number;
  items: Lot[];
}

export async function createLot(body: CreateLotReq) {
  return apiPost<Lot>('/api/lots', body);
}

export async function listProductLots(productId: number) {
  return apiGet<ListLotsResp>(`/api/products/${productId}/lots`);
}

export async function patchLot(id: number, body: PatchLotReq) {
  return apiPatch<Lot>(`/api/lots/${id}`, body);
}

export async function deleteLot(id: number) {
  return apiDelete<{ message: string }>(`/api/lots/${id}`);
}

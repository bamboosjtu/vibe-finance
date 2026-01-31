import { apiGet, apiPost, apiDelete } from './api';

export interface Transaction {
  id: number;
  product_id: number;
  account_id: number;
  category: 'buy' | 'redeem_request' | 'redeem_settle' | 'fee';
  trade_date: string;
  settle_date?: string;
  amount: number;
  note?: string;
}

export interface CreateTransactionReq {
  product_id: number;
  account_id: number;
  category: string;
  trade_date: string;
  amount: number;
  settle_date?: string;
  note?: string;
}

export interface ListTransactionsResp {
  items: Transaction[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export async function createTransaction(data: CreateTransactionReq): Promise<Transaction> {
  return apiPost<Transaction>('/api/transactions', data);
}

export async function listTransactions(params?: {
  product_id?: number;
  account_id?: number;
  category?: string;
  from?: string;
  to?: string;
  page?: number;
  page_size?: number;
}): Promise<ListTransactionsResp> {
  return apiGet<ListTransactionsResp>('/api/transactions', params as Record<string, unknown>);
}

export async function deleteTransaction(id: number): Promise<void> {
  return apiDelete<void>(`/api/transactions/${id}`);
}

export async function getProductTransactions(
  productId: number,
  params?: { from?: string; to?: string; window?: string }
): Promise<{ product_id: number; items: Transaction[] }> {
  return apiGet<{ product_id: number; items: Transaction[] }>(`/api/products/${productId}/transactions`, params as Record<string, unknown>);
}

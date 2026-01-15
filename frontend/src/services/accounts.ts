import { apiGet, apiPatch, apiPost } from './api';

export type AccountType = 'cash' | 'debit' | 'credit' | 'investment_cash' | 'other';

export interface Account {
  id: number;
  name: string;
  institution_id: number | null;
  type: AccountType;
  currency: string;
  is_liquid: boolean;
}

export interface ListAccountsResp {
  items: Account[];
}

export interface CreateAccountReq {
  name: string;
  institution_id?: number | null;
  type: AccountType;
  currency?: string;
  is_liquid?: boolean;
}

export interface PatchAccountReq {
  name?: string;
  institution_id?: number | null;
  type?: AccountType;
  currency?: string;
  is_liquid?: boolean;
}

export async function listAccounts() {
  return apiGet<ListAccountsResp>('/api/accounts');
}

export async function createAccount(body: CreateAccountReq) {
  return apiPost<Account>('/api/accounts', body);
}

export async function patchAccount(id: number, body: PatchAccountReq) {
  return apiPatch<Account>(`/api/accounts/${id}`, body);
}

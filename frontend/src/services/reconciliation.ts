import { apiGet } from './api';

export interface ReconciliationWarning {
  date: string;
  account_id: number;
  snapshot_balance: number;
  derived_balance: number;
  diff: number;
  severity: 'warning';
  hint?: string;
}

export interface ReconciliationWarningsResp {
  items: ReconciliationWarning[];
  note?: string;
}

export async function getReconciliationWarnings(date?: string) {
  return apiGet<ReconciliationWarningsResp>('/api/reconciliation/warnings', { date });
}

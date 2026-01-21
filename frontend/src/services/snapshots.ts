import { apiGet, apiPost } from './api';

export interface SnapshotItem {
  date: string;
  account_id: number;
  balance: number;
}

export interface BatchUpsertReq {
  source?: string;
  rows: SnapshotItem[];
}

export interface BatchUpsertResp {
  inserted: number;
  updated: number;
  warnings: string[];
}

export interface ListSnapshotsResp {
  date: string;
  items: {
    account_id: number;
    balance: number;
  }[];
}

export async function batchUpsertSnapshots(data: BatchUpsertReq) {
  return apiPost<BatchUpsertResp>('/api/snapshots/batch_upsert', data);
}

export async function listSnapshots(date: string, fill?: boolean) {
  return apiGet<ListSnapshotsResp>('/api/snapshots', { date, fill });
}

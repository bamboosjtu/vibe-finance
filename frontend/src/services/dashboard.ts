import { apiGet } from './api';

export interface DashboardSummary {
  date: string;
  total_assets: number;
  liquid_assets: number;
  liabilities: number;
  available_cash: number;
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

export async function getDashboardSummary(date: string) {
  return apiGet<DashboardSummary>('/api/dashboard/summary', { date });
}

export async function getLatestSnapshotDate() {
  return apiGet<LatestDateResp>('/api/dashboard/latest_date');
}

export async function getAvailableDates() {
  return apiGet<AvailableDatesResp>('/api/dashboard/available_dates');
}

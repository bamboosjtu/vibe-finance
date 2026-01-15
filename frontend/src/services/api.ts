import { request } from '@umijs/max';
import type { RequestOptions } from '@umijs/max';

export interface ApiEnvelope<T> {
  code: number;
  data: T;
  message: string;
}

async function apiRequest<T>(url: string, options?: RequestOptions) {
  const opts: RequestOptions | undefined = options
    ? {
        ...options,
        getResponse: false,
      }
    : undefined;

  const resp = opts
    ? await request<ApiEnvelope<T>>(url, opts)
    : await request<ApiEnvelope<T>>(url);

  if (!resp || typeof resp.code !== 'number') {
    throw new Error('Invalid API response');
  }

  if (resp.code !== 200) {
    throw new Error(resp.message || 'Request failed');
  }

  return resp.data;
}

export function apiGet<T>(url: string, params?: Record<string, unknown>) {
  return apiRequest<T>(url, {
    method: 'GET',
    params,
  });
}

export function apiPost<T>(url: string, body?: unknown) {
  return apiRequest<T>(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

export function apiPatch<T>(url: string, body?: unknown) {
  return apiRequest<T>(url, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
  });
}

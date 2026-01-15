import { apiGet, apiPost } from './api';

export interface Institution {
  id: number;
  name: string;
}

export interface ListInstitutionsResp {
  items: Institution[];
}

export interface CreateInstitutionReq {
  name: string;
}

export async function listInstitutions() {
  return apiGet<ListInstitutionsResp>('/api/institutions');
}

export async function createInstitution(body: CreateInstitutionReq) {
  return apiPost<Institution>('/api/institutions', body);
}

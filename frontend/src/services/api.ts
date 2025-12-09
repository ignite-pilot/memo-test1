import axios from 'axios';
import type { Memo, MemoCreate } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8501';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const memoService = {
  async getMemos(): Promise<Memo[]> {
    const response = await api.get<Memo[]>('/api/memos');
    return response.data;
  },

  async createMemo(memo: MemoCreate): Promise<Memo> {
    const response = await api.post<Memo>('/api/memos', memo);
    return response.data;
  },

  async deleteMemo(id: number): Promise<void> {
    await api.delete(`/api/memos/${id}`);
  },
};


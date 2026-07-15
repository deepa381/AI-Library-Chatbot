import api from './axios';
import type { Fine } from '../types';
import type { PaginatedResponse } from './books';

export const finesApi = {
  getFines: async () => {
    const response = await api.get<Fine[]>('/fines/');
    return response.data;
  },
  
  payFine: async (fineId: number) => {
    // Simulated payment endpoint
    const response = await api.post(`/fines/${fineId}/pay/`);
    return response.data;
  }
};

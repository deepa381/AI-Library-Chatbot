import api from './axios';
import type { RecommendationResponse } from '../types';

export const recommendApi = {
  getRecommendations: async (query: string) => {
    const response = await api.post<RecommendationResponse>('/recommend/', { query });
    return response.data;
  }
};

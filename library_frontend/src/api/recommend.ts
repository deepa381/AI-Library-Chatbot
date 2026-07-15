import api from './axios';
import type { RecommendationHistory } from '../types';

export const recommendApi = {
  getRecommendations: async (query: string) => {
    const response = await api.post<RecommendationHistory>('/recommend/', { query });
    return response.data;
  }
};

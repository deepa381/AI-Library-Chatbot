import api from './axios';
import type { Book } from '../types';

export const searchApi = {
  searchBooks: async (query: string) => {
    const response = await api.get<Book[]>('/search/', { params: { q: query } });
    return response.data;
  }
};

import api from './axios';
import type { Book, Category, Author, Tag } from '../types';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const booksApi = {
  getBooks: async (params?: Record<string, any>) => {
    const response = await api.get<PaginatedResponse<Book>>('/books/', { params });
    return response.data;
  },
  
  getBook: async (id: string) => {
    const response = await api.get<Book>(`/books/${id}/`);
    return response.data;
  },

  getCategories: async () => {
    const response = await api.get<Category[]>('/categories/');
    return response.data;
  },

  getAuthors: async () => {
    const response = await api.get<Author[]>('/authors/');
    return response.data;
  },
  
  getTags: async () => {
    const response = await api.get<Tag[]>('/tags/');
    return response.data;
  }
};

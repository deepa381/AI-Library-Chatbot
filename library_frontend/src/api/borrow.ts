import api from './axios';
import type { BorrowRecord } from '../types';

export const borrowApi = {
  getBorrows: async () => {
    const response = await api.get<BorrowRecord[]>('/borrow/');
    return response.data;
  },
  
  borrowBook: async (bookId: number) => {
    const response = await api.post<BorrowRecord>('/borrow/', { book_id: bookId });
    return response.data;
  },

  renewBorrow: async (borrowId: number) => {
    const response = await api.patch<BorrowRecord>(`/borrow/${borrowId}/renew/`);
    return response.data;
  }
};

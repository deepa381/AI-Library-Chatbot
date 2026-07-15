import api from './axios';
import type { Reservation } from '../types';
import type { PaginatedResponse } from './books';

export const reservationsApi = {
  getReservations: async () => {
    const response = await api.get<Reservation[]>('/reservations/');
    return response.data;
  },
  
  reserveBook: async (bookId: number) => {
    const response = await api.post<Reservation>('/reservations/', { book_id: bookId });
    return response.data;
  },

  cancelReservation: async (reservationId: number) => {
    const response = await api.delete(`/reservations/${reservationId}/`);
    return response.data;
  }
};

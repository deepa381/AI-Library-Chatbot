import api from './axios';

export interface DashboardData {
  statistics: {
    total_book_titles: number;
    total_physical_copies: number;
    available_physical_copies: number;
    borrowed_books: number;
    reserved_books: number;
    total_members: number;
    active_members: number;
    pending_fines: number;
    collected_fines: number;
  };
  most_borrowed_books: {
    id: number;
    title: string;
    isbn: string;
    borrow_count: number;
  }[];
  recently_added_books: {
    id: number;
    title: string;
    isbn: string;
    created_at: string;
  }[];
}

export const dashboardApi = {
  getDashboard: async () => {
    const response = await api.get<DashboardData>('/dashboard/');
    return response.data;
  }
};

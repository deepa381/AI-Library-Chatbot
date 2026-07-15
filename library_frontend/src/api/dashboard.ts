import api from './axios';

export interface DashboardData {
  total_books: number;
  total_members: number;
  active_borrows: number;
  pending_reservations: number;
  overdue_borrows: number;
  total_fines: string;
  monthly_borrows: { month: string; count: number }[];
  popular_categories: { name: string; borrow_count: number }[];
  recent_borrows: any[];
}

export const dashboardApi = {
  getDashboard: async () => {
    const response = await api.get<DashboardData>('/dashboard/');
    return response.data;
  }
};

import api from './axios';
import type { User } from '../types';

interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export const authApi = {
  login: async (credentials: any) => {
    const response = await api.post<LoginResponse>('/auth/login/', credentials);
    return response.data;
  },
  
  register: async (userData: any) => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get<User>('/auth/profile/');
    return response.data;
  },

  updateProfile: async (profileData: { first_name?: string; last_name?: string; phone?: string; department?: string }) => {
    const response = await api.patch<User>('/auth/profile/', profileData);
    return response.data;
  }
};

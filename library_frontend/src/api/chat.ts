import api from './axios';
import type { ChatSession } from '../types';

export const chatApi = {
  getSessions: async () => {
    const response = await api.get<ChatSession[]>('/chat/history/');
    return response.data;
  },

  getSession: async (sessionId: string) => {
    const response = await api.get<ChatSession>(`/chat/history/${sessionId}/`);
    return response.data;
  },

  deleteSession: async (sessionId: string) => {
    const response = await api.delete(`/chat/history/${sessionId}/`);
    return response.data;
  },

  sendMessage: async (message: string, sessionId?: string) => {
    const payload: any = { message };
    if (sessionId) payload.session_id = sessionId;
    
    // Using any since the backend response might have session_id along with the message
    const response = await api.post<any>('/chat/', payload);
    return response.data;
  }
};

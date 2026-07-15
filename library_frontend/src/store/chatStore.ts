import { create } from 'zustand';

interface ChatState {
  activeSessionId: string | null;
  setActiveSession: (id: string | null) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  activeSessionId: null,
  setActiveSession: (id) => set({ activeSessionId: id }),
}));

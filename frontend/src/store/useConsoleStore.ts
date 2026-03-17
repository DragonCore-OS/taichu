import { create } from 'zustand';

export type PageKey = 'overview' | 'round' | 'persona' | 'gate3' | 'artifacts' | 'health' | 'settings';

interface ConsoleStore {
  page: PageKey;
  selectedAgent?: string;
  darkMode: boolean;
  setPage: (page: PageKey) => void;
  setSelectedAgent: (seatId?: string) => void;
  toggleDarkMode: () => void;
}

export const useConsoleStore = create<ConsoleStore>((set) => ({
  page: 'overview',
  darkMode: true,
  setPage: (page) => set({ page }),
  setSelectedAgent: (selectedAgent) => set({ selectedAgent }),
  toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
}));

'use client';
import { create } from 'zustand';
import api from '@/lib/api-client';

interface User {
  id: string;
  phone: string;
  name: string | null;
  email: string | null;
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  initAuth: () => void;
  sendOTP: (email: string) => Promise<{ otp?: string }>;
  verifyOTP: (email: string, otp: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,  // 初始 false，避免 hydration mismatch
  isLoading: false,

  initAuth: () => {
    if (typeof window !== 'undefined' && localStorage.getItem('access_token')) {
      set({ isAuthenticated: true });
    }
  },

  sendOTP: async (email: string) => {
    const res = await api.post('/api/v1/auth/otp/send', { email, method: 'email' });
    return res.data.data;
  },

  verifyOTP: async (email: string, otp: string) => {
    const res = await api.post('/api/v1/auth/otp/verify', { email, otp });
    const { user, tokens } = res.data.data;
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    set({ user, isAuthenticated: true });
  },

  logout: async () => {
    try {
      await api.post('/api/v1/auth/logout');
    } catch {}
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false });
  },

  loadUser: async () => {
    try {
      set({ isLoading: true });
      const res = await api.get('/api/v1/customers/profile');
      set({ user: res.data.data, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
}));

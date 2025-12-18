"""Authentication State Store"""

import create from 'zustand';

interface AuthState {
  isAuthenticated: boolean;
  user: any | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('access_token'),
  user: null,
  token: localStorage.getItem('access_token') || null,
  
  login: async (email: string, password: string) => {
    // Call backend
    const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v1/auth/email/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    
    if (!response.ok) throw new Error('Login failed');
    const data = await response.json();
    
    localStorage.setItem('access_token', data.access_token);
    set({
      isAuthenticated: true,
      token: data.access_token,
      user: data.user,
    });
  },
  
  logout: () => {
    localStorage.removeItem('access_token');
    set({
      isAuthenticated: false,
      user: null,
      token: null,
    });
  },
  
  setToken: (token: string) => {
    localStorage.setItem('access_token', token);
    set({ token, isAuthenticated: true });
  },
}));

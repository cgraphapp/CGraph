"";
"Authentication State Store";
"";
import create from 'zustand';
export const useAuthStore = create((set) => ({
    isAuthenticated: !!localStorage.getItem('access_token'),
    user: null,
    token: localStorage.getItem('access_token') || null,
    login: async (email, password) => {
        // Call backend
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/v1/auth/email/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        if (!response.ok)
            throw new Error('Login failed');
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
    setToken: (token) => {
        localStorage.setItem('access_token', token);
        set({ token, isAuthenticated: true });
    },
}));

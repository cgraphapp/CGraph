import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginForm } from './LoginForm';
describe('LoginForm', () => {
    it('should render login form', () => {
        render(<LoginForm />);
        expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    });
    it('should handle form submission', async () => {
        global.fetch = jest.fn(() => Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ access_token: 'test_token' }),
        }));
        render(<LoginForm />);
        fireEvent.change(screen.getByPlaceholderText('Email'), {
            target: { value: 'test@example.com' },
        });
        fireEvent.change(screen.getByPlaceholderText('Password'), {
            target: { value: 'password123' },
        });
        fireEvent.click(screen.getByRole('button', { name: /login/i }));
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalled();
        });
    });
});

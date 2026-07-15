import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/auth';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'react-hot-toast';
import { BookOpen } from 'lucide-react';

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const setTokens = useAuthStore((state) => state.setTokens);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await authApi.login({ username, password });
      setTokens(data.access, data.refresh);
      const userProfile = await authApi.getProfile();
      setAuth(userProfile, data.access, data.refresh);
      toast.success('Logged in successfully');
      navigate('/');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-background p-8 shadow-lg border">
        <div className="flex flex-col items-center text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <BookOpen className="h-6 w-6 text-primary" />
          </div>
          <h2 className="mt-4 text-2xl font-bold tracking-tight">Welcome back</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Sign in to access the library
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium leading-none">Username</label>
              <Input
                className="mt-2"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
              />
            </div>
            <div>
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium leading-none">Password</label>
                <Link to="/forgot-password" className="text-sm text-primary hover:underline">
                  Forgot password?
                </Link>
              </div>
              <Input
                className="mt-2"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            Don't have an account?{' '}
            <Link to="/register" className="font-medium text-primary hover:underline">
              Register here
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}

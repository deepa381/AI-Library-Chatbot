import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { BookOpen, LogOut, User as UserIcon } from 'lucide-react';
import { Button } from '../ui/button';

export function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between px-4 sm:px-8">
        <Link to="/" className="flex items-center space-x-2">
          <BookOpen className="h-6 w-6 text-primary" />
          <span className="font-bold hidden sm:inline-block">
            Lumina Library
          </span>
        </Link>

        <div className="flex items-center space-x-4">
          {isAuthenticated ? (
            <>
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <UserIcon className="h-4 w-4" />
                <span className="hidden sm:inline-block">{user?.first_name} {user?.last_name}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline-block">Logout</span>
              </Button>
            </>
          ) : (
            <div className="flex space-x-2">
              <Button variant="ghost" size="sm" asChild>
                <Link to="/login">Login</Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

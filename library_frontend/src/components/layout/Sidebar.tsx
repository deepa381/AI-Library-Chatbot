import { NavLink } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { 
  LayoutDashboard, 
  Library, 
  MessageSquare, 
  Sparkles, 
  Search, 
  User,
  History
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Browse Books', path: '/books', icon: Library },
  { name: 'Search', path: '/search', icon: Search },
  { name: 'Ask Librarian AI', path: '/chat', icon: MessageSquare },
  { name: 'AI Recommendations', path: '/recommend', icon: Sparkles },
  { name: 'My Borrowing', path: '/borrowing', icon: History },
  { name: 'Profile', path: '/profile', icon: User },
];

export function Sidebar() {
  return (
    <aside className="fixed top-14 z-30 -ml-2 hidden h-[calc(100vh-3.5rem)] w-full shrink-0 md:sticky md:block md:w-64 border-r overflow-y-auto bg-background px-4 py-6">
      <nav className="flex flex-col space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
                isActive 
                  ? "bg-primary text-primary-foreground" 
                  : "text-muted-foreground hover:bg-muted hover:text-primary"
              )
            }
          >
            <item.icon className="h-5 w-5" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';

export function AppShell() {
  return (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />
      <div className="flex-1 items-start md:grid md:grid-cols-[220px_minmax(0,1fr)] lg:grid-cols-[256px_minmax(0,1fr)]">
        <Sidebar />
        <main className="flex w-full flex-col overflow-hidden py-6 px-4 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/dashboard';
import { borrowApi } from '../api/borrow';
import { reservationsApi } from '../api/reservations';
import { finesApi } from '../api/fines';
import { Skeleton } from '../components/ui/skeleton';
import { Book, Users, BookOpen, Clock, AlertCircle, DollarSign, Bookmark, Copy, Calendar } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export function DashboardPage() {
  const { user } = useAuthStore();
  const isLibrarian = user?.profile?.role === 'LIBRARIAN';

  // LIBRARIAN queries
  const { data: adminData, isLoading: isAdminLoading, error: adminError } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getDashboard,
    enabled: isLibrarian,
  });

  // MEMBER queries
  const { data: memberBorrows, isLoading: isMemberBorrowsLoading } = useQuery({
    queryKey: ['borrows'],
    queryFn: borrowApi.getBorrows,
    enabled: !isLibrarian,
  });

  const { data: memberReservations, isLoading: isMemberReservationsLoading } = useQuery({
    queryKey: ['reservations'],
    queryFn: reservationsApi.getReservations,
    enabled: !isLibrarian,
  });

  const { data: memberFines, isLoading: isMemberFinesLoading } = useQuery({
    queryKey: ['fines'],
    queryFn: finesApi.getFines,
    enabled: !isLibrarian,
  });

  const isLoading = isLibrarian 
    ? isAdminLoading 
    : (isMemberBorrowsLoading || isMemberReservationsLoading || isMemberFinesLoading);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map(i => <Skeleton key={i} className="h-32 w-full rounded-xl" />)}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-80 w-full rounded-xl" />
          <Skeleton className="h-80 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (isLibrarian) {
    if (adminError || !adminData || !adminData.statistics) {
      return <div className="p-4 text-destructive">Failed to load librarian dashboard data.</div>;
    }

    const stats = [
      { name: 'Total Book Titles', value: adminData.statistics.total_book_titles, icon: Book, color: 'text-blue-500' },
      { name: 'Total Copies', value: adminData.statistics.total_physical_copies, icon: Copy, color: 'text-indigo-500' },
      { name: 'Available Copies', value: adminData.statistics.available_physical_copies, icon: BookOpen, color: 'text-emerald-500' },
      { name: 'Borrowed Books', value: adminData.statistics.borrowed_books, icon: AlertCircle, color: 'text-red-500' },
      { name: 'Reserved Books', value: adminData.statistics.reserved_books, icon: Bookmark, color: 'text-amber-500' },
      { name: 'Total Members', value: adminData.statistics.total_members, icon: Users, color: 'text-purple-500' },
      { name: 'Pending Fines', value: `$${adminData.statistics.pending_fines.toFixed(2)}`, icon: DollarSign, color: 'text-rose-500' },
    ];

    const mostBorrowedBooks = adminData?.most_borrowed_books ?? [];
    const recentlyAddedBooks = adminData?.recently_added_books ?? [];

    return (
      <div className="space-y-6 pb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Librarian Dashboard</h1>
          <p className="text-muted-foreground mt-1">Welcome back, {user?.first_name || user?.username}. Here's the latest overview.</p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {stats.map((stat, i) => (
            <div key={i} className="rounded-xl border bg-card p-6 shadow-sm">
              <div className="flex items-center space-x-4">
                <div className={`p-3 rounded-full bg-muted/50 ${stat.color}`}>
                  <stat.icon className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{stat.name}</p>
                  <h3 className="text-2xl font-bold">{stat.value}</h3>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-xl border bg-card p-6 shadow-sm">
            <h3 className="text-lg font-semibold mb-4">Most Borrowed Books</h3>
            {mostBorrowedBooks.length > 0 ? (
              <div className="space-y-4">
                {mostBorrowedBooks.map((book: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                    <div>
                      <p className="font-medium">{book.title}</p>
                      <p className="text-sm text-muted-foreground">ISBN: {book.isbn}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{book.borrow_count} borrows</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">No books have been borrowed yet.</p>
            )}
          </div>

          <div className="rounded-xl border bg-card p-6 shadow-sm">
            <h3 className="text-lg font-semibold mb-4">Recently Added Books</h3>
            {recentlyAddedBooks.length > 0 ? (
              <div className="space-y-4">
                {recentlyAddedBooks.map((book: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                    <div>
                      <p className="font-medium">{book.title}</p>
                      <p className="text-sm text-muted-foreground">ISBN: {book.isbn}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{new Date(book.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">No recently added books.</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // MEMBER Dashboard Layout
  const activeBorrows = memberBorrows?.filter(b => b.status === 'BORROWED' || b.status === 'OVERDUE') ?? [];
  const activeReservations = memberReservations?.filter(r => r.status === 'WAITING' || r.status === 'ACTIVE') ?? [];
  const pendingFinesList = memberFines?.filter(f => f.status === 'PENDING') ?? [];
  const totalPendingFines = pendingFinesList.reduce((acc, f) => acc + parseFloat(f.amount), 0);

  const stats = [
    { name: 'Total Borrowed Books', value: memberBorrows?.length ?? 0, icon: Book, color: 'text-blue-500' },
    { name: 'Active Borrows', value: activeBorrows.length, icon: BookOpen, color: 'text-emerald-500' },
    { name: 'Active Reservations', value: activeReservations.length, icon: Clock, color: 'text-amber-500' },
    { name: 'Pending Fines', value: `$${totalPendingFines.toFixed(2)}`, icon: DollarSign, color: 'text-red-500' },
  ];

  return (
    <div className="space-y-6 pb-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Member Dashboard</h1>
        <p className="text-muted-foreground mt-1">Welcome back, {user?.first_name || user?.username}. Here's your borrowing overview.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <div key={i} className="rounded-xl border bg-card p-6 shadow-sm">
            <div className="flex items-center space-x-4">
              <div className={`p-3 rounded-full bg-muted/50 ${stat.color}`}>
                <stat.icon className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">{stat.name}</p>
                <h3 className="text-2xl font-bold">{stat.value}</h3>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Active Borrows */}
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">My Active Borrows</h3>
          {activeBorrows.length > 0 ? (
            <div className="space-y-4">
              {activeBorrows.map((record) => (
                <div key={record.id} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                  <div>
                    <p className="font-medium line-clamp-1">{record.book?.title}</p>
                    <p className="text-sm text-muted-foreground flex items-center mt-1">
                      <Calendar className="mr-1 h-3 w-3" />
                      Due: {new Date(record.due_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      record.status === 'OVERDUE' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {record.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">You don't have any active borrows.</p>
          )}
        </div>

        {/* Active Reservations */}
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">My Active Reservations</h3>
          {activeReservations.length > 0 ? (
            <div className="space-y-4">
              {activeReservations.map((record) => (
                <div key={record.id} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
                  <div>
                    <p className="font-medium line-clamp-1">{record.book?.title}</p>
                    <p className="text-sm text-muted-foreground flex items-center mt-1">
                      <Calendar className="mr-1 h-3 w-3" />
                      Reserved: {new Date(record.reservation_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                      Queue #{record.queue_position} ({record.status})
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">You don't have any active reservations.</p>
          )}
        </div>
      </div>
    </div>
  );
}

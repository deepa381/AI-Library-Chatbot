import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { borrowApi } from '../api/borrow';
import { Skeleton } from '../components/ui/skeleton';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { toast } from 'react-hot-toast';
import { BookOpen, Calendar, Clock, RefreshCw } from 'lucide-react';

export function BorrowingPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['borrows'],
    queryFn: borrowApi.getBorrows,
  });

  const renewMutation = useMutation({
    mutationFn: (id: number) => borrowApi.renewBorrow(id),
    onSuccess: () => {
      toast.success('Book renewed successfully!');
      queryClient.invalidateQueries({ queryKey: ['books'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['borrows'] });
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.non_field_errors?.[0] || 
                       error.response?.data?.detail || 
                       (error.response?.data && typeof error.response.data === 'object' ? Object.values(error.response.data).flat()[0] : null) ||
                       'Failed to renew book';
      toast.error(String(errorMsg));
    }
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">My Borrowing</h1>
        <div className="space-y-4">
          {[1,2,3].map(i => <Skeleton key={i} className="h-32 w-full rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Borrowing</h1>
        <p className="text-muted-foreground mt-1">Manage your active and past borrowed books.</p>
      </div>

      {data?.length === 0 ? (
        <div className="text-center py-20 bg-muted/30 rounded-xl border border-dashed">
          <BookOpen className="h-12 w-12 mx-auto text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold">No borrow history</h3>
          <p className="text-muted-foreground">You haven't borrowed any books yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {data?.map((record) => {
            const isOverdue = record.status === 'OVERDUE';
            const isActive = record.status === 'BORROWED';
            
            return (
              <div key={record.id} className="flex flex-col sm:flex-row gap-6 p-6 rounded-xl border bg-card shadow-sm">
                <div className="h-32 w-24 shrink-0 overflow-hidden rounded-md bg-muted">
                  {record.book?.cover_image ? (
                    <img src={record.book.cover_image} alt={record.book.title} className="h-full w-full object-cover" />
                  ) : (
                    <div className="flex h-full items-center justify-center text-xs text-muted-foreground text-center p-2">No Cover</div>
                  )}
                </div>
                
                <div className="flex-1 flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between">
                      <h3 className="text-lg font-semibold line-clamp-1">{record.book?.title}</h3>
                      <Badge variant={isActive ? "success" : isOverdue ? "destructive" : "secondary"}>
                        {record.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-1">
                      {record.book?.authors?.map(a => `${a.first_name} ${a.last_name}`).join(', ')}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                    <div className="flex items-center text-muted-foreground">
                      <Calendar className="mr-2 h-4 w-4" />
                      <span>Borrowed: {new Date(record.borrow_date).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center text-muted-foreground">
                      <Clock className="mr-2 h-4 w-4" />
                      <span className={isOverdue ? "text-destructive font-medium" : ""}>
                        Due: {new Date(record.due_date).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col justify-end sm:border-l sm:pl-6">
                  {isActive && (
                    <Button 
                      variant="outline" 
                      onClick={() => renewMutation.mutate(record.id)}
                      disabled={renewMutation.isPending}
                    >
                      <RefreshCw className={`mr-2 h-4 w-4 ${renewMutation.isPending ? 'animate-spin' : ''}`} />
                      Renew
                    </Button>
                  )}
                  {record.status === 'RETURNED' && (
                    <div className="text-sm text-muted-foreground mt-auto">
                      Returned on: {new Date(record.return_date!).toLocaleDateString()}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

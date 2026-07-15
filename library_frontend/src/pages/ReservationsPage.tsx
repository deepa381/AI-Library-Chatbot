import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reservationsApi } from '../api/reservations';
import { Skeleton } from '../components/ui/skeleton';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { toast } from 'react-hot-toast';
import { BookmarkMinus, Calendar, XCircle } from 'lucide-react';

export function ReservationsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['reservations'],
    queryFn: reservationsApi.getReservations,
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => reservationsApi.cancelReservation(id),
    onSuccess: () => {
      toast.success('Reservation cancelled successfully!');
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['borrows'] });
      queryClient.invalidateQueries({ queryKey: ['books'] });
    },
    onError: (error: any) => {
      const err = error.response?.data;
      const message = err?.detail || err?.non_field_errors?.[0] || Object.values(err || {}).flat().join(' ') || 'Failed to cancel reservation';
      toast.error(message);
    }
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">My Reservations</h1>
        <div className="space-y-4">
          {[1,2,3].map(i => <Skeleton key={i} className="h-32 w-full rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Reservations</h1>
        <p className="text-muted-foreground mt-1">Manage your waitlisted books.</p>
      </div>

      {data?.length === 0 ? (
        <div className="text-center py-20 bg-muted/30 rounded-xl border border-dashed">
          <BookmarkMinus className="h-12 w-12 mx-auto text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold">No active reservations</h3>
          <p className="text-muted-foreground">You don't have any books on reserve.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {data?.map((record) => {
            const isPending = record.status === 'WAITING' || record.status === 'ACTIVE';
            
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
                      <Badge variant={isPending ? "secondary" : "default"}>
                        {record.status.toUpperCase()}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-1">
                      {record.book?.authors?.map(a => `${a.first_name} ${a.last_name}`).join(', ')}
                    </p>
                  </div>
                  
                  <div className="mt-4 text-sm">
                    <div className="flex items-center text-muted-foreground">
                      <Calendar className="mr-2 h-4 w-4" />
                      <span>Reserved on: {new Date(record.reservation_date).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col justify-end sm:border-l sm:pl-6">
                  {isPending && (
                    <Button 
                      variant="destructive" 
                      onClick={() => cancelMutation.mutate(record.id)}
                      disabled={cancelMutation.isPending}
                    >
                      <XCircle className={`mr-2 h-4 w-4 ${cancelMutation.isPending ? 'animate-spin' : ''}`} />
                      Cancel
                    </Button>
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

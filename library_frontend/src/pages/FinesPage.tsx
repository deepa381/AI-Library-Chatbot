import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { finesApi } from '../api/fines';
import { Skeleton } from '../components/ui/skeleton';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { toast } from 'react-hot-toast';
import { DollarSign, AlertTriangle } from 'lucide-react';

export function FinesPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ['fines'],
    queryFn: finesApi.getFines,
  });

  const payMutation = useMutation({
    mutationFn: (id: number) => finesApi.payFine(id),
    onSuccess: () => {
      toast.success('Fine paid successfully!');
      queryClient.invalidateQueries({ queryKey: ['fines'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['borrows'] });
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      queryClient.invalidateQueries({ queryKey: ['books'] });
    },
    onError: (error: any) => {
      const err = error.response?.data;
      const message = err?.detail || err?.non_field_errors?.[0] || Object.values(err || {}).flat().join(' ') || 'Failed to process payment';
      toast.error(message);
    }
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">My Fines</h1>
        <div className="space-y-4">
          {[1,2,3].map(i => <Skeleton key={i} className="h-32 w-full rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">My Fines</h1>
        <p className="text-muted-foreground mt-1">Manage your pending and paid fines.</p>
      </div>

      {data?.length === 0 ? (
        <div className="text-center py-20 bg-muted/30 rounded-xl border border-dashed">
          <DollarSign className="h-12 w-12 mx-auto text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold">No fines</h3>
          <p className="text-muted-foreground">You don't have any fines on your account.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {data?.map((fine) => {
            const isPaid = fine.status === 'PAID';
            
            return (
              <div key={fine.id} className="flex flex-col sm:flex-row gap-6 p-6 rounded-xl border bg-card shadow-sm">
                <div className="flex items-center justify-center h-16 w-16 shrink-0 rounded-full bg-muted text-muted-foreground">
                  {isPaid ? <DollarSign className="h-8 w-8 text-emerald-500" /> : <AlertTriangle className="h-8 w-8 text-destructive" />}
                </div>
                
                <div className="flex-1 flex flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between">
                      <h3 className="text-lg font-semibold">
                        Fine for: {fine.borrow_record?.book?.title || 'Unknown Book'}
                      </h3>
                      <Badge variant={isPaid ? "success" : "destructive"}>
                        {isPaid ? "PAID" : "PENDING"}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {fine.reason}
                    </p>
                  </div>
                  
                  <div className="mt-4 text-sm font-medium">
                    Amount: <span className="text-lg">${fine.amount}</span>
                  </div>
                </div>

                <div className="flex flex-col justify-end sm:border-l sm:pl-6">
                  {!isPaid && (
                    <Button 
                      onClick={() => payMutation.mutate(fine.id)}
                      disabled={payMutation.isPending}
                    >
                      {payMutation.isPending ? 'Processing...' : 'Pay Now'}
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

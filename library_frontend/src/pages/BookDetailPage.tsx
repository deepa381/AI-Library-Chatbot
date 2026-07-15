import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { booksApi } from '../api/books';
import { borrowApi } from '../api/borrow';
import { reservationsApi } from '../api/reservations';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { toast } from 'react-hot-toast';
import { ArrowLeft, BookOpen, Clock, Tag } from 'lucide-react';

export function BookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: book, isLoading } = useQuery({
    queryKey: ['book', id],
    queryFn: () => booksApi.getBook(id!),
    enabled: !!id,
  });

  const borrowMutation = useMutation({
    mutationFn: () => borrowApi.borrowBook(Number(id)),
    onSuccess: () => {
      toast.success('Book borrowed successfully!');
      queryClient.invalidateQueries({ queryKey: ['book', id] });
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
                       'Failed to borrow book';
      toast.error(String(errorMsg));
    }
  });

  const reserveMutation = useMutation({
    mutationFn: () => reservationsApi.reserveBook(Number(id)),
    onSuccess: () => {
      toast.success('Book reserved successfully!');
      queryClient.invalidateQueries({ queryKey: ['book', id] });
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
                       'Failed to reserve book';
      toast.error(String(errorMsg));
    }
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-32" />
        <div className="grid md:grid-cols-3 gap-8">
          <Skeleton className="aspect-[2/3] w-full rounded-xl" />
          <div className="md:col-span-2 space-y-4">
            <Skeleton className="h-10 w-3/4" />
            <Skeleton className="h-6 w-1/2" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (!book) {
    return <div className="p-4 text-center">Book not found.</div>;
  }

  const isAvailable = book.available_copies > 0;

  return (
    <div className="space-y-6 pb-8">
      <Button variant="ghost" className="mb-4 -ml-4" onClick={() => navigate(-1)}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back
      </Button>

      <div className="grid md:grid-cols-3 gap-8">
        {/* Left Column: Cover & Actions */}
        <div className="space-y-6">
          <div className="aspect-[2/3] w-full overflow-hidden rounded-xl bg-muted shadow-lg">
            {book.cover_image ? (
              <img src={book.cover_image} alt={book.title} className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground p-4 text-center">
                No Cover Available
              </div>
            )}
          </div>

          <div className="rounded-xl border bg-card p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-muted-foreground">Status</span>
              <Badge variant={isAvailable ? "success" : "secondary"}>
                {isAvailable ? `${book.available_copies} Available` : 'Waitlist'}
              </Badge>
            </div>
            
            <Button 
              className="w-full" 
              size="lg"
              onClick={() => borrowMutation.mutate()}
              disabled={!isAvailable || borrowMutation.isPending}
            >
              <BookOpen className="mr-2 h-4 w-4" />
              {borrowMutation.isPending ? 'Processing...' : 'Borrow Book'}
            </Button>
            
            <Button 
              className="w-full" 
              variant="outline" 
              size="lg"
              onClick={() => reserveMutation.mutate()}
              disabled={isAvailable || reserveMutation.isPending}
            >
              <Clock className="mr-2 h-4 w-4" />
              {reserveMutation.isPending ? 'Processing...' : 'Reserve (Waitlist)'}
            </Button>
          </div>
        </div>

        {/* Right Column: Details */}
        <div className="md:col-span-2 space-y-8">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">{book.title}</h1>
            {book.subtitle && <h2 className="text-xl text-muted-foreground mt-2">{book.subtitle}</h2>}
            <p className="text-lg font-medium mt-4">
              by {book.authors.map(a => `${a.first_name} ${a.last_name}`).join(', ')}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {book.categories.map(c => (
              <Badge key={c.id} variant="outline" className="text-sm px-3 py-1 bg-primary/5">
                {c.name}
              </Badge>
            ))}
          </div>

          <div>
            <h3 className="text-xl font-semibold mb-3">About this book</h3>
            <div className="prose dark:prose-invert max-w-none text-muted-foreground">
              {book.description || 'No description available.'}
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-6 pt-6 border-t">
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-1">Details</h4>
              <ul className="space-y-2 text-sm">
                <li><span className="font-medium">ISBN:</span> {book.isbn}</li>
                <li><span className="font-medium">Publisher:</span> {book.publisher?.name || 'Unknown'}</li>
                <li><span className="font-medium">Published:</span> {book.publication_date}</li>
                <li><span className="font-medium">Pages:</span> {book.page_count}</li>
                <li><span className="font-medium">Language:</span> {book.language.toUpperCase()}</li>
              </ul>
            </div>
            
            {book.tags && book.tags.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2 flex items-center">
                  <Tag className="mr-2 h-4 w-4" /> Subjects & Tags
                </h4>
                <div className="flex flex-wrap gap-1">
                  {book.tags.map(t => (
                    <Badge key={t.id} variant="secondary" className="text-xs font-normal">
                      {t.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

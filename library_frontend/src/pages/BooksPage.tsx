import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { booksApi } from '../api/books';
import { BookCard } from '../components/books/BookCard';
import { Skeleton } from '../components/ui/skeleton';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Search, BookOpen } from 'lucide-react';

export function BooksPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['books', page, search],
    queryFn: () => booksApi.getBooks({ page, search }),
    placeholderData: (prev) => prev,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  return (
    <div className="space-y-6 pb-8">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Browse Library</h1>
          <p className="text-muted-foreground mt-1">Discover your next great read.</p>
        </div>
        
        <form onSubmit={handleSearch} className="flex w-full md:max-w-sm gap-2">
          <Input 
            placeholder="Search titles, authors..." 
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <Button type="submit" size="icon">
            <Search className="h-4 w-4" />
          </Button>
        </form>
      </div>

      {isLoading ? (
        <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 lg:gap-8 xl:grid-cols-5">
          {[1,2,3,4,5,6,7,8,9,10].map(i => <Skeleton key={i} className="aspect-[2/3] w-full rounded-xl" />)}
        </div>
      ) : (
        <>
          {data?.results?.length === 0 ? (
            <div className="text-center py-20 bg-muted/30 rounded-xl border border-dashed">
              <BookOpen className="h-12 w-12 mx-auto text-muted-foreground" />
              <h3 className="mt-4 text-lg font-semibold">No books found</h3>
              <p className="text-muted-foreground">Try adjusting your search criteria.</p>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 lg:gap-8 xl:grid-cols-5">
              {data?.results?.map(book => (
                <BookCard key={book.id} book={book} />
              ))}
            </div>
          )}

          {/* Pagination */}
          <div className="flex items-center justify-between border-t pt-4">
            <div className="text-sm text-muted-foreground">
              Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, data?.count || 0)} of {data?.count} results
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setPage(p => p - 1)}
                disabled={!data?.previous}
              >
                Previous
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setPage(p => p + 1)}
                disabled={!data?.next}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

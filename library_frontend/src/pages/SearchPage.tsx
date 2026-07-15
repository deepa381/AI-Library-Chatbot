import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { searchApi } from '../api/search';
import { BookCard } from '../components/books/BookCard';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { Search as SearchIcon, SlidersHorizontal } from 'lucide-react';

export function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const [query, setQuery] = useState(initialQuery);
  const [searchInput, setSearchInput] = useState(initialQuery);

  const { data, isLoading } = useQuery({
    queryKey: ['search', query],
    queryFn: () => searchApi.searchBooks(query),
    enabled: !!query,
  });

  useEffect(() => {
    if (initialQuery !== query) {
      setSearchInput(initialQuery);
      setQuery(initialQuery);
    }
  }, [initialQuery]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    setSearchParams({ q: searchInput });
    setQuery(searchInput);
  };

  return (
    <div className="space-y-6 pb-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Global Search</h1>
          <p className="text-muted-foreground mt-1">Search across books, authors, categories, and tags.</p>
        </div>
      </div>

      <div className="rounded-xl border bg-card p-4 shadow-sm">
        <form onSubmit={handleSearch} className="flex gap-2 w-full">
          <Input 
            className="h-12 text-base flex-1"
            placeholder="Search for anything..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <Button type="submit" size="lg" className="px-8">
            <SearchIcon className="mr-2 h-5 w-5" /> Search
          </Button>
          <Button type="button" variant="outline" size="lg" className="px-4">
            <SlidersHorizontal className="h-5 w-5" />
          </Button>
        </form>
      </div>

      {!query ? (
        <div className="text-center py-20 text-muted-foreground">
          <SearchIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Enter a query to start searching the entire catalog.</p>
        </div>
      ) : isLoading ? (
        <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 lg:gap-8 xl:grid-cols-5">
          {[1,2,3,4,5].map(i => <Skeleton key={i} className="aspect-[2/3] w-full rounded-xl" />)}
        </div>
      ) : (
        <div className="space-y-4">
          <h2 className="text-lg font-medium">
            Found {data?.length || 0} result{data?.length !== 1 ? 's' : ''} for "{query}"
          </h2>
          
          {data?.length === 0 ? (
            <div className="text-center py-20 bg-muted/30 rounded-xl border border-dashed">
              <h3 className="mt-4 text-lg font-semibold">No results found</h3>
              <p className="text-muted-foreground">Try adjusting your search keywords.</p>
            </div>
          ) : (
            <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 lg:gap-8 xl:grid-cols-5">
              {data?.map(book => (
                <BookCard key={book.id} book={book} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

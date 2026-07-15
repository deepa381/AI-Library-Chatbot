import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { recommendApi } from '../api/recommend';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { BookCard } from '../components/books/BookCard';
import { toast } from 'react-hot-toast';
import { Sparkles, Search } from 'lucide-react';
import type { Book } from '../types';

export function RecommendPage() {
  const [query, setQuery] = useState('');

  const mutation = useMutation({
    mutationFn: (q: string) => recommendApi.getRecommendations(q),
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to get recommendations');
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || mutation.isPending) return;
    mutation.mutate(query);
  };

  return (
    <div className="space-y-8 pb-8 max-w-6xl mx-auto">
      <div className="text-center max-w-2xl mx-auto space-y-4">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <Sparkles className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">AI Book Recommendations</h1>
        <p className="text-muted-foreground text-lg">
          Tell us what you're in the mood for. Our AI will analyze your reading history and the library's catalog to find the perfect match.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex max-w-2xl mx-auto gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. 'A sci-fi book like Dune but shorter' or 'An inspiring biography'"
          className="h-12 text-base"
          disabled={mutation.isPending}
        />
        <Button type="submit" size="lg" disabled={!query.trim() || mutation.isPending}>
          {mutation.isPending ? (
            <span className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
          ) : (
            <Search className="h-5 w-5" />
          )}
        </Button>
      </form>

      {mutation.isSuccess && mutation.data && (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="rounded-xl border bg-muted/30 p-6 sm:p-8">
            <div className="prose prose-sm sm:prose-base dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {mutation.data.response}
              </ReactMarkdown>
            </div>
          </div>

          {mutation.data.books && mutation.data.books.length > 0 && (
            <div>
              <h3 className="text-2xl font-bold tracking-tight mb-6 flex items-center">
                <Sparkles className="h-6 w-6 mr-2 text-primary" />
                Featured Recommendations
              </h3>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {mutation.data.books.map((book: Book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

import { Link } from 'react-router-dom';
import type { Book } from '../../types';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

import { cn } from '../../lib/utils';

interface BookCardProps {
  book: Book;
  className?: string;
}

export function BookCard({ book, className }: BookCardProps) {
  const isAvailable = book.available_copies > 0;

  return (
    <div className={cn("group relative flex flex-col rounded-xl border bg-card text-card-foreground shadow-sm transition-all hover:shadow-md overflow-hidden", className)}>
      <div className="aspect-[2/3] w-full overflow-hidden bg-muted">
        {book.cover_image ? (
          <img 
            src={book.cover_image} 
            alt={book.title} 
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center bg-secondary/50 text-muted-foreground p-4 text-center">
            No Cover Available
          </div>
        )}
      </div>
      
      <div className="flex flex-1 flex-col p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold line-clamp-1 flex-1" title={book.title}>
            {book.title}
          </h3>
          <Badge variant={isAvailable ? "success" : "secondary"} className="shrink-0">
            {isAvailable ? 'Available' : 'Out'}
          </Badge>
        </div>
        
        <p className="mt-1 text-sm text-muted-foreground line-clamp-1">
          {book.authors?.map(a => `${a.first_name} ${a.last_name}`).join(', ') || 'Unknown Author'}
        </p>
        
        <div className="mt-2 flex flex-wrap gap-1">
          {book.categories?.slice(0, 2).map(c => (
            <span key={c.id} className="inline-flex items-center rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary ring-1 ring-inset ring-primary/20">
              {c.name}
            </span>
          ))}
        </div>

        <div className="mt-auto pt-4 flex gap-2">
          <Button className="w-full" variant="outline" asChild>
            <Link to={`/books/${book.id}`}>Details</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

export interface MemberProfile {
  membership_id: string;
  phone: string;
  department: string;
  membership_type: string;
  borrow_limit: number;
  role: 'LIBRARIAN' | 'MEMBER';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  profile?: MemberProfile;
}

export interface Author {
  id: number;
  first_name: string;
  last_name: string;
  biography?: string;
  date_of_birth?: string;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
}

export interface Tag {
  id: number;
  name: string;
}

export interface Book {
  id: number;
  title: string;
  subtitle?: string;
  isbn: string;
  description: string;
  publication_date: string;
  page_count: number;
  language: string;
  cover_image?: string;
  available_copies: number;
  total_copies: number;
  authors: Author[];
  categories: Category[];
  tags: Tag[];
  publisher: any;
}

export interface BorrowRecord {
  id: number;
  book: Book;
  member: any;
  borrow_date: string;
  due_date: string;
  return_date?: string;
  status: 'BORROWED' | 'RETURNED' | 'OVERDUE';
}

export interface Reservation {
  id: number;
  book: Book;
  member: any;
  reservation_date: string;
  expiry_date?: string;
  status: 'ACTIVE' | 'WAITING' | 'COMPLETED' | 'CANCELLED' | 'EXPIRED';
  queue_position: number;
  remarks?: string;
}

export interface Fine {
  id: number;
  borrow_record: BorrowRecord;
  member: any;
  amount: string;
  reason: string;
  status: 'PENDING' | 'PAID' | 'WAIVED';
  created_at: string;
  paid_at?: string;
}

export interface ChatMessage {
  id: number;
  sender: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: number;
  title: string;
  created_at: string;
  messages: ChatMessage[];
}

export interface RecommendationHistory {
  id: number;
  query: string;
  response: string;
  created_at: string;
  recommended_books: Book[];
}

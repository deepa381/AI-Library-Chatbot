import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/ProtectedRoute';

import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { BooksPage } from './pages/BooksPage';
import { BookDetailPage } from './pages/BookDetailPage';
import { BorrowingPage } from './pages/BorrowingPage';
import { ReservationsPage } from './pages/ReservationsPage';
import { FinesPage } from './pages/FinesPage';
import { ChatPage } from './pages/ChatPage';
import { RecommendPage } from './pages/RecommendPage';
import { SearchPage } from './pages/SearchPage';
import { ProfilePage } from './pages/ProfilePage';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/books" element={<BooksPage />} />
              <Route path="/books/:id" element={<BookDetailPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/recommend" element={<RecommendPage />} />
              <Route path="/borrowing" element={<BorrowingPage />} />
              <Route path="/reservations" element={<ReservationsPage />} />
              <Route path="/fines" element={<FinesPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

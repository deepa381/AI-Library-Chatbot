# Library API Guide

Base URL: `http://localhost:8000/api`

## Authentication (`/api/auth/`)
- `POST /token/` - Obtain JWT tokens (Login)
- `POST /token/refresh/` - Refresh JWT token
- `POST /register/` - Register a new user
- `GET /me/` - Get current user profile (Auth required)

## Dashboard (`/api/dashboard/`)
- `GET /` - Get library overview stats, recent borrows, and charts (Auth required)

## Books & Catalog (`/api/`)
- `GET /books/` - List and search books (Pagination supported)
- `GET /books/<id>/` - Retrieve specific book details
- `GET /categories/` - List all book categories
- `GET /authors/` - List all authors
- `GET /tags/` - List all tags
- `GET /search/?q=<query>` - Global search across books, authors, and categories

## Operations (`/api/`)
- `GET /borrow/` - List user's borrow history (Auth required)
- `POST /borrow/` - Borrow a book. Body: `{ "book": <id> }`
- `PATCH /borrow/<id>/renew/` - Renew an active borrow
- `GET /reservations/` - List user's reservations (Auth required)
- `POST /reservations/` - Reserve/Waitlist a book. Body: `{ "book": <id> }`
- `DELETE /reservations/<id>/` - Cancel a reservation
- `GET /fines/` - List user's fines (Auth required)
- `POST /fines/<id>/pay/` - Simulate paying a fine

## AI Features (`/api/`)
- `GET /chat/history/` - Get user's chat sessions (Auth required)
- `GET /chat/history/<id>/` - Get specific chat session and messages
- `DELETE /chat/history/<id>/` - Delete a chat session
- `POST /chat/` - Send a message to the Librarian AI. Body: `{ "message": "query", "session_id": "optional" }`
- `POST /recommend/` - Get AI book recommendations. Body: `{ "query": "description of what you want" }`

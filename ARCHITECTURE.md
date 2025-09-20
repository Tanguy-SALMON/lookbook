# Lookbook MPC Architecture

This document describes the correct architecture for the Lookbook MPC system, which follows a **Python-first** approach with clear separation between backend logic and frontend interface.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Next.js)                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │   Dashboard     │  │   Admin Panel   │  │   Settings Page         │ │
│  │   (React)       │  │   (React)       │  │   (React)               │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │
│                                   │                                     │
│                            HTTP Requests                                │
│                                   │                                     │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │ Proxy: /api/python/* → :8000/*
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                         BACKEND (Python FastAPI)                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │   API Routes    │  │   Business      │  │   Data Layer            │ │
│  │   - /v1/ingest  │  │   Logic         │  │   - SQLite Database     │ │
│  │   - /v1/reco    │  │   - Use Cases   │  │   - Repository Pattern │ │
│  │   - /v1/chat    │  │   - Domain      │  │   - Adapters           │ │
│  │   - /v1/images  │  │     Entities    │  │                         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │
│                                   │                                     │
│                            External APIs                                │
│                                   │                                     │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
    ┌───────────┐             ┌───────────┐           ┌───────────┐
    │  Ollama   │             │    S3     │           │  MySQL    │
    │  (AI/ML)  │             │ (Images)  │           │ (Shop DB) │
    └───────────┘             └───────────┘           └───────────┘
```

## Core Principles

### 1. **Python-First Backend**
- All business logic, API endpoints, and data processing happen in Python
- FastAPI serves as the main API server on port 8000
- Clean Architecture with domain entities, use cases, and adapters
- Single source of truth for data and business rules

### 2. **Next.js as Pure Frontend**
- React-based dashboard for administration and monitoring
- Runs on port 3000 and proxies API calls to Python backend
- No business logic or data processing in JavaScript
- Only handles UI state management and user interactions

### 3. **API Proxy Pattern**
- Next.js proxies `/api/python/*` requests to `http://localhost:8000/*`
- Frontend calls `/api/python/v1/ingest/items` → Python handles `/v1/ingest/items`
- Environment variables managed through Python configuration endpoints
- No duplicate API logic between frontend and backend

## Current API Endpoints (Python)

### Items Management
- `GET /v1/ingest/items` - List ingested items with pagination and filtering
- `DELETE /v1/ingest/items/{id}` - Delete specific item
- `GET /v1/ingest/stats` - Get ingestion statistics
- `POST /v1/ingest/items` - Start new ingestion process

### Recommendations
- `POST /v1/recommendations` - Get outfit recommendations
- `GET /v1/recommendations/popular` - Get popular recommendations
- `GET /v1/recommendations/trending` - Get trending recommendations

### Chat Interface
- `POST /v1/chat` - Send chat message for recommendations
- `GET /v1/chat/sessions` - List chat sessions
- `GET /v1/chat/sessions/{id}` - Get specific session
- `DELETE /v1/chat/sessions/{id}` - Delete session

### Images
- `GET /v1/images/{key}` - Serve images with optional resizing
- `GET /v1/images/{key}/redirect` - Redirect to original image URL

## Data Flow Examples

### 1. Viewing Items in Dashboard
```
Browser → GET /admin/items
Next.js → Fetch /api/python/v1/ingest/items
Python → Query SQLite database
Python → Return JSON response
Next.js → Render items table
```

### 2. Deleting Items
```
User → Click delete button
Next.js → DELETE /api/python/v1/ingest/items/123
Python → Remove item from database
Python → Return success response
Next.js → Update UI state
```

### 3. Environment Configuration
```
User → Update settings page
Next.js → POST /api/python/config/environment
Python → Update .env file
Python → Restart services if needed
Next.js → Show success message
```

## File Structure

```
test-roocode/
├── main.py                     # Python FastAPI application entry point
├── lookbook_mpc/               # Python backend package
│   ├── api/                    # FastAPI routes
│   │   └── routers/            # Route modules
│   ├── domain/                 # Business logic and entities
│   ├── adapters/               # External service adapters
│   └── config/                 # Configuration management
├── shadcn/                     # Next.js frontend
│   ├── app/                    # Next.js 13+ app directory
│   │   ├── admin/              # Admin dashboard pages
│   │   └── api/                # Next.js API routes (minimal)
│   ├── components/             # React components
│   └── lib/                    # Frontend utilities
└── lookbook.db                 # SQLite database
```

## Development Workflow

### Starting the System
1. **Start Python Backend**: `poetry run python main.py` (port 8000)
2. **Start Next.js Frontend**: `npm run dev` (port 3000)
3. **Access Dashboard**: http://localhost:3000

### Adding New Features
1. **Add API endpoint** in Python (`lookbook_mpc/api/routers/`)
2. **Update database service** in Next.js (`lib/database.ts`)
3. **Create UI components** in React (`app/admin/*/page.tsx`)
4. **Test integration** between frontend and backend

### Environment Management
- Python backend reads from `.env` file in project root
- Settings page in dashboard calls Python API to manage environment
- No direct file system access from Next.js

## Benefits of This Architecture

1. **Single Source of Truth**: All business logic in Python
2. **Type Safety**: Python provides robust type hints and validation
3. **Performance**: Direct database access from Python, no serialization overhead
4. **Maintainability**: Clear separation of concerns
5. **Scalability**: Can deploy frontend and backend independently
6. **Testing**: Business logic testable without UI dependencies

## Anti-Patterns to Avoid

❌ **DON'T**: Create duplicate API logic in Next.js API routes
❌ **DON'T**: Access the database directly from Next.js
❌ **DON'T**: Put business logic in React components
❌ **DON'T**: Manage environment variables from frontend

✅ **DO**: Proxy all data requests to Python backend
✅ **DO**: Keep frontend focused on UI and user interactions
✅ **DO**: Use Python for all data processing and business rules
✅ **DO**: Manage configuration through Python API endpoints

## Next Steps

1. **Complete Python API**: Add missing CRUD endpoints for outfits, rules
2. **Environment API**: Implement configuration management endpoints
3. **Real-time Updates**: Add WebSocket support for live data updates
4. **Authentication**: Implement proper auth flow through Python backend
5. **Error Handling**: Standardize error responses across all APIs
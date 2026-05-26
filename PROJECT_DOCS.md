# 🚀 NexusAI — Smart User Intelligence Platform

## 📋 Project Overview

**NexusAI** is an AI-powered user management platform built on top of a FastAPI + MySQL backend. It combines traditional CRUD operations with intelligent AI features — allowing you to chat with an AI that understands your user database, generate professional content for users, and get AI-driven analytics insights.

**What makes it unique:** The system has a **multi-provider AI fallback engine** — if one AI provider fails (e.g., OpenAI quota exceeded), it automatically switches to the next available provider (Gemini → Groq) without any user intervention.

---

## 🏗️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI (Python) | REST API, dependency injection, auto-docs |
| **Database** | MySQL + SQLAlchemy ORM | Data persistence, user/chat/content storage |
| **Authentication** | JWT (JSON Web Tokens) | Secure login, route protection |
| **Password Security** | bcrypt (via passlib) | Password hashing |
| **AI Provider 1** | OpenAI GPT-4o-mini | Primary AI engine |
| **AI Provider 2** | Google Gemini 2.0 Flash | Free fallback AI |
| **AI Provider 3** | Groq Llama 3.3 70B | Fast free fallback AI |
| **Frontend** | HTML + Tailwind CSS + Alpine.js | Reactive UI, no build step needed |
| **Markdown Rendering** | marked.js | Renders AI responses as formatted HTML |

---

## 📁 Project Structure

```
python-crud-api/
│
├── main.py                    # App entry point — mounts routes, serves UI
├── database.py                # MySQL connection, SQLAlchemy engine setup
├── models.py                  # Database tables (User, ChatMessage, AIContent)
├── schemas.py                 # Pydantic validation schemas (input/output shapes)
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (DB creds, API keys)
│
├── controllers/
│   ├── user_controllers.py    # CRUD logic for users
│   ├── auth_controller.py     # Register & login logic
│   └── ai_controller.py       # Multi-provider AI engine + chat/generate/insights
│
├── routes/
│   ├── user_routes.py         # /users/* endpoints (protected by JWT)
│   ├── auth_routes.py         # /auth/register, /auth/login endpoints
│   └── ai_routes.py           # /ai/chat, /ai/generate, /ai/insights, /ai/providers
│
├── utils/
│   ├── security.py            # JWT creation/verification, password hashing
│   └── dependencies.py        # Auth middleware (extracts user from Bearer token)
│
└── templates/
    └── index.html             # Full UI — dashboard, chat, content generator
```

---

## 🔄 Application Flow

### 1. Startup Flow

```
.env loaded → database.py creates MySQL connection
     ↓
models.py defines 3 tables (users, chat_messages, ai_contents)
     ↓
main.py creates FastAPI app → creates tables if missing
     ↓
AI controller detects available providers (OpenAI/Gemini/Groq)
     ↓
Routes mounted → Server starts on http://127.0.0.1:8000
```

### 2. Authentication Flow

```
User visits http://127.0.0.1:8000
     ↓
Clicks "Login" → Auth modal opens
     ↓
Register: POST /auth/register → password hashed with bcrypt → saved to DB
     ↓
Login: POST /auth/login → verify password → JWT token generated → stored in browser
     ↓
All /users/* requests include "Authorization: Bearer <token>" header
     ↓
JWT middleware validates token before controller runs
```

### 3. AI Chat Flow (with auto-fallback)

```
User types message in chat UI
     ↓
POST /ai/chat { message: "How many users do I have?" }
     ↓
Controller fetches all users from DB → builds context string
     ↓
Constructs prompt: System instructions + User data + User question
     ↓
┌─────────────────────────────────────────┐
│         Multi-Provider Fallback         │
│                                         │
│  Try OpenAI (gpt-4o-mini)               │
│    ├─ Success? → Return response        │
│    └─ Failed? (429/quota/error)         │
│         ↓                               │
│  Try Gemini (gemini-2.0-flash)          │
│    ├─ Success? → Return response        │
│    └─ Failed?                           │
│         ↓                               │
│  Try Groq (llama-3.3-70b-versatile)     │
│    ├─ Success? → Return response        │
│    └─ Failed? → Return error to user    │
└─────────────────────────────────────────┘
     ↓
AI response saved to chat_messages table
     ↓
Response rendered as Markdown in chat UI
```

### 4. Content Generation Flow

```
User selects: Content Type (email/bio/report/social_post)
            + Target User (optional)
            + Extra Instructions (optional)
     ↓
POST /ai/generate { content_type: "bio", user_id: 5 }
     ↓
Controller fetches target user data from DB
     ↓
Builds specialized prompt based on content type
     ↓
Sends to AI (with same fallback chain)
     ↓
Result saved to ai_contents table
     ↓
Rendered in UI with copy-to-clipboard button
```

### 5. AI Insights Flow

```
User clicks "Generate Insights" on dashboard
     ↓
POST /ai/insights {}
     ↓
Controller calculates: total users, average age
     ↓
Fetches all user data → sends to AI with analytics prompt
     ↓
AI returns: trends, demographics analysis, recommendations
     ↓
Displayed on dashboard as formatted Markdown
```

---

## 🗄️ Database Schema

### `users` table
| Column | Type | Notes |
|--------|------|-------|
| id | INT (PK) | Auto-increment |
| name | VARCHAR(100) | Required |
| email | VARCHAR(150) | Unique, indexed |
| password | VARCHAR(255) | bcrypt hashed |
| age | INT | Required |
| created_at | TIMESTAMP | Auto-filled by MySQL |

### `chat_messages` table
| Column | Type | Notes |
|--------|------|-------|
| id | INT (PK) | Auto-increment |
| user_id | INT (FK) | Links to users.id (nullable) |
| role | VARCHAR(20) | "user" or "assistant" |
| content | TEXT | Message content |
| created_at | TIMESTAMP | Auto-filled |

### `ai_contents` table
| Column | Type | Notes |
|--------|------|-------|
| id | INT (PK) | Auto-increment |
| user_id | INT (FK) | Links to users.id (nullable) |
| content_type | VARCHAR(50) | "email", "bio", "report", "social_post" |
| prompt | TEXT | What was asked |
| result | TEXT | AI-generated content |
| created_at | TIMESTAMP | Auto-filled |

---

## 🔌 API Endpoints

### Auth (Public)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new account |
| POST | `/auth/login` | Get JWT access token |

### Users (Protected — requires JWT)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/` | List all users |
| GET | `/users/{id}` | Get single user |
| POST | `/users/` | Create user |
| PUT | `/users/{id}` | Update user |
| DELETE | `/users/{id}` | Delete user |

### AI (Public)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/chat` | Chat with AI about your users |
| POST | `/ai/generate` | Generate content (email/bio/report/post) |
| POST | `/ai/insights` | Get AI analytics about user base |
| GET | `/ai/chat/history` | Fetch recent chat messages |
| GET | `/ai/providers` | Check which AI providers are active |

### UI & Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | NexusAI Dashboard (HTML UI) |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger interactive API docs |

---

## 🤖 Multi-Provider AI Engine — How It Works

```python
# Priority order defined in ai_controller.py
providers = [
    OpenAIProvider(),    # Priority 1 — gpt-4o-mini
    GeminiProvider(),    # Priority 2 — gemini-2.0-flash (FREE)
    GroqProvider(),      # Priority 3 — llama-3.3-70b (FREE)
]
```

**At startup:**
- Each provider checks if its API key exists in `.env`
- Only providers with valid keys are marked as "available"

**On every AI request:**
1. Try Provider #1 (OpenAI)
2. If it fails (quota exceeded, rate limit, network error) → catch exception
3. Try Provider #2 (Gemini)
4. If it fails → try Provider #3 (Groq)
5. If all fail → return error with details from each provider

**Why this matters:**
- OpenAI costs money and has quotas → fails with 429
- Gemini has a generous free tier → great fallback
- Groq is blazing fast with free inference → last resort
- **User never sees downtime** — it just works

---

## 🎨 Frontend UI Features

The entire UI is a **single HTML file** (`templates/index.html`) with no build step:

- **Tailwind CSS** (CDN) — utility-first styling
- **Alpine.js** (CDN) — reactive data binding without React/Vue complexity
- **marked.js** (CDN) — renders AI Markdown responses beautifully

### UI Sections:

| Tab | Features |
|-----|----------|
| **Dashboard** | User stats, AI insights panel, users table with inline AI actions |
| **AI Chat** | Real-time chat with NexusAI, typing indicator, quick prompts |
| **Content AI** | Generate emails/bios/reports/posts, copy to clipboard |

### Design:
- **Glassmorphism dark theme** — translucent cards with blur effects
- **Gradient accents** — violet/indigo color scheme
- **Animations** — chat bubbles slide in, typing dots, pulse indicators
- **Responsive** — works on desktop and mobile

---

## ⚙️ Environment Variables (.env)

```env
# Database
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=python_crud

# Auth
SECRET_KEY=your_random_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI Providers (auto-fallback: OpenAI → Gemini → Groq)
OPENAI_API_KEY=sk-...          # paid
GEMINI_API_KEY=AIza...         # FREE from aistudio.google.com
GROQ_API_KEY=gsk_...           # FREE from console.groq.com
```

---

## ▶️ How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up MySQL database
#    Create a database called "python_crud" in MySQL

# 3. Configure .env
#    Add your DB credentials and at least one AI API key

# 4. Start the server
python -m uvicorn main:app --reload --app-dir "path/to/python-crud-api"

# 5. Open in browser
#    UI:      http://127.0.0.1:8000
#    API Docs: http://127.0.0.1:8000/docs
```

---

## 🔒 Security Features

- **Passwords** are hashed with bcrypt (never stored in plain text)
- **JWT tokens** expire after 60 minutes
- **Protected routes** require valid Bearer token
- **Email enumeration prevention** — login returns same error for wrong email and wrong password
- **SQL injection protection** — SQLAlchemy ORM parameterizes all queries
- **Input validation** — Pydantic schemas enforce field constraints
- **API keys** stored in `.env` (not in source code)

---

## 📊 Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│                    Browser (UI)                       │
│  ┌─────────┐  ┌──────────┐  ┌───────────────────┐   │
│  │Dashboard │  │ AI Chat  │  │ Content Generator │   │
│  └────┬─────┘  └────┬─────┘  └────────┬──────────┘   │
│       │              │                 │              │
└───────┼──────────────┼─────────────────┼──────────────┘
        │              │                 │
        ▼              ▼                 ▼
┌──────────────────────────────────────────────────────┐
│                 FastAPI Backend                       │
│                                                      │
│  /auth/*  →  Auth Controller  →  JWT + bcrypt        │
│  /users/* →  User Controller  →  CRUD Operations     │
│  /ai/*    →  AI Controller    →  Multi-Provider AI   │
│                                                      │
│  ┌──────────────────────────────────────────┐        │
│  │        AI Fallback Engine                │        │
│  │  OpenAI → Gemini → Groq (auto-switch)   │        │
│  └──────────────────────────────────────────┘        │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   MySQL Database │
              │                 │
              │  users          │
              │  chat_messages  │
              │  ai_contents    │
              └─────────────────┘
```

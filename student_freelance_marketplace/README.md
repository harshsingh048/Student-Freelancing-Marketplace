# 🎓 Student Freelancing Marketplace — Backend API

A production-ready REST API built with **FastAPI + PostgreSQL + JWT Auth**.  
Students sell services (gigs), clients buy them, payments are held in escrow, and an admin panel oversees everything.

---

## 📁 Project Structure

```
student_freelance_marketplace/
├── app/
│   ├── main.py                     # FastAPI app entry point
│   ├── config/
│   │   ├── database.py             # Async SQLAlchemy engine + session
│   │   └── settings.py             # Pydantic-settings (.env loader)
│   ├── models/
│   │   ├── user.py                 # User (student / client / admin)
│   │   ├── gig.py                  # Gig / service listing
│   │   ├── order.py                # Order with escrow payment fields
│   │   ├── review.py               # Client review of student
│   │   └── message.py              # Direct chat messages
│   ├── controllers/
│   │   ├── schemas.py              # All Pydantic v2 request/response models
│   │   ├── auth_controller.py      # Signup, login, token refresh
│   │   ├── user_controller.py      # Profile management
│   │   ├── gig_controller.py       # Gig CRUD
│   │   ├── order_controller.py     # Full order lifecycle + escrow
│   │   ├── review_controller.py    # Reviews + auto rating recalc
│   │   ├── admin_controller.py     # Admin controls
│   │   └── message_controller.py  # Chat / messaging
│   ├── routes/
│   │   ├── auth.py                 # /api/v1/auth/*
│   │   ├── users.py                # /api/v1/users/*
│   │   ├── gigs.py                 # /api/v1/gigs/*
│   │   ├── orders.py               # /api/v1/orders/*
│   │   ├── reviews.py              # /api/v1/reviews/*
│   │   ├── messages.py             # /api/v1/messages/*
│   │   └── admin.py                # /api/v1/admin/*
│   ├── middleware/
│   │   └── auth.py                 # JWT dependency + role guards
│   └── utils/
│       ├── security.py             # bcrypt hashing + JWT helpers
│       ├── responses.py            # Standardised JSON envelope
│       ├── file_upload.py          # Local file upload handler
│       └── payment.py              # Mock Razorpay + escrow logic
├── alembic/                        # DB migration scripts
│   ├── env.py
│   └── versions/
├── tests/
│   └── test_api.py                 # Integration tests
├── uploads/                        # Uploaded files (git-ignored)
├── .env.example                    # Copy to .env and fill in values
├── alembic.ini
└── requirements.txt
```

---

## ⚡ Quick Start

### 1. Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| PostgreSQL | 14+ |
| pip | latest |

### 2. Clone & set up virtual environment

```bash
git clone <your-repo-url>
cd student_freelance_marketplace

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Open `.env` and update:

```env
DATABASE_URL=postgresql+asyncpg://YOUR_USER:YOUR_PASSWORD@localhost:5432/student_marketplace
SECRET_KEY=replace-with-a-random-64-char-string
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=YourStrongAdminPass@1
```

### 4. Create the PostgreSQL database

```bash
psql -U postgres -c "CREATE DATABASE student_marketplace;"
```

### 5. Run the server

```bash
# Tables are created automatically on first startup
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Explore the API

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc (clean docs) |
| http://localhost:8000/health | Health check |

---

## 🗄️ Database Migrations (Alembic)

```bash
# Generate a new migration after changing models
alembic revision --autogenerate -m "describe your change"

# Apply pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

---

## 🔐 Authentication

All protected routes require a **Bearer token** in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

Tokens are obtained from `POST /api/v1/auth/login`.  
Access tokens expire in **60 minutes**; refresh tokens in **7 days**.

---

## 📡 API Reference

### Auth Endpoints

#### Register Student
```http
POST /api/v1/auth/signup/student
Content-Type: application/json

{
  "full_name": "Alice Dev",
  "email": "alice@example.com",
  "password": "SecurePass1",
  "skills": ["Python", "FastAPI", "React"],
  "bio": "CS final-year student specializing in backend development"
}
```

**Response `201`:**
```json
{
  "success": true,
  "message": "Student registered successfully.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "3f7a1b2c-...",
      "email": "alice@example.com",
      "full_name": "Alice Dev",
      "role": "student",
      "skills": ["Python", "FastAPI", "React"],
      "average_rating": 0.0,
      "total_reviews": 0
    }
  }
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "alice@example.com",
  "password": "SecurePass1"
}
```

---

### Gig Endpoints

#### Create a Gig (Student only)
```http
POST /api/v1/gigs
Authorization: Bearer <student_token>
Content-Type: application/json

{
  "title": "I will build a FastAPI REST API for your project",
  "description": "Professional backend API using FastAPI, PostgreSQL, JWT auth, and full documentation. Includes all CRUD operations, proper error handling, and deployment guide.",
  "category": "web_development",
  "price": 2500.00,
  "delivery_days": 5,
  "revision_count": 2
}
```

**Response `201`:**
```json
{
  "success": true,
  "message": "Gig created.",
  "data": {
    "id": "9a4c7d3e-...",
    "student_id": "3f7a1b2c-...",
    "title": "I will build a FastAPI REST API for your project",
    "category": "web_development",
    "price": 2500.0,
    "delivery_days": 5,
    "is_active": true,
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

#### List Gigs (Public, with filters)
```http
GET /api/v1/gigs?category=web_development&min_price=500&max_price=5000&search=fastapi&page=1&page_size=10
```

---

### Order Endpoints

#### Step 1 — Place Order (Client)
```http
POST /api/v1/orders
Authorization: Bearer <client_token>
Content-Type: application/json

{
  "gig_id": "9a4c7d3e-...",
  "requirements": "I need a REST API for my e-commerce app. Must include product, cart, and checkout endpoints."
}
```

**Response `201`:**
```json
{
  "success": true,
  "message": "Order placed. Proceed to payment.",
  "data": {
    "order": {
      "id": "b1d2e3f4-...",
      "status": "pending",
      "payment_status": "unpaid",
      "amount": 2500.0,
      "platform_fee": 250.0,
      "student_earnings": 2250.0
    },
    "payment_details": {
      "razorpay_order_id": "order_mock_abc123",
      "amount_paise": 250000,
      "currency": "INR",
      "key_id": "rzp_test_mock_key"
    }
  }
}
```

#### Step 2 — Verify Payment (Client)
```http
POST /api/v1/orders/verify-payment
Authorization: Bearer <client_token>
Content-Type: application/json

{
  "order_id": "b1d2e3f4-...",
  "razorpay_order_id": "order_mock_abc123",
  "razorpay_payment_id": "pay_mock_xyz789",
  "razorpay_signature": "mock_signature_here"
}
```

#### Step 3 — Deliver Order (Student)
```http
POST /api/v1/orders/b1d2e3f4-.../deliver
Authorization: Bearer <student_token>
Content-Type: application/json

{
  "delivery_note": "Completed API with all requested endpoints. GitHub repo: https://github.com/... Deployment guide included in README."
}
```

#### Step 4 — Approve & Release Payment (Client)
```http
POST /api/v1/orders/b1d2e3f4-.../approve
Authorization: Bearer <client_token>
```

---

### Review Endpoints

#### Submit Review (Client, after order completion)
```http
POST /api/v1/reviews
Authorization: Bearer <client_token>
Content-Type: application/json

{
  "order_id": "b1d2e3f4-...",
  "rating": 5,
  "comment": "Alice delivered outstanding work ahead of schedule. Highly recommended!"
}
```

---

### Chat Endpoints

#### Send Message
```http
POST /api/v1/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "receiver_id": "3f7a1b2c-...",
  "content": "Hi Alice, I have a question about your gig before placing an order."
}
```

#### Get Conversation
```http
GET /api/v1/messages/3f7a1b2c-...?page=1&page_size=20
Authorization: Bearer <token>
```

---

### Admin Endpoints

#### Get Platform Stats
```http
GET /api/v1/admin/stats
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "users": { "total": 150, "students": 80, "clients": 70 },
    "orders": { "total": 320, "completed": 280, "disputed": 5 },
    "platform_revenue": 125000.0
  }
}
```

#### Ban a User
```http
POST /api/v1/admin/users/3f7a1b2c-.../ban
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "reason": "Repeated violations of community guidelines."
}
```

#### Resolve Dispute
```http
POST /api/v1/admin/orders/b1d2e3f4-.../resolve-dispute?decision=release
Authorization: Bearer <admin_token>
```

---

## 💳 Payment Flow (Escrow)

```
Client places order
       │
       ▼
  status: PENDING
  payment: UNPAID
       │
       │  Client pays via Razorpay
       ▼
  status: IN_PROGRESS
  payment: HELD  ◄── funds held in escrow
       │
       │  Student delivers work
       ▼
  status: DELIVERED
       │
       ├──► Client APPROVES ──► status: COMPLETED  / payment: RELEASED → Student paid
       │
       └──► Client DISPUTES ──► status: DISPUTED
                                      │
                               Admin resolves:
                               ├─ release → Student paid
                               └─ refund  → Client refunded
```

**Platform fee:** 10% (configurable via `PLATFORM_FEE_PERCENT` in `.env`)

---

## 🧪 Running Tests

```bash
# Install test dependencies (already in requirements.txt)
pip install pytest pytest-asyncio aiosqlite

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --tb=short
```

---

## 🏗️ GigCategory Values

| Value | Description |
|-------|-------------|
| `web_development` | Websites & web apps |
| `mobile_app` | iOS / Android apps |
| `graphic_design` | Logos, UI/UX, illustrations |
| `content_writing` | Articles, blogs, copywriting |
| `data_science` | ML models, data analysis |
| `video_editing` | Video production & editing |
| `digital_marketing` | SEO, social media, ads |
| `tutoring` | Academic tutoring & coaching |
| `other` | Anything else |

---

## 🔒 Role Permissions Summary

| Endpoint | Student | Client | Admin |
|----------|---------|--------|-------|
| Create gig | ✅ | ❌ | ❌ |
| Place order | ❌ | ✅ | ❌ |
| Deliver order | ✅ | ❌ | ❌ |
| Approve / dispute | ❌ | ✅ | ❌ |
| Write review | ❌ | ✅ | ❌ |
| Ban users | ❌ | ❌ | ✅ |
| View all orders | ❌ | ❌ | ✅ |
| Resolve disputes | ❌ | ❌ | ✅ |
| Send messages | ✅ | ✅ | ✅ |

---

## 🚀 Production Deployment Tips

1. **Set `DEBUG=False`** in `.env` — disables SQL query logging and stack traces in errors.
2. **Use a strong `SECRET_KEY`** — generate with `openssl rand -hex 32`.
3. **Serve behind Nginx** as a reverse proxy with SSL (Let's Encrypt).
4. **Use Gunicorn** as the process manager:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
5. **Replace local file storage** with Cloudinary or AWS S3 in `utils/file_upload.py`.
6. **Replace mock Razorpay** with the real SDK in `utils/payment.py`.
7. **Set up Alembic** for all future schema changes — never edit tables manually.

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | Async ORM |
| `asyncpg` | PostgreSQL async driver |
| `alembic` | DB migrations |
| `python-jose` | JWT encoding/decoding |
| `passlib[bcrypt]` | Password hashing |
| `pydantic-settings` | `.env` configuration |
| `aiofiles` | Async file I/O |
| `python-multipart` | File upload parsing |

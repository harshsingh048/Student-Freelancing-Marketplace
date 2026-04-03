# 🚀 Student Freelancing Marketplace

A full-stack backend API for a **Student Freelancing Platform** where students can showcase skills, create gigs, and clients can hire them.

---

## 📌 Features

### 👤 Authentication

* JWT-based authentication
* Access & Refresh tokens
* Secure password hashing (bcrypt)

### 🧑‍🎓 Users

* Student (Seller)
* Client (Buyer)
* Admin
* Profile management

### 💼 Gigs

* Create, update, delete gigs
* Categories & pricing
* Portfolio showcase

### 📦 Orders

* Place orders
* Order status tracking
* Payment simulation

### ⭐ Reviews

* Rating system
* Feedback for gigs

### 💬 Messaging

* Chat between client & student

### 🛡 Admin Panel

* Manage users
* Monitor platform

---

## 🏗️ Tech Stack

* **Backend**: FastAPI
* **Database**: PostgreSQL
* **ORM**: SQLAlchemy (Async)
* **Auth**: JWT (python-jose)
* **Password Hashing**: Passlib + bcrypt
* **Server**: Uvicorn

---

## 📁 Project Structure

```
backend/
│── app/
│   ├── main.py
│   ├── config/
│   │   ├── database.py
│   │   ├── settings.py
│   ├── models/
│   ├── schemas/
│   ├── routes/
│   ├── controllers/
│   ├── utils/
│   ├── services/
│
│── .venv/
│── requirements.txt
```

---

## ⚙️ Installation

### 1️⃣ Clone the repo

```bash
git clone https://github.com/your-username/student-freelance-marketplace.git
cd student-freelance-marketplace
```

---

### 2️⃣ Create virtual environment

```bash
python -m venv .venv
```

Activate:

```bash
# Windows
.venv\Scripts\activate
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

If issues occur:

```bash
pip install fastapi uvicorn sqlalchemy asyncpg passlib[bcrypt] python-jose pydantic-settings aiofiles
```

---

## 🗄️ Database Setup (PostgreSQL)

### 1️⃣ Create database in pgAdmin

* Name: `student_marketplace`

---

### 2️⃣ Set password

```sql
ALTER USER postgres WITH PASSWORD 'Harsh1012';
```

---

### 3️⃣ Update config

```python
DATABASE_URL = "postgresql+asyncpg://postgres:Harsh1012@localhost:5432/student_marketplace"
```

---

## ▶️ Run the Project

```bash
python -m uvicorn app.main:app --reload
```

---

## 🌐 API Docs

Open in browser:

```
http://127.0.0.1:8000/docs
```

---

## 🔑 Default Admin

```
Email: admin@marketplace.com  
Password: Harsh@1012
```

---

## 🧪 Example Endpoints

| Method | Endpoint       | Description   |
| ------ | -------------- | ------------- |
| POST   | /auth/register | Register user |
| POST   | /auth/login    | Login         |
| GET    | /users         | Get users     |
| POST   | /gigs          | Create gig    |
| POST   | /orders        | Place order   |

---

## ⚠️ Common Issues & Fixes

### ❌ asyncpg not found

```bash
pip install asyncpg
```

### ❌ bcrypt error

```bash
pip uninstall bcrypt passlib -y
pip install bcrypt==4.0.1 passlib[bcrypt]
```

### ❌ DB connection error

* Check password
* Avoid special characters like `@`

---

## 🚀 Future Improvements

* Frontend (React / Next.js)
* Payment Gateway Integration
* Real-time chat (WebSockets)
* AI-based gig recommendations

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first.

---

## 📄 License

This project is open-source and free to use.

---

## 👨‍💻 Author

Harsh Kumar Singh , Biprajit Bhattacharya 
B.Tech Students | AI & Backend Enthusiast

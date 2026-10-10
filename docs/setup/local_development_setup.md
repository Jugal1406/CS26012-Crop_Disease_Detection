# Local Development Setup Guide

This guide details the steps to set up and run the Crop Disease Detection application on a local development machine (Windows, Linux, or macOS).

---

## Prerequisites

- **Python**: 3.10 to 3.12 (64-bit)
- **Node.js**: v18.x or v20.x+ with `npm`
- **PostgreSQL**: v14, v15, or v16+ running locally on port `5432`
- **Git**

---

## 1. Clone & Python Environment

```powershell
# In project root:
python -m venv .venv

# Activate on Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Or on Linux / macOS:
# source .venv/bin/activate

# Upgrade pip and install root dependencies:
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2. PostgreSQL Database Setup

1. Start your local PostgreSQL server.
2. Create the project database:
   ```sql
   CREATE DATABASE crop_disease_db;
   ```
3. Configure `backend/.env`:
   ```powershell
   cd backend
   copy .env.example .env
   ```
   Edit `backend/.env` with your local PostgreSQL credentials:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=crop_disease_db
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   ```

4. Run database migrations with Alembic:
   ```powershell
   # From backend/ directory:
   alembic upgrade head
   ```

5. Seed reference crops and disease classes:
   ```powershell
   python seed.py
   ```

6. Verify database connectivity:
   ```powershell
   python tests/test_db_connection.py
   ```

---

## 3. External Service Credentials

In `backend/.env`, configure:
- **Clerk Secret Key**: Obtain from [Clerk Dashboard](https://dashboard.clerk.com/) -> API Keys (`CLERK_SECRET_KEY=sk_test_...`).
- **Groq API Keys**: Configure up to three keys for multi-key rotation and rate-limit fallback:
  ```env
  GROQ_API_KEY_1=gsk_...
  GROQ_API_KEY_2=gsk_...
  GROQ_API_KEY_3=gsk_...
  GROQ_MODEL=openai/gpt-oss-120b
  ```

---

## 4. Frontend Setup

In another terminal window:

```powershell
cd frontend
copy .env.example .env
npm install
```

Configure `frontend/.env` with your Clerk publishable key:
```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

---

## 5. Running the Application

### Start the FastAPI Backend:
```powershell
cd backend
python -m uvicorn main:app --reload --port 8000
```
Backend API will be accessible at: `http://localhost:8000` (Swagger docs: `http://localhost:8000/docs`).

### Start the React Frontend:
```powershell
cd frontend
npm run dev
```
Frontend web application will be accessible at: `http://localhost:5173`.

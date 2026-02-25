import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# --- Database Config ---
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tickets_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# --- FastAPI App ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: verify DB connection
    conn = get_db_connection()
    if conn:
        print("Successfully connected to PostgreSQL at startup.")
        conn.close()
    else:
        print("Warning: Could not connect to PostgreSQL at startup. Will retry on requests.")
    yield
    # Shutdown logic

app = FastAPI(title="Dashboard API", lifespan=lifespan)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/tickets")
def get_tickets(limit: int = 50, offset: int = 0):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM tickets ORDER BY date DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            tickets = cur.fetchall()
            
            # Count total for pagination
            cur.execute("SELECT COUNT(*) as count FROM tickets")
            total = cur.fetchone()['count']
            
            return {
                "total": total,
                "tickets": tickets
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/kpis")
def get_kpis():
    """Returns aggregated data for charts"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection failed")
    
    try:
        kpis = {}
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Total tickets
            cur.execute("SELECT COUNT(*) as count FROM tickets")
            kpis['total_tickets'] = cur.fetchone()['count']
            
            # 2. Tickets by origin
            cur.execute("SELECT origin as name, COUNT(*) as value FROM tickets GROUP BY origin")
            kpis['by_origin'] = cur.fetchall()
            
            # 3. Tickets by category
            cur.execute("SELECT category as name, COUNT(*) as value FROM tickets GROUP BY category")
            kpis['by_category'] = cur.fetchall()
            
            # 4. Tickets by priority
            cur.execute("SELECT priority as name, COUNT(*) as value FROM tickets GROUP BY priority")
            kpis['by_priority'] = cur.fetchall()
            
            return kpis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

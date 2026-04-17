from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import mysql.connector
from mysql.connector import Error

app = FastAPI()

# Enable CORS so your HTML files can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Configuration
db_config = {
    "host": "192.168.1.6",
    "user": "root",
    "password": "stanley",
    "database": "agroboost_db"
}

# --- Models ---
class Farmer(BaseModel):
    name: str
    village: str
    phone: str

class Production(BaseModel):
    farmer: str
    crop: str
    quantity: int

# --- Helper function for DB connection ---
def get_db():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Error: {e}")
        return None

# --- API Endpoints ---

@app.post("/farmers")
def add_farmer(farmer: Farmer):
    conn = get_db()
    cursor = conn.cursor()
    query = "INSERT INTO farmers (name, village, phone) VALUES (%s, %s, %s)"
    cursor.execute(query, (farmer.name, farmer.village, farmer.phone))
    conn.commit()
    conn.close()
    return {"message": "Farmer registered successfully"}

@app.post("/productions")
def add_production(prod: Production):
    # Calculate bonus based on your UI logic
    bonus = 0
    if prod.quantity > 1000:
        bonus = 5000
    elif prod.quantity >= 500:
        bonus = 2000
    
    conn = get_db()
    cursor = conn.cursor()
    query = "INSERT INTO productions (farmer_name, crop, quantity, bonus) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (prod.farmer, prod.crop, prod.quantity, bonus))
    conn.commit()
    conn.close()
    return {"message": "Production recorded", "bonus": bonus}

@app.get("/dashboard-stats")
def get_stats():
    conn = get_db()  
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
        
    try:
        cursor = conn.cursor(dictionary=True)
        # ... the rest of your select queries ...
        
        cursor.execute("SELECT COUNT(*) as total_farmers FROM farmers")
        f_count = cursor.fetchone()['total_farmers']
        
        cursor.execute("SELECT SUM(quantity) as total_qty, SUM(bonus) as total_bonus FROM productions")
        prod_data = cursor.fetchone()
        
        return {
            "total_farmers": f_count,
            "total_qty": prod_data['total_qty'] or 0,
            "total_bonus": prod_data['total_bonus'] or 0
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        conn.close()

@app.get("/records")
def get_records():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT farmer_name as farmer, crop, quantity, bonus FROM productions ORDER BY id DESC")
    results = cursor.fetchall()
    conn.close()
    return results
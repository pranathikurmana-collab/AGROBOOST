from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests

# --- GOVT API LOGIC ---
def get_market_price(commodity: str):
    # REPLACE THIS with your key from data.gov.in
    API_KEY = "579b464db66ec23bdd00000115f7591d366241ce716b47198b87d19f" 
    url = f"https://api.data.gov.in/resource/9ef542fd-9a8d-4d86-b006-7c376a053e43?api-key={API_KEY}&format=json&filters[commodity]={commodity}&filters[state]=Telangana"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('records'):
            # Modal price is usually per Quintal (100kg), converting to per kg
            return float(data['records'][0]['modal_price']) / 100
    except Exception as e:
        print(f"API Error: {e}")
    
    return 40.0  # Fallback price per kg if API fails or crop not found

# --- MySQL Connection Setup ---
USER = "root"
PASSWORD = ""  # Your XAMPP password (usually empty)
HOST = "localhost"
PORT = "3306"
DB_NAME = "agroboost_db1"

DATABASE_URL = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Database Models ---
class FarmerDB(Base):
    __tablename__ = "farmers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    village = Column(String(100))
    phone = Column(String(20))

class ProductionDB(Base):
    __tablename__ = "productions"
    id = Column(Integer, primary_key=True, index=True)
    farmer = Column(String(100))
    crop = Column(String(50))
    quantity = Column(Integer)
    market_price = Column(Float) # New: Price per kg from API
    market_value = Column(Float) # New: Qty * Price
    bonus = Column(Float)

# Create/Update tables
Base.metadata.create_all(bind=engine)

# --- FastAPI App ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas ---
class FarmerCreate(BaseModel):
    name: str
    village: str
    phone: str

class ProductionCreate(BaseModel):
    farmer: str
    crop: str
    quantity: int

# --- Business Logic ---
def calculate_bonus(qty: int) -> int:
    if qty >= 1001: return 5000
    if qty >= 500: return 2000
    return 0

# --- API Endpoints ---

@app.get("/dashboard-stats")
def get_stats():
    db = SessionLocal()
    total_farmers = db.query(FarmerDB).count()
    productions = db.query(ProductionDB).all()
    
    total_qty = sum(p.quantity for p in productions)
    total_bonus = sum(p.bonus for p in productions)
    # New: Total value including market price
    total_revenue = sum((p.market_value or 0) + p.bonus for p in productions)
    
    db.close()
    return {
        "total_farmers": total_farmers,
        "total_qty": total_qty,
        "total_bonus": total_bonus,
        "total_revenue": total_revenue
    }

@app.get("/records")
def get_records():
    db = SessionLocal()
    records = db.query(ProductionDB).order_by(ProductionDB.id.desc()).all()
    db.close()
    return records

@app.post("/farmers")
def add_farmer(farmer: FarmerCreate):
    db = SessionLocal()
    new_farmer = FarmerDB(name=farmer.name, village=farmer.village, phone=farmer.phone)
    db.add(new_farmer)
    db.commit()
    db.close()
    return {"status": "success"}

@app.post("/productions")
def add_production(prod: ProductionCreate):
    db = SessionLocal()
    
    # 1. Get real-time price from Govt API
    current_price = get_market_price(prod.crop)
    
    # 2. Calculate values
    bonus_amt = calculate_bonus(prod.quantity)
    mkt_value = prod.quantity * current_price
    
    # 3. Save to Database
    new_prod = ProductionDB(
        farmer=prod.farmer, 
        crop=prod.crop, 
        quantity=prod.quantity,
        market_price=current_price,
        market_value=mkt_value,
        bonus=bonus_amt
    )
    db.add(new_prod)
    db.commit()
    db.close()
    return {
        "status": "success", 
        "fetched_price": current_price,
        "total_earning": mkt_value + bonus_amt
    }

@app.delete("/clear-records")
def clear_records():
    db = SessionLocal()
    db.query(ProductionDB).delete()
    db.commit()
    db.close()
    return {"status": "cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
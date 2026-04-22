from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, create_engine, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import requests

# --- MySQL Connection Setup ---
USER = "root"
PASSWORD = ""  # Add your password if you have one
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
    market_price = Column(Float)
    market_value = Column(Float)
    bonus = Column(Float)
    status = Column(String(50), default="Pending")
    payment_status = Column(String(50), default="Unpaid")

Base.metadata.create_all(bind=engine)

# --- FastAPI Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class FarmerCreate(BaseModel):
    name: str
    village: str
    phone: str

class ProductionCreate(BaseModel):
    farmer: str
    crop: str
    quantity: int

# --- Helper Functions ---
def get_market_price(commodity: str):
    API_KEY = "579b464db66ec23bdd00000115f7591d366241ce716b47198b87d19f"
    local_market_prices = {
        "maize": 22.50, "paddy": 20.40, "rice": 45.00,
        "onion": 35.00, "tomato": 25.00, "wheat": 28.00, "cotton": 75.00
    }
    search_term = commodity.lower().strip()
    url = f"https://api.data.gov.in/resource/9ef542fd-9a8d-4d86-b006-7c376a053e43?api-key={API_KEY}&format=json&filters[state]=Telangana"
    try:
        response = requests.get(url, timeout=3)
        data = response.json()
        if data.get('records'):
            for record in data['records']:
                if search_term in record['commodity'].lower():
                    return float(record['modal_price']) / 100 
    except: pass
    return local_market_prices.get(search_term, 40.0)

def calculate_bonus(qty: int) -> int:
    if qty >= 1001: return 5000
    if qty >= 500: return 2000
    return 1000

# --- API Endpoints ---

@app.get("/dashboard-stats")
def get_stats():
    db = SessionLocal()
    total_farmers = db.query(FarmerDB).count()
    productions = db.query(ProductionDB).all()
    total_qty = sum(p.quantity for p in productions)
    total_revenue = sum((p.market_value or 0) + (p.bonus or 0) for p in productions)
    db.close()
    return {"total_farmers": total_farmers, "total_qty": total_qty, "total_revenue": total_revenue}
@app.post("/farmers")
def add_farmer(farmer: FarmerCreate):
    db = SessionLocal()
    try:
        new_farmer = FarmerDB(
            name=farmer.name, 
            village=farmer.village, 
            phone=farmer.phone
        )
        db.add(new_farmer)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/records")
def get_records():
    db = SessionLocal()
    records = db.query(ProductionDB).order_by(desc(ProductionDB.id)).all()
    db.close()
    return records

@app.post("/productions")
def add_production(prod: ProductionCreate):
    db = SessionLocal()
    price = get_market_price(prod.crop)
    bonus = calculate_bonus(prod.quantity)
    new_prod = ProductionDB(
        farmer=prod.farmer, crop=prod.crop, quantity=prod.quantity,
        market_price=price, market_value=prod.quantity * price, bonus=bonus
    )
    db.add(new_prod)
    db.commit()
    db.close()
    return {"status": "success"}

@app.post("/purchase")
def process_purchase(crop: str, buy_qty: int):
    db = SessionLocal()
    try:
        records = db.query(ProductionDB).filter(ProductionDB.crop == crop, ProductionDB.quantity > 0).order_by(ProductionDB.id).all()
        total_available = sum(r.quantity for r in records)
        
        if total_available < buy_qty:
            raise HTTPException(status_code=400, detail=f"Only {total_available}kg available.")

        remaining = buy_qty
        for r in records:
            if remaining <= 0: break
            if r.quantity <= remaining:
                remaining -= r.quantity
                r.quantity = 0
            else:
                r.quantity -= remaining
                remaining = 0
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    db = SessionLocal()
    record = db.query(ProductionDB).filter(ProductionDB.id == record_id).first()
    if record:
        db.delete(record)
        db.commit()
    db.close()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
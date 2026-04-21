from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests

# --- GOVT API LOGIC ---
def get_market_price(commodity: str):
    API_KEY = "579b464db66ec23bdd00000115f7591d366241ce716b47198b87d19f" 
    # Fetching all Telangana records to search locally for better matching
    url = f"https://api.data.gov.in/resource/9ef542fd-9a8d-4d86-b006-7c376a053e43?api-key={API_KEY}&format=json&filters[state]=Telangana"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('records'):
            search_term = commodity.lower()
            for record in data['records']:
                # Flexible matching: checks if user input (e.g., "Rice") is in the record (e.g., "Rice(Paddy)")
                if search_term in record['commodity'].lower():
                    modal_price = float(record['modal_price'])
                    return modal_price / 100 
    except Exception as e:
        print(f"Govt API Error: {e}")
    
    return 40.0 # Default price per kg

# --- MySQL Connection Setup ---
USER = "root"
PASSWORD = "" 
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
    # NEW COLUMNS for Logistics and Payments
    status = Column(String(50), default="Pending") # Pending, In Transit, Delivered
    payment_status = Column(String(50), default="Unpaid") # Unpaid, Paid

Base.metadata.create_all(bind=engine)

# --- FastAPI Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    if qty >= 1001: 
        return 5000
    if qty >= 500: 
        return 2000
    # Updated: Now ₹1000 for everything below 500kg
    return 1000

# --- API Endpoints ---

@app.get("/")
def home():
    return {"message": "AgroBoost API is running!"}

@app.get("/dashboard-stats")
def get_stats():
    db = SessionLocal()
    total_farmers = db.query(FarmerDB).count()
    productions = db.query(ProductionDB).all()
    
    total_qty = sum(p.quantity for p in productions)
    # Sum up everything the farmer is owed
    total_revenue = sum((p.market_value or 0) + (p.bonus or 0) for p in productions)
    
    # Count how many are currently being delivered
    active_deliveries = db.query(ProductionDB).filter(ProductionDB.status == "In Transit").count()
    
    db.close()
    return {
        "total_farmers": total_farmers,
        "total_qty": total_qty,
        "total_revenue": total_revenue,
        "active_deliveries": active_deliveries
    }

@app.get("/records")
def get_records():
    db = SessionLocal()
    records = db.query(ProductionDB).order_by(ProductionDB.id.desc()).all()
    db.close()
    return records

@app.get("/get-price/{crop_name}")
def fetch_price(crop_name: str):
    price = get_market_price(crop_name)
    return {"price": price}

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
    current_market_price = get_market_price(prod.crop)
    bonus_amt = calculate_bonus(prod.quantity)
    total_market_value = prod.quantity * current_market_price
    
    new_prod = ProductionDB(
        farmer=prod.farmer, 
        crop=prod.crop, 
        quantity=prod.quantity,
        market_price=current_market_price,
        market_value=total_market_value,
        bonus=bonus_amt
    )
    db.add(new_prod)
    db.commit()
    db.close()
    return {"status": "success", "price_used": current_market_price}
@app.post("/process-payout/{farmer_name}")
def process_payout(farmer_name: str):
    db = SessionLocal()
    # Find all unpaid records for this farmer and mark them paid
    unpaid_records = db.query(ProductionDB).filter(
        ProductionDB.farmer == farmer_name, 
        ProductionDB.payment_status == "Unpaid"
    ).all()
    
    for record in unpaid_records:
        record.payment_status = "Paid"
    
    db.commit()
    db.close()
    return {"status": "success", "message": f"Payments processed for {farmer_name}"}

@app.delete("/records/{record_id}")
def delete_record(record_id: int):
    db = SessionLocal()
    record = db.query(ProductionDB).filter(ProductionDB.id == record_id).first()
    if record:
        db.delete(record)
        db.commit()
        db.close()
        return {"status": "success"}
    db.close()
    return {"status": "error"}, 404

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
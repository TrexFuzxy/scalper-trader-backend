from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
import os
import random
import time

app = FastAPI(title="Scalper Trader API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def root():
    return {
        "message": "Scalper Trader API is running", 
        "version": "1.0.0",
        "endpoints": ["/analyze/", "/signals/{user_id}", "/feedback/", "/risk/"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/analyze/")
async def analyze(file: UploadFile = File(...), timeframe: str = Form(...), user_id: str = Form(...)):
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "csv"]:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use JPG, PNG, or CSV.")
        
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Generate mock trading signal (replace with real analysis later)
        actions = ["BUY", "SELL"]
        action = random.choice(actions)
        
        signal = {
            "action": action,
            "entry": round(random.uniform(1800, 2100), 2),
            "take_profit": round(random.uniform(2100, 2300), 2) if action == "BUY" else round(random.uniform(1600, 1800), 2),
            "stop_loss": round(random.uniform(1600, 1800), 2) if action == "BUY" else round(random.uniform(2100, 2300), 2),
            "confidence": f"{random.randint(70, 95)}%",
            "timeframe": timeframe,
            "timestamp": time.time()
        }
        
        caption = f"AI Analysis: {action} signal detected with {signal['confidence']} confidence on {timeframe} timeframe."
        
        # Mock annotated chart URL (in production, this would be the actual annotated image)
        annotated_chart = f"https://via.placeholder.com/800x600/4CAF50/white?text={action}+Signal"
        
        return {
            "signal": signal,
            "annotated_chart": annotated_chart,
            "caption": caption,
            "file_processed": file.filename
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/signals/{user_id}")
def get_signals(user_id: str):
    # Mock signal history (replace with database query later)
    mock_signals = [
        {
            "id": "signal_1",
            "date": "2024-01-15",
            "action": "BUY",
            "entry": 1950.50,
            "take_profit": 1980.00,
            "stop_loss": 1920.00,
            "confidence": "85%",
            "outcome": "WIN",
            "pnl": "+29.50"
        },
        {
            "id": "signal_2", 
            "date": "2024-01-16",
            "action": "SELL",
            "entry": 1975.25,
            "take_profit": 1945.00,
            "stop_loss": 2005.00,
            "confidence": "78%",
            "outcome": "LOSS",
            "pnl": "-29.75"
        }
    ]
    return {"user_id": user_id, "signals": mock_signals}

@app.post("/feedback/")
def feedback(user_id: str = Form(...), signal_id: str = Form(...), rating: int = Form(...), comment: str = Form(None)):
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    return {
        "message": "Feedback saved successfully",
        "user_id": user_id,
        "signal_id": signal_id,
        "rating": rating,
        "comment": comment,
        "timestamp": time.time()
    }

@app.post("/risk/")
def risk(account_size: float = Form(...), stop_loss: float = Form(...), risk_pct: float = Form(...)):
    if account_size <= 0 or risk_pct <= 0 or risk_pct > 100:
        raise HTTPException(status_code=400, detail="Invalid input values")
    
    # Calculate position size based on risk management
    risk_amount = account_size * (risk_pct / 100)
    position_size = risk_amount / abs(stop_loss)
    
    return {
        "account_size": account_size,
        "risk_percentage": risk_pct,
        "risk_amount": round(risk_amount, 2),
        "stop_loss": stop_loss,
        "position_size": round(position_size, 4),
        "max_loss": round(risk_amount, 2)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

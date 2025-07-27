from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import shutil
import os
import time
from typing import Optional
from technical_analysis import TechnicalAnalyzer
from firebase_service import FirebaseService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Scalper Trader API", version="2.0.0")
security = HTTPBearer(auto_error=False)

# Initialize services
technical_analyzer = TechnicalAnalyzer()
firebase_service = FirebaseService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://scalper-trader-frontend.vercel.app"  # Replace with your actual Vercel frontend URL if different
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Authentication helper
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Get current user from Firebase token"""
    if not credentials:
        return None
    
    user = firebase_service.verify_token(credentials.credentials)
    return user

@app.get("/")
def root():
    return {
        "message": "Scalper Trader API v2.0 - Advanced Trading Signals", 
        "version": "2.0.0",
        "features": ["Real Technical Analysis", "User Authentication", "Signal History", "Advanced Algorithms"],
        "endpoints": ["/analyze/", "/signals/", "/feedback/", "/risk/", "/stats/"]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "timestamp": time.time(),
        "firebase": firebase_service.initialized,
        "technical_analysis": "enabled"
    }

@app.post("/analyze/")
async def analyze(
    file: UploadFile = File(...), 
    timeframe: str = Form(...), 
    user_id: str = Form(...),
    current_user: Optional[dict] = Depends(get_current_user)
):
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "csv"]:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use JPG, PNG, or CSV.")
        
        # Validate timeframe
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        if timeframe not in valid_timeframes:
            raise HTTPException(status_code=400, detail=f"Invalid timeframe. Use: {', '.join(valid_timeframes)}")
        
        # Save uploaded file
        timestamp = int(time.time())
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Perform real technical analysis
        if ext == "csv":
            analysis_result = technical_analyzer.analyze_csv_data(file_path, timeframe)
        else:  # Image files
            analysis_result = technical_analyzer.analyze_chart_image(file_path, timeframe)
        
        # Check for analysis errors
        if analysis_result.get("error"):
            raise HTTPException(status_code=400, detail=analysis_result["message"])
        
        # Generate caption based on analysis
        action = analysis_result["action"]
        confidence = analysis_result["confidence"]
        analysis_type = analysis_result.get("analysis_type", "technical")
        
        if analysis_type == "technical_indicators":
            indicators = analysis_result.get("indicators", {})
            caption = f"Technical Analysis: {action} signal with {confidence} confidence on {timeframe}. RSI: {indicators.get('rsi', 'N/A')}, MACD: {indicators.get('macd', 'N/A')}"
        else:
            caption = f"Chart Pattern Analysis: {action} signal detected with {confidence} confidence on {timeframe} timeframe."
        
        # Generate annotated chart URL (placeholder for now)
        annotated_chart = f"https://via.placeholder.com/800x600/{'4CAF50' if action == 'BUY' else 'F44336'}/white?text={action}+Signal+{confidence}"
        
        # Save signal to database
        signal_saved = firebase_service.save_signal(
            user_id=user_id or "anonymous",
            signal_data=analysis_result,
            file_name=file.filename
        )
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except:
            pass
        
        return {
            "signal": analysis_result,
            "annotated_chart": annotated_chart,
            "caption": caption,
            "file_processed": file.filename,
            "saved_to_history": signal_saved
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/signals/")
def get_signals(
    user_id: str = None,
    limit: int = 50,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get user's trading signals"""
    if not user_id and current_user:
        user_id = current_user["uid"]
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    signals = firebase_service.get_user_signals(user_id, limit)
    return {"user_id": user_id, "signals": signals, "total": len(signals)}

@app.get("/stats/")
def get_user_stats(
    user_id: str = None,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get user trading statistics"""
    if not user_id and current_user:
        user_id = current_user["uid"]
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    stats = firebase_service.get_user_stats(user_id)
    return {"user_id": user_id, "stats": stats}

@app.post("/feedback/")
def feedback(
    user_id: str = Form(...), 
    signal_id: str = Form(...), 
    rating: int = Form(...), 
    comment: str = Form(None),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Save user feedback for a signal"""
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Use authenticated user ID if available
    if current_user:
        user_id = current_user["uid"]
    
    success = firebase_service.save_feedback(user_id, signal_id, rating, comment)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save feedback")
    
    return {
        "message": "Feedback saved successfully",
        "user_id": user_id,
        "signal_id": signal_id,
        "rating": rating,
        "comment": comment,
        "timestamp": time.time()
    }

@app.post("/risk/")
def risk_calculator(
    account_size: float = Form(...), 
    stop_loss: float = Form(...), 
    risk_pct: float = Form(...)
):
    """Advanced risk management calculator"""
    if account_size <= 0 or risk_pct <= 0 or risk_pct > 100:
        raise HTTPException(status_code=400, detail="Invalid input values")
    
    # Calculate position size based on risk management
    risk_amount = account_size * (risk_pct / 100)
    position_size = risk_amount / abs(stop_loss)
    
    # Additional risk metrics
    max_drawdown = risk_amount
    reward_risk_ratio = 2.0  # Default 2:1 RR
    potential_profit = risk_amount * reward_risk_ratio
    
    # Position sizing recommendations
    conservative_size = position_size * 0.5
    aggressive_size = position_size * 1.5
    
    return {
        "account_size": account_size,
        "risk_percentage": risk_pct,
        "risk_amount": round(risk_amount, 2),
        "stop_loss": stop_loss,
        "position_size": round(position_size, 4),
        "max_loss": round(max_drawdown, 2),
        "potential_profit": round(potential_profit, 2),
        "reward_risk_ratio": reward_risk_ratio,
        "recommendations": {
            "conservative": round(conservative_size, 4),
            "normal": round(position_size, 4),
            "aggressive": round(aggressive_size, 4)
        }
    }

@app.get("/market-analysis/")
def market_analysis(symbol: str = "XAUUSD", timeframe: str = "1h"):
    """Get general market analysis for a symbol"""
    # Mock market analysis (replace with real data feed)
    import random
    
    trend = random.choice(["BULLISH", "BEARISH", "SIDEWAYS"])
    volatility = random.choice(["LOW", "MEDIUM", "HIGH"])
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "trend": trend,
        "volatility": volatility,
        "support_levels": [1850.00, 1820.00, 1780.00],
        "resistance_levels": [1950.00, 1980.00, 2020.00],
        "key_events": [
            "Federal Reserve meeting next week",
            "Non-farm payrolls data pending",
            "Geopolitical tensions affecting gold"
        ],
        "recommendation": f"Market shows {trend.lower()} bias with {volatility.lower()} volatility",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

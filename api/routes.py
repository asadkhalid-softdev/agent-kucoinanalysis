from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Dict, Optional, Annotated
import jwt
from datetime import datetime, timedelta
import json
import os

from api.schemas import (
    SymbolRequest, SymbolResponse, AnalysisResponse, 
    AnalysisSummaryResponse, TokenResponse, ConfigRequest
)
from api.middleware import verify_token, get_current_user
from config.settings import Settings
from data.storage import SymbolStorage
from analysis.engine import AnalysisEngine
from data.kucoin_client import KuCoinClient
from config.user_config import UserConfig

# Initialize user config
user_config = UserConfig()

# Initialize FastAPI app
app = FastAPI(
    title="KuCoin Spot Analysis Bot",
    description="AI-powered technical analysis for cryptocurrency markets",
    version="1.0.0"
)

# Initialize components
settings = Settings()
symbol_storage = SymbolStorage()
kucoin_client = KuCoinClient(
    api_key=settings.kucoin_api_key,
    api_secret=settings.kucoin_api_secret,
    api_passphrase=settings.kucoin_api_passphrase
)
analysis_engine = AnalysisEngine()

# Setup OAuth2 with Password Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define API routes
@app.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Get access token for API authentication
    """
    # In a production app, you would verify against a database
    if form_data.username != settings.api_username or form_data.password != settings.api_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

@app.post("/api/symbols", response_model=SymbolResponse)
async def add_symbol(
    symbol_request: SymbolRequest, 
    current_user: str = Depends(get_current_user)
):
    """
    Add a new symbol to track for analysis
    """
    symbol = symbol_request.symbol.upper()
    
    # Validate symbol exists on KuCoin
    try:
        ticker = kucoin_client.get_ticker(symbol)
        if "error" in ticker:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid symbol: {symbol}. Error: {ticker['error']}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error validating symbol: {str(e)}"
        )
    
    # Add symbol to storage
    success = symbol_storage.add_symbol(symbol)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Symbol {symbol} already exists"
        )
    
    return {"symbol": symbol, "status": "added"}

@app.delete("/api/symbols/{symbol}", response_model=SymbolResponse)
async def remove_symbol(
    symbol: str, 
    current_user: str = Depends(get_current_user)
):
    """
    Remove a symbol from tracking
    """
    symbol = symbol.upper()
    success = symbol_storage.remove_symbol(symbol)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol} not found"
        )
    
    return {"symbol": symbol, "status": "removed"}

@app.get("/api/symbols", response_model=List[str])
async def get_symbols(current_user: str = Depends(get_current_user)):
    """
    Get list of all tracked symbols
    """
    return symbol_storage.get_symbols()

@app.get("/api/analysis/{symbol}", response_model=AnalysisResponse)
async def get_symbol_analysis(
    symbol: str, 
    current_user: str = Depends(get_current_user)
):
    """
    Get detailed technical analysis for a specific symbol
    """
    symbol = symbol.upper()
    
    # Check if symbol is being tracked
    if not symbol_storage.symbol_exists(symbol):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol {symbol} is not being tracked"
        )
    
    # Get latest analysis from storage
    analysis = symbol_storage.get_analysis(symbol)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analysis available for {symbol}"
        )
    
    return analysis

@app.get("/api/analysis", response_model=List[AnalysisSummaryResponse])
async def get_all_analyses(
    current_user: str = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get analysis summaries for all tracked symbols
    """
    analyses = []
    symbols = symbol_storage.get_symbols()
    
    for symbol in symbols[:limit]:
        analysis = symbol_storage.get_analysis(symbol)
        if analysis:
            analysis_summary = {
                "symbol": symbol,
                "timestamp": analysis["timestamp"],
                "price": analysis.get("price", 0.0),  # Use get with default value
                "sentiment": analysis["sentiment"],
                "analysis_summary": analysis.get("analysis_summary", "No analysis available")
            }
            analyses.append(analysis_summary)
    
    return analyses

@app.get("/api/analysis/sentiment", response_model=Dict[str, dict])
async def get_sentiment_summary(current_user: str = Depends(get_current_user)):
    """
    Get only sentiment summary for all symbols
    """
    sentiment_summary = {}
    symbols = symbol_storage.get_symbols()
    
    for symbol in symbols:
        analysis = symbol_storage.get_analysis(symbol)
        if analysis and "sentiment" in analysis:
            sentiment_summary[symbol] = analysis["sentiment"]
    
    return sentiment_summary

@app.get("/api/config")
async def get_config(current_user: str = Depends(get_current_user)):
    """
    Get current configuration
    """
    return user_config.get_config()

@app.put("/api/config")
async def update_config(
    config_request: ConfigRequest, 
    current_user: str = Depends(get_current_user)
):
    """
    Update configuration
    """
    # Convert Pydantic model to dict, excluding None values
    config_dict = config_request.dict(exclude_unset=True)
    
    # Update configuration
    success = user_config.update_config(config_dict)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update configuration"
        )
    
    return {"status": "success", "message": "Configuration updated"}

@app.post("/api/config/reset")
async def reset_config(current_user: str = Depends(get_current_user)):
    """
    Reset configuration to defaults
    """
    success = user_config.reset_to_defaults()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset configuration"
        )
    
    return {"status": "success", "message": "Configuration reset to defaults"}
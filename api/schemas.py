from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class SymbolRequest(BaseModel):
    """Request model for adding a symbol"""
    symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTC-USDT')")

class SymbolResponse(BaseModel):
    """Response model for symbol operations"""
    symbol: str
    status: str

class TokenResponse(BaseModel):
    """Response model for token endpoint"""
    access_token: str
    token_type: str

class SentimentData(BaseModel):
    """Model for sentiment data"""
    overall: str = Field(..., description="Overall sentiment (buy, sell, neutral)")
    strength: str = Field(..., description="Sentiment strength (strong, moderate, weak, none)")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    score: Optional[float] = Field(None, description="Raw sentiment score")

class IndicatorValue(BaseModel):
    """Model for indicator values"""
    indicator: str
    value: Any

class AnalysisSummaryResponse(BaseModel):
    """Response model for analysis summary"""
    symbol: str
    timestamp: str
    price: float
    sentiment: SentimentData
    analysis_summary: str

class AnalysisResponse(BaseModel):
    """Response model for detailed analysis"""
    symbol: str
    timestamp: str
    price: float
    indicators: Dict[str, Any]
    sentiment: SentimentData
    analysis_summary: str
    error: Optional[str] = None

class ConfigRequest(BaseModel):
    """Request model for updating configuration"""
    analysis_interval: Optional[int] = Field(None, description="Analysis interval in minutes")
    indicators: Optional[List[str]] = Field(None, description="List of indicators to use")
    timeframes: Optional[List[str]] = Field(None, description="List of timeframes to analyze")

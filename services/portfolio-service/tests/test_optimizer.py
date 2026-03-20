import pandas as pd
import numpy as np
from app.services.optimizer import PortfolioOptimizer

def test_optimize_markowitz_low_risk():
    # Create dummy price data (3 assets, 10 days)
    data = {
        "BTC": [100, 120, 80, 110, 90, 130, 70, 100, 110, 90], # Highly volatile
        "ETH": [200, 220, 180, 210, 190, 230, 170, 200, 210, 190], # Volatile
        "USDT": [1.0, 1.0, 1.0001, 0.9999, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], # Ultra stable
    }
    df = pd.DataFrame(data)
    
    # Low Risk (risk_tolerance = 0.1)
    result = PortfolioOptimizer.optimize_markowitz(df, risk_tolerance=0.1)
    
    assert "weights" in result
    assert "expected_return" in result
    assert "volatility" in result
    # Low risk should favor USDT (stable)
    assert result["weights"]["USDT"] > 0.5 

def test_optimize_markowitz_high_risk():
    data = {
        "BTC": [100, 110, 105, 120, 115, 130, 125, 140, 135, 150], # High return, high volatility
        "ETH": [200, 210, 220, 230, 240, 250, 260, 270, 280, 290], # High return
        "USDT": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # Zero return
    }
    df = pd.DataFrame(data)
    
    # High Risk (risk_tolerance = 0.9)
    result = PortfolioOptimizer.optimize_markowitz(df, risk_tolerance=0.9)
    
    assert "weights" in result
    # High risk should favor high return assets (BTC/ETH) over USDT
    assert result["weights"]["USDT"] < 0.1

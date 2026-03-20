import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, risk_models, expected_returns
from typing import List, Dict

class PortfolioOptimizer:
    @staticmethod
    def optimize_markowitz(prices_df: pd.DataFrame, risk_tolerance: float = 0.5) -> Dict:
        """
        Optimize portfolio based on risk tolerance.
        0.0 - 0.3: Min Volatility (Low Risk)
        0.3 - 0.7: Max Sharpe Ratio (Medium Risk)
        0.7 - 1.0: Efficient Risk (High Risk - target 25% annual volatility)
        """
        # Calculate expected returns and sample covariance
        mu = expected_returns.mean_historical_return(prices_df)
        S = risk_models.sample_cov(prices_df)

        ef = EfficientFrontier(mu, S)
        
        if risk_tolerance < 0.3:
            # Low Risk: Minimize volatility
            weights = ef.min_volatility()
        elif risk_tolerance < 0.7:
            # Medium Risk: Maximize Sharpe Ratio
            weights = ef.max_sharpe()
        else:
            # High Risk: Target specific volatility (e.g., 25%)
            try:
                weights = ef.efficient_risk(target_volatility=0.25)
            except:
                # Fallback to max_sharpe if target is unreachable
                weights = ef.max_sharpe()

        cleaned_weights = ef.clean_weights()
        
        # Performance metrics
        ret, vol, sharpe = ef.portfolio_performance(verbose=False)
        
        return {
            "weights": dict(cleaned_weights),
            "expected_return": float(ret),
            "volatility": float(vol),
            "sharpe_ratio": float(sharpe)
        }

    @staticmethod
    def calculate_risk_metrics(prices_df: pd.DataFrame, weights: Dict[str, float]) -> Dict:
        """
        Calculate Beta, VaR, and Volatility for a given set of weights.
        """
        returns = prices_df.pct_change().dropna()
        portfolio_returns = (returns * pd.Series(weights)).sum(axis=1)
        
        volatility = portfolio_returns.std() * np.sqrt(252)
        var_95 = np.percentile(portfolio_returns, 5)
        
        return {
            "annual_volatility": float(volatility),
            "var_95": float(var_95)
        }

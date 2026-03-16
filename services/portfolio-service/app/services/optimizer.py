import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, risk_models, expected_returns
from typing import List, Dict

class PortfolioOptimizer:
    @staticmethod
    def optimize_markowitz(prices_df: pd.DataFrame) -> Dict:
        """
        Optimize portfolio using Markowitz model (Max Sharpe Ratio).
        Expects a DataFrame where columns are Tickers and rows are timestamps.
        """
        # Calculate expected returns and sample covariance
        mu = expected_returns.mean_historical_return(prices_df)
        S = risk_models.sample_cov(prices_df)

        # Optimize for maximal Sharpe ratio
        ef = EfficientFrontier(mu, S)
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

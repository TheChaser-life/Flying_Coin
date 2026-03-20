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

        def perform_optimization(ef_obj, tolerance):
            if tolerance < 0.3:
                return ef_obj.min_volatility()
            elif tolerance < 0.7:
                return ef_obj.max_sharpe()
            else:
                try:
                    return ef_obj.efficient_risk(target_volatility=0.25)
                except:
                    return ef_obj.max_sharpe()

        try:
            weights = perform_optimization(ef, risk_tolerance)
        except (ValueError, Exception):
            # Fallback for math errors (e.g. returns < risk-free rate)
            ef = EfficientFrontier(mu, S)
            weights = ef.min_volatility()

        cleaned_weights = ef.clean_weights()
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

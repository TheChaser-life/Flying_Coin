import pandas as pd
import numpy as np
from typing import Dict, List

class BacktestEngine:
    @staticmethod
    def run_sma_crossover(df: pd.DataFrame, short_window: int = 20, long_window: int = 50, initial_capital: float = 10000.0) -> Dict:
        """
        Simple Moving Average Crossover strategy.
        """
        # Calculate signals
        df['short_mavg'] = df['close'].rolling(window=short_window, min_periods=1).mean()
        df['long_mavg'] = df['close'].rolling(window=long_window, min_periods=1).mean()
        
        df['signal'] = 0.0
        df['signal'] = np.where(df['short_mavg'] > df['long_mavg'], 1.0, 0.0)
        df['positions'] = df['signal'].diff().fillna(0.0)

        # Backtest
        positions = pd.DataFrame(index=df.index).fillna(0.0)
        positions['asset'] = 100 * df['signal'] # Example: buy 100 units
        
        portfolio = positions.multiply(df['close'], axis=0)
        pos_diff = positions.diff()
        
        portfolio['cash'] = initial_capital - (pos_diff.multiply(df['close'], axis=0)).cumsum()
        portfolio['total'] = portfolio['cash'] + portfolio['asset']
        portfolio['returns'] = portfolio['total'].pct_change()
        
        # Metrics
        final_total = portfolio['total'].iloc[-1]
        total_return = (final_total / initial_capital) - 1 if initial_capital > 0 else 0
        
        returns = portfolio['returns'].dropna()
        if len(returns) > 1 and returns.std() != 0:
            sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()
        else:
            sharpe_ratio = 0.0
        
        # Max Drawdown
        rolling_max = portfolio['total'].cummax()
        drawdown = portfolio['total'] / rolling_max - 1.0
        max_drawdown = drawdown.min()
        
        # Win Rate
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0
        
        equity_curve = [{"timestamp": str(idx), "value": float(val)} for idx, val in portfolio['total'].items()]
        
        def safe_float(v):
            return float(v) if np.isfinite(v) else 0.0

        return {
            "total_return": safe_float(total_return),
            "sharpe_ratio": safe_float(sharpe_ratio),
            "max_drawdown": safe_float(max_drawdown),
            "win_rate": safe_float(win_rate),
            "equity_curve": equity_curve
        }

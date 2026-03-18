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
        total_return = (portfolio['total'].iloc[-1] / initial_capital) - 1
        sharpe_ratio = np.sqrt(252) * portfolio['returns'].mean() / portfolio['returns'].std()
        
        # Max Drawdown
        rolling_max = portfolio['total'].cummax()
        drawdown = portfolio['total'] / rolling_max - 1.0
        max_drawdown = drawdown.min()
        
        # Win Rate
        trades = portfolio['returns'].dropna()
        win_rate = (trades > 0).sum() / len(trades) if len(trades) > 0 else 0
        
        equity_curve = [{"timestamp": str(idx), "value": float(val)} for idx, val in portfolio['total'].items()]
        
        return {
            "total_return": float(total_return),
            "sharpe_ratio": float(sharpe_ratio) if not np.isnan(sharpe_ratio) else 0.0,
            "max_drawdown": float(max_drawdown),
            "win_rate": float(win_rate),
            "equity_curve": equity_curve
        }

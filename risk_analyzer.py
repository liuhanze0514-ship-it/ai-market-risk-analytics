import numpy as np
import pandas as pd
from scipy.stats import norm

from data_fetcher import fetch_daily_returns


class VarCalculator:
    """Value-at-Risk calculator using historical simulation and parametric methods."""

    def __init__(self, returns: pd.DataFrame):
        if isinstance(returns, pd.Series):
            returns = returns.to_frame()
        self.returns = returns.dropna()

    def historical_var(self, ticker: str, confidence: float = 0.95) -> float:
        """Calculate VaR using historical simulation."""
        if ticker not in self.returns.columns:
            raise KeyError(f"Ticker '{ticker}' not found in returns data")

        losses = -self.returns[ticker]
        quantile = losses.quantile(confidence)
        return float(quantile)

    def parametric_var(self, ticker: str, confidence: float = 0.95) -> float:
        """Calculate VaR using the parametric (variance-covariance) method."""
        if ticker not in self.returns.columns:
            raise KeyError(f"Ticker '{ticker}' not found in returns data")

        series = self.returns[ticker]
        mu = series.mean()
        sigma = series.std(ddof=1)
        z = norm.ppf(1 - confidence)
        var = -(mu + sigma * z)
        return float(var)

    def compare_vars(self, tickers, confidences=(0.95, 0.99)) -> pd.DataFrame:
        rows = []
        for ticker in tickers:
            for confidence in confidences:
                hist = self.historical_var(ticker, confidence)
                param = self.parametric_var(ticker, confidence)
                rows.append({
                    "Ticker": ticker,
                    "Confidence": f"{int(confidence * 100)}%",
                    "Historical VaR": hist,
                    "Parametric VaR": param,
                })
        return pd.DataFrame(rows)


if __name__ == "__main__":
    tickers = ["^GSPC", "TSLA"]
    close_prices, daily_returns = fetch_daily_returns(tickers)

    analyzer = VarCalculator(daily_returns)
    comparison = analyzer.compare_vars(tickers, confidences=(0.95, 0.99))

    print("\nValue-at-Risk (VaR) comparison for 1-day horizon")
    print("Data source: daily returns for ^GSPC and TSLA")
    print("(VaR is shown as positive loss magnitude)")
    print(comparison.to_string(index=False, float_format="{:.6f}".format))

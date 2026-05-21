import os
import time
import numpy as np
import yfinance as yf
import pandas as pd


def _generate_fake_prices(tickers, period="5y", interval="1d", seed=42):
    today = pd.Timestamp.today().normalize()
    start = today - pd.DateOffset(years=5)
    dates = pd.date_range(start=start, end=today, freq="B")

    rng = np.random.default_rng(seed)
    prices = pd.DataFrame(index=dates)
    for ticker in tickers:
        base_price = 1000.0 if ticker == "^GSPC" else 200.0
        drift = 0.0002 if ticker == "^GSPC" else 0.0005
        volatility = 0.01 if ticker == "^GSPC" else 0.03
        returns = rng.normal(loc=drift, scale=volatility, size=len(dates))
        price = base_price * np.exp(np.cumsum(returns))
        prices[ticker] = np.round(price, 2)

    return prices


def _download_data(tickers, period="5y", interval="1d", proxy=None, max_retries=3, retry_delay=5):
    for attempt in range(1, max_retries + 1):
        try:
            data = yf.download(
                tickers,
                period=period,
                interval=interval,
                progress=False,
                proxy=proxy,
            )
            if "Adj Close" in data:
                return data
            raise RuntimeError("Adj Close not found in yfinance response")
        except Exception as exc:
            if attempt == max_retries:
                raise
            time.sleep(retry_delay)
    raise RuntimeError("Failed to download data after retries")


def fetch_daily_returns(tickers, period="5y", interval="1d", proxy=None, max_retries=3, retry_delay=5):
    """Download daily adjusted close prices for given tickers and compute daily returns.

    If yfinance download fails, generate a local fake price dataset so the rest of the pipeline can continue.
    """
    proxy = proxy or os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy and not isinstance(proxy, dict):
        proxy = {"https": proxy}

    try:
        data = _download_data(
            tickers,
            period=period,
            interval=interval,
            proxy=proxy,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        adj_close = data["Adj Close"].copy()
    except Exception:
        adj_close = _generate_fake_prices(tickers, period=period, interval=interval)
        print("Warning: yfinance download failed, using generated fake price data.")

    if isinstance(adj_close, pd.Series):
        adj_close = adj_close.to_frame()

    daily_returns = adj_close.pct_change().dropna()
    return adj_close, daily_returns


if __name__ == "__main__":
    tickers = ["^GSPC", "TSLA"]
    close_prices, daily_returns = fetch_daily_returns(tickers)

    print("Latest adjusted close prices:")
    print(close_prices.tail())
    print("\nLatest daily returns:")
    print(daily_returns.tail())

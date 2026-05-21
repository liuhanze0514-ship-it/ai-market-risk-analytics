import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest

from data_fetcher import fetch_daily_returns


def rolling_max_drawdown(returns: pd.Series, window: int) -> pd.Series:
    """Compute rolling max drawdown over the given window (as a positive number).

    For each window, convert returns to cumulative price path starting at 1,
    compute running peak and drawdowns, and return the maximum drawdown (positive).
    """
    def _window_mdd(arr):
        # arr is a 1D numpy array of returns for the window
        if np.isnan(arr).any():
            return np.nan
        prices = np.cumprod(1 + arr)
        peaks = np.maximum.accumulate(prices)
        drawdowns = prices / peaks - 1.0
        return -np.min(drawdowns) if drawdowns.size > 0 else np.nan

    return returns.rolling(window).apply(_window_mdd, raw=True)


def build_features(returns: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    features = []
    for col in returns.columns:
        series = returns[col]
        vol = series.rolling(window).std(ddof=1)  # rolling volatility (std of daily returns)
        mdd = rolling_max_drawdown(series, window)
        df = pd.DataFrame({f"{col}_vol{window}": vol, f"{col}_mdd{window}": mdd})
        features.append(df)

    feat = pd.concat(features, axis=1)
    return feat


def detect_anomalies(features: pd.DataFrame, contamination: float = 0.01, random_state: int = 42):
    clf = IsolationForest(n_estimators=200, contamination=contamination, random_state=random_state)
    X = features.dropna()
    if X.empty:
        raise ValueError("No feature rows available for training. Check input data and rolling window size.")

    clf.fit(X.values)
    preds = clf.predict(X.values)  # -1 anomaly, 1 normal
    results = X.copy()
    results["anomaly"] = (preds == -1).astype(int)
    scores = clf.decision_function(X.values)
    results["anomaly_score"] = scores
    return results


if __name__ == "__main__":
    tickers = ["^GSPC", "TSLA"]
    _, daily_returns = fetch_daily_returns(tickers)

    window = 5
    features = build_features(daily_returns, window=window)

    contamination = 0.002  # expect ~0.2% of days as anomalies; adjust as needed
    try:
        results = detect_anomalies(features, contamination=contamination)
    except ValueError as e:
        print("Error running anomaly detection:", e)
        raise

    total_anomalies = int(results["anomaly"].sum())
    print(f"\nTotal anomaly days detected (IsolationForest): {total_anomalies}")

    # Join back the returns for reporting
    report = results.join(daily_returns, how="left")

    anomalies = report[report["anomaly"] == 1]
    if anomalies.empty:
        print("No anomalies detected with current contamination setting.")
    else:
        recent = anomalies.sort_index(ascending=False).head(5)
        print("\nMost recent 5 detected anomaly days:")
        display_cols = []
        for t in tickers:
            display_cols.append(t)
            display_cols.append(f"{t}_vol{window}")
            display_cols.append(f"{t}_mdd{window}")
        display_cols = [c for c in display_cols if c in recent.columns]

        to_show = recent[display_cols]
        # Format and print: ensure full columns and wide output
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.float_format', '{:.6f}'.format)
        print(to_show)

    print("\nYou can adjust `contamination` or the rolling `window` in this script to tune sensitivity.")

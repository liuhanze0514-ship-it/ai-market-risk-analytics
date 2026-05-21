AI-Driven Market & Trading Risk Analytics Dashboard

## Project Overview

AI-Driven Market & Trading Risk Analytics Dashboard implements end-to-end market risk analysis tools including simulated/retrieved market data, Value-at-Risk (VaR) calculations, and stress testing for both systemic and idiosyncratic events.

Key capabilities:
- Simulated or real historical price retrieval (via yfinance, with proxy & fallback to generated data)
- VaR calculation using Historical Simulation and Parametric (variance-covariance) methods
- Stress testing for crisis and black-swan scenarios
- Simple visual reporting (PNG) for stress-test results

## Core Tech Stack

- Python
- yfinance
- pandas
- NumPy
- SciPy
- Matplotlib
- Seaborn

## Repository Files

- `data_fetcher.py` — download prices / generate fallback synthetic prices and compute daily returns
- `risk_analyzer.py` — VaR calculations (historical & parametric)
- `stress_tester.py` — scenario-based stress testing and visualization
- `ml_risk_detector.py` — machine-learning based anomaly detection (IsolationForest) using rolling volatility and drawdown features
- `requirements.txt` — Python dependencies
- `stress_test_report.png` — example output image (created after running `stress_tester.py`)

## Quick Start (Windows PowerShell)

1. Create and activate a virtual environment:

```powershell
cd d:\Code\ai-market-risk-analytics
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the VaR analyzer:

```powershell
python risk_analyzer.py
```

3.1 Run the machine-learning anomaly detector:

```powershell
python ml_risk_detector.py
```

4. Run the stress tester (will produce `stress_test_report.png`):

```powershell
python stress_tester.py
```

The stress test script prints a summary to the terminal and saves a chart named `stress_test_report.png` in the project root.

## Result Preview

![Stress Test Report](stress_test_report.png)

## Notes

- If `yfinance` cannot reach remote data sources (network/proxy issues), `data_fetcher.py` falls back to generating realistic-looking synthetic price series so downstream analysis can continue offline.
- You can control proxy settings via the `HTTPS_PROXY` / `https_proxy` environment variable or by modifying the call to `fetch_daily_returns()`.

## Machine Learning Anomaly Detection & Tuning

The project includes an unsupervised anomaly detection module (`ml_risk_detector.py`) that extracts rolling features (5-day volatility and 5-day maximum drawdown) from historical daily returns and applies `IsolationForest` to identify extreme market anomaly days.

Why tuning matters:

- The default anomaly `contamination=0.01` (1%) produced around 13 detected anomaly days over the 5-year history, which proved too noisy for operational risk monitoring. To focus on the most extreme events, we tuned `contamination` to `0.002` (0.2%), which reduces false positives and isolates the top ~2–3 extreme days.

Latest detected extreme days (representative analysis):

- **2025-01-09 / 2025-01-10** — consecutive systemic hits: both days show large negative returns for `^GSPC` accompanied by elevated 5-day volatility and drawdown across the market, consistent with a short-lived but deep market crisis period.
- **2023-05-01** — idiosyncratic TSLA event: the S&P500 exhibited a strong positive move while `TSLA` suffered a marked negative return; rolling volatility and drawdown for `TSLA` spike sharply, indicating a company-specific shock (recall/regulatory or event-driven sell-off).

You can reproduce or retune the detection by running:

```powershell
python ml_risk_detector.py
```

Adjust the `contamination` parameter in the script to change sensitivity (smaller -> fewer, more extreme anomalies).



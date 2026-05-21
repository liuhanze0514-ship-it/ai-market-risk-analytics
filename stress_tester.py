import matplotlib.pyplot as plt
import pandas as pd

from data_fetcher import fetch_daily_returns


class StressTester:
    """Stress testing module for a simple two-asset portfolio."""

    def __init__(self, returns: pd.DataFrame, portfolio: dict):
        if isinstance(returns, pd.Series):
            returns = returns.to_frame()
        self.returns = returns.dropna()
        self.portfolio = portfolio
        self.portfolio_value = sum(portfolio.values())

    def scenario_loss(self, scenario: dict) -> dict:
        """Compute absolute and percentage loss for a stress scenario."""
        loss_amount = 0.0
        for ticker, shock in scenario.items():
            position = self.portfolio.get(ticker, 0.0)
            loss_amount += position * abs(shock)

        loss_pct = loss_amount / self.portfolio_value if self.portfolio_value else 0.0
        return {
            "loss_amount": loss_amount,
            "loss_pct": loss_pct,
            "portfolio_value": self.portfolio_value,
            "scenario": scenario,
        }

    def run_scenarios(self, scenarios: dict) -> pd.DataFrame:
        rows = []
        for name, scenario in scenarios.items():
            result = self.scenario_loss(scenario)
            rows.append(
                {
                    "Scenario": name,
                    "^GSPC Shock": f"{scenario.get('^GSPC', 0.0) * 100:+.1f}%",
                    "TSLA Shock": f"{scenario.get('TSLA', 0.0) * 100:+.1f}%",
                    "Portfolio Loss ($)": result["loss_amount"],
                    "Portfolio Loss (%)": result["loss_pct"] * 100,
                }
            )
        return pd.DataFrame(rows)


    def portfolio_values(self, scenarios: dict) -> pd.DataFrame:
        rows = []
        for name, scenario in scenarios.items():
            result = self.scenario_loss(scenario)
            remaining_value = self.portfolio_value - result["loss_amount"]
            rows.append(
                {
                    "Scenario": name,
                    "Portfolio Value": remaining_value,
                }
            )
        return pd.DataFrame(rows)


def format_results(df: pd.DataFrame) -> str:
    return df.to_string(index=False, float_format="{:.2f}".format)


def plot_portfolio_values(df: pd.DataFrame, output_path: str):
    plt.figure(figsize=(9, 6))
    bars = plt.bar(df["Scenario"], df["Portfolio Value"], color=["#4C72B0", "#DD8452", "#55A868"])
    plt.title("Portfolio Value Under Stress Scenarios")
    plt.xlabel("Scenario")
    plt.ylabel("Portfolio Value (USD)")
    plt.ylim(0, df["Portfolio Value"].max() * 1.1)
    plt.grid(axis="y", linestyle="--", alpha=0.25)

    for bar in bars:
        height = bar.get_height()
        plt.annotate(
            f"${height:,.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


if __name__ == "__main__":
    tickers = ["^GSPC", "TSLA"]
    _, daily_returns = fetch_daily_returns(tickers)

    portfolio = {"^GSPC": 10000.0, "TSLA": 5000.0}
    scenarios = {
        "Crisis Scenario": {"^GSPC": -0.08, "TSLA": -0.15},
        "Black Swan Scenario": {"^GSPC": 0.00, "TSLA": -0.25},
    }

    stress_tester = StressTester(daily_returns, portfolio)
    results = stress_tester.run_scenarios(scenarios)

    print("\nStress Testing Results")
    print("========================")
    print("Initial portfolio value: ${:,.2f}".format(stress_tester.portfolio_value))
    print("Portfolio allocation: 10,000 USD in ^GSPC, 5,000 USD in TSLA")
    print("\nExtreme stress scenarios and portfolio loss estimates:")
    print(format_results(results))

    values_df = stress_tester.portfolio_values(scenarios)
    values_df = pd.concat([
        pd.DataFrame([{"Scenario": "Initial", "Portfolio Value": stress_tester.portfolio_value}]),
        values_df,
    ], ignore_index=True)

    output_path = "stress_test_report.png"
    plot_portfolio_values(values_df, output_path)
    print(f"\nSaved stress test chart to: {output_path}")

"""Generate a reproducible synthetic Order-to-Cash event log.

The dataset is synthetic and is intended for learning and portfolio demonstration.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


def generate_event_log(n_cases: int = 1500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    start = pd.Timestamp("2025-01-01 08:00:00")
    for i in range(1, n_cases + 1):
        case_id = f"ORD-{i:05d}"
        customer = f"CUST-{rng.integers(1, 251):04d}"
        region = rng.choice(["North", "South", "East", "West"], p=[.28, .25, .22, .25])
        order_value = round(float(rng.lognormal(mean=5.2, sigma=.75)), 2)
        ts = start + pd.Timedelta(minutes=int(rng.integers(0, 180 * 24 * 60)))
        rows.append((case_id, "Order Created", ts, customer, region, order_value))

        # A small number of cases fail credit check and are cancelled.
        if rng.random() < .055:
            ts += pd.Timedelta(hours=int(rng.integers(2, 48)))
            rows.append((case_id, "Credit Check", ts, customer, region, order_value))
            ts += pd.Timedelta(hours=int(rng.integers(1, 12)))
            rows.append((case_id, "Order Cancelled", ts, customer, region, order_value))
            continue

        ts += pd.Timedelta(hours=float(rng.gamma(2.0, 2.2)))
        rows.append((case_id, "Credit Check", ts, customer, region, order_value))

        # Some orders require a manual credit review, creating a rework loop.
        if rng.random() < .13:
            ts += pd.Timedelta(hours=float(rng.uniform(5, 30)))
            rows.append((case_id, "Manual Review", ts, customer, region, order_value))
            ts += pd.Timedelta(hours=float(rng.uniform(2, 18)))
            rows.append((case_id, "Credit Check", ts, customer, region, order_value))

        ts += pd.Timedelta(hours=float(rng.gamma(1.8, 2.0)))
        rows.append((case_id, "Payment Received", ts, customer, region, order_value))
        ts += pd.Timedelta(hours=float(rng.gamma(2.0, 3.5)))
        rows.append((case_id, "Order Approved", ts, customer, region, order_value))

        # Inventory shortage creates a delay and an additional procurement step.
        if rng.random() < .18:
            ts += pd.Timedelta(hours=float(rng.uniform(18, 72)))
            rows.append((case_id, "Inventory Replenished", ts, customer, region, order_value))
        ts += pd.Timedelta(hours=float(rng.gamma(2.0, 4.0)))
        rows.append((case_id, "Pick and Pack", ts, customer, region, order_value))

        # A small re-pick loop models operational rework.
        if rng.random() < .045:
            ts += pd.Timedelta(hours=float(rng.uniform(2, 10)))
            rows.append((case_id, "Pick and Pack", ts, customer, region, order_value))

        ts += pd.Timedelta(hours=float(rng.gamma(2.0, 5.0)))
        rows.append((case_id, "Shipped", ts, customer, region, order_value))
        ts += pd.Timedelta(hours=float(rng.gamma(2.0, 10.0)))
        rows.append((case_id, "Delivered", ts, customer, region, order_value))

    df = pd.DataFrame(rows, columns=["case_id", "activity", "timestamp", "customer_id", "region", "order_value"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values(["case_id", "timestamp", "activity"]).reset_index(drop=True)


if __name__ == "__main__":
    df = generate_event_log()
    out = DATA / "order_to_cash_event_log.csv"
    df.to_csv(out, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print(f"Saved {len(df):,} events across {df.case_id.nunique():,} cases to {out}")

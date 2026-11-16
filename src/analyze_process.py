"""Analyze an event log and export case, activity, and transition metrics."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def load_event_log(path: Path | None = None) -> pd.DataFrame:
    path = path or DATA / "order_to_cash_event_log.csv"
    df = pd.read_csv(path, parse_dates=["timestamp"])
    required = {"case_id", "activity", "timestamp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Event log is missing required columns: {sorted(missing)}")
    if df[list(required)].isna().any().any():
        raise ValueError("case_id, activity, and timestamp must not contain null values")
    return df.sort_values(["case_id", "timestamp", "activity"]).reset_index(drop=True)


def build_metrics(df: pd.DataFrame):
    grouped = df.groupby("case_id", sort=False)
    cases = grouped.agg(
        start_time=("timestamp", "min"),
        end_time=("timestamp", "max"),
        event_count=("activity", "size"),
        region=("region", "first"),
        order_value=("order_value", "first"),
    ).reset_index()
    cases["cycle_time_hours"] = (cases.end_time - cases.start_time).dt.total_seconds() / 3600
    final_activity = grouped.tail(1).set_index("case_id")["activity"]
    cases["final_activity"] = cases.case_id.map(final_activity)
    cases["is_cancelled"] = cases.final_activity.eq("Order Cancelled")
    cases["is_delivered"] = cases.final_activity.eq("Delivered")
    cases["is_rework"] = grouped["activity"].apply(
        lambda s: s.duplicated().any()
    ).reindex(cases.case_id).fillna(False).to_numpy()
    cases["is_delayed"] = cases.cycle_time_hours.gt(72) & cases.is_delivered

    activity = df.groupby("activity").agg(
        event_count=("case_id", "size"),
        cases=("case_id", "nunique"),
        first_seen=("timestamp", "min"),
    ).reset_index().sort_values("event_count", ascending=False)

    ordered = df.sort_values(["case_id", "timestamp"]).copy()
    ordered["next_activity"] = ordered.groupby("case_id")["activity"].shift(-1)
    ordered["next_timestamp"] = ordered.groupby("case_id")["timestamp"].shift(-1)
    transitions = ordered.dropna(subset=["next_activity"]).copy()
    transitions["wait_hours"] = (transitions.next_timestamp - transitions.timestamp).dt.total_seconds() / 3600
    transitions = transitions.groupby(["activity", "next_activity"]).agg(
        transition_count=("case_id", "size"),
        avg_wait_hours=("wait_hours", "mean"),
        median_wait_hours=("wait_hours", "median"),
    ).reset_index().sort_values("transition_count", ascending=False)

    variants = grouped["activity"].apply(lambda s: " → ".join(s.astype(str))).value_counts().rename_axis("process_variant").reset_index(name="case_count")
    variants["share_pct"] = variants.case_count / cases.case_id.nunique() * 100
    return cases, activity, transitions, variants


def main():
    df = load_event_log()
    cases, activity, transitions, variants = build_metrics(df)
    cases.to_csv(OUT / "case_metrics.csv", index=False)
    activity.to_csv(OUT / "activity_metrics.csv", index=False)
    transitions.to_csv(OUT / "transition_metrics.csv", index=False)
    variants.to_csv(OUT / "process_variants.csv", index=False)
    print(f"Cases: {len(cases):,}; events: {len(df):,}")
    print(f"Delivered: {cases.is_delivered.mean():.1%}; cancelled: {cases.is_cancelled.mean():.1%}")
    print(f"Median cycle time: {cases.loc[cases.is_delivered, 'cycle_time_hours'].median():.1f} hours")
    print(f"Delivered orders over 72h: {cases.is_delayed.sum():,}")
    print(f"Cases with repeated activities: {cases.is_rework.sum():,}")
    print(f"Top transition: {transitions.iloc[0].activity} → {transitions.iloc[0].next_activity}")


if __name__ == "__main__":
    main()

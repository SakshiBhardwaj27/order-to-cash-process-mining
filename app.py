from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.analyze_process import load_event_log, build_metrics

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Order-to-Cash Process Intelligence", page_icon="📊", layout="wide")
st.title("Order-to-Cash Process Intelligence")
st.caption("Explore process performance, bottlenecks, variants and rework using a synthetic event log.")

@st.cache_data
def get_data():
    df = load_event_log()
    return df, build_metrics(df)

try:
    df, metrics = get_data()
    cases, activity, transitions, variants = metrics
except Exception as exc:
    st.error(f"Could not load the event log: {exc}")
    st.stop()

regions = ["All"] + sorted(cases.region.dropna().unique().tolist())
region = st.sidebar.selectbox("Region", regions)
min_date = cases.start_time.min().date()
max_date = cases.start_time.max().date()
date_range = st.sidebar.date_input("Order start date", value=(min_date, max_date), min_value=min_date, max_value=max_date)
filtered = cases.copy()
if region != "All":
    filtered = filtered[filtered.region == region]
if isinstance(date_range, tuple) and len(date_range) == 2:
    filtered = filtered[filtered.start_time.dt.date.between(date_range[0], date_range[1])]
filtered_ids = set(filtered.case_id)
filtered_events = df[df.case_id.isin(filtered_ids)]

completed = filtered[filtered.is_delivered]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total cases", f"{len(filtered):,}")
col2.metric("Delivered", f"{filtered.is_delivered.mean():.1%}" if len(filtered) else "—")
col3.metric("Median delivered cycle time", f"{completed.cycle_time_hours.median():.1f} hrs" if len(completed) else "—")
col4.metric("Cancellation rate", f"{filtered.is_cancelled.mean():.1%}" if len(filtered) else "—")

left, right = st.columns(2)
with left:
    st.subheader("Case outcomes")
    outcome = filtered.final_activity.value_counts().rename_axis("Outcome").reset_index(name="Cases")
    st.plotly_chart(px.pie(outcome, names="Outcome", values="Cases", hole=.45), use_container_width=True)
with right:
    st.subheader("Cycle time distribution")
    if len(completed):
        st.plotly_chart(px.histogram(completed, x="cycle_time_hours", nbins=30, title="Delivered orders only", labels={"cycle_time_hours":"Cycle time (hours)"}), use_container_width=True)
    else:
        st.info("No delivered cases in this filter.")

st.subheader("Activity frequency")
activity_filtered = filtered_events.groupby("activity").agg(Events=("case_id", "size"), Cases=("case_id", "nunique")).reset_index().sort_values("Events", ascending=True)
st.plotly_chart(px.bar(activity_filtered, x="Events", y="activity", orientation="h", labels={"activity":"Activity"}), use_container_width=True)

st.subheader("Transitions and average waiting time")
ordered = filtered_events.sort_values(["case_id", "timestamp"]).copy()
ordered["next_activity"] = ordered.groupby("case_id").activity.shift(-1)
ordered["next_timestamp"] = ordered.groupby("case_id").timestamp.shift(-1)
trans = ordered.dropna(subset=["next_activity"]).copy()
trans["wait_hours"] = (trans.next_timestamp - trans.timestamp).dt.total_seconds()/3600
trans = trans.groupby(["activity", "next_activity"]).agg(Cases=("case_id", "size"), Avg_wait_hours=("wait_hours", "mean")).reset_index().sort_values("Avg_wait_hours", ascending=False)
if len(trans):
    st.dataframe(trans.round(2), use_container_width=True, hide_index=True)
    st.plotly_chart(px.bar(trans.head(12), x="Avg_wait_hours", y=trans.head(12).apply(lambda r: f"{r.activity} → {r.next_activity}", axis=1), orientation="h", labels={"y":"Transition", "Avg_wait_hours":"Average wait (hours)"}), use_container_width=True)

st.subheader("Most common process variants")
variant_rows = filtered_events.sort_values(["case_id", "timestamp"]).groupby("case_id").activity.apply(lambda x: " → ".join(x)).value_counts().head(10).rename_axis("Process variant").reset_index(name="Cases")
st.dataframe(variant_rows, use_container_width=True, hide_index=True)

st.subheader("Cases requiring attention")
attention = filtered[(filtered.is_delayed) | (filtered.is_cancelled) | (filtered.is_rework)].sort_values("cycle_time_hours", ascending=False)
st.dataframe(attention[["case_id", "region", "final_activity", "cycle_time_hours", "event_count", "is_delayed", "is_cancelled", "is_rework"]].head(100).round(2), use_container_width=True, hide_index=True)

st.download_button("Download filtered event log", filtered_events.to_csv(index=False).encode("utf-8"), "filtered_event_log.csv", "text/csv")
st.caption("Dataset is synthetic. The 72-hour delay threshold is an illustrative analytical assumption, not an industry benchmark.")

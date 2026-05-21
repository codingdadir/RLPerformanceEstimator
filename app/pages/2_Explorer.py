from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Rank Explorer",
    page_icon="📊",
    layout="wide"
)

st.title("Rank Explorer")
st.write(
    "Explore which Rocket League stats change the most across ranks."
)


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "database_v2.db"


RANK_NAMES = {
    7: "Gold 1",
    8: "Gold 2",
    9: "Gold 3",
    10: "Platinum 1",
    11: "Platinum 2",
    12: "Platinum 3",
    13: "Diamond 1",
    14: "Diamond 2",
    15: "Diamond 3",
    16: "Champion 1",
    17: "Champion 2",
    18: "Champion 3",
    19: "Grand Champion 1",
    20: "Grand Champion 2",
    21: "Grand Champion 3",
}


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        "SELECT * FROM player_stats",
        conn
    )

    conn.close()

    return df


def clean_for_analysis(df):
    analysis_df = df.copy()

    columns_to_drop = [
        "replay_id",
        "rank",
        "team",
        "duration",
        "positioning_goals_against_while_last_defender"
    ]

    analysis_df = analysis_df.drop(
        columns=[col for col in columns_to_drop if col in analysis_df.columns]
    )

    analysis_df = analysis_df.dropna()

    return analysis_df


df = load_data()
analysis_df = clean_for_analysis(df)


st.subheader("Dataset Overview")

total_rows = len(df)
total_replays = df["replay_id"].nunique()
total_features = analysis_df.drop(columns=["rank_tier"]).shape[1]
rank_count = df["rank_tier"].nunique()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Player Rows", f"{total_rows:,}")
c2.metric("Unique Replays", f"{total_replays:,}")
c3.metric("Rank Tiers", rank_count)
c4.metric("Model Features", total_features)


st.divider()


st.subheader("Rank Distribution")

rank_counts = (
    df["rank_tier"]
    .value_counts()
    .sort_index()
    .rename_axis("rank_tier")
    .reset_index(name="player_rows")
)

rank_counts["rank_name"] = rank_counts["rank_tier"].map(RANK_NAMES)

st.bar_chart(
    rank_counts,
    x="rank_name",
    y="player_rows",
    use_container_width=True
)

st.write(
    "The v2 dataset is balanced with 600 player rows per rank tier, "
    "which equals 100 ranked-standard 3v3 replays per tier."
)


st.divider()


st.subheader("Stats Most Related to Rank")

correlations = (
    analysis_df
    .corr(numeric_only=True)["rank_tier"]
    .drop("rank_tier")
)

correlation_summary = pd.DataFrame({
    "stat": correlations.index,
    "correlation": correlations.values,
    "strength": correlations.abs().values
}).sort_values("strength", ascending=False)

top_correlations = correlation_summary.head(20)

st.dataframe(
    top_correlations,
    use_container_width=True,
    hide_index=True
)

st.write(
    "Positive correlation means the stat tends to increase as rank increases. "
    "Negative correlation means the stat tends to decrease as rank increases."
)

st.bar_chart(
    top_correlations.sort_values("correlation"),
    x="stat",
    y="correlation",
    horizontal=True,
    use_container_width=True
)


st.divider()


st.subheader("Stat Trend by Rank")

numeric_columns = [
    col for col in analysis_df.columns
    if col != "rank_tier" and pd.api.types.is_numeric_dtype(analysis_df[col])
]

default_stats = [
    "movement_percent_high_air",
    "movement_avg_speed",
    "boost_bpm",
    "movement_percent_slow_speed"
]

available_defaults = [
    stat for stat in default_stats
    if stat in numeric_columns
]

selected_stat = st.selectbox(
    "Choose a stat to explore",
    options=numeric_columns,
    index=numeric_columns.index(available_defaults[0]) if available_defaults else 0
)

rank_means = (
    analysis_df
    .groupby("rank_tier")[selected_stat]
    .mean()
    .reset_index()
    .sort_values("rank_tier")
)

rank_order = [RANK_NAMES[tier] for tier in sorted(RANK_NAMES)]

rank_means["rank_name"] = rank_means["rank_tier"].map(RANK_NAMES)
rank_means["rank_name"] = pd.Categorical(
    rank_means["rank_name"],
    categories=rank_order,
    ordered=True
)

st.line_chart(
    rank_means,
    x="rank_name",
    y=selected_stat,
    use_container_width=True
)

st.divider()


st.subheader("Key Findings")

st.markdown(
    """
    The strongest rank-separating stats are mostly related to movement, boost usage,
    aerial involvement, and positioning.

    Higher-ranked players tend to:

    - Spend more time high in the air
    - Move faster on average
    - Spend more time at supersonic speed
    - Use and collect more boost
    - Powerslide more often
    - Spend less time moving slowly
    - Spend less time grounded

    Basic scoreboard stats like goals, score, and assists are less strongly related to rank
    than pace, boost activity, aerial play, and movement efficiency.
    """
)
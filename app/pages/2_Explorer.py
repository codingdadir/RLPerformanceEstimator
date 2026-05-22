from pathlib import Path
import sqlite3
import altair as alt
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

STAT_NAMES = {
    "core_shots": "Shots",
    "core_goals": "Goals",
    "core_saves": "Saves",
    "core_assists": "Assists",
    "core_score": "Score",
    "core_shooting_percentage": "Shooting %",
    "core_mvp": "MVP",
    "boost_bpm": "Boost Used Per Min",
    "boost_bcpm": "Boost Collected Per Min",
    "boost_avg_amount": "Avg Boost Amount",
    "boost_amount_collected": "Boost Collected",
    "boost_amount_stolen": "Boost Stolen",
    "boost_amount_collected_big": "Big Pad Collected",
    "boost_amount_collected_small": "Small Pad Collected",
    "boost_amount_stolen_big": "Big Pad Stolen",
    "boost_amount_stolen_small": "Small Pad Stolen",
    "boost_count_collected_big": "Big Pad Pickups",
    "boost_count_collected_small": "Small Pad Pickups",
    "boost_count_stolen_big": "Big Pad Steals",
    "boost_count_stolen_small": "Small Pad Steals",
    "boost_amount_overfill": "Boost Overfill",
    "boost_amount_overfill_stolen": "Boost Overfill Stolen",
    "boost_amount_used_while_supersonic": "Boost Used Supersonic",
    "boost_time_zero_boost": "Time at Zero Boost",
    "boost_percent_zero_boost": "% Time at Zero Boost",
    "boost_time_full_boost": "Time at Full Boost",
    "boost_percent_full_boost": "% Time at Full Boost",
    "boost_time_boost_0_25": "Time 0-25% Boost",
    "boost_time_boost_25_50": "Time 25-50% Boost",
    "boost_time_boost_50_75": "Time 50-75% Boost",
    "boost_time_boost_75_100": "Time 75-100% Boost",
    "movement_avg_speed": "Avg Speed",
    "movement_total_distance": "Total Distance",
    "movement_time_supersonic_speed": "Time at Supersonic",
    "movement_time_boost_speed": "Time at Boost Speed",
    "movement_time_slow_speed": "Time at Slow Speed",
    "movement_time_ground": "Time on Ground",
    "movement_time_low_air": "Time Low in Air",
    "movement_time_high_air": "Time High in Air",
    "movement_time_powerslide": "Time Powersliding",
    "movement_count_powerslide": "Powerslide Count",
    "movement_avg_powerslide_duration": "Avg Powerslide Duration",
    "movement_avg_speed_percentage": "Avg Speed %",
    "movement_percent_slow_speed": "% Time Slow",
    "movement_percent_boost_speed": "% Time Boost Speed",
    "movement_percent_supersonic_speed": "% Time Supersonic",
    "movement_percent_ground": "% Time Grounded",
    "movement_percent_low_air": "% Time Low Air",
    "movement_percent_high_air": "% Time High Air",
    "positioning_avg_distance_to_ball": "Avg Distance to Ball",
    "positioning_avg_distance_to_ball_possession": "Avg Distance to Ball (Possession)",
    "positioning_avg_distance_to_ball_no_possession": "Avg Distance to Ball (No Possession)",
    "positioning_avg_distance_to_mates": "Avg Distance to Teammates",
    "positioning_time_defensive_third": "Time in Defensive Third",
    "positioning_time_neutral_third": "Time in Neutral Third",
    "positioning_time_offensive_third": "Time in Offensive Third",
    "positioning_time_defensive_half": "Time in Defensive Half",
    "positioning_time_offensive_half": "Time in Offensive Half",
    "positioning_time_behind_ball": "Time Behind Ball",
    "positioning_time_infront_ball": "Time Ahead of Ball",
    "positioning_percent_defensive_third": "% Time Defensive Third",
    "positioning_percent_offensive_third": "% Time Offensive Third",
    "positioning_percent_neutral_third": "% Time Neutral Third",
    "positioning_percent_defensive_half": "% Time Defensive Half",
    "positioning_percent_offensive_half": "% Time Offensive Half",
    "positioning_percent_behind_ball": "% Time Behind Ball",
    "positioning_percent_infront_ball": "% Time Ahead of Ball",
    "demo_inflicted": "Demos Inflicted",
    "demo_taken": "Demos Taken",
    "core_shots_against": "Shots Against",
    "core_goals_against": "Goals Against",
    "boost_percent_boost_0_25": "% Time 0-25% Boost",
    "boost_percent_boost_25_50": "% Time 25-50% Boost",
    "boost_percent_boost_50_75": "% Time 50-75% Boost",
    "boost_percent_boost_75_100": "% Time 75-100% Boost",
    "positioning_time_most_back": "Time as Last Defender",
    "positioning_time_most_forward": "Time as Most Forward",
    "positioning_time_closest_to_ball": "Time Closest to Ball",
    "positioning_time_farthest_from_ball": "Time Farthest from Ball",
    "positioning_percent_most_back": "% Time as Last Defender",
    "positioning_percent_most_forward": "% Time as Most Forward",
    "positioning_percent_closest_to_ball": "% Time Closest to Ball",
    "positioning_percent_farthest_from_ball": "% Time Farthest from Ball",
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
    width="stretch"
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

top_correlations = top_correlations.copy()
top_correlations["stat"] = top_correlations["stat"].map(lambda x: STAT_NAMES.get(x, x))

st.dataframe(
    top_correlations,
    width="stretch",
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
    width="stretch"
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
    format_func=lambda x: STAT_NAMES.get(x, x),
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

# st.line_chart(
#     rank_means,
#     x="rank_name",
#     y=selected_stat,
#     y_label=STAT_NAMES.get(selected_stat, selected_stat),
#     width="stretch"
# )

chart = alt.Chart(rank_means).mark_line(point=True).encode(
    x=alt.X(
        "rank_name:N",
        sort=rank_order,
        title="Rank"
    ),
    y=alt.Y(
        f"{selected_stat}:Q",
        title=STAT_NAMES.get(selected_stat, selected_stat),
        scale=alt.Scale(zero=False)
    ),
    tooltip=[
        alt.Tooltip("rank_name:N", title="Rank"),
        alt.Tooltip(f"{selected_stat}:Q", title=STAT_NAMES.get(selected_stat, selected_stat))
    ]
)

st.altair_chart(chart, width="stretch")

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
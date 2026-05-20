
import pickle
from pathlib import Path
import sklearn
import pandas as pd
import streamlit as st
import requests
from dotenv import load_dotenv
import os
from pprint import pprint
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from src.collect import extract_player_stats

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

TOKEN = os.getenv("BALLCHASING_TOKEN")

headers = {
    "Authorization": TOKEN
}

st.set_page_config(page_title="What Rank Did You Play Like?", page_icon="🏎️", layout="wide")

st.title("What Rank Did You Play Like?")

MODEL_PATH = Path(__file__).resolve().parents[2] / "model" / "model.pkl"
FEATURES_PATH = Path(__file__).resolve().parents[2] / "model" / "features.pkl"
RANK_ICON_DIR = Path(__file__).resolve().parents[2] / "Rank Icons"
RANK_IMAGES = {
    "gold": RANK_ICON_DIR / "gold-1.png",
    "platinum": RANK_ICON_DIR / "plat-1.png",
    "diamond": RANK_ICON_DIR / "diamond-1.png",
    "champion": RANK_ICON_DIR / "champ-1.png",
    "grand_champion": RANK_ICON_DIR / "gc1.png",
}


with open(MODEL_PATH, "rb") as file:
    model = pickle.load(file)

with open(FEATURES_PATH, "rb") as file:
    features = pickle.load(file)


def get_replay_id(url):
    return url.strip().split("/")[-1]


def flatten_stats(stats):
    flattend_stats = {}
    for category, stat_group in stats.items():
                    for stat_name, value in stat_group.items():
                        flattend_stats[f"{category}_{stat_name}"] = value

    return flattend_stats


@st.dialog("Replay not found")
def replay_not_found():
    st.write("Could not fetch this replay. Check that the URL or replay ID is correct.")
    st.write("Also make sure the replay is public on Ballchasing.")

c1, c2 = st.columns([1.5, 1])

with c1:
    replay_url = st.text_input("Enter BallChasing URL or Replay ID:", value="https://ballchasing.com/replay/7263fbda-ee32-4d5c-b892-bf712d69d744", placeholder="https://ballchasing.com/replay/xxx...")

with c2:
    options = [
         "Random Forest exact-tier model: 21.7% Accuracy",
         "Random Forest broad-rank model: 53.3% Accuracy",
         "Logistic Regression broad-rank model: Coming Soon"
         ]
    selected_model = st.selectbox("What Model Would You Like to Use:", options=options, placeholder="Select Model", disabled=True)

_, c2, _ = st.columns([1, 0.2, 1])


with c2:
    run_button = st.button("Go!", type="primary", width="stretch")


if "replay_data" not in st.session_state:
    st.session_state.replay_data = None

if "selected_player" not in st.session_state:
    st.session_state.selected_player = None

if "selected_team" not in st.session_state:
    st.session_state.selected_team = None





if run_button:
    replay_id = get_replay_id(replay_url)

    print("Replay ID: ",replay_id)

    replay_response = requests.get(f"https://ballchasing.com/api/replays/{replay_id}",headers=headers, timeout=15)

    if replay_response.status_code != 200:
        replay_not_found()
        st.stop()

    st.session_state.replay_data = replay_response.json()
    st.session_state.selected_player = None
    st.session_state.selected_team = None

    st.session_state.replay_data = replay_response.json()

   

data = st.session_state.replay_data

if data:
    st.markdown("<h3 style='text-align: center;'>Which player are you?</h3>", unsafe_allow_html=True)

    flex = st.container(horizontal=True, horizontal_alignment="distribute")
    for team in ["blue", "orange"]:
        for player in data[team]["players"]:
            player_name = player.get("name")

            if flex.button(player_name, width="stretch", key=f"{team}_{player_name}_{player.get('id')}"):
                st.session_state.selected_player = player
                st.session_state.selected_team = team

    if st.session_state.selected_player:
        player = st.session_state.selected_player
        
        
        player_rank = player.get("rank", {})
        actual_rank = player_rank.get("id")
        actual_tier = player_rank.get("tier")

        player_stats = flatten_stats(player.get("stats", {}))

        input_row = {}

        for feature in features:
            input_row[feature] = player_stats.get(feature, 0)

        input_df = pd.DataFrame([input_row])

        prediction = model.predict(input_df)[0]

        rank_image = RANK_IMAGES.get(prediction)

        pretty_rank = prediction.replace("_", " ").title()
        
                
        _, center, _ = st.columns([1, 1, 1])

        with center:
            st.markdown(
                f"<h2 style='text-align: center;'>{pretty_rank}</h2>",
                unsafe_allow_html=True
            )

            if rank_image and rank_image.exists():
                st.image(str(rank_image), width="content")

  

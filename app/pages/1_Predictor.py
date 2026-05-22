
import pickle
from pathlib import Path
import pandas as pd
import streamlit as st
import requests
from dotenv import load_dotenv
import os
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

TOKEN = st.secrets["BALLCHASING_TOKEN"]

headers = {
    "Authorization": TOKEN
}

st.set_page_config(page_title="What Rank Did You Play Like?", page_icon="🏎️", layout="wide")

st.title("What Rank Did You Play Like?")
st.write("Paste a Ballchasing replay URL, select your player, and the model will estimate what broad rank your performance looked like.")

MODEL_PATH = Path(__file__).resolve().parents[2] / "model" / "log_reg_broad_rank_model_v2.pkl"
FEATURES_PATH = Path(__file__).resolve().parents[2] / "model" / "features_v2.pkl"
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
    st.write("Also make sure the replay is public on Ballchasing, and the gamemode is Ranked Standard.")


replay_url = st.text_input("Enter BallChasing URL or Replay ID:", placeholder="https://ballchasing.com/replay/xxx...")

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

    print("Replay ID: ", replay_id)

    if not replay_id:
        st.error("Enter a Replay.")
        print("E")
        st.stop()

    replay_response = requests.get(f"https://ballchasing.com/api/replays/{replay_id}",headers=headers, timeout=15)

    if (replay_response.status_code != 200):
        replay_not_found()
        st.stop()
        
    data = replay_response.json()

    if data.get("playlist_id") != "ranked-standard":
        st.error("This replay is not Ranked-Standard (Ranked 3v3).")
        st.stop()
         
    st.session_state.replay_data = data
    st.session_state.selected_player = None
    st.session_state.selected_team = None

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
        missing_features = []

        for feature in features:
            if feature in player_stats:
                input_row[feature] = player_stats[feature]
            else:
                input_row[feature] = 0
                missing_features.append(feature)

        input_df = pd.DataFrame([input_row])

        prediction = model.predict(input_df)[0]

        rank_image = RANK_IMAGES.get(prediction)

        pretty_rank = prediction.replace("_", " ").title()
        
        _, center, _ = st.columns([1, 1, 1])

        with center:
            st.markdown(
                f"<h2 style='text-align: center;'>{st.session_state.selected_player.get('name')} played like a {pretty_rank}.</h2>",
                unsafe_allow_html=True
            )

            if rank_image and rank_image.exists():
                st.image(str(rank_image), width="content")

            if missing_features:
                st.info(f"{len(missing_features)} stats were missing from this replay and defaulted to 0. This may affect prediction accuracy.")

  

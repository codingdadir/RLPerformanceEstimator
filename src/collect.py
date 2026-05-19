import os
from pathlib import Path
from pprint import pprint
import requests
from dotenv import load_dotenv
import pandas as pd
import time
from urllib.parse import urlparse, parse_qs
import sqlite3


RANK_TIERS = {
    "bronze-1": 1,
    "bronze-2": 2,
    "bronze-3": 3,

    "silver-1": 4,
    "silver-2": 5,
    "silver-3": 6,

    "gold-1": 7,
    "gold-2": 8,
    "gold-3": 9,

    "platinum-1": 10,
    "platinum-2": 11,
    "platinum-3": 12,

    "diamond-1": 13,
    "diamond-2": 14,
    "diamond-3": 15,

    "champion-1": 16,
    "champion-2": 17,
    "champion-3": 18,

    "grand-champion-1": 19,
    "grand-champion-2": 20,
    "grand-champion-3": 21
}
TARGET_RANKS = [

    ("champion", "champion-1"),
    ("champion", "champion-2"),
    ("champion", "champion-3"),

    ("grand-champion", "grand-champion-1"),
    ("grand-champion", "grand-champion-2"),
    ("grand-champion", "grand-champion-3"),
]
MAX_TIER_DIFF = {
    "bronze": 3,
    "silver": 2,
    "gold": 2,
    "platinum": 1,
    "diamond": 1,
    "champion": 1,
    "grand-champion": 1,
}
MAX_CHECKED = {
    "bronze": 2000,
    "silver": 1000,
    "gold": 500,
    "platinum": 500,
    "diamond": 500,
    "champion": 1000,
    "grand-champion": 3000,
}


def is_replay_valid(replay, rank_label, target_rank):
    target_tier = RANK_TIERS[target_rank]

    if "status" not in replay:
        return False

    if replay["status"] != "ok":
        return False
    
    if replay["playlist_id"] != "ranked-standard":
        return False
    
    if replay["duration"] < 300:
        return False
    
    if abs(replay["blue"]["stats"]["core"]["goals"] - replay["orange"]["stats"]["core"]["goals"]) > 2:
        return False
    
    rank_tiers = []

    for team in ["blue", "orange"]:
        for player in replay[team]["players"]:
            if player.get("stats", None) is None:
                return False
            
            rank_tier = player.get("rank", {}).get("tier")

            if rank_tier is None:
                return False
            
            if abs(rank_tier - target_tier) > MAX_TIER_DIFF[rank_label]:
                return False
            
            rank_tiers.append(rank_tier)
    
#     MAX_RANK_SPREAD_BY_LABEL = {
#     "bronze": 3,
#     "silver": 3,
#     "gold": 3,
#     "platinum": 3,
#     "diamond": 2,
#     "champion": 2,
#     "grand-champion": 1,
#     "supersonic-legend": 0,
# }
#     rank_spread = max(rank_tiers) - min(rank_tiers)
#     max_allowed_spread = MAX_RANK_SPREAD_BY_LABEL[rank_label]
    
#     if rank_spread > max_allowed_spread:
#         return False
            
    return True
            

def extract_player_stats(detailed_response):
    rows = []
    
    for team in ["blue", "orange"]:
        for player in detailed_response[team]["players"]:
                player_dict = {}
                player_dict["replay_id"] = detailed_response["id"]
                player_dict["rank"] = player.get("rank", {}).get("id")
                player_dict["rank_tier"] = player.get("rank", {}).get("tier")
                player_dict["team"] = team
                player_dict["duration"] = detailed_response.get("duration", None)
                for category, stat_group in player.get("stats", {}).items():
                    for stat_name, value in stat_group.items():
                        player_dict[f"{category}_{stat_name}"] = value

                rows.append(player_dict)

    return rows


def collect_rows_from_replays(data, rank_label, target_rank):
    all_rows = []
    for replay in data:
        replay_id = replay["id"]
        try:
            response = requests.get(
                f"https://ballchasing.com/api/replays/{replay_id}",
                headers=headers,
                timeout=15
            )
            detailed_data = response.json()
        except requests.exceptions.RequestException:
            print(replay_id, "Rejected: request failed")
            continue

        if is_replay_valid(detailed_data, rank_label, target_rank):
            all_rows.extend(extract_player_stats(detailed_data))
    
    return all_rows


def save_rows_to_csv(rows, path):
    df = pd.DataFrame(rows)

    df.to_csv(path, index=False)

 
def collect_until_target(rank_label, target_rank, params, headers, target, max_checked=500):
    valid_replays = 0
    checked_replays = 0
    all_rows = []
    seen_replay_ids = set()

    next_url = "https://ballchasing.com/api/replays"

    while valid_replays < target and checked_replays < max_checked and next_url:
        response = requests.get(next_url, headers=headers, params=params, timeout=15)
        data = response.json()
        params = None  # only use params on the first page

        for replay in data["list"]:
            replay_id = replay["id"]

            if replay_id in seen_replay_ids:
                continue

            seen_replay_ids.add(replay_id)
            checked_replays += 1

            try:
                detail_response = requests.get(
                    f"https://ballchasing.com/api/replays/{replay_id}",
                    headers=headers,
                    timeout=15
                )
                detailed_data = detail_response.json()
                time.sleep(0.6)
            except requests.exceptions.RequestException:
                print(replay_id, "Rejected: request failed")
                continue

            if is_replay_valid(detailed_data, rank_label, target_rank):
                all_rows.extend(extract_player_stats(detailed_data))
                valid_replays += 1

            print(f"\rChecked: {checked_replays} | Valid: {valid_replays} | Rejected: {checked_replays - valid_replays}", end="", flush=True)

            if valid_replays >= target or checked_replays >= max_checked:
                break
            
            
        
        next_url = data.get("next")

        if next_url:
            after_token = parse_qs(urlparse(next_url).query)["after"][0]

            params = {
                "min-rank": target_rank,
                "max-rank": target_rank,
                "playlist": "ranked-standard",
                "count": 50,
                "after": after_token
            }

            next_url = "https://ballchasing.com/api/replays"

    print()  # newline after the overwriting line
    print(f"Done -- Checked: {checked_replays} | Valid: {valid_replays} | Rows: {len(all_rows)}")
    return all_rows


def save_rows_to_database(rows, db_path, table_name):
    df = pd.DataFrame(rows)

    conn = sqlite3.connect(db_path)

    df.to_sql(table_name, conn, if_exists="append", index=False)
    conn.close()

    return


def collect_all_ranks(headers):
    for rank_label, target_rank in TARGET_RANKS:
        print("Starting:", target_rank)
        params ={
            "min-rank": target_rank,
            "max-rank": target_rank,
            "playlist": "ranked-standard",
            "count": 50
        }
        target = 51 if target_rank == "bronze-3" else 17
        all_rows = collect_until_target(rank_label, target_rank, params, headers, target, max_checked=MAX_CHECKED[rank_label])
        save_rows_to_csv(all_rows, f"data/csv/{target_rank}_rows.csv")
        print(target_rank, ".csv created.")

        save_rows_to_database(all_rows, "data/raw/database.db", "player_stats")
        print(target_rank, " Added to DB.")


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TOKEN = os.getenv("BALLCHASING_TOKEN")

headers = {
    "Authorization": TOKEN
}

if __name__ == "__main__":
    collect_all_ranks(headers)

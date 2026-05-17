# Rocket League Rank Predictor

Rocket League Rank Predictor is a data science project that uses Rocket League replay statistics from Ballchasing.com to estimate what rank a player performs like based on their in-game stats.

The project is built around one main question:

> What Rocket League stats actually separate ranks?

Instead of only looking at MMR, wins, or losses, this project focuses on player-level replay data such as boost usage, movement, positioning, shooting, saves, demos, and other performance metrics.

## Project Status

This project is currently in the data collection phase.

Current progress:

- Connected to the Ballchasing API
- Loaded the API token securely from a local `.env` file
- Fetched ranked 3v3 replay listings by rank filter
- Fetched detailed replay data from replay IDs
- Built replay validation logic to filter cleaner ranked games
- Extracted player-level stats from blue and orange teams
- Flattened nested player stats into clean row dictionaries
- Tested multi-replay collection on small batches

## Data Source

Replay data comes from the Ballchasing.com API.

The current version focuses on:

- Playlist: Ranked Standard / 3v3
- Replay type: Public uploaded replays
- Data level: Player-level stats
- Stat categories:
  - Core
  - Boost
  - Movement
  - Positioning
  - Demos

## Current Data Pipeline

The current collection flow is:

```text
Load API token
→ Fetch replay listings by rank
→ Fetch detailed replay data
→ Validate replay quality
→ Extract player stats
→ Convert players into dataset rows
```

Each valid ranked 3v3 replay can become up to six player rows.

## Replay Validation

To keep the dataset cleaner, replays are filtered before player stats are extracted.

Current validation rules include:

- Replay status must be `ok`
- Playlist must be `ranked-standard`
- Game duration must be at least 300 seconds
- Final goal difference must be 2 or less
- Every player must have stats
- Every player must have rank tier data
- Rank spread must stay within an allowed range for that rank level

These filters are meant to reduce noisy examples such as short forfeits, blowouts, missing-rank players, smurf-heavy games, and uneven lobbies.

## Rank Spread Rules

The project allows small rank differences inside a lobby, since real ranked matches often contain players from nearby ranks.

Current max rank spread rules:

```python
MAX_RANK_SPREAD_BY_LABEL = {
    "bronze": 3,
    "silver": 3,
    "gold": 3,
    "platinum": 3,
    "diamond": 2,
    "champion": 2,
    "grand-champion": 1,
    "supersonic-legend": 0,
}
```

The idea is that lower and mid ranks can tolerate slightly wider variation, while higher ranks need stricter filtering because each rank gap represents a larger skill difference.

## Extracted Player Rows

The API returns nested JSON, but the project converts each player into a flat row dictionary.

Example row structure:

```text
replay_id
team
duration
rank_id
rank_tier
core_shots
core_goals
core_saves
core_assists
core_score
boost_bpm
boost_bcpm
boost_avg_amount
movement_avg_speed
movement_total_distance
positioning_avg_distance_to_ball
positioning_time_defensive_third
positioning_time_offensive_third
demo_inflicted
demo_taken
...
```

This flat structure makes the data easier to save as CSV, load into SQLite, analyze with pandas, and use in machine learning models.

## Planned Features

The final version of the project will include:

- Larger replay collection across multiple rank tiers
- Clean CSV and SQLite storage
- Exploratory data analysis in Jupyter notebooks
- Feature engineering
- Baseline machine learning models
- Model comparison across:
  - Logistic Regression
  - Random Forest
  - XGBoost
- Feature importance analysis
- Streamlit dashboard with:
  - Project overview
  - Rank predictor
  - Rank/stat explorer

## Tech Stack

Current and planned tools:

- Python
- requests
- python-dotenv
- pandas
- SQLite
- Jupyter Notebook
- scikit-learn
- XGBoost
- Streamlit
- Git / GitHub
- Ballchasing.com API

## Project Structure

Current planned structure:

```text
RLRankPredictor/
├── app/
│   ├── main.py
│   ├── home.py
│   ├── predictor.py
│   └── explorer.py
│
├── data/
│   └── raw/
│
├── model/
│
├── notebooks/
│   └── eda.ipynb
│
├── src/
│   ├── collect.py
│   ├── model.py
│   └── utils.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

## Environment Variables

This project uses a local `.env` file for the Ballchasing API token.

Example:

```text
BALLCHASING_TOKEN=your_token_here
```

The `.env` file should not be committed to GitHub.

## How to Run Locally

Clone the repository:

```bash
git clone https://github.com/codingdadir/RLRankPredictor.git
cd RLRankPredictor
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root and add your Ballchasing API token:

```text
BALLCHASING_TOKEN=your_token_here
```

Run the collection script:

```bash
python src/collect.py
```

## Current Limitations

This project is still early. The current version focuses on API access, replay validation, and player-row extraction.

The following parts are not finished yet:

- Full replay dataset collection
- CSV export
- SQLite database creation
- Exploratory data analysis
- Model training
- Streamlit dashboard
- Deployment

## Project Goal

The final app will allow a user to enter Rocket League stats and receive a predicted rank based on how their performance compares to players across different ranks.

The broader goal is to build a portfolio-quality data science project that combines:

- API data collection
- Data cleaning
- Feature engineering
- Machine learning
- Model interpretation
- Interactive dashboard development

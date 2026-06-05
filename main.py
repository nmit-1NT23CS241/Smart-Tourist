import json
import os
import random
from collections import deque

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="SafarAI RL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Dataset loading ──────────────────────────────────────────────────────────

# Map the rich trip_types from the JSON to your app's 5 travel categories.
# A destination can match multiple categories; the first match is its primary tag.
TRIP_TYPE_MAP = {
    "nature":    {"Nature", "Wildlife", "Trekking", "Trekking_base", "Mountain",
                  "Valley_scenery", "Rainforest", "Wetland", "Waterfalls",
                  "Waterfall", "Birding", "High_altitude", "High_altitude_valley",
                  "High_mountain", "High_mountain_village", "Eco_tourism", "Monsoon",
                  "Camping", "Snow_destination", "Snow_views", "Mountain_views",
                  "Plantations", "Tea_gardens", "Tea_estates", "Coffee_estates",
                  "River", "Riverside"},
    "heritage":  {"Heritage", "History", "UNESCO", "Heritage_rail", "Rock_sculpture",
                  "Caves", "Buddhist_circuit", "Monasteries"},
    "beach":     {"Beach", "Coastal", "Coastal_drive", "Offbeat_beach",
                  "Snorkelling", "Diving", "Water_sports", "Swimming",
                  "Island", "Cliff_scenery", "Desert_coastal"},
    "culture":   {"Cultural", "Culture", "Culture_combo", "Religious", "Spiritual",
                  "Pilgrimage", "Pilgrimage_hub", "Ganga_ghats", "Ashram",
                  "Tribal_culture", "Music_culture", "Festival", "Food",
                  "Handicrafts", "Shopping", "Yoga", "Wellness", "Café_town"},
    "adventure": {"Adventure", "Backpacking", "Backpacker", "Road_trip",
                  "Skiing", "Light_adventure", "Short_trek", "Short_treks",
                  "Desert", "Desert_landscape", "Offbeat", "Offbeat_hill",
                  "High_mountain", "Living_root_bridges"},
}


def _primary_tags(trip_types: list[str]) -> list[str]:
    """Return ordered list of matched app categories for a destination."""
    tags = []
    for category, type_set in TRIP_TYPE_MAP.items():
        if any(t in type_set for t in trip_types):
            tags.append(category)
    return tags if tags else ["nature"]


def _budget_midpoint(dest: dict) -> int:
    """Use mid_range total_daily_range midpoint × ideal_days as trip cost proxy."""
    mid = dest["mid_range_category"]["total_daily_range"]
    daily = (mid[0] + mid[1]) / 2
    ideal_days = max(dest.get("ideal_days", 3), 1)
    return int(daily * ideal_days)


def _crowd_score(dest: dict) -> float:
    """Normalise popularity_score (4–10) to a 0–1 crowd level."""
    return (dest["popularity_score"] - 4) / 6.0


def _sustainability_score(dest: dict) -> float:
    """Derive sustainability from safety_rating (6–9) as a proxy (0–1)."""
    # The JSON has sustainability_notes text but no numeric score.
    # We use safety_rating + inverse of popularity (popular = more footprint).
    safety = (dest["safety_rating"] - 6) / 3.0          # 0–1
    low_crowd_bonus = 1.0 - _crowd_score(dest) * 0.4
    return round(min(safety * 0.6 + low_crowd_bonus * 0.4, 1.0), 2)


def load_destinations(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    destinations = []
    for i, d in enumerate(raw):
        tags = _primary_tags(d["trip_types"])
        budget = _budget_midpoint(d)
        mid = d["mid_range_category"]["total_daily_range"]
        lux = d["luxury_category"]["total_daily_range"]

        # Build a human-readable description from the rich JSON fields
        primary_attractions = ", ".join(d.get("primary_attractions", [])[:3])
        unique = d.get("unique_experiences", "")
        description = f"{unique} Key attractions: {primary_attractions}." if unique else primary_attractions

        destinations.append({
            "id":              i,                              # 0-indexed for Q-table
            "source_id":       d["id"],                        # original dataset ID
            "name":            d["destination_name"],
            "state":           d["state"],
            "district":        d.get("district", ""),
            "region":          d.get("region", ""),
            "tags":            tags,
            "trip_types":      d["trip_types"],                # full list kept for filtering
            "budget":          budget,                         # mid-range trip cost proxy
            "budget_min":      mid[0],                        # per-day budget lower bound
            "budget_max":      lux[1],                        # luxury upper bound
            "sustainability":  _sustainability_score(d),
            "crowd":           _crowd_score(d),
            "description":     description,
            "ideal_days":      d.get("ideal_days", 3),
            "best_seasons":    d.get("best_seasons", []),
            "activities":      d.get("activities_available", []),
            "ideal_for":       d.get("ideal_for", []),
            "popularity":      d["popularity_score"],
            "safety_rating":   d["safety_rating"],
            "permits_required": d.get("permits_required", False),
            "coordinates":     d.get("coordinates", {}),
            "food_scene":      d.get("food_scene", ""),
            "local_cuisine":   d.get("local_cuisine_must_try", []),
            "accommodation_types": d.get("accommodation_types", []),
        })
    return destinations


# Load from the dataset file — place india_tourism_dataset.json in the same
# directory as main.py, or set TOURISM_DATASET env var to point elsewhere.
DATASET_PATH = os.environ.get(
    "TOURISM_DATASET",
    os.path.join(os.path.dirname(__file__), "india_tourism_dataset.json"),
)
DESTINATIONS = load_destinations(DATASET_PATH)
ACTION_SIZE = len(DESTINATIONS)

# ─── RL / DQN agent ──────────────────────────────────────────────────────────

GAMMA = 0.95
LEARNING_RATE = 0.1
EPSILON_INIT = 0.3
EPSILON_MIN = 0.05
EPSILON_DECAY = 0.99

Q_TABLE_SIZE = 5000
Q_TABLE_PATH = os.path.join(os.path.dirname(__file__), "qtable.npy")

CSV_CATEGORY_MAP = {
    "Cultural":  "culture",
    "Natural":   "nature",
    "Historic":  "heritage",
    "Monument":  "heritage",
    "Religious": "culture",
}


def prewarm_qtable(q: np.ndarray, csv_path: str) -> np.ndarray:
    """
    Use real visitor data from the CSV to pre-initialize Q-values.
    Matches CSV rows to destinations by state + travel_type, then sets
    Q-values proportional to the average final_recommendation_score.
    """
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        df["travel_type"] = df["category"].map(CSV_CATEGORY_MAP)
        df = df.dropna(subset=["travel_type", "final_recommendation_score"])

        # Average score per state + travel_type (0–1 range)
        avg_scores = (
            df.groupby(["state", "travel_type"])["final_recommendation_score"]
            .mean()
            .to_dict()
        )

        warmed = 0
        for dest in DESTINATIONS:
            dest_state = dest["state"]
            for tag in dest["tags"]:
                key = (dest_state, tag)
                if key in avg_scores:
                    # Convert 0-1 score to a small positive Q-value seed
                    q_seed = float(avg_scores[key]) * 2.0  # scale: 0–2
                    # Apply to all state slots for this action
                    q[:, dest["id"]] = np.where(
                        q[:, dest["id"]] == 0,
                        q_seed,
                        q[:, dest["id"]]
                    )
                    warmed += 1
                    break

        print(f"Q-table pre-warmed from CSV: {warmed} destinations seeded")
    except Exception as e:
        print(f"CSV pre-warming skipped: {e}")
    return q


# Load persisted Q-table if it exists, otherwise pre-warm from CSV
CSV_PATH = os.environ.get(
    "TOURISM_CSV",
    os.path.join(os.path.dirname(__file__), "indian_tourist_places_dataset.csv"),
)

if os.path.exists(Q_TABLE_PATH):
    q_table = np.load(Q_TABLE_PATH)
    # Resize if destination count changed since last save
    if q_table.shape[1] != ACTION_SIZE:
        new_q = np.zeros((Q_TABLE_SIZE, ACTION_SIZE))
        cols = min(q_table.shape[1], ACTION_SIZE)
        new_q[:, :cols] = q_table[:, :cols]
        q_table = new_q
else:
    q_table = np.zeros((Q_TABLE_SIZE, ACTION_SIZE))
    # Pre-warm from CSV on first run
    if os.path.exists(CSV_PATH):
        q_table = prewarm_qtable(q_table, CSV_PATH)
        np.save(Q_TABLE_PATH, q_table)
        print("Pre-warmed Q-table saved.")

replay_buffer: deque = deque(maxlen=500)
interaction_count: int = 0

# Per-user epsilon tracking so different users don't affect each other
user_epsilon: dict[str, float] = {}


def state_to_index(state: list) -> int:
    discretized = [int(s * 20) for s in state]   # finer buckets than before
    return abs(hash(tuple(discretized))) % Q_TABLE_SIZE


def get_state(prefs: dict) -> list:
    budget_mid = (prefs["budget_min"] + prefs["budget_max"]) / 2
    budget_norm = min(budget_mid / 150_000.0, 1.0)
    return [
        budget_norm,
        1.0 if prefs["travel_type"] == "nature"    else 0.0,
        1.0 if prefs["travel_type"] == "heritage"  else 0.0,
        1.0 if prefs["travel_type"] == "beach"     else 0.0,
        1.0 if prefs["travel_type"] == "culture"   else 0.0,
        1.0 if prefs["travel_type"] == "adventure" else 0.0,
        prefs["sustainability_pref"] / 10.0,
    ]


def score_destination(dest: dict, prefs: dict) -> float:
    budget_min = prefs["budget_min"]
    budget_max = prefs["budget_max"]
    dest_cost  = dest["budget"]

    if budget_min <= dest_cost <= budget_max:
        budget_fit = 1.0
    else:
        distance   = max(dest_cost - budget_max, budget_min - dest_cost, 0)
        budget_fit = max(0.0, 1.0 - distance / max(budget_max, 1))

    travel_type = prefs["travel_type"]
    if dest["tags"] and dest["tags"][0] == travel_type:
        type_match = 1.0
    elif travel_type in dest["tags"]:
        type_match = 0.75
    else:
        type_match = 0.0

    sust_score = dest["sustainability"] * (prefs["sustainability_pref"] / 10.0)
    crowd_pen  = 1.0 - dest["crowd"] * 0.4

    return (budget_fit * 0.35) + (type_match * 0.40) + (sust_score * 0.15) + (crowd_pen * 0.10)


def update_q_table(state_idx: int, action: int, reward: float, next_state_idx: int):
    current_q  = q_table[state_idx][action]
    max_next_q = np.max(q_table[next_state_idx])
    new_q      = current_q + LEARNING_RATE * (reward + GAMMA * max_next_q - current_q)
    q_table[state_idx][action] = new_q


def save_q_table():
    np.save(Q_TABLE_PATH, q_table)


# ─── Pydantic models ─────────────────────────────────────────────────────────

class UserPreferences(BaseModel):
    budget_min:         int
    budget_max:         int
    travel_type:        str   # nature | heritage | beach | culture | adventure
    sustainability_pref: int  # 0–10
    user_id:            str


class FeedbackRequest(BaseModel):
    user_id:            str
    destination_id:     int   # 0-indexed ID used in Q-table
    liked:              bool
    budget_min:         int
    budget_max:         int
    travel_type:        str
    sustainability_pref: int


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":             "SafarAI RL API is running",
        "total_destinations": len(DESTINATIONS),
        "dataset":            DATASET_PATH,
    }


@app.post("/recommend")
def recommend(prefs: UserPreferences):
    global interaction_count

    state     = get_state(prefs.dict())
    state_idx = state_to_index(state)

    # Initialise per-user epsilon
    if prefs.user_id not in user_epsilon:
        user_epsilon[prefs.user_id] = EPSILON_INIT

    epsilon = user_epsilon[prefs.user_id]

    scored = []
    for dest in DESTINATIONS:
        base_score = score_destination(dest, prefs.dict())
        q_val      = float(q_table[state_idx][dest["id"]])
        blended    = base_score * 0.5 + (q_val / (abs(q_val) + 1)) * 0.5

        # ε-greedy: occasionally boost a random destination for exploration
        if random.random() < epsilon:
            blended += random.uniform(0, 0.1)

        in_budget = prefs.budget_min <= dest["budget"] <= prefs.budget_max

        scored.append({
            "id":               dest["id"],
            "name":             dest["name"],
            "state":            dest["state"],
            "district":         dest["district"],
            "region":           dest["region"],
            "type":             dest["tags"][0] if dest["tags"] else "nature",
            "tags":             dest["tags"],
            "trip_types":       dest["trip_types"],
            "description":      dest["description"],
            "estimated_cost":   dest["budget"],
            "budget_range":     [dest["budget_min"], dest["budget_max"]],
            "ideal_days":       dest["ideal_days"],
            "best_seasons":     dest["best_seasons"],
            "activities":       dest["activities"][:5],
            "ideal_for":        dest["ideal_for"],
            "food_scene":       dest["food_scene"],
            "local_cuisine":    dest["local_cuisine"][:3],
            "accommodation_types": dest["accommodation_types"],
            "sustainability":   round(dest["sustainability"] * 10, 1),
            "crowd_level":      ("Low" if dest["crowd"] < 0.4
                                 else "Medium" if dest["crowd"] < 0.7
                                 else "High"),
            "popularity":       dest["popularity"],
            "safety_rating":    dest["safety_rating"],
            "permits_required": dest["permits_required"],
            "coordinates":      dest["coordinates"],
            "score":            round(blended, 3),
            "match_reason":     _match_reason(dest, prefs.dict(), in_budget),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    # Decay this user's epsilon
    user_epsilon[prefs.user_id] = max(EPSILON_MIN, epsilon * EPSILON_DECAY)
    interaction_count += 1

    # Diversity filter — max 1 per state
    seen_states: dict[str, int] = {}
    diverse = []
    for item in scored:
        dest_state = item["state"]
        if seen_states.get(dest_state, 0) < 1:
            diverse.append(item)
            seen_states[dest_state] = seen_states.get(dest_state, 0) + 1
        if len(diverse) == 10:
            break

    return {
        "recommendations": diverse,
        "model_info": {
            "interactions":     interaction_count,
            "exploration_rate": round(user_epsilon[prefs.user_id], 3),
            "learning_mode":    ("exploring" if user_epsilon[prefs.user_id] > 0.15
                                 else "exploiting"),
        },
    }


@app.post("/feedback")
def feedback(fb: FeedbackRequest):
    prefs = {
        "budget_min":         fb.budget_min,
        "budget_max":         fb.budget_max,
        "travel_type":        fb.travel_type,
        "sustainability_pref": fb.sustainability_pref,
    }

    state       = get_state(prefs)
    state_idx   = state_to_index(state)

    # Slightly perturb next_state_idx to represent state transition
    # (in a stateless tourism app there's no true next-state; we offset the hash)
    next_state_idx = (state_idx + fb.destination_id) % Q_TABLE_SIZE

    reward = 1.0 if fb.liked else -0.5
    replay_buffer.append((state_idx, fb.destination_id, reward, next_state_idx))

    # Mini-batch update
    batch = random.sample(replay_buffer, min(16, len(replay_buffer)))
    for s, a, r, ns in batch:
        update_q_table(s, a, r, ns)

    # Persist Q-table to disk after every feedback
    save_q_table()

    return {
        "status":         "Model updated",
        "reward_applied": reward,
        "destination":    DESTINATIONS[fb.destination_id]["name"] if fb.destination_id < len(DESTINATIONS) else "unknown",
    }


@app.get("/destinations")
def get_destinations(
    travel_type: str | None = None,
    state:       str | None = None,
    max_budget:  int | None = None,
):
    """Return all destinations with optional filters."""
    results = DESTINATIONS
    if travel_type:
        results = [d for d in results if travel_type in d["tags"]]
    if state:
        results = [d for d in results if d["state"].lower() == state.lower()]
    if max_budget:
        results = [d for d in results if d["budget"] <= max_budget]
    return {"destinations": results, "total": len(results)}


@app.get("/stats")
def stats():
    """RL model stats — useful for demo/presentation."""
    nonzero = int(np.count_nonzero(q_table))
    total   = Q_TABLE_SIZE * ACTION_SIZE
    top_actions = np.argsort(np.max(q_table, axis=0))[-5:][::-1]
    top_destinations = [
        {"name": DESTINATIONS[i]["name"], "state": DESTINATIONS[i]["state"], "q_value": round(float(np.max(q_table[:, i])), 3)}
        for i in top_actions if i < len(DESTINATIONS)
    ]
    return {
        "total_interactions":      interaction_count,
        "q_table_size":            f"{Q_TABLE_SIZE} states × {ACTION_SIZE} actions",
        "q_table_sparsity":        f"{(total - nonzero) / total * 100:.1f}% zeros",
        "active_users":            len(user_epsilon),
        "top_q_destinations":      top_destinations,
        "replay_buffer_size":      len(replay_buffer),
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _match_reason(dest: dict, prefs: dict, in_budget: bool) -> str:
    reasons = []
    if in_budget:
        reasons.append("fits your budget")
    if prefs["travel_type"] in dest["tags"]:
        reasons.append(f"matches {prefs['travel_type']} preference")
    if dest["sustainability"] >= 0.75:
        reasons.append("eco-friendly")
    if dest["crowd"] < 0.4:
        reasons.append("low crowds")
    if dest["safety_rating"] >= 8:
        reasons.append("highly safe")
    return ", ".join(reasons) if reasons else "recommended by RL model"

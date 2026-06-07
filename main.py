import json
import os
import random
import time
from collections import deque
from typing import Optional

import httpx
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore as admin_firestore

# ─── Firebase Admin SDK ───────────────────────────────────────────────────────
if not firebase_admin._apps:
    cred = credentials.Certificate("/etc/secrets/firebase-key.json")
    firebase_admin.initialize_app(cred)

admin_db = admin_firestore.client()

# ─── Weather config ───────────────────────────────────────────────────────────
try:
    from config import OPENWEATHER_API_KEY as WEATHER_API_KEY
except ImportError:
    WEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_CACHE_TTL = 3600
_weather_cache: dict = {}

app = FastAPI(title="SafarAI RL API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Dataset loading ──────────────────────────────────────────────────────────
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
    tags = []
    for category, type_set in TRIP_TYPE_MAP.items():
        if any(t in type_set for t in trip_types):
            tags.append(category)
    return tags if tags else ["nature"]


def _budget_midpoint(dest: dict) -> int:
    mid = dest["mid_range_category"]["total_daily_range"]
    daily = (mid[0] + mid[1]) / 2
    ideal_days = max(dest.get("ideal_days", 3), 1)
    return int(daily * ideal_days)


def _budget_range_full(dest: dict) -> tuple[int, int]:
    return dest["full_budget_min"], dest["full_budget_max"]


def _crowd_score(dest: dict) -> float:
    return (dest["popularity_score"] - 4) / 6.0


def _sustainability_score(dest: dict) -> float:
    safety = (dest["safety_rating"] - 6) / 3.0
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

        primary_attractions = ", ".join(d.get("primary_attractions", [])[:3])
        unique = d.get("unique_experiences", "")
        description = f"{unique} Key attractions: {primary_attractions}." if unique else primary_attractions

        ideal_days = max(d.get("ideal_days", 3), 1)
        bud_tier = d["budget_category"]["total_daily_range"]
        mid_tier = d["mid_range_category"]["total_daily_range"]
        lux_tier = d["luxury_category"]["total_daily_range"]

        destinations.append({
            "id":              i,
            "source_id":       d["id"],
            "name":            d["destination_name"],
            "state":           d["state"],
            "district":        d.get("district", ""),
            "region":          d.get("region", ""),
            "tags":            tags,
            "trip_types":      d["trip_types"],
            "budget":          budget,
            "budget_min":      mid[0],
            "budget_max":      lux[1],
            "tier_budget":     (int(bud_tier[0]*ideal_days), int(bud_tier[1]*ideal_days)),
            "tier_mid":        (int(mid_tier[0]*ideal_days), int(mid_tier[1]*ideal_days)),
            "tier_luxury":     (int(lux_tier[0]*ideal_days), int(lux_tier[1]*ideal_days)),
            "full_budget_min":  int(bud_tier[0] * ideal_days),
            "full_budget_max":  int(lux_tier[1] * ideal_days),
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
            "accessibility":   d.get("accessibility", ""),
            "road_connectivity": d.get("road_connectivity", ""),
            "coordinates":     d.get("coordinates", {}),
            "food_scene":      d.get("food_scene", ""),
            "local_cuisine":   d.get("local_cuisine_must_try", []),
            "accommodation_types": d.get("accommodation_types", []),
            "avoid_seasons":   d.get("avoid_seasons", []),
            "avg_temp_by_season": d.get("average_temperature", {}),
        })
    return destinations


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
    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
        df["travel_type"] = df["category"].map(CSV_CATEGORY_MAP)
        df = df.dropna(subset=["travel_type", "final_recommendation_score"])
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
                    q_seed = float(avg_scores[key]) * 2.0
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


CSV_PATH = os.environ.get(
    "TOURISM_CSV",
    os.path.join(os.path.dirname(__file__), "indian_tourist_places_dataset.csv"),
)

if os.path.exists(Q_TABLE_PATH):
    q_table = np.load(Q_TABLE_PATH)
    if q_table.shape[1] != ACTION_SIZE:
        new_q = np.zeros((Q_TABLE_SIZE, ACTION_SIZE))
        cols = min(q_table.shape[1], ACTION_SIZE)
        new_q[:, :cols] = q_table[:, :cols]
        q_table = new_q
else:
    q_table = np.zeros((Q_TABLE_SIZE, ACTION_SIZE))
    if os.path.exists(CSV_PATH):
        q_table = prewarm_qtable(q_table, CSV_PATH)
        np.save(Q_TABLE_PATH, q_table)
        print("Pre-warmed Q-table saved.")

replay_buffer: deque = deque(maxlen=500)
interaction_count: int = 0
user_epsilon: dict[str, float] = {}


def state_to_index(state: list) -> int:
    discretized = [int(s * 20) for s in state]
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


def _matched_tier(dest: dict, budget_min: int, budget_max: int) -> tuple[str, int]:
    budget_mid = (budget_min + budget_max) / 2
    tb_min, tb_max = dest["tier_budget"]
    tm_min, tm_max = dest["tier_mid"]
    tl_min, tl_max = dest["tier_luxury"]

    def overlap(tmin, tmax):
        return max(0, min(budget_max, tmax) - max(budget_min, tmin))

    bud_overlap = overlap(tb_min, tb_max)
    mid_overlap = overlap(tm_min, tm_max)
    lux_overlap = overlap(tl_min, tl_max)

    if lux_overlap >= mid_overlap and lux_overlap >= bud_overlap:
        return "luxury", int((tl_min + tl_max) / 2)
    elif mid_overlap >= bud_overlap:
        return "mid", int((tm_min + tm_max) / 2)
    else:
        return "budget", int((tb_min + tb_max) / 2)


MONTH_NAMES = ['January','February','March','April','May','June',
               'July','August','September','October','November','December']


def _month_to_season(month: int) -> str:
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'summer'
    elif month in [6, 7, 8, 9]:
        return 'monsoon'
    else:
        return 'post_monsoon'


def _season_suitability(month: int, best_seasons: list, avoid_seasons: list) -> str:
    if month == 0:
        return 'okay'
    season = _month_to_season(month)
    season_keywords = {
        'winter':      ['winter', 'dec', 'jan', 'feb', 'cool', 'cold'],
        'summer':      ['summer', 'mar', 'apr', 'may', 'hot'],
        'monsoon':     ['monsoon', 'rain', 'jun', 'jul', 'aug', 'sep'],
        'post_monsoon': ['post', 'oct', 'nov', 'autumn']
    }
    keywords = season_keywords.get(season, [])
    for avoid in avoid_seasons:
        if any(k in avoid.lower() for k in keywords):
            return 'avoid'
    for best in best_seasons:
        if any(k in best.lower() for k in keywords):
            return 'best'
    return 'okay'


def _seasonal_temp(dest_raw_temp: dict, month: int) -> str:
    if month == 0 or not dest_raw_temp:
        return None
    season = _month_to_season(month)
    season_map = {
        'winter': 'winter',
        'summer': 'summer',
        'monsoon': 'monsoon',
        'post_monsoon': 'monsoon'
    }
    key = season_map.get(season, 'summer')
    return dest_raw_temp.get(key)


async def fetch_monthly_temp(lat: float, lon: float, month: int) -> Optional[float]:
    if month == 0:
        return None
    try:
        from datetime import datetime
        year = datetime.now().year - 1
        month_str = f"{month:02d}"
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        start = f"{year}-{month_str}-01"
        end = f"{year}-{month_str}-{last_day}"
        url = (f"https://archive-api.open-meteo.com/v1/archive"
               f"?latitude={lat}&longitude={lon}"
               f"&start_date={start}&end_date={end}"
               f"&daily=temperature_2m_mean&timezone=Asia/Kolkata")
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                temps = data.get("daily", {}).get("temperature_2m_mean", [])
                if temps:
                    valid = [t for t in temps if t is not None]
                    return round(sum(valid) / len(valid), 1) if valid else None
    except Exception:
        pass
    return None


def _best_cost_estimate(dest: dict, budget_min: int, budget_max: int) -> int:
    _, cost = _matched_tier(dest, budget_min, budget_max)
    return cost


def score_destination(dest: dict, prefs: dict) -> float:
    budget_min = prefs["budget_min"]
    budget_max = prefs["budget_max"]

    tier_name, tier_cost = _matched_tier(dest, budget_min, budget_max)

    if tier_name == "budget":
        tb_min, tb_max = dest["tier_budget"]
        tier_range = (tb_min, tb_max)
    elif tier_name == "mid":
        tier_range = dest["tier_mid"]
    else:
        tier_range = dest["tier_luxury"]

    overlap = max(0, min(budget_max, tier_range[1]) - max(budget_min, tier_range[0]))
    user_range = max(budget_max - budget_min, 1)
    tier_span = max(tier_range[1] - tier_range[0], 1)

    if overlap > 0:
        budget_fit = min(1.0, overlap / min(user_range, tier_span))
    else:
        distance = max(tier_range[0] - budget_max, budget_min - tier_range[1], 0)
        budget_fit = max(0.0, 1.0 - distance / max(budget_max, 1))
        if budget_fit < 0.2:
            budget_fit = 0.0

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


async def fetch_weather(dest: dict) -> Optional[dict]:
    dest_id = dest["id"]
    coords  = dest.get("coordinates", {})
    lat     = coords.get("latitude")
    lon     = coords.get("longitude")
    if not lat or not lon:
        return None
    cached = _weather_cache.get(dest_id)
    if cached and (time.time() - cached["ts"]) < WEATHER_CACHE_TTL:
        return cached["data"]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(WEATHER_BASE_URL, params={
                "lat": lat, "lon": lon,
                "appid": WEATHER_API_KEY, "units": "metric",
            })
            if resp.status_code != 200:
                return None
            raw  = resp.json()
            data = {
                "temp_c":            round(raw["main"]["temp"], 1),
                "feels_like":        round(raw["main"]["feels_like"], 1),
                "humidity":          raw["main"]["humidity"],
                "description":       raw["weather"][0]["description"].title(),
                "icon":              raw["weather"][0]["icon"],
                "wind_kmh":          round(raw["wind"]["speed"] * 3.6, 1),
                "is_suitable":       _is_weather_suitable(raw),
                "suitability_score": _weather_suitability_score(raw),
            }
            _weather_cache[dest_id] = {"data": data, "ts": time.time()}
            return data
    except Exception:
        return None


def _is_weather_suitable(raw: dict) -> bool:
    condition = raw["weather"][0]["main"].lower()
    temp = raw["main"]["temp"]
    if condition in {"thunderstorm", "tornado", "squall"}:
        return False
    if temp > 42 or temp < 0:
        return False
    return True


def _weather_suitability_score(raw: dict) -> float:
    condition = raw["weather"][0]["main"].lower()
    temp      = raw["main"]["temp"]
    humidity  = raw["main"]["humidity"]
    condition_scores = {
        "clear": 1.0, "clouds": 0.8, "drizzle": 0.6,
        "rain": 0.4, "snow": 0.5, "mist": 0.6,
        "fog": 0.5, "haze": 0.6, "thunderstorm": 0.1, "tornado": 0.0,
    }
    base = condition_scores.get(condition, 0.6)
    if 18 <= temp <= 32:
        temp_score = 1.0
    elif 10 <= temp < 18 or 32 < temp <= 38:
        temp_score = 0.7
    else:
        temp_score = 0.3
    humidity_score = 1.0 if humidity < 70 else 0.7 if humidity < 85 else 0.5
    return round(base * 0.5 + temp_score * 0.3 + humidity_score * 0.2, 2)


# ─── Pydantic models ─────────────────────────────────────────────────────────
class UserPreferences(BaseModel):
    budget_min:         int
    budget_max:         int
    travel_type:        str
    sustainability_pref: int
    user_id:            str
    travel_month:       int = 0


class FeedbackRequest(BaseModel):
    user_id:            str
    destination_id:     int
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
async def recommend(prefs: UserPreferences):
    global interaction_count

    state     = get_state(prefs.dict())
    state_idx = state_to_index(state)

    if prefs.user_id not in user_epsilon:
        user_epsilon[prefs.user_id] = EPSILON_INIT

    epsilon = user_epsilon[prefs.user_id]

    scored = []
    filtered_destinations = [
        d for d in DESTINATIONS
        if not (prefs.budget_max < d["full_budget_min"] or prefs.budget_min > d["full_budget_max"])
    ]
    if len(filtered_destinations) < 10:
        filtered_destinations = DESTINATIONS
    for dest in filtered_destinations:
        base_score = score_destination(dest, prefs.dict())
        q_val      = float(q_table[state_idx][dest["id"]])
        blended    = base_score * 0.5 + (q_val / (abs(q_val) + 1)) * 0.5

        if random.random() < epsilon:
            blended += random.uniform(0, 0.1)

        dest_min, dest_max = _budget_range_full(dest)
        in_budget = not (prefs.budget_max < dest_min or prefs.budget_min > dest_max)

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
            "estimated_cost":   _best_cost_estimate(dest, prefs.budget_min, prefs.budget_max),
            "budget_tier":      _matched_tier(dest, prefs.budget_min, prefs.budget_max)[0],
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
            "weather":          None,
            "season_suitability": None,
            "seasonal_temp":     None,
            "travel_month":      prefs.travel_month,
            "travel_month_name": MONTH_NAMES[prefs.travel_month - 1] if prefs.travel_month > 0 else None,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    user_epsilon[prefs.user_id] = max(EPSILON_MIN, epsilon * EPSILON_DECAY)
    interaction_count += 1

    seen_states: dict[str, int] = {}
    diverse = []
    for item in scored:
        dest_state = item["state"]
        if seen_states.get(dest_state, 0) < 1:
            diverse.append(item)
            seen_states[dest_state] = seen_states.get(dest_state, 0) + 1
        if len(diverse) == 10:
            break

    import asyncio
    dest_map = {d["id"]: d for d in DESTINATIONS}
    weather_results = []
    for item in diverse:
        w = await fetch_weather(dest_map[item["id"]])
        weather_results.append(w)
        await asyncio.sleep(0.1)

    for item, weather in zip(diverse, weather_results):
        item["weather"] = weather
        dest = dest_map[item["id"]]

        suitability = _season_suitability(
            prefs.travel_month,
            dest.get("best_seasons", []),
            dest.get("avoid_seasons", [])
        )
        item["season_suitability"] = suitability
        item["seasonal_temp"] = _seasonal_temp(
            dest.get("avg_temp_by_season", {}),
            prefs.travel_month
        )

        if weather:
            ws = weather.get("suitability_score", 0.8)
            item["score"] = round(item["score"] * (0.85 + ws * 0.15), 3)

        if suitability == "avoid":
            item["score"] = round(item["score"] * 0.7, 3)
        elif suitability == "best":
            item["score"] = round(item["score"] * 1.1, 3)

    diverse.sort(key=lambda x: x["score"], reverse=True)

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
    next_state_idx = (state_idx + fb.destination_id) % Q_TABLE_SIZE

    reward = 1.0 if fb.liked else -0.5
    replay_buffer.append((state_idx, fb.destination_id, reward, next_state_idx))

    batch = random.sample(replay_buffer, min(16, len(replay_buffer)))
    for s, a, r, ns in batch:
        update_q_table(s, a, r, ns)

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


# ─── Digital Travel ID endpoint ───────────────────────────────────────────────
@app.get("/documents/{user_id}", response_class=HTMLResponse)
async def get_user_documents(user_id: str):
    try:
        docs = admin_db.collection("travel_documents").where("userId", "==", user_id).get()

        doc_items = ""
        if docs:
            categories = {}
            for doc in docs:
                data = doc.to_dict()
                cat = data.get("category", "Other")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(data.get("base64Image", ""))

            for cat, images in categories.items():
                doc_items += f'<div class="doc-section"><h3>📄 {cat}</h3>'
                for img in images:
                    if img:
                        doc_items += f'<img src="data:image/jpeg;base64,{img}" style="width:100%;border-radius:8px;margin-bottom:8px;"/>'
                doc_items += '</div>'
        else:
            doc_items = '<p style="color:#999">No documents uploaded yet</p>'

    except Exception as e:
        doc_items = f'<p style="color:#999">Unable to load documents: {str(e)}</p>'

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SafarAI Digital Travel ID</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .header {{ background: #1A1A2E; color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 20px; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 5px 0 0; color: #aaa; }}
            .card {{ background: white; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .verified {{ color: #2E7D6E; font-weight: bold; font-size: 18px; text-align: center; margin: 20px 0; }}
            .doc-section {{ margin-bottom: 16px; }}
            .doc-section h3 {{ color: #1A1A2E; margin-bottom: 8px; }}
            .uid {{ color: #999; font-size: 12px; text-align: center; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌍 SafarAI</h1>
            <p>Digital Travel ID</p>
        </div>
        <div class="verified">✅ Verified Traveller</div>
        <div class="card">
            <b>Traveller ID</b><br>
            <span style="color:#1A1A2E">ST-{user_id[:8].upper()}</span>
        </div>
        <div class="card">
            <b>Uploaded Documents</b><br><br>
            {doc_items}
        </div>
        <div class="uid">Powered by SafarAI · nmit-1NT23CS241</div>
    </body>
    </html>
    """

import os
import time
import itertools
from typing import List, Dict

import dotenv
import requests
import pandas as pd

dotenv.load_dotenv()

client_id = os.getenv("CLIENT_ID")


def authenticate_trakt() -> None:
    client_secret = os.getenv("CLIENT_SECRET")
    headers = {"Content-Type": "application/json"}

    # Generate new device codes
    body = {
        "client_id": client_id
    }
    r = requests.post("https://api.trakt.tv/oauth/device/code", headers=headers, json=body).json()
    input(f"""Go to {r["verification_url"]} and enter [{r["user_code"]}]: \nPress ENTER when ready.""")

    dotenv.set_key(".env", "DEVICE_CODE", r["device_code"])
    dotenv.set_key(".env", "USER_CODE", r["user_code"])

    # Poll for the access_token
    body = {
        "code": r["device_code"],
        "client_id": client_id,
        "client_secret": client_secret

    }
    r = requests.post("https://api.trakt.tv/oauth/device/token", headers=headers, json=body).json()

    dotenv.set_key(".env", "ACTIVATION_EPOCH", str(r["created_at"]))
    dotenv.set_key(".env", "EXPIRES_IN", str(r["expires_in"]))
    dotenv.set_key(".env", "ACCESS_TOKEN", r["access_token"])
    dotenv.set_key(".env", "REFRESH_TOKEN", r["refresh_token"])


def get_history_page(page: int) -> List[List[Dict]]:
    limit = 100
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": client_id,
        "X-Pagination-Page": "10"
    }
    history = requests.get(f"https://api.trakt.tv/users/StinutsPeanuts/history?page={page}&limit={limit}", headers=headers).json()
    return history


def get_complete_history() -> List[List[Dict] | List[List[Dict]]]:
    idx = 1
    complete_history = []
    while True:
        page_history = get_history_page(idx)
        if page_history:
            # print(page_history)
            complete_history.append(page_history)
        else:
            break
        idx += 1

    complete_history = list(itertools.chain.from_iterable(complete_history))
    return complete_history


def restructure_data(data) -> List[Dict]:
    restructured_data = []
    for d in data:
        video_type = d["type"]

        structured_data = {
            "id": d["id"],
            "watched_at": d["watched_at"],
            "type": video_type,
            "title": d[video_type]["title"],
            "trakt_id": d[video_type]["ids"]["trakt"],
            "imdb_id": d[video_type]["ids"]["imdb"],
            "tmdb_id": d[video_type]["ids"]["tmdb"],
            "action": d["action"],
        }

        #TODO: typing
        if video_type == "episode":
            structured_data["year"] = d["show"]["year"]
            structured_data["show_name"] = d["show"]["title"]
            structured_data["episode_season"] = d[video_type]["season"]
            structured_data["episode_number"] = d[video_type]["number"]
            structured_data["slug"] = d["show"]["ids"]["slug"]
            structured_data["show_trakt_id"] = d["show"]["ids"]["trakt"]
            structured_data["show_tvdb_id"] = d["show"]["ids"]["tvdb"]
            structured_data["show_imdb_id"] = d["show"]["ids"]["imdb"]
            structured_data["show_tmdb_id"] = d["show"]["ids"]["tmdb"]
        else:
            structured_data["year"] = d[video_type]["year"]
            structured_data["show_name"] = None
            structured_data["episode_season"] = None
            structured_data["episode_number"] = None
            structured_data["slug"] = d[video_type]["ids"]["slug"]
            structured_data["show_trakt_slug"] = None
            structured_data["show_trakt_id"] = None
            structured_data["show_tvdb_id"] = None
            structured_data["show_imdb_id"] = None
            structured_data["show_tmdb_id"] = None

        restructured_data.append(structured_data)
    return restructured_data


def main():
    if int(time.time()) > int(os.getenv("ACTIVATION_EPOCH")) + int(os.getenv("EXPIRES_IN")) - 86400:
        authenticate_trakt()
    else:
        complete_history = get_complete_history()
        restructured_history = restructure_data(complete_history)
        df = pd.DataFrame.from_records(restructured_history)
        df["year"] = df["year"]
        df["episode_season"] = df["episode_season"].apply(lambda x: str(x).rstrip("0").rstrip(".") if "." in str(x) else x)
        df["episode_number"] = df["episode_number"].apply(lambda x: str(x).rstrip("0").rstrip(".") if "." in str(x) else x)
        df["show_trakt_id"] = df["show_trakt_id"].apply(lambda x: str(x).rstrip("0").rstrip(".") if "." in str(x) else x)
        df["show_tvdb_id"] = df["show_tvdb_id"].apply(lambda x: str(x).rstrip("0").rstrip(".") if "." in str(x) else x)
        df["show_tmdb_id"] = df["show_tmdb_id"].apply(lambda x: str(x).rstrip("0").rstrip(".") if "." in str(x) else x)
        print(df)
        df.to_excel("./trakt_history.xlsx", sheet_name="Trakt")


if __name__ == "__main__":
    main()

import itertools
import os
import time

import dotenv
import pandas as pd
import requests

dotenv.load_dotenv()

client_id = os.getenv("CLIENT_ID")


def authenticate_trakt():
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


def get_history(page: int):
    limit = 100
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": client_id,
        "X-Pagination-Page": "10"
    }
    history = requests.get(f"https://api.trakt.tv/users/StinutsPeanuts/history?page={page}&limit={limit}", headers=headers).json()
    return history


def main():
    if int(time.time()) > int(os.getenv("ACTIVATION_EPOCH")) + int(os.getenv("EXPIRES_IN")) - 86400:
        authenticate_trakt()
    else:
        full_history = []
        idx = 1
        while True:
            page_history = get_history(idx)
            if page_history:
                print(page_history)
                full_history.append(page_history)
            else:
                break
            idx += 1
        full_history = list(itertools.chain.from_iterable(full_history))
        pd.options.display.max_columns = None
        df = pd.DataFrame.from_records(full_history, columns=["id", "watched_at", "action", "type", "video_data", "extra"])
        print(df.head())

        new_data = []

        # iterate through each dictionary in the list
        for d in full_history:
            # extract the relevant information
            id = d['id']
            watched_at = d['watched_at']
            action = d['action']
            type = d['type']
            video_data = d[type]
            if type == 'episode':
                video_data.update(d['show'])
            # add the extracted information to the new list
            new_data.append({
                "id": id,
                "watched_at": watched_at,
                "action": action,
                "type": type,
                "video_data": video_data
            })

        # create a DataFrame from the new list of dictionaries
        df = pd.DataFrame.from_records(new_data, columns=["id", "watched_at", "action", "type", "video_data", "show_data"])

        # display the DataFrame
        print()
        print(df)
        print()
        print(df.head())


if __name__ == "__main__":
    main()

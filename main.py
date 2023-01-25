import os
import time

import dotenv
import requests

dotenv.load_dotenv()


def authenticate_trakt():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    headers = {"Content-Type": "application/json"}

    # Generate new device codes
    body = {
        "client_id": client_id
    }
    r = requests.post("https://api.trakt.tv/oauth/device/code", headers=headers, json=body).json()
    input(f"""Go to {r["verification_url"]} and enter [{r["user_code"]}]: """)

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


def main():
    if int(time.time()) > int(os.getenv("ACTIVATION_EPOCH")) + int(os.getenv("EXPIRES_IN")) - 86400:
        authenticate_trakt()
    else:
        print("Main can continue...")


if __name__ == "__main__":
    main()

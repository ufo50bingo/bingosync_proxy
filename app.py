# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import signal
import sys
import re
import requests

from types import FrameType
from flask import Flask, json, request

from utils.logging import logger

app = Flask(__name__)


@app.route("/create", methods=["POST"])
def hello_world():
    bingosync_url = "https://www.bingosync.com"

    client = requests.session()

    # janky way to get CSRF cookie and token
    initial_response = client.get(bingosync_url)
    result = re.search(
        'name="csrfmiddlewaretoken" value="([a-zA-Z0-9]+)"',
        initial_response.content.decode("utf-8"),
    )
    if result is None:
        raise Exception("failed to find csrf token")

    # post to room create url and include CSRF cookie and token
    create_response = client.post(
        bingosync_url,
        cookies=initial_response.cookies,
        data={
            "csrfmiddlewaretoken": result.group(1),
            "room_name": request.form["room_name"],
            "passphrase": request.form["passphrase"],
            "nickname": "ufo50bingobot",
            "game_type": "18",
            "variant_type": "187",
            "custom_json": request.form["custom_json"],
            "lockout_mode": "2",
            "seed": "",
            "is_spectator": "on",
            "hide_card": "on",
        },
    )
    if create_response.status_code != 200:
        raise Exception("bad status code from bingosync")

    # response URL is the new board URL
    response = json.jsonify({"url": create_response.url})
    return response, {
        "Access-Control-Allow-Origin": "*",
    }


def shutdown_handler(signal_int: int, frame: FrameType) -> None:
    logger.info(f"Caught Signal {signal.strsignal(signal_int)}")

    from utils.logging import flush

    flush()

    # Safely exit program
    sys.exit(0)


if __name__ == "__main__":
    # Running application locally, outside of a Google Cloud Environment

    # handles Ctrl-C termination
    signal.signal(signal.SIGINT, shutdown_handler)

    app.run(host="localhost", port=8080, debug=True)
else:
    # handles Cloud Run container termination
    signal.signal(signal.SIGTERM, shutdown_handler)

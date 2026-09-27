import os
import sys
import json
import time
import logging
import ssl
import requests
from src import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OpenF1LiveWorker")

try:
    import paho.mqtt.client as mqtt
except ImportError:
    logger.error("paho-mqtt is not installed. Live stream worker requires paho-mqtt==2.1.0. Exiting.")
    target_filepath = sys.argv[1] if len(sys.argv) > 1 else config.LIVE_STREAM_TXT
    err_path = target_filepath + ".err"
    with open(err_path, 'w', encoding='utf-8') as err_file:
        err_file.write("MQTT Library Missing: paho-mqtt==2.1.0 is required.")
    sys.exit(1)

# State Dictionary
live_state = {
    "laps": [],
    "location": [],
    "drivers": [],
    "weather": [],
    "race_control": []
}

def get_oauth_token():
    client_id = os.environ.get("OPENF1_CLIENT_ID")
    client_secret = os.environ.get("OPENF1_CLIENT_SECRET")
    if not client_id or not client_secret:
        logger.warning("Missing OPENF1_CLIENT_ID or OPENF1_CLIENT_SECRET environment variables.")
        return None

    try:
        resp = requests.post("https://api.openf1.org/token", data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }, timeout=config.DEFAULT_HTTP_TIMEOUT)
        if resp.status_code == 200:
            return resp.json().get("access_token")
        logger.error(f"Failed to fetch token: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"Auth error: {e}")
    return None

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Connected to OpenF1 MQTT stream successfully!")
        client.subscribe("v1/laps")
        client.subscribe("v1/location")
        client.subscribe("v1/car_data")
        client.subscribe("v1/weather")
        client.subscribe("v1/race_control")
        client.subscribe("v1/sessions")
    else:
        logger.error(f"Failed to connect, return code {rc}")
        if rc in [4, 5]: # Bad credentials or not authorized
            filepath = userdata.get("filepath", config.LIVE_STREAM_TXT) if isinstance(userdata, dict) else config.LIVE_STREAM_TXT
            err_path = filepath + ".err"
            with open(err_path, 'w', encoding='utf-8') as err_file:
                err_file.write(f"OpenF1 Authentication Failed (RC {rc}). Please verify OPENF1_CLIENT_ID and OPENF1_CLIENT_SECRET environment variables.")

import tempfile

def atomic_write_json(filepath: str, data: dict) -> None:
    """Atomically writes JSON payload to disk to prevent partial read race conditions."""
    dir_name = os.path.dirname(os.path.abspath(filepath)) or "."
    os.makedirs(dir_name, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
        json.dump(data, tf)
        temp_name = tf.name
    os.replace(temp_name, filepath)

import threading

state_lock = threading.Lock()
last_write_time = 0.0

def on_message(client, userdata, msg):
    global live_state, last_write_time
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode('utf-8'))

        with state_lock:
            if topic == "v1/laps":
                live_state["laps"].append(payload)
            elif topic == "v1/location":
                live_state["location"].append(payload)
                if len(live_state["location"]) > 1000:
                    live_state["location"] = live_state["location"][-1000:]
            elif topic == "v1/weather":
                live_state["weather"].append(payload)
            elif topic == "v1/race_control":
                live_state["race_control"].append(payload)

            current_time = time.time()
            if current_time - last_write_time >= 1.0:
                filepath = userdata.get("filepath", config.LIVE_STREAM_TXT) if isinstance(userdata, dict) else config.LIVE_STREAM_TXT
                atomic_write_json(filepath, live_state)
                last_write_time = current_time

    except Exception as e:
        logger.error(f"Message parsing error: {e}")

def on_disconnect(client, userdata, rc, properties=None):
    logger.warning(f"Disconnected from MQTT stream (rc={rc}). Attempting auto-reconnect...")

def start_worker(filepath=None):
    if not filepath:
        filepath = config.LIVE_STREAM_TXT
    token = get_oauth_token()
    if not token:
        logger.warning("Starting without auth token. Connection may be rejected if enforced.")

    try:
        # Compatibility across paho-mqtt versions
        if hasattr(mqtt, 'CallbackAPIVersion') and hasattr(mqtt.CallbackAPIVersion, 'VERSION1'):
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="pitwall-openf1-worker", clean_session=True)
        else:
            client = mqtt.Client(client_id="pitwall-openf1-worker", clean_session=True)
    except Exception:
        client = mqtt.Client(client_id="pitwall-openf1-worker", clean_session=True)

    client.user_data_set({"filepath": filepath})

    if token:
        client.username_pw_set(username="pitwall", password=token)

    try:
        ctx = ssl.create_default_context()
        client.tls_set_context(ctx)
    except Exception as e:
        logger.error(f"Failed to configure TLS: {e}")
        sys.exit(1)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.reconnect_delay_set(min_delay=1, max_delay=120)

    try:
        logger.info("Connecting to mqtt.openf1.org:8883...")
        client.connect("mqtt.openf1.org", 8883, keepalive=60)
        client.loop_forever()
    except Exception as e:
        logger.error(f"Critical MQTT connection failure: {e}")

if __name__ == '__main__':
    target_filepath = sys.argv[1] if len(sys.argv) > 1 else config.LIVE_STREAM_TXT
    os.makedirs(os.path.dirname(os.path.abspath(target_filepath)), exist_ok=True)
    start_worker(target_filepath)

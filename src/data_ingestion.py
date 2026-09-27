import fastf1

import os

import pandas as pd

import numpy as np

import logging

from data_providers import get_provider

from src import config



logger = logging.getLogger(__name__)



config.ensure_directories()



# Configure local persistence layer

CACHE_DIR = config.CACHE_DIR



# Enable FastF1 native disk cache

fastf1.Cache.enable_cache(CACHE_DIR)



def safe_extract(val, default=0):

    """Safely extracts a scalar from a Pandas Series, preventing ambiguity errors."""

    try:

        if isinstance(val, pd.Series):

            if val.empty:

                return default

            return val.iloc[0]

        return val

    except Exception:

        return default



def get_calendar(year):

    """Fetches the official race event schedule for the chosen season."""

    try:

        schedule = fastf1.get_event_schedule(year)

        return schedule['EventName'].tolist()

    except Exception as e:

        logger.warning(f"Failed to fetch calendar schedule for {year}: {e}")

        return ["Spanish Grand Prix", "Monaco Grand Prix", "Silverstone Grand Prix"]



def fetch_session_data(year, event, session_type):

    """Fetches session from FIA servers and extracts decoupled DataFrames via Providers."""

    provider = get_provider()

    return provider.fetch_session_data(year, event, session_type)



def fetch_live_session_data(year, event, session_type, live_file_path=None):

    """Parses the live JSON stream via Providers."""

    if not live_file_path:

        live_file_path = config.LIVE_STREAM_TXT

    provider = get_provider()

    return provider.fetch_live_session_data(year, event, session_type, live_file_path)



def get_driver_telemetry(session, driver_code):

    """

    Extracts high-frequency telemetry for a specific driver's fastest lap.

    Used for Mode A deep-dives.

    """

    try:

        if hasattr(session.laps, 'pick_drivers'):

            driver_laps = session.laps.pick_drivers(driver_code)

        else:

            driver_laps = session.laps[session.laps['Driver'] == driver_code]



        if driver_laps.empty:

            return pd.DataFrame()



        fastest_lap = driver_laps.pick_fastest()

        telemetry = fastest_lap.get_telemetry().add_distance()

        return telemetry

    except Exception:

        return pd.DataFrame()



import streamlit as st



@st.cache_data(ttl=30)

def get_auto_live_session():

    """

    Scans the OpenF1 REST API for an active session.

    If no session is active, returns (None, None, None).

    """

    from datetime import datetime, timezone

    import requests



    try:

        current_year = datetime.now(timezone.utc).year

        url = f"{config.OPENF1_BASE_URL}/sessions?year={current_year}"

        resp = requests.get(url, timeout=config.DEFAULT_HTTP_TIMEOUT)



        if resp.status_code == 200:

            sessions = resp.json()

            if sessions:

                sessions = sorted(sessions, key=lambda x: x.get('date_start', ''), reverse=True)

                latest = sessions[0]



                now = datetime.now(timezone.utc)

                date_start = datetime.fromisoformat(latest['date_start'].replace('Z', '+00:00'))

                date_end = datetime.fromisoformat(latest['date_end'].replace('Z', '+00:00'))



                if date_start <= now <= date_end:

                    sess_map = {'Practice 1': 'FP1', 'Practice 2': 'FP2', 'Practice 3': 'FP3', 'Sprint': 'S', 'Sprint Shootout': 'SQ', 'Qualifying': 'Q', 'Race': 'R'}

                    return latest['year'], latest['country_name'], sess_map.get(latest['session_name'], 'R')



        return None, None, None



    except Exception as e:

        logger.error(f"OpenF1 live session query failed: {e}")

        return None, None, None

"""
Centralized Configuration & Theme Design Tokens for F1 Pitwall Command Center.
Includes typed constants, FIA team color maps, API limits, and UI visual tokens.
"""

import os
from typing import Dict

# --- APP IDENTIFICATION ---
APP_TITLE = "F1 PIT-WALL | COMMAND CENTER"
APP_ICON = "️"
LAYOUT_MODE = "wide"

# --- NETWORK & API CONFIGURATION ---
OPENF1_BASE_URL = "https://api.openf1.org/v1"
DEFAULT_HTTP_TIMEOUT = 5.0  # Seconds
MAX_HTTP_RETRIES = 3
CACHE_TTL_SHORT = 60      # Seconds
CACHE_TTL_LONG = 86400    # 24 Hours

# --- PATHS & DIRECTORIES ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "f1_cache")
TRACK_CACHE_DIR = os.path.join(BASE_DIR, "track_cache")
LIVE_STREAM_TXT = os.path.join(CACHE_DIR, "live_stream.txt")
LIVE_ERR_FILE = os.path.join(CACHE_DIR, "live_stream.txt.err")

def ensure_directories():
    """Ensure required directories exist (delayed to runtime, not import time)."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(TRACK_CACHE_DIR, exist_ok=True)

# --- OFFICIAL FIA TEAM COLOR MAP (HIGH-CONTRAST HEX) ---
TEAM_COLORS: Dict[str, str] = {
    'VER': '#3671C6', 'PER': '#3671C6', 'RED BULL RACING': '#3671C6', 'RED BULL': '#3671C6', 'RBR': '#3671C6',
    'HAM': '#27F4D2', 'RUS': '#27F4D2', 'MERCEDES': '#27F4D2', 'MER': '#27F4D2',
    'LEC': '#E80020', 'SAI': '#E80020', 'FERRARI': '#E80020', 'FER': '#E80020',
    'NOR': '#FF8000', 'PIA': '#FF8000', 'MCLAREN': '#FF8000', 'MCL': '#FF8000',
    'ALO': '#229971', 'STR': '#229971', 'ASTON MARTIN': '#229971', 'AMR': '#229971',
    'GAS': '#0093CC', 'OCO': '#0093CC', 'ALPINE': '#0093CC', 'ALP': '#0093CC',
    'ALB': '#37BEDD', 'SAR': '#37BEDD', 'WILLIAMS': '#37BEDD', 'WIL': '#37BEDD',
    'TSU': '#52697F', 'RIC': '#52697F', 'LAW': '#52697F', 'RB': '#52697F', 'VCARB': '#52697F',
    'BOT': '#C92D4B', 'ZHO': '#C92D4B', 'KICK SAUBER': '#C92D4B', 'SAUBER': '#C92D4B', 'SAU': '#C92D4B',
    'MAG': '#B6BABD', 'HUL': '#B6BABD', 'BEA': '#B6BABD', 'HAAS': '#B6BABD', 'HAA': '#B6BABD',
}

# DEFAULT FALLBACK COLOR
DEFAULT_ACCENT_COLOR = "#4A90E2"

# --- TYRE COMPOUND PALETTE ---
TYRE_COLORS: Dict[str, str] = {
    'SOFT': '#FF0026',
    'S': '#FF0026',
    'MEDIUM': '#FFD000',
    'M': '#FFD000',
    'HARD': '#FFFFFF',
    'H': '#FFFFFF',
    'INTERMEDIATE': '#39B54A',
    'I': '#39B54A',
    'WET': '#004BFF',
    'W': '#004BFF',
    'UNKNOWN': '#64748B'
}

# --- SECTOR PERFORMANCE COLORS ---
SECTOR_COLORS: Dict[str, str] = {
    'purple': '#A020F0',
    'green': '#00FF7F',
    'yellow': '#FFEA00',
    'gray': '#64748B'
}



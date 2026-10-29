"""
Session identification and parsing utility for Pitwall F1.
Robustly parses session IDs, round indicators, event names, and session types
without fragile string splitting.
"""

from typing import Tuple, Union, Optional
import re

SESSION_TYPE_MAP = {
    "R": "R",
    "RACE": "R",
    "Q": "Q",
    "QUALIFYING": "Q",
    "QUAL": "Q",
    "S": "S",
    "SPRINT": "S",
    "SQ": "SQ",
    "SPRINT_QUALIFYING": "SQ",
    "SPRINT_SHOOTOUT": "SQ",
    "FP1": "FP1",
    "P1": "FP1",
    "PRACTICE 1": "FP1",
    "FP2": "FP2",
    "P2": "FP2",
    "PRACTICE 2": "FP2",
    "FP3": "FP3",
    "P3": "FP3",
    "PRACTICE 3": "FP3",
}

VALID_SESSION_CODES = {"R", "Q", "S", "SQ", "FP1", "FP2", "FP3"}

def standardize_session_type(session_type: Optional[str]) -> str:
    """Normalize session type code to standard FIA/FastF1 representation (R, Q, S, SQ, FP1, FP2, FP3)."""
    if not session_type:
        return "R"
    clean = str(session_type).strip().upper()
    return SESSION_TYPE_MAP.get(clean, clean if clean in VALID_SESSION_CODES else "R")

def parse_session_id(session_id: Optional[str], default_session_type: str = "R") -> Tuple[int, Union[str, int], str]:
    """
    Parses a session identifier into (year, event_or_round, session_type).
    
    Handles formats like:
      - 'S-2024-SPAIN' -> (2024, 'Spain', 'R')
      - 'S-2024-EMILIA-ROMAGNA' -> (2024, 'Emilia Romagna', 'R')
      - 'S-2024-EMILIA-ROMAGNA-Q' -> (2024, 'Emilia Romagna', 'Q')
      - 'S-2024-ROUND_10' -> (2024, 10, 'R')
      - 'S-2024-ROUND_10-FP1' -> (2024, 10, 'FP1')
      - '2023-MONACO' -> (2023, 'Monaco', 'R')
      - '2024-10' -> (2024, 10, 'R')
    """
    if not session_id:
        return 2024, "Spanish Grand Prix", standardize_session_type(default_session_type)
    
    raw = str(session_id).strip()
    
    # Strip leading 'S-' or 's-' prefix if present
    if raw.upper().startswith("S-"):
        raw = raw[2:]
        
    parts = raw.split("-")
    if not parts or not parts[0]:
        return 2024, "Spanish Grand Prix", standardize_session_type(default_session_type)
        
    # Extract year
    try:
        year = int(parts[0])
    except ValueError:
        year = 2024
        
    remaining_parts = parts[1:]
    if not remaining_parts:
        return year, "Spanish Grand Prix", standardize_session_type(default_session_type)
        
    # Check if the last part is a session type indicator
    session_type = default_session_type
    last_token = remaining_parts[-1].upper()
    if last_token in SESSION_TYPE_MAP or last_token in VALID_SESSION_CODES:
        session_type = standardize_session_type(last_token)
        remaining_parts = remaining_parts[:-1]
        
    if not remaining_parts:
        return year, "Spanish Grand Prix", session_type
        
    event_str = "-".join(remaining_parts).strip()
    
    # Check if event_str is a round number, e.g. 'ROUND_10', 'ROUND-10', 'R10', or purely digits '10'
    round_match = re.match(r'^(?:ROUND[_\-\s]?|R)(\d+)$', event_str, re.IGNORECASE)
    if round_match:
        return year, int(round_match.group(1)), session_type
        
    if event_str.isdigit():
        return year, int(event_str), session_type
        
    # Replace underscores with spaces and hyphens if they represent word separators
    # E.g. 'EMILIA-ROMAGNA' -> 'Emilia Romagna', 'SPANISH_GRAND_PRIX' -> 'Spanish Grand Prix'
    cleaned_event = event_str.replace("_", " ").replace("-", " ").strip()
    # Title-case for better readability and matching
    cleaned_event = " ".join([word.capitalize() for word in cleaned_event.split()])
    
    return year, cleaned_event, session_type

def format_session_id(year: int, event: Union[str, int], session_type: str = "R") -> str:
    """Format canonical session ID."""
    clean_type = standardize_session_type(session_type)
    if isinstance(event, int):
        ev = f"ROUND_{event}"
    else:
        ev = str(event).upper().replace(" ", "_")
    return f"S-{year}-{ev}-{clean_type}"

def pick_driver_laps(laps, driver_id: str):
    """
    Safely filter FastF1 laps DataFrame by driver identifier without triggering
    FastF1 deprecation warnings (pick_driver vs pick_drivers).
    """
    if laps is None or (hasattr(laps, 'empty') and laps.empty):
        return laps
    if hasattr(laps, 'pick_drivers'):
        try:
            return laps.pick_drivers(driver_id)
        except Exception:
            pass
    if hasattr(laps, 'pick_driver'):
        try:
            return laps.pick_driver(driver_id)
        except Exception:
            pass
    if hasattr(laps, 'columns') and 'Driver' in laps.columns:
        return laps[laps['Driver'] == driver_id]
    return laps

CIRCUIT_LAPS_MAP = {
    "SPAIN": 66,
    "SPANISH": 66,
    "BARCELONA": 66,
    "CATALUNYA": 66,
    "MONACO": 78,
    "MONTE CARLO": 78,
    "SILVERSTONE": 52,
    "BRITISH": 52,
    "GREAT BRITAIN": 52,
    "BELGIAN": 44,
    "SPA": 44,
    "ITALIAN": 53,
    "MONZA": 53,
    "BAHRAIN": 57,
    "SAKHIR": 57,
    "AUSTRIA": 71,
    "AUSTRIAN": 71,
    "RED BULL RING": 71,
    "HUNGARY": 70,
    "HUNGARIAN": 70,
    "HUNGARORING": 70,
    "DUTCH": 72,
    "NETHERLANDS": 72,
    "ZANDVOORT": 72,
    "SINGAPORE": 62,
    "MARINA BAY": 62,
    "JAPAN": 53,
    "JAPANESE": 53,
    "SUZUKA": 53,
    "UNITED STATES": 56,
    "USA": 56,
    "AUSTIN": 56,
    "COTA": 56,
    "MEXICO": 71,
    "MEXICAN": 71,
    "MEXICO CITY": 71,
    "BRAZIL": 71,
    "BRAZILIAN": 71,
    "SAO PAULO": 71,
    "INTERLAGOS": 71,
    "LAS VEGAS": 50,
    "QATAR": 57,
    "LUSAIL": 57,
    "ABU DHABI": 58,
    "YAS MARINA": 58,
    "AUSTRALIA": 58,
    "AUSTRALIAN": 58,
    "MELBOURNE": 58,
    "ALBERT PARK": 58,
    "CHINA": 56,
    "CHINESE": 56,
    "SHANGHAI": 56,
    "MIAMI": 57,
    "CANADA": 70,
    "CANADIAN": 70,
    "MONTREAL": 70,
    "AZERBAIJAN": 51,
    "BAKU": 51,
    "SAUDI ARABIA": 50,
    "SAUDI": 50,
    "JEDDAH": 50,
    "EMILIA ROMAGNA": 63,
    "IMOLA": 63
}

def get_circuit_laps(circuit_name: Optional[str], fallback: int = 66) -> int:
    """Returns canonical total race lap count for a given circuit or event name."""
    if not circuit_name:
        return fallback
    clean = str(circuit_name).upper().replace("_", " ").replace("-", " ")
    for key, laps in CIRCUIT_LAPS_MAP.items():
        if key in clean:
            return laps
    return fallback


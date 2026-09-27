import os

def is_rl_enabled() -> bool:
    """
    Authoritative central check for whether EXPERIMENTAL_RL_ENABLED is active.
    Missing -> disabled
    "false", "FALSE", "0", "" -> disabled
    "true", "TRUE", "True" -> enabled
    """
    return os.environ.get("EXPERIMENTAL_RL_ENABLED", "false").lower() == "true"

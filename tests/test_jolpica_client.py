import pytest
from unittest.mock import patch, MagicMock
from src.jolpica_client import JolpicaF1Client
import requests

@pytest.fixture
def jolpica_client():
    return JolpicaF1Client(cache_name="memory", expire_after=0)

@patch('requests_cache.CachedSession.get')
def test_get_seasons_success(mock_get, jolpica_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "MRData": {
            "SeasonTable": {
                "Seasons": [{"season": "2024", "url": "http://en.wikipedia.org/wiki/2024_Formula_One_World_Championship"}]
            }
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = jolpica_client.get_seasons()
    assert len(result) == 1
    assert result[0]["season"] == "2024"
    mock_get.assert_called_once()

@patch('requests_cache.CachedSession.get')
def test_get_driver_standings_empty(mock_get, jolpica_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "MRData": {
            "StandingsTable": {
                "StandingsLists": []
            }
        }
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = jolpica_client.get_driver_standings(year=2025)
    assert result == []

@patch('requests_cache.CachedSession.get')
def test_timeout_handling(mock_get, jolpica_client):
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
    
    result = jolpica_client.get_circuits(year=2024)
    assert result == []
    assert mock_get.call_count == jolpica_client.max_retries

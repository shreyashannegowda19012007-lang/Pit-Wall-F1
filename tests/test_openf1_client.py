import pytest
from unittest.mock import patch, MagicMock
from src.openf1_client import OpenF1Client
import requests

@pytest.fixture
def openf1_client():
    return OpenF1Client(cache_name="memory", expire_after=0)

@patch('requests_cache.CachedSession.get')
def test_get_meetings_success(mock_get, openf1_client):
    mock_response = MagicMock()
    mock_response.json.return_value = [{"meeting_key": 1, "year": 2024}]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = openf1_client.get_meetings(year=2024)
    assert len(result) == 1
    assert result[0]["meeting_key"] == 1
    mock_get.assert_called_once()

@patch('requests_cache.CachedSession.get')
def test_timeout_handling(mock_get, openf1_client):
    # Simulate timeout on all retries
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
    
    result = openf1_client.get_meetings(year=2024)
    assert result == []
    # Should retry max_retries times
    assert mock_get.call_count == openf1_client.max_retries

@patch('requests_cache.CachedSession.get')
def test_rate_limit_handling(mock_get, openf1_client):
    # Simulate a 429 Too Many Requests response
    mock_response_429 = MagicMock()
    mock_response_429.raise_for_status.side_effect = requests.exceptions.HTTPError(response=MagicMock(status_code=429))
    
    # Simulate a successful response after one failure
    mock_response_200 = MagicMock()
    mock_response_200.json.return_value = [{"meeting_key": 1}]
    mock_response_200.raise_for_status.return_value = None
    
    mock_get.side_effect = [mock_response_429.raise_for_status.side_effect, mock_response_200]
    
    result = openf1_client.get_meetings(year=2024)
    assert len(result) == 1
    assert mock_get.call_count == 2

@patch('requests_cache.CachedSession.get')
def test_empty_response_handling(mock_get, openf1_client):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = openf1_client.get_meetings(year=2024)
    assert result == []

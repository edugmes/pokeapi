from unittest import mock

from fastapi.testclient import TestClient

# Mock init since we're using cache decorator
mock.patch("fastapi_cache.decorator.cache", lambda *args, **kwargs: lambda f: f).start()

from .main import app

client = TestClient(app)


def test_all_berries_stats():
    response = client.get("/allBerryStats")
    assert response.status_code == 200
    assert list(response.json().keys()) == [
        "berries_names",
        "min_growth_time",
        "median_growth_time",
        "max_growth_time",
        "variance_growth_time",
        "mean_growth_time",
        "frequency_growth_time",
    ]

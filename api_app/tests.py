import json
from unittest.mock import patch
from urllib.parse import unquote
import requests
from django.test import TestCase
from rest_framework.test import APIClient

class MovieTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    class MockResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(f"HTTP {self.status_code}")

        def json(self):
            return self._payload

    @patch("api_app.views.requests.get")
    def test_movie_api_missing_param_returns_400(self, mock_get):
        response = self.client.get("/api/v1/movie-actor-summary/")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data.get("error"), "Movie name is required")
        mock_get.assert_not_called()

    @patch("api_app.views.requests.get")
    def test_movie_api_movie_not_found_returns_404(self, mock_get):
        def side_effect(url, timeout=None, **kwargs):
            if "/search/movie" in url:
                return self.MockResponse(200, {"results": []})
            raise AssertionError(f"Unexpected URL: {url}")

        mock_get.side_effect = side_effect
        response = self.client.get("/api/v1/movie-actor-summary/?movie=SomeNotRealMovie")
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data.get("error"), "Movie not found")

    @patch("api_app.views.requests.get")
    def test_movie_api_success_mocked_returns_unified_payload(self, mock_get):
        def side_effect(url, timeout=None, **kwargs):
            if "/search/movie" in url:
                return self.MockResponse(
                    200,
                    {
                        "results": [
                            {
                                "id": 123,
                                "title": "Avatar",
                                "release_date": "2009-12-18",
                                "vote_average": 7.5,
                            }
                        ]
                    },
                )
            if "/credits" in url:
                return self.MockResponse(
                    200,
                    {
                        "cast": [
                            {"name": "Actor One", "character": "Character One"},
                            {"name": "Actor Two", "character": "Character Two"},
                        ]
                    },
                )
            if "en.wikipedia.org/api/rest_v1/page/summary/" in url:
                title = unquote(url.rsplit("/", 1)[-1])
                if title == "Actor One":
                    return self.MockResponse(
                        200,
                        {
                            "extract": "Actor One is an actor known for ...",
                            "content_urls": {
                                "desktop": {
                                    "page": "https://en.wikipedia.org/wiki/Actor_One"
                                }
                            },
                        },
                    )
                if title == "Actor Two":
                    # simulate missing Wikipedia bio
                    return self.MockResponse(404, None)
                return self.MockResponse(404, None)
            raise AssertionError(f"Unexpected URL: {url}")

        mock_get.side_effect = side_effect
        response = self.client.get("/api/v1/movie-actor-summary/?movie=Avatar")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("movie", data)
        self.assertIn("top_actors", data)
        self.assertEqual(data["movie"]["title"], "Avatar")
        self.assertEqual(data["movie"]["rating"], 7.5)
        top_actors = data["top_actors"]
        self.assertEqual(len(top_actors), 2)
        self.assertEqual(top_actors[0]["name"], "Actor One")
        self.assertIn("bio_extract", top_actors[0])
        self.assertEqual(top_actors[1]["name"], "Actor Two")
        self.assertNotIn("bio_extract", top_actors[1])

    @patch("api_app.views.requests.get")
    def test_movie_api_external_failure_returns_500(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("timeout")
        response = self.client.get("/api/v1/movie-actor-summary/?movie=Avatar")
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertEqual(data.get("error"), "External API failed")
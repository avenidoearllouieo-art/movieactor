import os

import requests
from requests import RequestException
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Keep a local fallback for development, but prefer setting TMDB_API_KEY in your environment.
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "a06c12b8c95a73b69938cefbe9395cb6")
TMDB_TIMEOUT_SECONDS = 15


def tmdb_get_json(url: str) -> dict:
    """
    Fetch JSON from TMDB with a timeout and consistent error handling.
    """
    try:
        res = requests.get(url, timeout=TMDB_TIMEOUT_SECONDS)
        res.raise_for_status()
        return res.json()
    except (RequestException, ValueError) as exc:
        # Normalize any external failure into an exception the view can map to HTTP 500.
        raise RuntimeError("External API failed") from exc

@api_view(['GET'])
def movie_actor_summary(request):
    movie_name = request.GET.get('movie')

    if not movie_name:
        return Response({"error": "Movie name is required"}, status=400)

    if not TMDB_API_KEY:
        return Response({"error": "TMDB API key is missing"}, status=500)

    try:
        # 1. Search movie
        movie_url = (
            "https://api.themoviedb.org/3/search/movie"
            f"?api_key={TMDB_API_KEY}&query={movie_name}"
        )
        movie_res = tmdb_get_json(movie_url)

        if not movie_res['results']:
            return Response({"error": "Movie not found"}, status=404)

        movie = movie_res['results'][0]
        movie_id = movie['id']

        # 2. Get movie credits (actors)
        credits_url = (
            f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
        )
        credits_res = tmdb_get_json(credits_url)

        actors = []
        for actor in credits_res['cast'][:5]:  # top 5 actors
            actors.append({
                "name": actor['name'],
                "character": actor['character']
            })

        # 3. Data Transformation (IMPORTANT)
        result = {
            "movie_title": movie['title'],
            "release_date": movie['release_date'],
            "rating": movie['vote_average'],
            "top_actors": actors
        }

        return Response(result)

    except (RuntimeError, KeyError, TypeError, ValueError):
        return Response({"error": "External API failed"}, status=500)

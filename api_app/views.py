import os
import time
from urllib.parse import quote

import requests
from requests import RequestException
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiParameter, extend_schema

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


def wiki_page_summary(title: str) -> dict | None:
    """
    Fetch Wikipedia page summary for an actor.

    Wikipedia is used as the second public API (actor/bio information).
    """
    if not title:
        return None

    # Wikipedia may block requests that don't include a user-agent header.
    headers = {"User-Agent": "movieactor-midterm/1.0 (Django DRF)"}
    # Try both normal titles and underscore-style titles (some APIs are picky).
    candidates = [title, title.replace(" ", "_")]

    for candidate in candidates:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(candidate)}"

        # Retry once for transient blocks/rate limiting.
        for attempt in range(2):
            try:
                res = requests.get(url, timeout=TMDB_TIMEOUT_SECONDS, headers=headers)

                if res.status_code == 404:
                    break

                if res.status_code in (403, 429) and attempt == 0:
                    time.sleep(1.0)
                    continue

                res.raise_for_status()
                payload = res.json()
                return payload
            except (RequestException, ValueError):
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                break

    # For Wikipedia, treat failures as "missing bio" rather than failing the whole request.
    return None

@extend_schema(
    tags=["Movie + Actor Summary"],
    summary="Search a movie and return the top actors with Wikipedia bios",
    parameters=[
        OpenApiParameter(
            name="movie",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="Movie title to search in TMDB",
        ),
    ],
    responses={
        200: dict,
        400: dict,
        404: dict,
        500: dict,
    },
)
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

        cast = credits_res.get('cast') or []
        if not cast:
            return Response({"error": "Actors not found"}, status=404)

        actors = []
        for actor in cast[:5]:  # top 5 actors
            actor_name = actor.get('name')
            character = actor.get('character')

            wiki = wiki_page_summary(actor_name)
            actor_payload = {}
            if actor_name:
                actor_payload["name"] = actor_name
            if character:
                actor_payload["character"] = character

            if wiki and wiki.get("extract"):
                actor_payload["bio_extract"] = wiki.get("extract")
                actor_payload["wikipedia_url"] = (
                    wiki.get("content_urls", {})
                    .get("desktop", {})
                    .get("page")
                )

            actors.append(actor_payload)

        # 3. Data Transformation (IMPORTANT)
        rating = movie.get('vote_average')
        rating = round(rating, 1) if isinstance(rating, (int, float)) else rating

        result = {
            "movie": {
                "title": movie.get('title'),
                "release_date": movie.get('release_date'),
                "rating": rating,
            },
            "top_actors": actors
        }

        return Response(result)

    except (RuntimeError, KeyError, TypeError, ValueError):
        return Response({"error": "External API failed"}, status=500)

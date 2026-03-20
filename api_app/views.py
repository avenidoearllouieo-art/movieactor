import os
import time
from urllib.parse import quote

import requests
from requests import RequestException
from rest_framework.decorators import api_view
from rest_framework.response import Response
from urllib.parse import quote
from django.shortcuts import render

API_KEY = "a06c12b8c95a73b69938cefbe9395cb6"

def home(request):
    """Render the home page"""
    return render(request, 'api_app/home.html')

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

        # 3. Get Wikipedia bios for top actors
        top_actors = []
        for actor in credits_res['cast'][:5]:  # top 5 actors
            actor_data = {
                "name": actor['name'],
                "character": actor['character']
            }
            
            # Try to get Wikipedia bio
            wikipedia_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(actor['name'])}"
            headers = {
                'User-Agent': 'MovieActorAPI/1.0 (https://movieactor.example.com)',
                'Accept': 'application/json'
            }
            try:
                wiki_response = requests.get(wikipedia_url, timeout=5, headers=headers)
                if wiki_response.status_code == 200:
                    wiki_data = wiki_response.json()
                    actor_data["bio_extract"] = wiki_data.get("extract", "")
                    actor_data["wikipedia_url"] = wiki_data.get("content_urls", {}).get("desktop", {}).get("page", "")
                else:
                    # Log failed response for debugging
                    print(f"Wikipedia API failed for {actor['name']}: Status {wiki_response.status_code}")
            except requests.exceptions.RequestException as e:
                # Log exception for debugging
                print(f"Wikipedia request failed for {actor['name']}: {str(e)}")
            except Exception as e:
                # Log any other exception
                print(f"Unexpected error for {actor['name']}: {str(e)}")
                
            top_actors.append(actor_data)

        # 4. Data Transformation - new structure
        result = {
            "movie": {
                "title": movie['title'],
                "release_date": movie['release_date'],
                "rating": movie['vote_average']
            },
            "top_actors": top_actors
        }

        return Response(result)

    except (RuntimeError, KeyError, TypeError, ValueError):
        return Response({"error": "External API failed"}, status=500)

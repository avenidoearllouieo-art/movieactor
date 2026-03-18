import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response

API_KEY = "a06c12b8c95a73b69938cefbe9395cb6"

@api_view(['GET'])
def movie_actor_summary(request):
    movie_name = request.GET.get('movie')

    if not movie_name:
        return Response({"error": "Movie name is required"}, status=400)

    try:
        # 1. Search movie
        movie_url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_name}"
        movie_res = requests.get(movie_url).json()

        if not movie_res['results']:
            return Response({"error": "Movie not found"}, status=404)

        movie = movie_res['results'][0]
        movie_id = movie['id']

        # 2. Get movie credits (actors)
        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={API_KEY}"
        credits_res = requests.get(credits_url).json()

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

    except Exception as e:
        return Response({"error": "External API failed"}, status=500)
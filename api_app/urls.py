from django.urls import path
from .views import movie_actor_summary, home

urlpatterns = [
    path('', home, name='home'),
    path('api/v1/movie-actor-summary/', movie_actor_summary),
]
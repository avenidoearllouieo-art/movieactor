from django.contrib import admin
from django.urls import path
from api_app.views import movie_actor_summary

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/movie-actor-summary/', movie_actor_summary),
]
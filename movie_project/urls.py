from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from api_app.views import movie_actor_summary

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/movie-actor-summary/', movie_actor_summary),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='swagger-ui'),
]
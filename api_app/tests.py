from django.test import TestCase
from rest_framework.test import APIClient

class MovieTest(TestCase):
    def test_movie_api(self):
        client = APIClient()
        response = client.get('/api/v1/movie-actor-summary/?movie=Avatar')
        self.assertEqual(response.status_code, 200)
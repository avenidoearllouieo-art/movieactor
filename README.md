# Movie + Actor Summary API (TMDB + Wikipedia)
## Endpoint
Base URL:
- http://127.0.0.1:8000
Unified endpoint (versioned):
- GET /api/v1/movie-actor-summary/?movie={movieTitle}
Query parameter:
- movie (required): Movie title to search in TMDB
Swagger/OpenAPI docs:
- GET /api/docs/
- GET /api/schema/
## Example request
```bash
curl "http://127.0.0.1:8000/api/v1/movie-actor-summary/?movie=Avatar"
```

Example success response (shape)

{
  "movie": {
    "title": "Avatar",
    "release_date": "2009-12-18",
    "rating": 7.5
  },
  "top_actors": [
    {
      "name": "Actor Name",
      "character": "Character Name",
      "bio_extract": "Short Wikipedia extract...",
      "wikipedia_url": "https://en.wikipedia.org/wiki/..."
    }
  ]
}

## Integration architecture

This backend integrates two public APIs:

### TMDB (TheMovieDB)
- Call 1: search the movie by title
- Call 2: fetch movie credits to get the top actors

### Wikipedia (public REST endpoint)
- For each top actor returned by TMDB, fetch the Wikipedia page summary to enrich actor data with a short biography extract.

## Data transformation logic

The system returns a clean unified JSON response:

- Computes/reshapes TMDB fields into a nested movie object: title, release_date, and numeric rating.
- Combines TMDB credits + Wikipedia bios into top_actors.
- Removes raw/unnecessary API fields by only returning the unified fields described above.
- Includes Wikipedia fields (bio_extract, wikipedia_url) only when available.

## Error handling strategy

- **400 Bad Request**: missing movie query parameter.
- **404 Not Found**: movie not found (or missing cast/actors).
- **500 Internal Server Error (external failure)**: when an external API request fails (timeout, network error, unexpected response).

## Versioning reasoning (why /api/v1/ and when /api/v2/)

A breaking change that would require v2:

- Changing the response schema (for example renaming/removing movie or top_actors, changing the structure of actor objects, or changing rating formatting).

Why versioning matters in integration systems:

- Clients and other services depend on a stable API contract. Versioning prevents breaking existing consumers when the backend evolves, while still allowing newer clients to adopt updated behavior.

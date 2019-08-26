import requests
from lxml import html
from tmdbv3api import TMDb
from tmdbv3api import Movie
import config_tools


def imdb_get_movies(plex, data):
    tmdb = TMDb()
    movie = Movie()
    tmdb.api_key = config_tools.TMDB().apikey
    imdb_url = data
    if imdb_url[-1:] == " ":
        imdb_url = imdb_url[:-1]
    imdb_map = {}
    library_language = plex.MovieLibrary.language
    r = requests.get(imdb_url, headers={'Accept-Language': library_language})
    tree = html.fromstring(r.content)
    title_ids = tree.xpath("//div[contains(@class, 'lister-item-image')]"
                           "//a/img//@data-tconst")
    for m in plex.MovieLibrary.all():
        if 'themoviedb://' in m.guid:
            if not tmdb.api_key == "None":
                tmdb_id = m.guid.split('themoviedb://')[1].split('?')[0]
                tmdbapi = movie.details(tmdb_id)
                imdb_id = tmdbapi.imdb_id
            else:
                imdb_id = None
        elif 'imdb://' in m.guid:
            imdb_id = m.guid.split('imdb://')[1].split('?')[0]
        else:
            imdb_id = None

        if imdb_id and imdb_id in title_ids:
            imdb_map[imdb_id] = m
        else:
            imdb_map[m.ratingKey] = m

    matched_imbd_movies = []
    missing_imdb_movies = []
    for imdb_id in title_ids:
        movie = imdb_map.pop(imdb_id, None)
        if movie:
            matched_imbd_movies.append(plex.Server.fetchItem(movie.ratingKey))
        else:
            missing_imdb_movies.append(imdb_id)

    return matched_imbd_movies, missing_imdb_movies

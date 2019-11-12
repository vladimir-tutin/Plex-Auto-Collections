import re
import requests
from lxml import html
from tmdbv3api import TMDb
from tmdbv3api import Movie
from tmdbv3api import Collection
from tmdbv3api import Person
import config_tools
from urllib.parse import urlparse
import trakt


def imdb_get_movies(plex, data):
    tmdb = TMDb()
    movie = Movie()
    tmdb.api_key = config_tools.TMDB().apikey
    imdb_url = data
    if imdb_url[-1:] == " ":
        imdb_url = imdb_url[:-1]
    imdb_map = {}
    library_language = plex.MovieLibrary.language
    try:
        r = requests.get(imdb_url, headers={'Accept-Language': library_language})
    except requests.exceptions.MissingSchema:
        return
    tree = html.fromstring(r.content)
    title_ids = tree.xpath("//div[contains(@class, 'lister-item-image')]"
                           "//a/img//@data-tconst")
    if title_ids:
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


def tmdb_get_movies(plex, data):
    try:
        tmdb_id = re.search('.*?(\\d+)', data)
        tmdb_id = tmdb_id.group(1)
    except AttributeError:  # Bad URL Provided
        return

    t_movie = Movie()
    tmdb = Collection()
    tmdb.api_key = config_tools.TMDB().apikey  # Set TMDb api key for Collection
    if tmdb.api_key == "None":
        raise KeyError("Invalid TMDb API Key")
    t_movie.api_key = tmdb.api_key  # Copy same api key to Movie
    t_col = tmdb.details(tmdb_id)
    t_movs = []
    for tmovie in t_col.parts:
        t_movs.append(tmovie['id'])

    # Create dictionary of movies and their guid
    # GUIDs reference from which source Plex has pulled the metadata
    p_m_map = {}
    p_movies = plex.MovieLibrary.all()
    for m in p_movies:
        guid = m.guid
        if "themoviedb://" in guid:
            guid = guid.split('themoviedb://')[1].split('?')[0]
        elif "imdb://" in guid:
            guid = guid.split('imdb://')[1].split('?')[0]
        else:
            guid = "None"
        p_m_map[m] = guid

    matched = []
    missing = []
    # We want to search for a match first to limit TMDb API calls
    # Too many rapid calls can cause a momentary block
    # If needed in future maybe add a delay after x calls to let the limit reset
    for mid in t_movs:  # For each TMBd ID in TMBd Collection
        match = False
        for m in p_m_map:  # For each movie in Plex
            if "tt" not in p_m_map[m] is not "None":  # If the Plex movie's guid does not start with tt
                if int(p_m_map[m]) == int(mid):
                    match = True
                    break
        if not match:
            imdb_id = t_movie.details(mid).entries['imdb_id']
            for m in p_m_map:
                if "tt" in p_m_map[m]:
                    if p_m_map[m] == imdb_id:
                        match = True
                        break
        if match:
            matched.append(m)
        else:
            missing.append(t_movie.details(mid).entries['imdb_id'])

    return matched, missing


def trakt_get_movies(plex, data):
    tmdb = TMDb()
    tmdb.api_key = config_tools.TMDB().apikey  # Set TMDb api key for Collection
    trakt.Trakt.configuration.defaults.client(config_tools.Trakt().client_id, config_tools.Trakt().client_secret)
    movie = Movie()
    tmdb.api_key = config_tools.TMDB().apikey
    trakt_url = data
    if trakt_url[-1:] == " ":
        trakt_url = trakt_url[:-1]
    imdb_map = {}
    library_language = plex.MovieLibrary.language
    trakt_list_path = urlparse(trakt_url).path
    trakt_list_items = trakt.Trakt[trakt_list_path].items()
    title_ids = [m.pk[1] for m in trakt_list_items if isinstance(m, trakt.objects.movie.Movie)]

    plex_movies = plex.MovieLibrary.all()
    if title_ids:
        for m in plex_movies:
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


def tmdb_get_summary(data, type):
    collection = Collection()
    person = Person()
    collection.api_key = config_tools.TMDB().apikey
    person.api_key = collection.api_key
    collection.language = config_tools.TMDB().language
    person.language = collection.language

    if type == "overview":
        return collection.details(data).overview
    elif type == "biography":
        return person.details(data).biography

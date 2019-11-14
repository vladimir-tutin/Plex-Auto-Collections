import config_tools
from urllib.parse import urlparse
import trakt

def trakt_get_movies(plex, data):
    trakt.Trakt.configuration.defaults.client(config_tools.Trakt().client_id, config_tools.Trakt().client_secret)
    trakt_url = data
    if trakt_url[-1:] == " ":
        trakt_url = trakt_url[:-1]
    imdb_map = {}
    trakt_list_path = urlparse(trakt_url).path
    trakt_list_items = trakt.Trakt[trakt_list_path].items()
    title_ids = [m.pk[1] for m in trakt_list_items if isinstance(m, trakt.objects.movie.Movie)]

    if title_ids:
        for item in plex.MovieLibrary.all():
            guid = urlparse(item.guid)
            item_type = guid.scheme.split('.')[-1]
            if item_type == 'imdb':
                imdb_id = guid.netloc
            elif item_type == 'themoviedb':
                tmdb_id = guid.netloc
                imdb_id = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'movie').get_key('imdb')
            else:
                imdb_id = None

            if imdb_id and imdb_id in title_ids:
                imdb_map[imdb_id] = item
            else:
                imdb_map[item.ratingKey] = item

        matched_imbd_movies = []
        missing_imdb_movies = []
        for imdb_id in title_ids:
            movie = imdb_map.pop(imdb_id, None)
            if movie:
                matched_imbd_movies.append(plex.Server.fetchItem(movie.ratingKey))
            else:
                missing_imdb_movies.append(imdb_id)

        return matched_imbd_movies, missing_imdb_movies

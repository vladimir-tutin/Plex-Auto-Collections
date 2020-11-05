import config_tools
from urllib.parse import urlparse
import plex_tools
import trakt
import os

def trakt_get_movies(config_path, plex, data, is_userlist=True):
    config_tools.TraktClient(config_path)
    if is_userlist:
        trakt_url = data
        if trakt_url[-1:] == " ":
            trakt_url = trakt_url[:-1]
        trakt_list_path = urlparse(trakt_url).path
        trakt_list_items = trakt.Trakt[trakt_list_path].items()
    else:
        # Trending list
        max_items = int(data)
        trakt_list_items = trakt.Trakt['movies'].trending(per_page=max_items)
    title_ids = [m.pk[1] for m in trakt_list_items if isinstance(m, trakt.objects.movie.Movie)]

    imdb_map = {}
    plex_tools.create_cache(config_path)
    if title_ids:
        for item in plex.Library.all():
            item_type = urlparse(item.guid).scheme.split('.')[-1]
            if item_type == 'plex':
                # Check cache for imdb_id
                imdb_id = plex_tools.query_cache(config_path, item.guid, 'imdb_id')
                if not imdb_id:
                    imdb_id, tmdb_id = plex_tools.alt_id_lookup(plex, item)
                    print("| Cache | + | {} | {} | {} | {}".format(item.guid, imdb_id, tmdb_id, item.title))
                    plex_tools.update_cache(config_path, item.guid, imdb_id=imdb_id, tmdb_id=tmdb_id)
            elif item_type == 'imdb':
                imdb_id = urlparse(item.guid).netloc
            elif item_type == 'themoviedb':
                tmdb_id = urlparse(item.guid).netloc
                # lookup can sometimes return a list
                lookup = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'movie')
                if lookup:
                    lookup = lookup[0] if isinstance(lookup, list) else lookup
                    imdb_id = lookup.get_key('imdb')
                else:
                    imdb_id = None
            else:
                imdb_id = None

            if imdb_id and imdb_id in title_ids:
                imdb_map[imdb_id] = item
            else:
                imdb_map[item.ratingKey] = item

        matched_imdb_movies = []
        missing_imdb_movies = []
        for imdb_id in title_ids:
            movie = imdb_map.pop(imdb_id, None)
            if movie:
                matched_imdb_movies.append(plex.Server.fetchItem(movie.ratingKey))
            else:
                missing_imdb_movies.append(imdb_id)

        return matched_imdb_movies, missing_imdb_movies
    else:
        # No movies
        return None, None

def trakt_get_shows(config_path, plex, data, is_userlist=True):
    config_tools.TraktClient(config_path)
    if is_userlist:
        trakt_url = data
        if trakt_url[-1:] == " ":
            trakt_url = trakt_url[:-1]
        trakt_list_path = urlparse(trakt_url).path
        trakt_list_items = trakt.Trakt[trakt_list_path].items()
    else:
        # Trending list
        max_items = int(data)
        trakt_list_items = trakt.Trakt['shows'].trending(per_page=max_items)

    tvdb_map = {}
    title_ids = []
    for m in trakt_list_items:
        if isinstance(m, trakt.objects.show.Show):
            if m.pk[1] not in title_ids:
                title_ids.append(m.pk[1])
        elif isinstance(m, trakt.objects.season.Season):
            if m.show.pk[1] not in title_ids:
                title_ids.append(m.show.pk[1])
        elif isinstance(m, trakt.objects.episode.Episode):
            if m.show.pk[1] not in title_ids:
                title_ids.append(m.show.pk[1])

    if title_ids:
        for item in plex.Library.all():
            guid = urlparse(item.guid)
            item_type = guid.scheme.split('.')[-1]
            # print('item_type', item, item_type)
            if item_type == 'thetvdb':
                tvdb_id = guid.netloc
            elif item_type == 'themoviedb':
                tmdb_id = guid.netloc
                lookup = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'show')
                if lookup:
                    lookup = lookup[0] if isinstance(lookup, list) else lookup
                    tvdb_id = lookup.get_key('tvdb')
                else:
                    tvdb_id = None
            else:
                tvdb_id = None

            if tvdb_id and tvdb_id in title_ids:
                tvdb_map[tvdb_id] = item
            else:
                tvdb_map[item.ratingKey] = item

        matched_tvdb_shows = []
        missing_tvdb_shows = []

        for tvdb_id in title_ids:
            show = tvdb_map.pop(tvdb_id, None)
            if show:
                matched_tvdb_shows.append(plex.Server.fetchItem(show.ratingKey))
            else:
                missing_tvdb_shows.append(tvdb_id)

        return matched_tvdb_shows, missing_tvdb_shows
    else:
        # No shows
        return None, None

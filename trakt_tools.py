import config_tools
from urllib.parse import urlparse
import plex_tools
import trakt

import logging
log = logging.getLogger(__name__)

def trakt_get_movies(config_path, plex, data):
    config_tools.TraktClient(config_path)
    trakt_url = data
    if trakt_url[-1:] == " ":
        trakt_url = trakt_url[:-1]
    imdb_map = {}
    trakt_list_path = urlparse(trakt_url).path
    log.debug('Downloading Trakt list.')
    trakt_list_items = trakt.Trakt[trakt_list_path].items()
    log.debug("Queuing Trakt list item IDs.")
    title_ids = [m.pk[1] for m in trakt_list_items if isinstance(m, trakt.objects.movie.Movie)]

    if title_ids:
        log.debug('Building list of Plex items from {}.'.format(plex.library))
        for item in plex.Library.all():
            guid = urlparse(item.guid)
            item_type = guid.scheme.split('.')[-1]
            if item_type == 'imdb':
                imdb_id = guid.netloc
            elif item_type == 'themoviedb':
                tmdb_id = guid.netloc
                # Use Trakt API to get the imdb id from the tmdb id
                lookup = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'movie')
                if lookup:
                    # lookup can sometimes return a list
                    if isinstance(lookup, list):
                        imdb_id = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'movie')[0].get_key('imdb')
                    else:
                        imdb_id = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'movie').get_key('imdb')
                else:
                    log.warning("Could not determine the IMDb ID from TMDb ID {}.".format(tmdb_id))
                    imdb_id = None
            else:
                log.warning("Unknown Plex item type from guid {}. Only 'imdb' and 'themoviedb' supported.".format(guid))
                imdb_id = None

            if imdb_id and imdb_id in title_ids:
                log.debug('Found {} in Plex.'.format(imdb_id))
                imdb_map[imdb_id] = item
            else:
                imdb_map[item.ratingKey] = item
        log.debug('Fetching Plex items - complete')

        matched_imbd_movies = []
        missing_imdb_movies = []
        for imdb_id in title_ids:
            movie = imdb_map.pop(imdb_id, None)
            if movie:
                log.debug('Found {}'.format(movie))
                matched_imbd_movies.append(plex.Server.fetchItem(movie.ratingKey))
            else:
                log.debug('*** {} NOT found.'.format(imdb_id))
                missing_imdb_movies.append(imdb_id)

        return matched_imbd_movies, missing_imdb_movies
    else:
        # No movies
        log.warning("No movies found in {}".format(trakt_url))
        return None, None

def trakt_get_shows(config_path, plex, data):
    config_tools.TraktClient(config_path)
    trakt_url = data
    if trakt_url[-1:] == " ":
        trakt_url = trakt_url[:-1]
    tvdb_map = {}
    trakt_list_path = urlparse(trakt_url).path
    log.debug('Downloading Trakt list.')
    trakt_list_items = trakt.Trakt[trakt_list_path].items()
    log.debug("Queuing Trakt list item IDs.")
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
        log.debug('Building list of Plex items from {}.'.format(plex.library))
        for item in plex.Library.all():
            guid = urlparse(item.guid)
            item_type = guid.scheme.split('.')[-1]
            if item_type == 'thetvdb':
                tvdb_id = guid.netloc
            elif item_type == 'themoviedb':
                tmdb_id = guid.netloc
                lookup = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'show')
                if lookup:
                    if isinstance(lookup, list):
                        tvdb_id = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'show')[0].get_key('tvdb')
                    else:
                        tvdb_id = trakt.Trakt['search'].lookup(tmdb_id, 'tmdb', 'show').get_key('tvdb')
                else:
                    log.warning("Could not determine the TVDb ID from TMDb ID {}.".format(tmdb_id))
                    tvdb_id = None
            else:
                log.warning("Unknown Plex item type from guid {}. Only 'thetvdb' and 'themoviedb' supported.".format(guid))
                tvdb_id = None

            if tvdb_id and tvdb_id in title_ids:
                log.debug('Found {} in Plex.'.format(tvdb_id))
                tvdb_map[tvdb_id] = item
            else:
                tvdb_map[item.ratingKey] = item
        log.debug('Fetching Plex items - complete')

        matched_tvdb_shows = []
        missing_tvdb_shows = []

        for tvdb_id in title_ids:
            show = tvdb_map.pop(tvdb_id, None)
            if show:
                log.debug('Found {}'.format(show))
                matched_tvdb_shows.append(plex.Server.fetchItem(show.ratingKey))
            else:
                log.debug('*** {} NOT found.'.format(tvdb_id))
                missing_tvdb_shows.append(tvdb_id)

        return matched_tvdb_shows, missing_tvdb_shows
    else:
        # No shows
        log.warning("No shows found in {}".format(trakt_url))
        return None, None

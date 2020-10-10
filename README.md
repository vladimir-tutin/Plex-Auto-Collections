# Plex Auto Collections
Plex Auto Collections is a Python 3 script that works off a configuration file to create/update Plex collections. Collection management with this tool can be automated in a varying degree of customizability. Supports IMDB, TMDb, and Trakt lists as well as built in Plex filters such as actors, genres, year, studio and more.

![https://i.imgur.com/iHAYFIZ.png](https://i.imgur.com/iHAYFIZ.png)

# Usage

This script can be used as an interactive Python shell script as well as a headless, configuration-driven script.

The interactive shell script has some limited abilities including the ability to add new collections based off filters, delete collections, search for collections and manage existing collections. The bulk of the feature-set is focused on configuration-driven updates.

## Local Installation
Some limited testing has been done only on Python 3.7 and 3.8 on Linux and Windows. Dependencies must be installed by running:

```shell
pip install -r requirements.txt
```

If there are issues installing dependencies try:

```shell
pip install -r requirements.txt --ignore-installed
```

To run the script in an interactive terminal run:

```shell
python plex_auto_collections.py
```

A `config.yml` file is required to run the script. The script checks for a `config.yml` file alongside `plex_auto_collections.py` as well as in `config/config.yml`. If desired, a different configuration file can be specified with `-c <path_to_config>` or `--config-path <path_to_config>`. This could be useful for creating collections against different libraries, such as a Movie and TV library (in this case, be sure to update the `library_type` in the configuration file).

```shell
python plex_auto_collections.py --config-path <path_to_config>
```

If you would like to run the script without any user interaction (e.g. to schedule the script to run on a schedule) the script can be launched with `-u` or `--update`:

```shell
python plex_auto_collections.py --update
```

## Docker

A simple `Dockerfile` is available in this repo if you'd like to build it yourself. The official build is also available from dockerhub here: https://hub.docker.com/r/burkasaurusrex/plex-auto-collections

The docker implementation today is limited but will improve over time. To use, try the following:

```shell
docker run -v '/mnt/user/plex-auto-collections/':'/config':'rw' 'burkasaurusrex/plex-auto-collections'
```

The `-v '/mnt/user/plex-auto-collections/':'/config'` mounts a persistent volume to store your config file. Today, the docker image defaults to running the config named `config.yml` in your persistent volume (eventually, the docker will support an environment variable to change the config path).

Lastly, you may need to run the docker with `-it` in order to interact with the script. For example, if you'd like to use Trakt lists, you need to go through the OAuth flow and interact with the script at first-run. After that, you should be able to run it without the `-it` flag.

# Configuration

The script allows utilizes a YAML config file to create collections in Plex. This is great for a few reasons:
- Setting metadata manually in Plex is cumbersome. Having a config file allows template to be reused, backed-up, transferred, etc.
- Plex often loses manually set metadata. Having a config file fixes metadata creep.
- Collections change often. Having a config file pointing to dynamic data keeps collections fresh.

There are currently six YAML mappings that can be set:
- `collections` (required)
- `plex` (required)
- `image_server` (optional)
- `tmdb` (optional, but recommended)
- `trakt` (optional)
- `radarr` (optional)

You can find a template config file in [config/config.yml.template](config/config.yml.template)

## Collections

Each collection is defined by the mapping name which becomes the name of the Plex collection. Additionally, there are three other attributes to set for each collection:
- List Type (required)
- Details (optional)
- Subfilters (optional)
- System Name (optional)

### List Type (Collection Attribute)

The only required attribute for each collection is the list type. There are four different list types to choose from:
- Plex Collection
- TMDb Collection
- IMDb List or Search
- Trakt List

Note that each list type supports multiple lists.

#### Plex Collection (List Type)

There are a number of built in Plex filters such as actors, genres, year, studio and more. For more filters refer to the [plexapi.video.Movie](https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Movie) documentation. Not everything has been tested, so results may vary based off the filter.

Here's some high-level ideas:

```yaml
collections:
  Documentaries:
    genres: Documentary
```
```yaml
collections:
  Dave Chappelle:
    actors: Dave Chappelle
```
```yaml
collections:
  Pixar:
    studio: Pixar
```
```yaml
collections:
  90s Movies:
    year:
      - 1990
      - 1991
      - 1992
      - 1993
      - 1994
      - 1995
      - 1996
      - 1997
      - 1998
      - 1999
```

#### TMDb Collection (List Type)

The Movie Database (TMDb) strives to group movies into logical collections. This script can easily leverage that data:

```yaml
collections:
  Jurassic Park:
    tmdb_list: https://www.themoviedb.org/collection/328
```
```yaml
collections:
  Alien (Past & Present):
    tmdb_list:
      - https://www.themoviedb.org/collection/8091
      - https://www.themoviedb.org/collection/135416
```

Alternatively you can specify which tmdb_list, tmdb_summary, tmdb_poster all at once by:

```yaml
collections:
  Jurassic Park:
    tmdbID: 328
```
```yaml
collections:
  Alien (Past & Present):
    tmdbID: 8091, 135416
```

Notes:
- The tmbdID can be either from a collection or an individual movie
- You can specify more then one tmdbID but it will pull the poster and summary from only the first one.
- Local posters are loaded over tmdb_poster if they exist unless tmdb_poster is also specified in details

#### IMDb List or Search (List Type)

This script can also scrape IMDb lists as well as searches (particularly useful for dynamic data):

```yaml
collections:
  James Bonds:
    imdb_list: https://www.imdb.com/list/ls006405458
```
```yaml
collections:
  IMDb Top 250:
    imdb_list: https://www.imdb.com/search/title/?groups=top_250&count=250
```
Note that searches can be useful to show / sort / filter IMDb large IMDb lists:
```yaml
collections:
  Marvel Cinematic Universe:
    imdb_list: https://www.imdb.com/search/title/?title_type=movie&lists=ls031310794&count=250
```

#### Trakt List (List Type)

Similarly, this script can also pull public or private Trakt lists via the Trakt API:

```yaml
collections:
  Christmas:
    trakt_list:
      - https://trakt.tv/users/movistapp/lists/christmas-movies
      - https://trakt.tv/users/2borno2b/lists/christmas-movies-extravanganza
```
```yaml
collections:
  Reddit Top 250:
    trakt_list: https://trakt.tv/users/jay-greene/lists/reddit-top-250-2019-edition
```

#### System Name Attribute

With the `system_name` attribute you can specify the name you use for this collection in the local file system. Useful when collections have characters that can't be in filepaths i.e. "/"

```yaml
collections:
  28 Days/Weeks Later:
    tmdbID: 1565
    system_name: 28 Days-Weeks Later
```

### Details (Collection Attribute)

The next optional attribute for any collection is the `details` key. There are two different subattributes for `details` to choose from:
- Sort Title (optional)
- Content Rating (optional)
- Summary (optional)
- Poster (optional)
- Background (optional)
- Collection Mode (optional)
- Collection Order (optional)

Note that the `details` attribute needs to be set in order for the script to search the local image server for any images (this will be fixed in future releases).

#### Sort Title (Details Subattribute)

Setting the sort title is possible for each collection. This can be helpful to rearrange the collections in alphabetical sort. One example of this might be to "promote" certain collections to the top of a library by creating a sort title starting with an asterisk.

```yaml
collections:
  IMDb Top 250:
    imdb_list: https://www.imdb.com/search/title/?groups=top_250&count=250
    details:
      sort_title: *100
  Reddit Top 250:
    trakt_list: https://trakt.tv/users/jay-greene/lists/reddit-top-250-2019-edition
    details:
      sort_title: *101
```

#### Content Rating (Details Subattribute)

Adding a content rating to each collection is possible:

```yaml
collections:
  Pixar:
    studio: Pixar
    details:
      content_rating: PG
```

#### Summary (Details Subattribute)

Adding a summary to the collection is possible by either pulling the overview from TMDb or by using a custom entry.

To use a TMDb entry a TMDb api-key as well as language is required, the default language is set to `en`. Match the following in the configuration file, input only the TMDb collections page's ID. Use the actor's page ID on TMBd if you wish to use their biography as the summary (experimental).

```yaml
collections:
  Jurassic Park:
    tmdb_list: https://www.themoviedb.org/collection/328
    details:
      tmdb_summary: 328
```
```yaml
collections:
  Dave Chappelle:
    actors: Dave Chappelle
    details:
      tmdb_summary: 4169
```
If you want to use a custom summary:
```yaml
collections:
  Pixar:
    studio: Pixar
    details:
      summary: A collection of Pixar movies
```
```yaml
collections:
  Alien (Past & Present):
    tmdb_list:
      - https://www.themoviedb.org/collection/8091
      - https://www.themoviedb.org/collection/135416
    details:
      summary: >-
        The Alien franchise is a science fiction horror franchise, consisting
        primarily of a series of films focusing on the species Xenomorph XX121,
        commonly referred to simply as "the Alien", a voracious endoparasitoid
        extraterrestrial species. Unlike the Predator franchise, which mostly
        consists of stand-alone movies, the Alien films generally form continuing
        story arcs, the principal of which follows Lieutenant Ellen Ripley
        as she battles the Aliens in a future time setting. Newer films preceding
        Ripley's exploits center around the android David, exploring the possible
        origins of the Aliens and their connection to an ancient, advanced
        civilization known as the Engineers.
```

#### Poster (Details Subattribute)

There are four ways to set a poster image for a collection: local image, public URL, TMDb collection, or TMDb actor.

Local assets are supported by running the script with posters in the `poster_directory` or `image_directory`. See the Image Server section below for more details or to specify a specific place in your file system for a poster use `file_poster`.

If multiple posters are found the script will ask which one you want to use or just take the first one in the list if update mode is on.

If you want to use an image publicly available on the internet:
```yaml
collections:
  Jurassic Park:
    tmdb_list: https://www.themoviedb.org/collection/328
    details:
      tmdb_summary: 328
      poster: https://i.imgur.com/QMjbyCX.png
```
If you want to use the default collection image on TMDb:
```yaml
collections:
  Alien (Past & Present):
    tmdb_list:
      - https://www.themoviedb.org/collection/8091
      - https://www.themoviedb.org/collection/135416
    details:
      tmdb_poster: 8091
```
If you want to use the default actor image on TMDb:
```yaml
collections:
  Dave Chappelle:
    actors: Dave Chappelle
    details:
      tmdb_summary: 4169
      tmdb_poster: 4169
```
If you want to use an image in your file system:
```yaml
collections:
  Jurassic Park:
    tmdb_list: https://www.themoviedb.org/collection/328
    details:
      tmdb_summary: 328
      file_poster: C:/Users/username/Desktop/2xE0R9I.png
      file_background: /config/backgrounds/Jurassic Park.png
```
#### Background (Details Subattribute)

There are two ways to set a background image for a collection: local image or public URL.

Local assets are supported by running the script with backgrounds in the `background_directory` or `image_directory`. See the Image Server section below for more details or to specify a specific place in your file system for a background use `file_background`.

If multiple backgrounds are found the script will ask which one you want to use or just take the first one in the list if update mode is on.

If you want to use an image publicly available on the internet:
```yaml
collections:
  Jurassic Park:
    tmdb_list: https://www.themoviedb.org/collection/328
    details:
      tmdb_summary: 328
      poster: https://i.imgur.com/QMjbyCX.png
      background: https://i.imgur.com/2xE0R9I.png
```

If you want to use an image in your file system:
```yaml
collections:
  Jurassic Park:
    tmdb_list: https://www.themoviedb.org/collection/328
    details:
      tmdb_summary: 328
      file_poster: C:/Users/username/Desktop/2xE0R9I.png
      file_background: /config/backgrounds/Jurassic Park.png
```

#### Collection Mode (Details Subattribute)

Plex allows for four different types of collection modes: library default, hide items in this collection, show this collection and its items, and hide collection (more details can be found in [Plex's Collection support article](https://support.plex.tv/articles/201273953-collections/#toc-2)). These options can be set with `default`, `hide_items`, `show_items`, and `hide`.

##### Options
- `default` (Library default)
- `hide` (Hide Collection)
- `hide_items` (Hide Items in this Collection)
- `show_items` (Show this Collection and its Items)

```yaml
collections:
  Jurassic Park:
    tmdb_list: https://www.themoviedb.org/collection/328
    details:
      tmdb_summary: 328
      poster: https://i.imgur.com/QMjbyCX.png
      background: https://i.imgur.com/2xE0R9I.png
      collection_mode: hide_items
```

#### Collection Order (Details Subattribute)

Lastly, Plex allows collections to be sorted by the media's release dates or alphabetically by title. These options can be set with `release` or `alpha`. Plex defaults all collections to `release`, but `alpha` can be helpful for rearranging collections. For example, with collections where the chronology does not follow the release dates, you could create custom sort titles for each media item and then sort the collection alphabetically.

##### Options
- `release` (Order Collection by release dates)
- `alpha` (Order Collection Alphabetically)

```yaml
collections:
  Alien (Past & Present):
    tmdb_list:
      - https://www.themoviedb.org/collection/8091
      - https://www.themoviedb.org/collection/135416
    details:
      collection_order: alpha
```

### Subfilters (Collection Attribute)

The next optional attribute for any collection is the `subfilters` key. Subfilters allows for a little more granular selection from a list of movies to add to a collection.

Many `subfilters` are supported such as actors, genres, year, studio and more. For more subfilters refer to the [plexapi.video.Movie](https://python-plexapi.readthedocs.io/en/latest/modules/video.html#plexapi.video.Movie) documentation. Not everything has been tested, so results may vary based off the subfilter. Additionally, subfilters for `audio_language`, `subtitle_language`, and `video_resolution` have been created.

Note that muliple subfilters are supported but a movie must match at least one value from **each** subfilter to be added to a collection. The values for each must match what Plex has including special characters in order to match.

```yaml
collections:
  1080p Documentaries:
    genres: Documentary
    details:
      summary: A collection of 1080p Documentaries
    subfilters:
      video_resolution: 1080
```
```yaml
collections:
  Daniel Craig only James Bonds:
    imdb_list: https://www.imdb.com/list/ls006405458/
    subfilters:
      actors: Daniel Craig
```
```yaml
collections:
  French Romance:
    genre: Romance
    subfilters:
      audio_language: Français
```

## Plex

A `plex` mapping in the config is required. Here's the full set of configurations:

```yaml
plex:                                         # Req
  library: Movies                             # Req - Name of Plex library
  library_type: movie                         # Req - Type of Plex library (movie or show)
  token: #####                                # Req - User's Plex authentication token
  url: http://192.168.1.1:32400               # Req - URL to access Plex
```

**This script does not currently support Plex's [new metadata agent / matching](https://forums.plex.tv/t/introducing-the-new-plex-movie-agent/615989)**. Do not "update matching" until the script's dependencies support the new agent (feel free to follow issue #33).

Note that Plex does not allow a `show` to be added to a `movie` library or vice versa.

This script can be run on a remote Plex server, but be sure that the `url` provided is publicly addressable and it's recommended to use `HTTPS`.

Lastly, if you need help finding your Plex authentication token, please see Plex's [support article](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).

## Image Server

An `image_server` mapping in the config is optional. There are two ways to store your posters and background. Using `poster_directory` and/or `background_directory` or by using `image_directory`.

### `poster_directory` and/or `background_directory`
By placing images in the `poster_directory` or `background_directory`, the script will attempt to match image names to collection names. For example, if there is a collection named `Jurassic Park` and the images `../config/posters/Jurassic Park.png` and `../config/backgrounds/Jurassic Park.png`, the script will upload those images to Plex.

```yaml
image_server:                                 # Opt
  poster_directory: /config/posters           # Opt - Desired dir of posters
  background_directory: /config/backgrounds   # Opt - Desired dir of backgrounds
```

### `image_directory`
By placing images in folders in the `image_directory` folder, the script will attempt to match folder names to collection names. For example, if there is a collection named `Jurassic Park` and the images `../config/images/Jurassic Park/poster.png` and `../config/images/Jurassic Park/background.png`, the script will upload those images to Plex.

```yaml
image_server:                                 # Opt
  image_directory: /config/images             # Opt - Desired dir of images
```

Note: these can be used together if you want the script will just ask you which one you want if there are multiple matching images.

## TMDb

If using TMDb lists, be sure to include your TMDb API key. If you do not have an API key please refer to this [guide](https://developers.themoviedb.org/3/getting-started/introduction). Here's the full set of configurations:

```yaml
tmdb:                                         # Opt
  apikey: #####                               # Req - User's TMDb API key
  language: en                                # Opt - User's language
```

## Trakt

If using Trakt lists, be sure to include your Trakt application credentials. To create a Trakt application and get your `client id` and `client secret`, please do the following:
1. [Create](https://trakt.tv/oauth/applications/new) a Trakt API application.
2. Enter a `Name` for the application.
3. Enter `urn:ietf:wg:oauth:2.0:oob` for `Redirect uri`.
4. Click the `SAVE APP` button.
5. Record the `Client ID` and `Client Secret`.

Here's the full set of configurations:
```yaml
trakt:                                        # Opt
  client_id: #####                            # Req - Trakt application client ID
  client_secret: #####                        # Req - Trakt application client secret
  authorization:                              # Req
    access_token:                             # LEAVE BLANK
    token_type:                               # LEAVE BLANK
    expires_in:                               # LEAVE BLANK
    refresh_token:                            # LEAVE BLANK
    scope:                                    # LEAVE BLANK
    created_at:                               # LEAVE BLANK
```

On the first run, the script will walk the user through the OAuth flow by producing a Trakt URL for the user to follow. Once authenticated at the Trakt URL, the user needs to return the code to the script. If the code is correct, the script will populate the `authorization` subattributes to use in subsequent runs.

## Radarr

When parsing TMBd, IMDb, or Trakt lists, the script will finds movies that are on the list but missing from Plex. If a TMDb and Radarr config are supplied, then you can add those missing movies to Radarr.

Here's the full set of configurations:
```yaml
radarr:                                       # Opt
  url: http://192.168.1.1:7878                # Req - URL to access Radarr
  version: v2                                 # Opt - 'v2' for <0.2, 'v3' for >3.0
  token: #####                                # Req - User's Radarr API key
  quality_profile_id: 4                       # Req - See below
  root_folder_path: /mnt/movies               # Req - See below
  add_movie: false                            # Opt - Add missing movies to Radarr
  search_movie: false                         # Opt - Search while adding missing movies
```

The `token` can be found by going to `Radarr > Settings > General > Security > API Key`

The `quality_profile_id` is the number of the desired profile. It can be found by going to `Radarr > Settings > Profiles`. Unfortunately, there's not an explicit place to find the `id`, but you can infer it from the `Profiles` page. Each profile is numbered, starting at `1` and incrementing by one, left-to-right, top-to-bottom. For example, the default Radarr installation comes with four profiles:
```
     1          2          3          4
    Any         SD      HD-720p    HD-1080p
```

If you were to add two more profiles, the `id` would be as follows:
```
     1          2          3          4
    Any         SD      HD-720p    HD-1080p

     5          6
 Ultra-HD HD-720p/1080p
```

In this example, to set any added movies to the `Ultra-HD` profile, set `quality_profile_id` to `5`. To set any added movies to `HD-1080p`, set `quality_profile_id` to `4`.

The `add_movie` key allows missing to movies to be added to Radarr. If this key is missing, the script will prompt the user to add missing movies or not. If you'd like to add movies but not had Radarr search, then set `search_movie` to `false`.

Note that Radarr support has not been tested with extensively Trakt lists and Sonarr support has not yet been implemented.

# Acknowledgements
- [vladimir-tutin](https://github.com/vladimir-tutin) for writing substantially all of the code in this fork
- [deva5610](https://github.com/deva5610) for writing [IMDBList2PlexCollection](https://github.com/deva5610/IMDBList2PlexCollection) which prompted the idea for a
configuration based collection manager
- [JonnyWong16](https://github.com/JonnyWong16) for writing the a [IMDb Top 250](https://gist.github.com/JonnyWong16/f5b9af386ea58e19bf18c09f2681df23) collection script which served as inspiration (and for [Tautulli](https://github.com/Tautulli/Tautulli)!)
- [pkkid](https://github.com/pkkid) and all other contributors for [python-plexapi](https://github.com/pkkid/python-plexapi)
- [AnthonyBloomer](https://github.com/AnthonyBloomer) and all other contributors for [tmdbv3api](https://github.com/AnthonyBloomer/tmdbv3api)
- [fuzeman](https://github.com/fuzeman) and all other contributors for [trakt.py](https://github.com/fuzeman/trakt.py) (and for [Plex-Trakt-Scrobbler](https://github.com/trakt/Plex-Trakt-Scrobbler)!)

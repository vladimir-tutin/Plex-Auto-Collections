# Plex Auto Collections
##### Version 2.8.1
Plex Auto Collections is a Python 3 script that works off a configuration file to create/update Plex collections. Collection management with this tool can be automated in a varying degree of customizability. Supports IMDB, TMDb, and Trakt lists as well as built in Plex Searches using actors, genres, year, studio and more.

![https://i.imgur.com/iHAYFIZ.png](https://i.imgur.com/iHAYFIZ.png)

# Table of Contents
1. [Usage](#usage)
    - [Local Installation](#local-installation)
    - [Docker](#docker)
2. [Configuration](#configuration)
    - [Collections](#collections)
      - [List Type](#list-type-collection-attribute)
        - [Plex Search (List Type)](#plex-search-list-type)
        - [Plex Collection (List Type)](#plex-collection-list-type)
        - [TMDb Collection (List Type)](#tmdb-collection-list-type)
        - [TMDb People (List Type)](#tmdb-people-list-type)
        - [TMDb Company (List Type)](#tmdb-company-list-type)
        - [TMDb Network (List Type)](#tmdb-network-list-type)
        - [TMDb Popular (List Type)](#tmdb-popular-list-type)
        - [TMDb Trending (List Type)](#tmdb-trending-list-type)
        - [TMDb Top Rated (List Type)](#tmdb-top-rated-list-type)
        - [TMDb Now Playing (List Type)](#tmdb-now-playing-list-type)
        - [TMDb Discover (List Type)](#tmdb-discover-list-type)
        - [TMDb List (List Type)](#tmdb-list-list-type)
        - [TMDb Movie (List Type)](#tmdb-movie-list-type)
        - [TMDb Show (List Type)](#tmdb-show-list-type)
        - [TVDb Show (List Type)](#tvdb-show-list-type)
        - [IMDb List or Search (List Type)](#imdb-list-or-search-list-type)
        - [Trakt List (List Type)](#trakt-list-list-type)
        - [Trakt Trending List (List Type)](#trakt-trending-list-list-type)
        - [Trakt Watchlist (List Type)](#trakt-watchlist-list-type)
        - [Tautulli List (List Type)](#tautulli-list-list-type)
      - [Collection Filters (Collection Attribute)](#collection-filters-collection-attribute)
      - [Sync Mode (Collection Attribute)](#sync-mode-collection-attribute)
      - [Sort Title (Collection Attribute)](#sort-title-collection-attribute)
      - [Content Rating (Collection Attribute)](#content-rating-collection-attribute)
      - [Summary (Collection Attribute)](#summary-collection-attribute)
      - [Collection Mode (Collection Attribute)](#collection-mode-collection-attribute)
      - [Collection Order (Collection Attribute)](#collection-order-collection-attribute)
      - [Poster (Collection Attribute)](#poster-collection-attribute)
      - [Background (Collection Attribute)](#background-collection-attribute)
      - [Name Mapping (Collection Attribute)](#name-mapping-collection-attribute)
    - [Plex](#plex)
    - [Image Server](#image-server)
      - [Poster and/or Background Directory](#poster-andor-background-directory)
      - [Image Directory](#image-directory)
    - [TMDb](#tmdb)
    - [Tautulli](#tautulli)
    - [Trakt](#trakt)
    - [Radarr](#radarr)
3. [Acknowledgements](#acknowledgements)

# Usage

This script can be used as an interactive Python shell script as well as a headless, configuration-driven script.

The interactive shell script has some limited abilities including the ability to add new collections based off searches, delete collections, search for collections and manage existing collections. The bulk of the feature-set is focused on configuration-driven updates.

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

If you would like the `-u` or `--update` option to update without updating metadata you can add `-nm` or `--no_meta` along with `-u` or `--update`:

```shell
python plex_auto_collections.py --update --no_meta
```

If you would like the `-u` or `--update` option to update without updating images you can add `-ni` or `--no_images` along with `-u` or `--update`:

```shell
python plex_auto_collections.py --update --no_images
```

Example command if you only want the collection to update without constantly updating metadata and images that don't change much

```shell
python plex_auto_collections.py --update --no_meta --no_images
```

## Docker

A simple `Dockerfile` is available in this repo if you'd like to build it yourself. The official build is also available from dockerhub here: https://hub.docker.com/r/mza921/plex-auto-collections

The docker implementation today is limited but will improve over time. To use, try the following:

```shell
docker run --rm -v '/mnt/user/plex-auto-collections/':'/config':'rw' 'mza921/plex-auto-collections' -u
```

The `-v '/mnt/user/plex-auto-collections/':'/config'` mounts a persistent volume to store your config file. Today, the docker image defaults to running the config named `config.yml` in your persistent volume (eventually, the docker will support an environment variable to change the config path).

Lastly, you may need to run the docker with `-it` and without `-u` in order to interact with the script. For example, if you'd like to use Trakt lists, you need to go through the OAuth flow and interact with the script at first-run. After that, you should be able to run it without the `-it` flag.

# Configuration

The script allows utilizes a YAML config file to create collections in Plex. This is great for a few reasons:
- Setting metadata manually in Plex is cumbersome. Having a config file allows template to be reused, backed-up, transferred, etc.
- Plex often loses manually set metadata. Having a config file fixes metadata creep.
- Collections change often. Having a config file pointing to dynamic data keeps collections fresh.

There are currently six YAML mappings that can be set:
- [`collections` (required)](#collections)
- [`plex` (required)](#plex)
- [`image_server` (optional)](#image-server)
- [`tmdb` (optional, but recommended)](#tmdb)
- [`tautulli` (optional)](#tautulli)
- [`trakt` (optional)](#trakt)
- [`radarr` (optional)](#radarr)

You can find a template config file in [config/config.yml.template](config/config.yml.template)

## Collections

Each collection is defined by the mapping name which becomes the name of the Plex collection. Additionally, there are many different attributes you can set for each collection:
- [List Type (required)](#list-type-collection-attribute)
- [Collection Filters (optional)](#collection-filters-collection-attribute)
- [Sync Mode (optional)](#sync-mode-collection-attribute)
- [Sort Title (optional)](#sort-title-collection-attribute)
- [Content Rating (optional)](#content-rating-collection-attribute)
- [Summary (optional)](#summary-collection-attribute)
- [Collection Mode (optional)](#collection-mode-collection-attribute)
- [Collection Order (optional)](#collection-order-collection-attribute)
- [Poster (optional)](#poster-collection-attribute)
- [Background (optional)](#background-collection-attribute)
- [Name Mapping (optional)](#name-mapping-collection-attribute)

### List Type (Collection Attribute)

The only required attribute for each collection is the list type. There are many different list types to choose from:
- [Plex Search](#plex-search-list-type)
- [Plex Collection](#plex-collection-list-type)
- [TMDb Collection](#tmdb-collection-list-type)
- [TMDb People](#tmdb-people-list-type)
- [TMDb Company](#tmdb-company-list-type)
- [TMDb Network](#tmdb-network-list-type)
- [TMDb Popular](#tmdb-popular-list-type)
- [TMDb Trending](#tmdb-trending-list-type)
- [TMDb Top Rated](#tmdb-top-rated-list-type)
- [TMDb Now Playing](#tmdb-now-playing-list-type)
- [TMDb Discover](#tmdb-discover-list-type)
- [TMDb List](#tmdb-list-list-type)
- [TMDb Movie](#tmdb-movie-list-type)
- [TMDb Show](#tmdb-show-list-type)
- [TVDb Show](#tvdb-show-list-type)
- [IMDb List or Search](#imdb-list-or-search-list-type)
- [Trakt List](#trakt-list-list-type)
- [Trakt Trending List](#trakt-trending-list-list-type)
- [Trakt Watchlist](#trakt-watchlist-list-type)
- [Tautulli List](#tautulli-list-list-type)

Note that most list types supports multiple lists, with the following exceptions:
- TMDb Popular
- TMDb Trending
- TMDb Top Rated
- TMDb Now Playing
- TMDb Discover
- Trakt Trending Lists
- Trakt Watchlist
- Tautulli Lists

#### Plex Search (List Type)

###### Works with Movie and TV Show Libraries

You can create a collection based on the Plex search feature using the `plex_search` attribute. The search will return any movie/show that matches at least one term from each search option. You can run multiple searches. The search options are listed below.

| Search Option | Description | Movie<br>Libraries | Show<br>Libraries |
| :-- | :-- | :--: | :--: |
| `actor` | Gets every movie with the specified actor | :heavy_check_mark: | :x: |
| `tmdb_actor` | Gets every movie with the specified actor as well as the added TMDb [metadata](#tmdb-people-list-type) | :heavy_check_mark: | :x: |
| `country` | Gets every movie with the specified country | :heavy_check_mark: | :x: |
| `decade` | Gets every movie from the specified year + the 9 that follow i.e. 1990 will get you 1990-1999 | :heavy_check_mark: | :x: |
| `director` | Gets every movie with the specified director | :heavy_check_mark: | :x: |
| `tmdb_director` | Gets every movie with the specified director as well as the added TMDb [metadata](#tmdb-people-list-type) | :heavy_check_mark: | :x: |
| `genre` | Gets every movie/show with the specified genre | :heavy_check_mark: | :heavy_check_mark: |
| `studio` | Gets every movie/show with the specified studio | :heavy_check_mark: | :heavy_check_mark: |
| `year` | Gets every movie/show with the specified year (Put a `-` between two years for a range i.e. `year: 1990-1999` or end with `NOW` to go till current i.e. `year: 2000-NOW`) | :heavy_check_mark: | :heavy_check_mark: |
| `writer` | Gets every movie with the specified writer | :heavy_check_mark: | :x: |
| `tmdb_writer` | Gets every movie with the specified writer as well as the added TMDb [metadata](#tmdb-people-list-type) | :heavy_check_mark: | :x: |

Here's some high-level ideas:

```yaml
collections:
  Documentaries:
    plex_search:
      genre: Documentary
```
```yaml
collections:
  Dave Chappelle Comedy:
    plex_search:
      actor: Dave Chappelle
      genre: Comedy
```
```yaml
collections:
  Pixar:
    plex_search:
      studio: Pixar
```
```yaml
collections:
  90s Movies:
    plex_search:
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
```yaml
collections:
  90s Movies:
    plex_search:
      year: 1990-1999
```
```yaml
collections:
  2010+ Movies:
    plex_search:
      year: 2010-NOW
```
```yaml
collections:
  90s Movies:
    plex_search:
      decade: 1990
```

Note if you only want to search using a single attribute you can do so without `plex_search`.

```yaml
collections:
  90s Movies:
    year: 1990-1999
```

Notes:
- You can only use each search option once per `plex_search` but you can give the search multiple values.
- If you want to restrict the search by multiples of the same attribute (i.e. You want every movie that is a Romance and Comedy) try using [filters](#collection-filters-collection-attribute).

#### Plex Collection (List Type)

###### Works with Movie and TV Show Libraries

You can create Collections based on collections already in Plex

```yaml
collections:
  Dinosaurs:
    plex_collection: Jurassic Park
```

 Note if you want to add multiple collections you have to use a list. Comma separated values will not work.

 ```yaml
 collections:
   Dinosaurs:
     plex_collection:
       - Jurassic Park
       - The Land Before Time
 ```

#### TMDb Collection (List Type)

###### Works with Movie Libraries

The Movie Database (TMDb) strives to group movies into logical collections. This script can easily leverage that data. You can use the full url or just type in the TMDb ID for the collection:

```yaml
collections:
  Jurassic Park:
    tmdb_collection: https://www.themoviedb.org/collection/328
```
```yaml
collections:
  Jurassic Park:
    tmdb_collection: 328
```
```yaml
collections:
  Alien (Past & Present):
    tmdb_collection:
      - https://www.themoviedb.org/collection/8091
      - 135416
```

Alternatively you can specify which [`tmdb_collection`](#tmdb-collection-list-type), [`tmdb_summary`](#summary-collection-attribute), [`tmdb_poster`](#poster-collection-attribute), and [`tmdb_background`](#background-collection-attribute) all at once by using `tmdb_id` and setting it to the collections page ID or URL:

```yaml
collections:
  Jurassic Park:
    tmdb_id: 328
```
```yaml
collections:
  Alien (Past & Present):
    tmdb_id: 8091, 135416
  Anaconda:
    tmdb_id: 105995, 336560
```

Notes:
- The `tmdb_id` can be either from a collection or an individual movie
- You can specify more than one `tmdb_id` but it will pull the summary, poster, and background from only the first one.
- Local posters/backgrounds are loaded over `tmdb_poster`/`tmdb_background` if they exist unless `tmdb_poster`/`tmdb_background` is also specified
- `tmdb_summary` will load unless `summary`,`tmdb_summary`, or `tmdb_biography` is also specified


#### TMDb People (List Type)

Similarly to `tmdb_id`, `tmdb_actor`, `tmdb_director`, `tmdb_writer` can specify [`tmdb_biography`](#summary-collection-attribute) and [`tmdb_profile`](#poster-collection-attribute) of the person's TMDb page ID or URL as well as search Plex using their respective [Plex Search](#plex-search-list-type) all with one attribute.

##### TMDb Actor (List Type)

###### Works with Movie and TV Show Libraries

```yaml
collections:
  Robin Williams:
    tmdb_actor: 2157
```

```yaml
collections:
  Robin Williams:
    tmdb_actor: https://www.themoviedb.org/person/2157-robin-williams
```

##### TMDb Director (List Type)

###### Works with Movie Libraries

```yaml
collections:
  Steven Spielberg:
    tmdb_director: 488
```

```yaml
collections:
  Steven Spielberg:
    tmdb_director: https://www.themoviedb.org/person/488-steven-spielberg
```

##### TMDb Writer (List Type)

###### Works with Movie Libraries

```yaml
collections:
  Quentin Tarantino:
    tmdb_writer: 138
```

```yaml
collections:
  Quentin Tarantino:
    tmdb_writer: https://www.themoviedb.org/person/138-quentin-tarantino
```

Notes:
- You can specify more than one `tmdb_actor`, `tmdb_director`, or `tmdb_writer` but it will pull the summary and poster from only the first one.
- Local posters are loaded over `tmdb_profile` if they exist unless `tmdb_profile` is also specified
- `tmdb_biography` will load unless `summary`,`tmdb_summary`, or `tmdb_biography` is also specified

#### TMDb Company (List Type)

###### Works with Movie and TV Show Libraries

You can use a TMDb Company to build a collection based on all it's movies/shows by using `tmdb_company`. You can use the full url or just type in the TMDb ID for the collection:

```yaml
collections:
  Studio Ghibli:
    tmdb_company: 10342
```

```yaml
collections:
  Studio Ghibli:
    tmdb_company: https://www.themoviedb.org/company/10342
```

#### TMDb Network (List Type)

###### Works with Show Libraries

Similarly to using a TMDb Company, you can also use a TMDb Network to build a collection based on all it's shows by using `tmdb_network`. You can use the full url or just type in the TMDb ID for the collection:

```yaml
collections:
  CBS:
    tmdb_network: 16
```

```yaml
collections:
  CBS:
    tmdb_network: https://www.themoviedb.org/network/16
```

#### TMDb Popular (List Type)

###### Works with Movie and TV Show Libraries

You can build a collection using TMDb's most popular movies/shows by using `tmdb_popular`. The `tmdb_popular` attribute only supports a single integer value. The `sync_mode: sync` option is recommended since the list is continuously updated.

```yaml
collections:
  TMDb Popular:
    tmdb_popular: 30
    sync_mode: sync
```

#### TMDb Trending (List Type)

###### Works with Movie and TV Show Libraries

You can build a collection using TMDb's daily or weekly trending movies/shows by using `tmdb_trending_daily` or `tmdb_trending_weekly`. Both attributes only support a single integer value. The `sync_mode: sync` option is recommended since the lists are continuously updated.

```yaml
collections:
  TMDb Daily Trending:
    tmdb_trending_daily: 30
    sync_mode: sync
```
```yaml
collections:
  TMDb Weekly Trending:
    tmdb_trending_weekly: 30
    sync_mode: sync
```

#### TMDb Top Rated (List Type)

###### Works with Movie and TV Show Libraries

You can build a collection using TMDb's top rated movies/shows by using `tmdb_top_rated`. The `tmdb_top_rated` attribute only supports a single integer value. The `sync_mode: sync` option is recommended since the list is continuously updated.

```yaml
collections:
  TMDb Top Rated:
    tmdb_top_rated: 30
    sync_mode: sync
```

#### TMDb Now Playing (List Type)

###### Works with Movie Libraries

You can build a collection using TMDb's release_type to get movies that are now in theaters by using `tmdb_now_playing`. The `tmdb_now_playing` attribute only supports a single integer value. The `sync_mode: sync` option is recommended since the list is continuously updated.

```yaml
collections:
  TMDb Now Playing:
    tmdb_now_playing: 30
    sync_mode: sync
```

#### TMDb Discover (List Type)

###### Works with Movie and TV Show Libraries

You can use [TMDb's discover engine](https://www.themoviedb.org/documentation/api/discover) to create a collection based on the search for movies/shows using all different sorts of parameters shown below. The parameters are directly from [TMDb Movie Discover](https://developers.themoviedb.org/3/discover/movie-discover) and [TMDb TV Discover](https://developers.themoviedb.org/3/discover/tv-discover)

| Type | Description |
| :-- | :-- |
| String | Any number of alphanumeric characters |
| Integer | Any whole number greater then zero i.e. 2, 10, 50 |
| Number | Any number greater then zero i.e. 2.5, 7.4, 9 |
| Boolean | Must be `true` or `false` |
| Date: `MM/DD/YYYY` | Date that fits the specified format |
| Year: `YYYY` | Year must be a 4 digit integer i.e. 1990 |

### Discover Movies
| Movie Parameters | Description | Type |
| :-- | :-- | :--: |
| `limit` | Specify how many movies you want returned by the query. (default: 100) | Integer |
| `language` | Specify a language to query translatable fields with. (default: en-US) | `([a-z]{2})-([A-Z]{2})` |
| `region` | Specify a [ISO 3166-1 code](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes) to filter release dates. Must be uppercase. | `^[A-Z]{2}$` |
| `sort_by` | Choose from one of the many available sort options. (default: `popularity.desc`) | See [sort options](#sort-options) below |
| `certification_country` | Used in conjunction with the certification parameter, use this to specify a country with a valid certification. | String |
| `certification` | Filter results with a valid certification from the `certification_country` parameter. | String |
| `certification.lte` | Filter and only include movies that have a certification that is less than or equal to the specified value. | String |
| `certification.gte` | Filter and only include movies that have a certification that is greater than or equal to the specified value. | String |
| `include_adult` | A filter and include or exclude adult movies. | Boolean |
| `primary_release_year` | A filter to limit the results to a specific primary release year. | Year: YYYY |
| `primary_release_date.gte` | Filter and only include movies that have a primary release date that is greater or equal to the specified value. | Date: `MM/DD/YYYY` |
| `primary_release_date.lte` | Filter and only include movies that have a primary release date that is less than or equal to the specified value. | Date: `MM/DD/YYYY` |
| `release_date.gte` | Filter and only include movies that have a release date (looking at all release dates) that is greater or equal to the specified value. | Date: `MM/DD/YYYY` |
| `release_date.lte` | Filter and only include movies that have a release date (looking at all release dates) that is less than or equal to the specified value. | Date: `MM/DD/YYYY` |
| `year` | A filter to limit the results to a specific year (looking at all release dates). | Year: YYYY |
| `vote_count.gte` | Filter and only include movies that have a vote count that is greater or equal to the specified value. | Integer |
| `vote_count.lte` | Filter and only include movies that have a vote count that is less than or equal to the specified value. | Integer |
| `vote_average.gte` | Filter and only include movies that have a rating that is greater or equal to the specified value. | Number |
| `vote_average.lte` | Filter and only include movies that have a rating that is less than or equal to the specified value. | Number |
| `with_cast` | A comma separated list of person ID's. Only include movies that have one of the ID's added as an actor. | String |
| `with_crew` | A comma separated list of person ID's. Only include movies that have one of the ID's added as a crew member. | String |
| `with_people` | A comma separated list of person ID's. Only include movies that have one of the ID's added as a either a actor or a crew member. | String |
| `with_companies` | A comma separated list of production company ID's. Only include movies that have one of the ID's added as a production company. | String |
| `with_genres` | Comma separated value of genre ids that you want to include in the results. | String |
| `without_genres` | Comma separated value of genre ids that you want to exclude from the results. | String |
| `with_keywords` | A comma separated list of keyword ID's. Only includes movies that have one of the ID's added as a keyword. | String |
| `without_keywords` | Exclude items with certain keywords. You can comma and pipe separate these values to create an 'AND' or 'OR' logic. | String |
| `with_runtime.gte` | Filter and only include movies that have a runtime that is greater or equal to a value. | Integer |
| `with_runtime.lte` | Filter and only include movies that have a runtime that is less than or equal to a value. | Integer |
| `with_original_language` | Specify an ISO 639-1 string to filter results by their original language value. | String |

### Discover Shows
| Show Parameters | Description | Type |
| :-- | :-- | :--: |
| `limit` | Specify how many movies you want returned by the query. (default: 100) | Integer |
| `language` | Specify a language to query translatable fields with. (default: en-US) | `([a-z]{2})-([A-Z]{2})` |
| `sort_by` | Choose from one of the many available sort options. (default: `popularity.desc`) | See [sort options](#sort-options) below |
| `air_date.gte` | Filter and only include TV shows that have a air date (by looking at all episodes) that is greater or equal to the specified value. | Date: `MM/DD/YYYY` |
| `air_date.lte` | Filter and only include TV shows that have a air date (by looking at all episodes) that is less than or equal to the specified value. | Date: `MM/DD/YYYY` |
| `first_air_date.gte` | Filter and only include TV shows that have a original air date that is greater or equal to the specified value. Can be used in conjunction with the `include_null_first_air_dates` filter if you want to include items with no air date. | Date: `MM/DD/YYYY` |
| `first_air_date.lte` | Filter and only include TV shows that have a original air date that is less than or equal to the specified value. Can be used in conjunction with the `include_null_first_air_dates` filter if you want to include items with no air date. | Date: `MM/DD/YYYY` |
| `first_air_date_year` | Filter and only include TV shows that have a original air date year that equal to the specified value. Can be used in conjunction with the `include_null_first_air_dates` filter if you want to include items with no air date. | Year: YYYY |
| `include_null_first_air_dates` | Use this filter to include TV shows that don't have an air date while using any of the `first_air_date` filters. | Boolean |
| `timezone` | Used in conjunction with the `air_date.gte/lte` filter to calculate the proper UTC offset. (default: America/New_York) | String |
| `vote_count.gte` | Filter and only include TV that have a vote count that is greater or equal to the specified value. | Integer |
| `vote_count.lte` | Filter and only include TV that have a vote count that is less than or equal to the specified value. | Integer |
| `vote_average.gte` | Filter and only include TV that have a rating that is greater or equal to the specified value. | Number |
| `vote_average.lte` | Filter and only include TV that have a rating that is less than or equal to the specified value. | Number |
| `with_networks` | Comma separated value of network ids that you want to include in the results. | String |
| `with_companies` | A comma separated list of production company ID's. Only include movies that have one of the ID's added as a production company. | String |
| `with_genres` | Comma separated value of genre ids that you want to include in the results. | String |
| `without_genres` | Comma separated value of genre ids that you want to exclude from the results. | String |
| `with_keywords` | A comma separated list of keyword ID's. Only includes TV shows that have one of the ID's added as a keyword. | String |
| `without_keywords` | Exclude items with certain keywords. You can comma and pipe separate these values to create an 'AND' or 'OR' logic. | String |
| `with_runtime.gte` | Filter and only include TV shows with an episode runtime that is greater than or equal to a value. | Integer |
| `with_runtime.lte` | Filter and only include TV shows with an episode runtime that is less than or equal to a value. | Integer |
| `with_original_language` | Specify an ISO 639-1 string to filter results by their original language value. | String |
| `screened_theatrically` | Filter results to include items that have been screened theatrically. | Boolean |

### Sort Options
| Sort Option | Movie Sort | Show Sort |
| :-- | :--: | :--: |
| `popularity.asc` | :heavy_check_mark: | :heavy_check_mark: |
| `popularity.desc` | :heavy_check_mark: | :heavy_check_mark: |
| `original_title.asc` | :heavy_check_mark: | :x: |
| `original_title.desc` | :heavy_check_mark: | :x: |
| `revenue.asc` | :heavy_check_mark: | :x: |
| `revenue.desc` | :heavy_check_mark: | :x: |
| `release_date.asc` | :heavy_check_mark: | :x: |
| `release_date.desc` | :heavy_check_mark: | :x: |
| `primary_release_date.asc` | :heavy_check_mark: | :x: |
| `primary_release_date.desc` | :heavy_check_mark: | :x: |
| `first_air_date.asc` | :x: | :heavy_check_mark: |
| `first_air_date.desc` | :x: | :heavy_check_mark: |
| `vote_average.asc` | :heavy_check_mark: | :heavy_check_mark: |
| `vote_average.desc` | :heavy_check_mark: | :heavy_check_mark: |
| `vote_count.asc` | :heavy_check_mark: | :x: |
| `vote_count.desc` | :heavy_check_mark: | :x: |

```yaml
collections:
  Movies Released in October 2020:
    tmdb_discover:
      primary_release_date.gte: 10/01/2020
      primary_release_date.lte: 10/31/2020
```
```yaml
collections:
  Popular Movies:
    tmdb_discover:
      sort_by: popularity.desc
```
```yaml
collections:
  Highest Rated R Movies:
    tmdb_discover:
      certification_country: US
      certification: R
      sort_by: vote_average.desc
```
```yaml
collections:
  Most Popular Kids Movies:
    tmdb_discover:
      certification_country: US
      certification.lte: G
      sort_by: popularity.desc
```
```yaml
collections:
  Highest Rated Movies From 2010:
    tmdb_discover:
      primary_release_year: 2010
      sort_by: vote_average.desc
```
```yaml
collections:
  Best Dramas From 2014:
    tmdb_discover:
      with_genres: 18
      primary_release_year: 2014
      sort_by: vote_average.desc
```
```yaml
collections:
  Highest Rated Science Fiction Movies with Tom Cruise:
    tmdb_discover:
      with_genres: 878
      with_cast: 500
      sort_by: vote_average.desc
```
```yaml
collections:
  Highest Grossing Comedy Movies with Will Ferrell:
    tmdb_discover:
      with_genres: 35
      with_cast: 23659
      sort_by: revenue.desc
```
```yaml
collections:
  Top Rated Movies with Brad Pitt and Edward Norton:
    tmdb_discover:
      with_people: 287,819
      sort_by: vote_average.desc
```
```yaml
collections:
  Popular Movies with David Fincher and Rooney Mara:
    tmdb_discover:
      with_people: 108916,7467
      sort_by: popularity.desc
```
```yaml
collections:
  Top Rated Dramas:
    tmdb_discover:
      with_genres: 18
      sort_by: vote_average.desc
      vote_count.gte: 10
```
```yaml
collections:
  Highest Grossing R Movies with Liam Neeson:
    tmdb_discover:
      certification_country: US
      certification: R
      sort_by: revenue.desc
      with_cast: 3896
```

#### TMDb List (List Type)

###### Works with Movie and TV Show Libraries

In addition to TMDb collections you can also build collections based off of TMDb Lists using `tmdb_list`.

```yaml
collections:
  Top 50 Grossing Films of All Time (Worldwide):
    tmdb_list: https://www.themoviedb.org/list/10
```
```yaml
collections:
  Top 50 Grossing Films of All Time (Worldwide):
    tmdb_list: 10
```

#### TMDb Movie (List Type)

###### Works with Movie Libraries

You can also add individual movies to a collection using `tmdb_movie`.

```yaml
collections:
  Anaconda:
    tmdb_collection: https://www.themoviedb.org/collection/105995
    tmdb_movie: https://www.themoviedb.org/movie/336560
```
```yaml
collections:
  Anaconda:
    tmdb_collection: 105995
    tmdb_movie: 336560
```

#### TMDb Show (List Type)

###### Works with TV Show Libraries

You can also add individual shows to a collection using `tmdb_show`.

```yaml
collections:
  Star Wars (Animated Shows):
    tmdb_show:
      - https://www.themoviedb.org/tv/4194-star-wars-the-clone-wars
      - https://www.themoviedb.org/tv/60554-star-wars-rebels
```
```yaml
collections:
  Star Wars (Animated Shows):
    tmdb_show:
      - 4194
      - 60554
```

#### TVDb Show (List Type)

###### Works with TV Show Libraries

You can also add individual shows to a collection using `tvdb_show` and the show's TVDb ID.

```yaml
collections:
  Star Wars (Animated Shows):
    tvdb_show:
      - 83268
      - 283468
```

#### IMDb List or Search (List Type)

###### Works with Movie Libraries

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

###### Works with Movie and TV Show Libraries

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

#### Trakt Trending List (List Type)

###### Works with Movie and TV Show Libraries

This script can pull a number of items from the Trakt Trending List for [Movies](https://trakt.tv/movies/trending) or [Shows](https://trakt.tv/shows/trending). The `trakt_trending` attribute only supports a single integer value. The `sync_mode: sync` option is recommended since the list is continuously updated.

```yaml
collections:
  Trakt Trending:
    trakt_trending: 30
    sync_mode: sync
```
#### Trakt Watchlist (List Type)

###### Works with Movie and TV Show Libraries

This script can pull items from a Trakt user's Watchlist for [Movies](https://trakt.tv/users/me/watchlist) or [Shows](https://trakt.tv/users/me/watchlist). Set the `trakt_watchlist` attribute to `me` to pull your own Watchlist. To pull other users' Watchlists, add their Trakt username to the attribute. The `sync_mode: sync` option is recommended.

```yaml
collections:
  Trakt Watchlist:
    trakt_watchlist:
      - me
      - friendontrakt
    sync_mode: sync
```

#### Tautulli List (List Type)

###### Works with Movie and TV Show Libraries

Tautulli has watch analytics that can show the most watched or most popular Movies/Shows in your Library. This script can easily leverage that data into making and sync collection based on those lists using the `tautulli` attribute. Unlike other lists this one has subattribute options:

| Attribute | Description | Required | Default |
| :-- | :-- | :--: | :--: |
| `list_type` | `watched` (For Most Watched Lists)<br>`popular` (For Most Popular Lists) | :heavy_check_mark: | :x: |
| `list_days` | Number of Days to look back of the list | :x: | 30 |
| `list_size` | Number of Movies/Shows to add to this list | :x: | 10 |
| `list_buffer` | Number of extra Movies/Shows to grab in case you have multiple show/movie Libraries. | :x: | 10 |

```yaml
collections:
  Most Popular Movies (30 Days):
    sync_mode: sync
    collection_mode: show_items
    tautulli:
      list_type: popular
      list_days: 30
      list_size: 10
```
```yaml
collections:
  Most Watched Movies (30 Days):
    sync_mode: sync
    collection_mode: show_items
    tautulli:
      list_type: watched
      list_days: 30
      list_size: 10
      list_buffer: 10
```

Note that if you have multiple movie Libraries or multiple show Libraries Tautulli combines those in the popular/watched lists so there might not be 10 movies/shows from the library to make your `list_size`. In order to get around that we added a `list_buffer` attribute that defaults to 10. This will get that many more movies from Tautulli but only add to the collection until the number in `list_size`. So if your collection doesn't have as many movies/shows as your `list_size` attribute increase the number in the `list_buffer` attribute.


### Collection Filters (Collection Attribute)

###### Works with Movie and TV Show Libraries

The next optional attribute for any collection is the `filters` attribute. Collection filters allows for you to filter every movie/show added to the collection from every List Type. All collection filter options are listed below.
In addition you can also use the `.not` at the end of any standard collection filter to do an inverse search matching everything that doesn't have the value specified. You can use `all: true` to start your filter from your entire library.

| Standard Filters | Description | Movie<br>Libraries | Show<br>Libraries |
| :-- | :-- | :--: | :--: |
| `actor` | Matches every movie/show with the specified actor | :heavy_check_mark: | :heavy_check_mark: |
| `content_rating` | Matches every movie/show with the specified content rating | :heavy_check_mark: | :heavy_check_mark: |
| `country` | Matches every movie with the specified country | :heavy_check_mark: | :x: |
| `director` | Matches every movie with the specified director | :heavy_check_mark: | :x: |
| `genre` | Matches every movie/show with the specified genre | :heavy_check_mark: | :heavy_check_mark: |
| `studio` | Matches every movie/show with the specified studio | :heavy_check_mark: | :heavy_check_mark: |
| `year` | Matches every movie/show with the specified year | :heavy_check_mark: | :heavy_check_mark: |
| `writer` | Matches every movie with the specified writer | :heavy_check_mark: | :x: |
| `video_resolution` | Matches every movie with the specified video resolution | :heavy_check_mark: | :x: |
| `audio_language` | Matches every movie with the specified audio language | :heavy_check_mark: | :x: |
| `subtitle_language` | Matches every movie with the specified subtitle language | :heavy_check_mark: | :x: |
| `plex_collection` | Matches every movie/show with the specified plex collection | :heavy_check_mark: | :heavy_check_mark: |

| Advanced Filters | Description | Movie<br>Libraries | Show<br>Libraries |
| :-- | :-- | :--: | :--: |
| `max_age` | Matches any movie/show whose Originally Available date is within the last specified number of days | :heavy_check_mark: | :heavy_check_mark: |
| `year.gte` | Matches any movie/show whose year is greater then or equal to the specified year | :heavy_check_mark: | :heavy_check_mark: |
| `year.lte` | Matches any movie/show whose year is less then or equal to the specified year | :heavy_check_mark: | :heavy_check_mark: |
| `rating.gte` | Matches any movie/show whose rating is greater then or equal to the specified rating | :heavy_check_mark: | :heavy_check_mark: |
| `rating.lte` | Matches any movie/show whose rating is less then or equal to the specified rating | :heavy_check_mark: | :heavy_check_mark: |
| `originally_available.gte` | Matches any movie/show whose originally_available date is greater then or equal to the specified originally_available date (Date must be in the MM/DD/YYYY Format) | :heavy_check_mark: | :heavy_check_mark: |
| `originally_available.lte` | Matches any movie/show whose originally_available date is less then or equal to the specified originally_available date (Date must be in the MM/DD/YYYY Format) | :heavy_check_mark: | :heavy_check_mark: |

Note only standard filters can take multiple values

```yaml
collections:
  1080p Documentaries:
    genre: Documentary
    summary: A collection of 1080p Documentaries
    filters:
      video_resolution: 1080
```
```yaml
collections:
  Daniel Craig only James Bonds:
    imdb_list: https://www.imdb.com/list/ls006405458/
    filters:
      actor: Daniel Craig
```
```yaml
collections:
  French Romance:
    genre: Romance
    filters:
      audio_language: Français
```
```yaml
collections:
  Romantic Comedies:
    genre: Romance
    filters:
      genre: Comedy
```
```yaml
collections:
  9.0 Movies:
    all: true
    filters:
      rating.gte: 9
```
```yaml
collections:
  Summer 2020 Movies:
    all: true
    filters:
      originally_available.gte: 5/1/2020
      originally_available.lte: 8/31/2020
```
```yaml
collections:
  Movies Released in the Last 180 Days:
    all: true
    filters:
      max_age: 180
```
```yaml
collections:
  Good Adam Sandler Romantic Comedies:
    plex_search:
      genre: Romance
      actor: Adam Sandler
    filters:
      genre: Comedy
      rating.gte: 7
```

Note that multiple collection filters are supported but a movie must match at least one value from **each** collection filter to be added to a collection. The values for each must match what Plex has including special characters in order to match.

### Sync Mode (Collection Attribute)
You can specify how collections sync using `sync_mode`. Set it to `append` to only add movies/shows to the collection or set it to `sync` to add movies/shows to the collection and remove movies/shows from a collection.

| Sync Options | Description |
| :-- | :-- |
| `append` | Only Add Items to the Collection |
| `sync` | Add & Remove Items from the Collection |

```yaml
collections:
  IMDb Top 250:
    imdb_list: https://www.imdb.com/search/title/?groups=top_250&count=25
    sync_mode: sync
```

### Sort Title (Collection Attribute)

Setting the sort title is possible for each collection. This can be helpful to rearrange the collections in alphabetical sort. One example of this might be to "promote" certain collections to the top of a library by creating a sort title starting with an asterisk. If you do use an asterisk or other special characters including `:` You have to surround the whole name with quotes.

```yaml
collections:
  IMDb Top 250:
    imdb_list: https://www.imdb.com/search/title/?groups=top_250&count=25
    sort_title: "*100"
  Reddit Top 250:
    trakt_list: https://trakt.tv/users/jay-greene/lists/reddit-top-250-2019-edition
    sort_title: "*101"
```

### Content Rating (Collection Attribute)

Adding a content rating to each collection is possible:

```yaml
collections:
  Pixar:
    studio: Pixar
    content_rating: PG
```

### Summary (Collection Attribute)

Adding a summary to the collection is possible by either pulling the overview from TMDb or by using a custom entry.

To use a TMDb entry a TMDb api-key as well as language is required, the default language is set to `en`. Match the following in the configuration file, input only the TMDb collection/movie/show page ID or URL. To use the actor's biography use `tmdb_biography` with their page ID or URL on TMDb if you wish to use their biography as the summary.

```yaml
collections:
  Jurassic Park:
    tmdb_collection: https://www.themoviedb.org/collection/328
    tmdb_summary: 328
```
```yaml
collections:
  Dave Chappelle:
    actor: Dave Chappelle
    tmdb_biography: 4169
```
If you want to use a custom summary:
```yaml
collections:
  Pixar:
    studio: Pixar
    summary: A collection of Pixar movies
```
```yaml
collections:
  Alien (Past & Present):
    tmdb_collection:
      - https://www.themoviedb.org/collection/8091
      - https://www.themoviedb.org/collection/135416
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

### Collection Mode (Collection Attribute)

Plex allows for four different types of collection modes: library default, hide items in this collection, show this collection and its items, and hide collection (more details can be found in [Plex's Collection support article](https://support.plex.tv/articles/201273953-collections/#toc-2)). These options can be set with `default`, `hide_items`, `show_items`, and `hide`.

| Collection Mode Options | Description |
| :-- | :-- |
| `default` | Library default |
| `hide` | Hide Collection |
| `hide_items` | Hide Items in this Collection |
| `show_items` | Show this Collection and its Items |

```yaml
collections:
  Jurassic Park:
    tmdb_collection: https://www.themoviedb.org/collection/328
    tmdb_summary: 328
    poster: https://i.imgur.com/QMjbyCX.png
    background: https://i.imgur.com/2xE0R9I.png
    collection_mode: hide_items
```

### Collection Order (Collection Attribute)

Lastly, Plex allows collections to be sorted by the media's release dates or alphabetically by title. These options can be set with `release` or `alpha`. Plex defaults all collections to `release`, but `alpha` can be helpful for rearranging collections. For example, with collections where the chronology does not follow the release dates, you could create custom sort titles for each media item and then sort the collection alphabetically.

| Collection Sort Options | Description |
| :-- | :-- |
| `release` | Order Collection by Release Dates |
| `alpha` | Order Collection Alphabetically |

```yaml
collections:
  Alien (Past & Present):
    tmdb_collection:
      - https://www.themoviedb.org/collection/8091
      - https://www.themoviedb.org/collection/135416
    collection_order: alpha
```

### Poster (Collection Attribute)

There are four ways to set a poster image for a collection: local image, public URL, TMDb collection, or TMDb actor.

Local assets are supported by running the script with posters in the `poster_directory` or `image_directory`. See the [Image Server](#image-server) section below for more details or to specify a specific place in your file system for a poster use `file_poster`.

If multiple posters are found the script will ask which one you want to use or just take the first one in the list if update mode is on.

Note if you want to use an actor's profile image from TMDb use `tmdb_profile` instead of `tmdb_poster`.

If you want to use an image publicly available on the internet:
```yaml
collections:
  Jurassic Park:
    tmdb_collection: https://www.themoviedb.org/collection/328
    tmdb_summary: 328
    poster: https://i.imgur.com/QMjbyCX.png
```
If you want to use the default collection image on TMDb:
```yaml
collections:
  Alien (Past & Present):
    tmdb_collection:
      - https://www.themoviedb.org/collection/8091
      - https://www.themoviedb.org/collection/135416
    tmdb_poster: 8091
```
If you want to use the default actor image on TMDb:
```yaml
collections:
  Dave Chappelle:
    actor: Dave Chappelle
    tmdb_biography: 4169
    tmdb_profile: 4169
```
If you want to use an image in your file system:
```yaml
collections:
  Jurassic Park:
    tmdb_collection: https://www.themoviedb.org/collection/328
    tmdb_summary: 328
    file_poster: C:/Users/username/Desktop/2xE0R9I.png
    file_background: /config/backgrounds/Jurassic Park.png
```

### Background (Collection Attribute)

There are three ways to set a background image for a collection: local image, public URL, or TMDb collection.

Local assets are supported by running the script with backgrounds in the `background_directory` or `image_directory`. See the [Image Server](#image-server) section below for more details or to specify a specific place in your file system for a background use `file_background`.

If multiple backgrounds are found the script will ask which one you want to use or just take the first one in the list if update mode is on.

If you want to use an image publicly available on the internet:
```yaml
collections:
  Jurassic Park:
    tmdb_collection: https://www.themoviedb.org/collection/328
    tmdb_summary: 328
    poster: https://i.imgur.com/QMjbyCX.png
    background: https://i.imgur.com/2xE0R9I.png
```
If you want to use the default collection image on TMDb:
```yaml
collections:
  Alien (Past & Present):
    tmdb_collection:
      - https://www.themoviedb.org/collection/8091
      - https://www.themoviedb.org/collection/135416
    tmdb_background: 8091
```
If you want to use an image in your file system:
```yaml
collections:
  Jurassic Park:
    tmdb_collection: https://www.themoviedb.org/collection/328
    tmdb_summary: 328
    file_poster: C:/Users/username/Desktop/2xE0R9I.png
    file_background: /config/backgrounds/Jurassic Park.png
```

### Name Mapping (Collection Attribute)

If you are using the image server and your collection name contains characters that are not allowed in filepaths (i.e. for windows `<`, `>`, `:`, `"`, `/`, `\`, `|`, `?`, `*` cannot be in the file path) but you want them in your collection name you can use the `name_mapping` attribute to specific this collection's name in the file system.

```yaml
collections:
  28 Days/Weeks Later:
    tmdb_id: 1565
    name_mapping: 28 Days-Weeks Later
```

## Plex

A `plex` mapping in the config is required. Here's the full set of configurations:

```yaml
plex:                                         # Req
  library: Movies                             # Req - Name of Plex library
  library_type: movie                         # Req - Type of Plex library (movie or show)
  token: #####                                # Req - User's Plex authentication token
  url: http://192.168.1.1:32400               # Req - URL to access Plex
  sync_mode: append                           # Opt - Global Sync Mode
```

Note that Plex does not allow a `show` to be added to a `movie` library or vice versa.

For `movie` libraries that use the new Plex Movie agent, a temporary copy of the Plex database is downloaded to facilitate the identification of movies. This occurs only during an initial run of the script, per config file. Depending on the size of the library, this can result in a large download.

This script can be run on a remote Plex server, but be sure that the `url` provided is publicly addressable and it's recommended to use `HTTPS`.

You can set the global default [Sync Mode](#sync-mode-collection-attribute) here by using `sync_mode`. Set it to `append` to only add movies/shows to the collection or set it to `sync` to add movies/shows to the collection and remove movies/shows from a collection.

| Sync Options | Description |
| :-- | :-- |
| `append` | Only Add Items to the Collection |
| `sync` | Add & Remove Items from the Collection |

Lastly, if you need help finding your Plex authentication token, please see Plex's [support article](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).

## Image Server

An `image_server` mapping in the config is optional. There are two ways to store your posters and background. Using `poster_directory` and/or `background_directory` or by using `image_directory`.

Note that attempting to upload larger images files (~10MB+) can sometimes throw errors like `[Errno 32] Broken pipe` in certain environments. Resize your images accordingly if you run into any issues.

### Poster and/or Background Directory
By placing images in the `poster_directory` or `background_directory`, the script will attempt to match image names to collection names. For example, if there is a collection named `Jurassic Park` and the images `../config/posters/Jurassic Park.png` and `../config/backgrounds/Jurassic Park.png`, the script will upload those images to Plex.

```yaml
image_server:                                 # Opt
  poster_directory: /config/posters           # Opt - Desired dir of posters
  background_directory: /config/backgrounds   # Opt - Desired dir of backgrounds
```

### Image Directory
By placing images in folders in the `image_directory` folder, the script will attempt to match folder names to collection names. For example, if there is a collection named `Jurassic Park` and the images `../config/images/Jurassic Park/poster.png` and `../config/images/Jurassic Park/background.png`, the script will upload those images to Plex.

```yaml
image_server:                                 # Opt
  image_directory: /config/images             # Opt - Desired dir of images
```

Note: these can be used together if you want, the script will just ask you which one you want if there are multiple matching images.

## TMDb

If using TMDb lists, be sure to include your TMDb API key. If you do not have an API key please refer to this [guide](https://developers.themoviedb.org/3/getting-started/introduction). Here's the full set of configurations:

```yaml
tmdb:                                         # Opt
  apikey: #####                               # Req - User's TMDb API key
  language: en                                # Opt - User's language
```

## Tautulli

If using Tautulli lists, be sure to include your Tautulli URL and API key.

```yaml
tautulli:                                     # Opt
    url: http://192.168.1.1:8181              # Req - URL to access Tautulli
    apikey: #####                             # Req - User's Tautulli API key
```

The `apikey` can be found by going to `Tautulli > Settings > Web Interface > API > API Key`

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
  auto_refresh_token: true                    # Req
  authorization:                              # Req
    access_token:                             # LEAVE BLANK
    token_type:                               # LEAVE BLANK
    expires_in:                               # LEAVE BLANK
    refresh_token:                            # LEAVE BLANK
    scope:                                    # LEAVE BLANK
    created_at:                               # LEAVE BLANK
```

On the first run, the script will walk the user through the OAuth flow by producing a Trakt URL for the user to follow. Once authenticated at the Trakt URL, the user needs to return the code to the script. If the code is correct, the script will populate the `authorization` subattributes to use in subsequent runs.

For docker users, please note that the docker container runs with the `--update` option and is designed for no user interaction. To authenticate Trakt the first time, you need run the container with the `-it` flags and run `plex_auto_collections.py` without the `--update` option and walk through the OAuth flow mentioned above. Once you have the Trakt authentication data saved into the YAML, you'll be able to run the container normally.

__NOTE__: When using multiple configuration files which share the same Trakt `access_token`, you must set the `auto_refresh_token` parameter to `false`. Since the `refresh_token` can only be used once, an `access_token` refresh in one file will invalidate the `access_token` in the all other files. The simplest workaround is to use different `authorization` values for each configuration file.

## Radarr

When parsing TMDb, IMDb, or Trakt lists, the script will finds movies that are on the list but missing from Plex. If a TMDb and Radarr config are supplied, then you can add those missing movies to Radarr.

Here's the full set of configurations:
```yaml
radarr:                                       # Opt
  url: http://192.168.1.1:7878                # Req - URL to access Radarr
  version: v2                                 # Opt - 'v2' for <0.2, 'v3' for >3.0
  token: #####                                # Req - User's Radarr API key
  quality_profile_id: 4                       # Req - See below
  root_folder_path: /mnt/movies               # Req - See below
  add_to_radarr: false                        # Opt - Add missing movies to Radarr
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

The `add_to_radarr` key allows missing to movies to be added to Radarr. If this key is missing, the script will prompt the user to add missing movies or not. If you'd like to add movies but not had Radarr search, then set `search_movie` to `false`. If you want to override this attribute per collection you can add the `add_to_radarr` attribute under a collection and set it to true or false to override any global choice.

# Acknowledgements
- [vladimir-tutin](https://github.com/vladimir-tutin) for writing substantially all of the code in this fork
- [deva5610](https://github.com/deva5610) for writing [IMDBList2PlexCollection](https://github.com/deva5610/IMDBList2PlexCollection) which prompted the idea for a
configuration based collection manager
- [JonnyWong16](https://github.com/JonnyWong16) for writing the a [IMDb Top 250](https://gist.github.com/JonnyWong16/f5b9af386ea58e19bf18c09f2681df23) collection script which served as inspiration (and for [Tautulli](https://github.com/Tautulli/Tautulli)!)
- [pkkid](https://github.com/pkkid) and all other contributors for [python-plexapi](https://github.com/pkkid/python-plexapi)
- [AnthonyBloomer](https://github.com/AnthonyBloomer) and all other contributors for [tmdbv3api](https://github.com/AnthonyBloomer/tmdbv3api)
- [fuzeman](https://github.com/fuzeman) and all other contributors for [trakt.py](https://github.com/fuzeman/trakt.py) (and for [Plex-Trakt-Scrobbler](https://github.com/trakt/Plex-Trakt-Scrobbler)!)
- [bearlikelion](https://github.com/bearlikelion) for writing [popularplex](https://github.com/bearlikelion/popularplex) which prompted Tautulli support
- [blacktwin](https://github.com/blacktwin) for writing [playlist_manager.py](https://github.com/blacktwin/JBOPS/blob/master/fun/playlist_manager.py)

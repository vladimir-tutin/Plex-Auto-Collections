# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.8.1] - 2020-12-14 - [#142](https://github.com/mza921/Plex-Auto-Collections/pull/150)
### Fixed
- [#147](https://github.com/mza921/Plex-Auto-Collections/issues/147) - Bad merge
- [#148](https://github.com/mza921/Plex-Auto-Collections/issues/148) - Bad merge

## [2.8.0] - 2020-12-14 - [#142](https://github.com/mza921/Plex-Auto-Collections/pull/142)
### Added
- Faster initialization of a GUID mapping database for the new Plex Movie Agent using the Plex database

### Removed
- `cache` and `cache_interval` options removed from the config. Movie/Show ID lookups are now always cached on each script execution.

### Fixed
- [#132](https://github.com/mza921/Plex-Auto-Collections/issues/132) - plex_search with a range of years

## [2.7.0] - 2020-11-26 - [#115](https://github.com/mza921/Plex-Auto-Collections/pull/115)
### Added
- Added `tmdb_trending_daily` and `tmdb_trending_weekly`
- Added requirements checking with an error message telling the user to update their requirements
- [#98](https://github.com/mza921/Plex-Auto-Collections/issues/98) - Added `cache` attribute to cache the IDs of movies/shows for quicker lookup and `cache_update_interval` to determine how often to update the cache
- [#123](https://github.com/mza921/Plex-Auto-Collections/issues/123) - Added new filter `plex_collection`
- [#125](https://github.com/mza921/Plex-Auto-Collections/issues/125) - Added error message for YAML Scan Failures

### Changed
- Created a mapping for TMDb ID to Plex Rating Key once each run instead of every time tmdb, imdb, tvdb, or trakt list was run.
- [#110](https://github.com/mza921/Plex-Auto-Collections/issues/110) - Added `add_to_radarr` as a collection level attribute override
- [#121](https://github.com/mza921/Plex-Auto-Collections/issues/121) - Added paging to `tmdb_network` and `tmdb_company` for show libraries
- Upgrade tmdbv3api dependency to 1.7.1

### Fixed
- [#109](https://github.com/mza921/Plex-Auto-Collections/issues/109) - The Cache shouldn't be created unless it has to be
- [#117](https://github.com/mza921/Plex-Auto-Collections/issues/117) - Typo
- [#118](https://github.com/mza921/Plex-Auto-Collections/issues/118) - Check for to see if the tmdb attribute exists
- [#120](https://github.com/mza921/Plex-Auto-Collections/issues/120) - Sometimes the collection wasn't found

## [2.6.0] - 2020-11-12 - [#113](https://github.com/mza921/Plex-Auto-Collections/pull/113)
### Added
- [#107](https://github.com/mza921/Plex-Auto-Collections/issues/107) - Added `plex_collection`
- [#86](https://github.com/mza921/Plex-Auto-Collections/issues/86) - Added `tmdb_company` and `tmdb_network`
- [#41](https://github.com/mza921/Plex-Auto-Collections/issues/41) - Added `tmdb_discover`
- Added `tmdb_popular`, `tmdb_top_rated`, `tmdb_now_playing`

### Fixed
- [#108](https://github.com/mza921/Plex-Auto-Collections/issues/108) - Fixed TMDb error
- [#102](https://github.com/mza921/Plex-Auto-Collections/issues/102) - If any APIs are invalid the collection switches to append

## [2.5.0] - 2020-11-11 - [#112](https://github.com/mza921/Plex-Auto-Collections/pull/112)
### Added
- [#72](https://github.com/mza921/Plex-Auto-Collections/issues/72) - `trakt_watchlist` support
- `auto_refresh_token` Trakt config parameter

### Fixed
- [#50](https://github.com/mza921/Plex-Auto-Collections/issues/50) - Trakt access_token refresh

## [2.4.7] - 2020-11-09 - [#103](https://github.com/mza921/Plex-Auto-Collections/pull/103)
### Fixed
- [#92](https://github.com/mza921/Plex-Auto-Collections/issues/92) - fixed New Plex Movie Agent id lookup behind a proxy
- [#75](https://github.com/mza921/Plex-Auto-Collections/issues/75) - fixed `tmdb_director`, `tmdb_actor`, and `tmdb_writer`

## [2.4.6] - 2020-11-06 - [#101](https://github.com/mza921/Plex-Auto-Collections/pull/101)
### Added
- Progress for filtering movies/shows and imdb lists
- IMDb list and search validation

### Fixed
- [#93](https://github.com/mza921/Plex-Auto-Collections/issues/93) - actually fixed `max_age`

## [2.4.5] - 2020-11-05 - [#97](https://github.com/mza921/Plex-Auto-Collections/pull/97)
### Changed
- `max_age` no longer takes years

### Fixed
- [#93](https://github.com/mza921/Plex-Auto-Collections/issues/93) - actually fixed `max_age`

## [2.4.4] - 2020-11-05 - [commit](https://github.com/mza921/Plex-Auto-Collections/commit/eb9f3ed2ebfcb3ba9fbdfb07ff0ec56da6ccd4be)
### Fixed
- [#94](https://github.com/mza921/Plex-Auto-Collections/issues/94) - Fixed `trakt_trending` (again)

## [2.4.3] - 2020-11-05 - [#96](https://github.com/mza921/Plex-Auto-Collections/pull/96)
### Fixed
- [#93](https://github.com/mza921/Plex-Auto-Collections/issues/93) - fixed `max_age`
- [#94](https://github.com/mza921/Plex-Auto-Collections/issues/94) - Fixed `trakt_trending`

## [2.4.2] - 2020-11-04 - [#90](https://github.com/mza921/Plex-Auto-Collections/pull/90)
### Fixed
- [#87](https://github.com/mza921/Plex-Auto-Collections/issues/87) - 1000+ IMDB Error Fixed
- [#89](https://github.com/mza921/Plex-Auto-Collections/issues/89) - Shouldn't crash when trakt cant find a show

## [2.4.1] - 2020-11-04 - [#85](https://github.com/mza921/Plex-Auto-Collections/pull/85)
### Fixed
- [#84](https://github.com/mza921/Plex-Auto-Collections/pull/84) - IndentationError
- Fixed CHANGELOG Links

## [2.4.0] - 2020-11-03 - [#76](https://github.com/mza921/Plex-Auto-Collections/pull/76)
### Added
- [#63](https://github.com/mza921/Plex-Auto-Collections/issues/63) - Added `plex_search` to AND searches together
- Added additional `filters` and allow for use of `.not` for inverse `filters`
- [#75](https://github.com/mza921/Plex-Auto-Collections/issues/75) - Added `tmdb_director` and `tmdb_writer` which function the same as `tmdb_actor` but for directors and writers
- More compatibility  with previous config files.

### Changed
- [#63](https://github.com/mza921/Plex-Auto-Collections/issues/63) - `Plex Filters` are now listed and have been tested and have been changed to `Plex Searches`
- `subfilters` are now listed and have been tested and have been changed to `filters`

### Fixed
- `collection_order` was in the code as `collection_sort`
- Upgrade PlexAPI dependency to 4.2.0

## [2.3.1] - 2020-11-03 - [#83](https://github.com/mza921/Plex-Auto-Collections/pull/83)
### Fixed
- [#82](https://github.com/mza921/Plex-Auto-Collections/issues/82) Fix movie id lookup when imdb/tmdb id doesn't exist

## [2.3.0] - 2020-11-03 - [#81](https://github.com/mza921/Plex-Auto-Collections/pull/81)
### Added
- [#33](https://github.com/mza921/Plex-Auto-Collections/issues/33) - Support for the new Plex Movie agent
- Cache database for IMDB/TMDB id lookups

### Changed
- [#73](https://github.com/mza921/Plex-Auto-Collections/issues/73) - Dockerfile no longer passes the update flag by default

## [2.2.1] - 2020-10-28 - [#71](https://github.com/mza921/Plex-Auto-Collections/pull/71)
### Added
- CHANGELOG.md

## [2.2.0] - 2020-10-27 - [#70](https://github.com/mza921/Plex-Auto-Collections/pull/70)
### Added
- [#61](https://github.com/mza921/Plex-Auto-Collections/issues/61) - `trakt_trending` list support

## [2.1.1] - 2020-10-27 - [#68](https://github.com/mza921/Plex-Auto-Collections/pull/68)
### Fixed
- Broken `tmdb_collection` list support due to typo
- Type mismatch error when parsing TMDb IDs
- Upgrade PlexAPI dependency to 4.1.2

## [2.1.0] - 2020-10-26 - [#66](https://github.com/mza921/Plex-Auto-Collections/pull/66)
### Added
- [#53](https://github.com/mza921/Plex-Auto-Collections/issues/53) - `tautulli` list support

### Changed
- [#60](https://github.com/mza921/Plex-Auto-Collections/issues/60) - Disambiguated TMDb collection and lists from actors (`tmdb_actor`, `tmdb_biography`, and `tmdb_profile`)
- Conformed `tmdbId` to `tmdb_id`

### Fixed
- [#58](https://github.com/mza921/Plex-Auto-Collections/issues/58) - Some broken `imdb_list` pagination
- [#63](https://github.com/mza921/Plex-Auto-Collections/issues/63) - Some broken Plex filters and subfilters

## [2.0.1] - 2020-10-26 - [#64](https://github.com/mza921/Plex-Auto-Collections/pull/64)
### Changed
- Indentation Changes

## [2.0.0] - 2020-10-24 - [#52](https://github.com/mza921/Plex-Auto-Collections/pull/52)
### Added
- `tmdb_list` support
- More robust show support
- Ability to add individual movies or shows with `tmdb_movie`, `tmdb_show`, or `tvbd_show`
- [#22](https://github.com/mza921/Plex-Auto-Collections/issues/22) - `sync_mode` support to allow users to `append` or `sync` items with lists
- `name_mapping` support to allow users to specific filename mappings
- [#11](https://github.com/mza921/Plex-Auto-Collections/issues/11) - `imdb_list` pagination support

### Changed
- Conformed to `snake_case` causing the following `config` variables to renamed:
  - `old-tag` -> `new_tag`
  - `imdb-list` -> `imdb_list`
  - `trakt-list` -> `trakt_list`
  - `video-resolution` -> `video_resolution`
  - `audio-language` -> `audio_language`
  - `subtitle-language` -> `subtitle_language`
  - `tmdb-poster` -> `tmdb_poster`
  - `image-server` -> `image_server`
  - `poster-directory` -> `poster_directory`
- Disambiguated TMDb collections from lists (`tmdb-list` -> `tmdb_collection`)

### Deprecated
- `details` subkey - removed key altogether to promote a flatter file structure

### Fixed
- [#14](https://github.com/mza921/Plex-Auto-Collections/issues/14), [#31](https://github.com/mza921/Plex-Auto-Collections/issues/31), [#48](https://github.com/mza921/Plex-Auto-Collections/issues/48) - Trakt authentication check
- [#57](https://github.com/mza921/Plex-Auto-Collections/issues/57) - `image_server` failure fix

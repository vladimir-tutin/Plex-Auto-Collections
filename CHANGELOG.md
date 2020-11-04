# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2020-11-03 - #76
### Added
- #63 - Added `plex_search` to AND searches together
- Added additional `filters` and allow for use of `.not` for inverse `filters`
- #75 - Added `tmdb_director` and `tmdb_writer` which function the same as `tmdb_actor` but for directors and writers
- More compatibility  with previous config files.

### Changed
- #63 - `Plex Filters` are now listed and have been tested and have been changed to `Plex Searches`
- `subfilters` are now listed and have been tested and have been changed to `filters`

### Fixed
- `collection_order` was in the code as `collection_sort`
- Upgrade PlexAPI dependency to 4.2.0

## [2.3.1] - 2020-11-03 - #83
### Fixed
- #82 Fix movie id lookup when imdb/tmdb id doesn't exist

## [2.3.0] - 2020-11-03 - #81
### Added
- #33 - Support for the new Plex Movie agent
- Cache database for IMDB/TMDB id lookups

### Changed
- #73 - Dockerfile no longer passes the update flag by default

## [2.2.1] - 2020-10-28 - #71
### Added
- CHANGELOG.md

## [2.2.0] - 2020-10-27 - #70
### Added
- #61 - `trakt_trending` list support

## [2.1.1] - 2020-10-27 - #68
### Fixed
- Broken `tmdb_collection` list support due to typo
- Type mismatch error when parsing TMDb IDs
- Upgrade PlexAPI dependency to 4.1.2

## [2.1.0] - 2020-10-26 - #66
### Added
- #53 - `tautulli` list support

### Changed
- #60 - Disambiguated TMDb collection and lists from actors (`tmdb_actor`, `tmdb_biography`, and `tmdb_profile`)
- Conformed `tmdbId` to `tmdb_id`

### Fixed
- #58 - Some broken `imdb_list` pagination
- #63 - Some broken Plex filters and subfilters

## [2.0.1] - 2020-10-26 - #64
### Changed
- Indentation Changes

## [2.0.0] - 2020-10-24 - #52
### Added
- `tmdb_list` support
- More robust show support
- Ability to add individual movies or shows with `tmdb_movie`, `tmdb_show`, or `tvbd_show`
- #22 - `sync_mode` support to allow users to `append` or `sync` items with lists
- `name_mapping` support to allow users to specific filename mappings
- #11 - `imdb_list` pagination support

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
- #31, #48, #50 - Trakt authentication check
- #57 - `image_server` failure fix

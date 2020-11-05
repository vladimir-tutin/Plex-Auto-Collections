# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

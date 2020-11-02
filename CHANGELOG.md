# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2020-11-02
### Added
- Support for the new Plex Movie agent
- Cache database for IMDB/TMDB id lookups

## [2.2.1] - 2020-10-28
### Added
- CHANGELOG.md

## [2.2.0] - 2020-10-27
### Added
- `trakt_trending` list support

## [2.1.1] - 2020-10-27
### Fixed
- Broken `tmdb_collection` list support due to typo
- Type mismatch error when parsing TMDb IDs
- Upgrade PlexAPI dependency to 4.1.2

## [2.1.0] - 2020-10-26
### Added
- `tautulli` list support

### Changed
- Disambiguated TMDb collection and lists from actors (`tmdb_actor`, `tmdb_biography`, and `tmdb_profile`)
- Conformed `tmdbId` to `tmdb_id`

### Fixed
- Some broken `imdb_list` pagination
- Some broken Plex filters and subfilters

## [2.0.0] - 2020-10-24
### Added
- `tmdb_list` support
- More robust show support
- Ability to add individual movies or shows with `tmdb_movie`, `tmdb_show`, or `tvbd_show`
- `sync_mode` support to allow users to `append` or `sync` items with lists
- `name_mapping` support to allow users to specific filename mappings
- `imdb_list` pagination support

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
- Trakt authentication check

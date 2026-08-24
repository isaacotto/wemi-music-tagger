# WEMI Music Tagger

A Python utility to extract MusicBrainz metadata and organize it into **IFLA LRM (WEMI)** sidecar JSON files for music libraries.

## What is WEMI?

**WEMI** is the IFLA Logical Reference Model:
- **Work**: The abstract musical composition (e.g., "Maiden Voyage")
- **Expression**: How the work was performed (e.g., Herbie Hancock's 1973 recording)
- **Manifestation**: The specific release/album (e.g., the 1980 CD reissue on CBS)
- **Item**: The physical file (e.g., your local FLAC copy)

This tool helps you leverage this framework to organize your music library with rich, facetable metadata.

## Features

✅ Scans FLAC files for MusicBrainz IDs (in existing tags)
✅ Fetches release and recording data from MusicBrainz API
✅ Organizes metadata into WEMI levels
✅ Writes clean JSON sidecar files (`.mb.json`) alongside your music
✅ Respects MusicBrainz rate limits (1 request/second)
✅ Comprehensive logging for debugging

## Installation

```bash
git clone https://github.com/isaacotto/wemi-music-tagger.git
cd wemi-music-tagger

pip install -r requirements.txt
```

## Quick Start

### Basic usage:

```bash
python main.py /path/to/your/music/library
```

This will:
1. Find all `.flac` files recursively
2. Read MusicBrainz IDs from ID3 tags
3. Fetch metadata from MusicBrainz API
4. Write `.mb.json` sidecar files next to each FLAC

### With verbose logging:

```bash
python main.py /path/to/music/library --verbose
```

## Sidecar File Format

Each sidecar file (e.g., `track.mb.json`) contains:

```json
{
  "item": {
    "filename": "01_maiden_voyage.flac",
    "filetype": "flac",
    "duration_ms": 360000,
    "track_number": 1
  },
  "manifestation": {
    "title": "Maiden Voyage",
    "release_id": "abc-123-def",
    "label_name": "Herbie Hancock Institute",
    "release_date": "1973-10-15",
    "release_country": "US"
  },
  "expression": {
    "recording_date": "1973-06-21",
    "recording_location": "CBS Studios, New York"
  },
  "work": {
    "work_title": "Maiden Voyage",
    "composer": [
      {
        "id": "herbie-id",
        "name": "Herbie Hancock",
        "role": "composer"
      }
    ],
    "work_type": "song"
  }
}
```

## Project Structure

- **`main.py`** - Entry point; handles directory scanning and orchestration
- **`extractor.py`** - Core extraction logic; reads files and builds WEMI objects
- **`wemi_schemas.py`** - Pydantic models defining the WEMI structure
- **`musicbrainz_client.py`** - MusicBrainz API client with rate limiting
- **`requirements.txt`** - Python dependencies

## Requirements

Your FLAC files should already have MusicBrainz IDs in the tags. You can add these using:

- **MusicBrainz Picard**: Official tagger with built-in MusicBrainz integration
- **beets**: Flexible music library manager with MusicBrainz plugin

## Next Steps

- [ ] Build a graph-browsing frontend (React + D3.js)
- [ ] Expand expression-level metadata (instrumentation, key, tempo)
- [ ] Add support for work relationships (same work, different expressions)
- [ ] Integrate with music player (Navidrome, Subsonic, etc.)
- [ ] Add CLI option to fill in missing MusicBrainz IDs

## License

MIT

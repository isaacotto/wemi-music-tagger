"""Client for fetching metadata from MusicBrainz API.

Handles rate limiting, error handling, and data transformation
from MusicBrainz JSON to our WEMI schema.
"""

import time
import logging
from datetime import date
from typing import Optional, Dict, Any, List

import musicbrainzngs as mbrainz
import requests


logger = logging.getLogger(__name__)

# Rate limit: MusicBrainz asks for 1 request per second
MB_RATE_LIMIT_DELAY = 1.0
last_request_time = 0


def init_musicbrainz():
    """Initialize MusicBrainz client with proper headers."""
    mbrainz.set_useragent("wemi-music-tagger", "1.0")
    logger.info("MusicBrainz client initialized")


def _respect_rate_limit():
    """Enforce 1 request/second to MusicBrainz."""
    global last_request_time
    elapsed = time.time() - last_request_time
    if elapsed < MB_RATE_LIMIT_DELAY:
        time.sleep(MB_RATE_LIMIT_DELAY - elapsed)
    last_request_time = time.time()


def fetch_release_by_id(release_id: str) -> Optional[Dict[str, Any]]:
    """Fetch complete release data from MusicBrainz.
    
    Args:
        release_id: MusicBrainz release UUID
        
    Returns:
        Release dict or None if not found
    """
    _respect_rate_limit()
    
    try:
        logger.debug(f"Fetching release {release_id} from MusicBrainz")
        result = mbrainz.get_release_by_id(
            release_id,
            includes=[
                "recordings",
                "labels",
                "artists",
                "release-groups",
                "works",
                "artist-credits"
            ]
        )
        return result.get('release')
    except mbrainz.NetworkError as e:
        logger.error(f"Network error fetching release {release_id}: {e}")
        return None
    except mbrainz.ResponseError as e:
        logger.error(f"Response error fetching release {release_id}: {e}")
        return None


def fetch_recording_by_id(recording_id: str) -> Optional[Dict[str, Any]]:
    """Fetch recording data from MusicBrainz.
    
    Args:
        recording_id: MusicBrainz recording UUID
        
    Returns:
        Recording dict or None if not found
    """
    _respect_rate_limit()
    
    try:
        logger.debug(f"Fetching recording {recording_id} from MusicBrainz")
        result = mbrainz.get_recording_by_id(
            recording_id,
            includes=["artists", "works", "releases"]
        )
        return result.get('recording')
    except (mbrainz.NetworkError, mbrainz.ResponseError) as e:
        logger.error(f"Error fetching recording {recording_id}: {e}")
        return None


def extract_composer_from_work(work: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Extract composer information from a MusicBrainz work.
    
    Args:
        work: MusicBrainz work dict
        
    Returns:
        Dict with id, name, role or None
    """
    if 'relations' not in work:
        return None
        
    for relation in work.get('relations', []):
        if relation.get('type') == 'composer':
            target = relation.get('target-credit') or relation.get('artist', {}).get('name')
            artist_id = relation.get('artist', {}).get('id')
            if target and artist_id:
                return {
                    'id': artist_id,
                    'name': target,
                    'role': 'composer'
                }
    return None


def extract_performers_from_recording(recording: Dict[str, Any]) -> List[Dict[str, str]]:
    """Extract performer information from a MusicBrainz recording.
    
    Args:
        recording: MusicBrainz recording dict
        
    Returns:
        List of dicts with id, name, role, instrument
    """
    performers = []
    
    # Use artist-credit for primary performers
    for credit in recording.get('artist-credit', []):
        if isinstance(credit, dict):
            artist = credit.get('artist', {})
            performers.append({
                'id': artist.get('id', ''),
                'name': credit.get('name', artist.get('name', '')),
                'role': 'performer'
            })
    
    return performers


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse ISO date string to date object.
    
    Args:
        date_str: ISO date string (YYYY, YYYY-MM, or YYYY-MM-DD)
        
    Returns:
        date object or None
    """
    if not date_str:
        return None
    
    try:
        # Handle various precision levels
        if len(date_str) == 4:  # YYYY
            date_str = f"{date_str}-01-01"
        elif len(date_str) == 7:  # YYYY-MM
            date_str = f"{date_str}-01"
        
        return date.fromisoformat(date_str)
    except (ValueError, AttributeError):
        logger.warning(f"Could not parse date: {date_str}")
        return None

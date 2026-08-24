"""Core extraction logic: read tags -> fetch MusicBrainz data -> write WEMI sidecar.

The main orchestrator that ties together file scanning, metadata fetching,
and sidecar writing.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from datetime import date

from mutagen.flac import FLAC

from wemi_schemas import (
    WEMISidecar,
    ItemMetadata,
    ManifestationMetadata,
    ExpressionMetadata,
    WorkMetadata,
    Agent
)
from musicbrainz_client import (
    init_musicbrainz,
    fetch_release_by_id,
    fetch_recording_by_id,
    extract_composer_from_work,
    extract_performers_from_recording,
    parse_date
)


logger = logging.getLogger(__name__)


def read_musicbrainz_ids_from_flac(flac_path: Path) -> tuple[Optional[str], Optional[str]]:
    """Extract MusicBrainz IDs from FLAC tags.
    
    Args:
        flac_path: Path to FLAC file
        
    Returns:
        Tuple of (release_id, recording_id) or (None, None) if not found
    """
    try:
        audio = FLAC(flac_path)
        
        # MusicBrainz FLAC tags use lowercase with underscores
        release_id = audio.get('musicbrainz_albumid', [None])[0]
        recording_id = audio.get('musicbrainz_recordingid', [None])[0]
        
        if release_id:
            logger.debug(f"Found release ID {release_id} in {flac_path.name}")
        if recording_id:
            logger.debug(f"Found recording ID {recording_id} in {flac_path.name}")
            
        return release_id, recording_id
    
    except Exception as e:
        logger.error(f"Error reading FLAC tags from {flac_path}: {e}")
        return None, None


def build_item_metadata(flac_path: Path, audio_tags: FLAC) -> ItemMetadata:
    """Build Item-level metadata from file.
    
    Args:
        flac_path: Path to FLAC file
        audio_tags: Mutagen FLAC object
        
    Returns:
        ItemMetadata object
    """
    # Duration is in seconds, convert to milliseconds
    duration_ms = int(audio_tags.info.length * 1000) if audio_tags.info else 0
    
    # Track number from tags, default to 1
    track_number = 1
    track_tag = audio_tags.get('tracknumber', ['1'])[0]
    try:
        # Handle "1/12" format
        track_number = int(track_tag.split('/')[0])
    except (ValueError, IndexError):
        track_number = 1
    
    return ItemMetadata(
        filename=flac_path.name,
        filetype="flac",
        duration_ms=duration_ms,
        track_number=track_number
    )


def build_manifestation_metadata(release_data: dict) -> ManifestationMetadata:
    """Build Manifestation-level metadata from MusicBrainz release.
    
    Args:
        release_data: MusicBrainz release dict
        
    Returns:
        ManifestationMetadata object
    """
    # Extract label info (usually first label)
    label_id = None
    label_name = None
    if release_data.get('label-info-list'):
        for label_info in release_data['label-info-list']:
            label = label_info.get('label', {})
            if label:
                label_id = label.get('id')
                label_name = label.get('name')
                break
    
    # Extract medium ID (usually first medium)
    medium_id = None
    if release_data.get('media'):
        medium_id = release_data['media'][0].get('id')
    
    return ManifestationMetadata(
        title=release_data.get('title', 'Unknown'),
        release_id=release_data.get('id', ''),
        label_id=label_id,
        label_name=label_name,
        medium_id=medium_id,
        release_date=parse_date(release_data.get('date')),
        release_country=release_data.get('country')
    )


def build_expression_metadata(recording_data: dict) -> ExpressionMetadata:
    """Build Expression-level metadata from MusicBrainz recording.
    
    Args:
        recording_data: MusicBrainz recording dict
        
    Returns:
        ExpressionMetadata object
    """
    # For now, we'll extract basic recording info
    # Extended metadata like key, tempo would require additional lookups
    
    recording_location = None
    recording_date = None
    recording_event = None
    
    # Try to extract from relations (simplified for prototype)
    if recording_data.get('relations'):
        for relation in recording_data['relations']:
            rel_type = relation.get('type')
            # In a full implementation, we'd parse these more thoroughly
    
    return ExpressionMetadata(
        arranger=None,  # Would need separate lookup
        key=None,  # Would need work data
        instrumentation=None,  # Would need session data
        tempo=None,  # Would need session data
        recording_date=parse_date(recording_data.get('first-release-date')),
        recording_location=recording_location,
        recording_event=recording_event
    )


def build_work_metadata(recording_data: dict) -> WorkMetadata:
    """Build Work-level metadata from MusicBrainz recording.
    
    Args:
        recording_data: MusicBrainz recording dict
        
    Returns:
        WorkMetadata object
    """
    work_title = recording_data.get('title', 'Unknown')
    composer = None
    work_type = None
    work_key = None
    
    # Try to extract work info from relations
    if recording_data.get('relations'):
        for relation in recording_data['relations']:
            if relation.get('type') == 'performance':
                work = relation.get('work', {})
                if work:
                    work_title = work.get('title', work_title)
                    work_type = work.get('type')
                    
                    # Extract composer from work
                    composer_data = extract_composer_from_work(work)
                    if composer_data:
                        composer = [Agent(**composer_data)]
    
    return WorkMetadata(
        composer=composer,
        work_title=work_title,
        work_type=work_type,
        work_key=work_key
    )


def extract_to_wemi_sidecar(flac_path: Path) -> Optional[WEMISidecar]:
    """Extract all metadata from a FLAC file into a WEMI sidecar.
    
    Args:
        flac_path: Path to FLAC file
        
    Returns:
        WEMISidecar object or None if extraction failed
    """
    logger.info(f"Extracting metadata for {flac_path.name}")
    
    # Read MusicBrainz IDs from tags
    release_id, recording_id = read_musicbrainz_ids_from_flac(flac_path)
    
    if not release_id:
        logger.warning(f"No MusicBrainz release ID found in {flac_path}")
        return None
    
    # Read file metadata
    try:
        audio = FLAC(flac_path)
    except Exception as e:
        logger.error(f"Could not read FLAC file {flac_path}: {e}")
        return None
    
    # Fetch release data from MusicBrainz
    release_data = fetch_release_by_id(release_id)
    if not release_data:
        logger.error(f"Could not fetch release {release_id} from MusicBrainz")
        return None
    
    # Fetch recording data if available
    recording_data = None
    if recording_id:
        recording_data = fetch_recording_by_id(recording_id)
    
    # Build WEMI components
    item = build_item_metadata(flac_path, audio)
    manifestation = build_manifestation_metadata(release_data)
    expression = build_expression_metadata(recording_data or {})
    work = build_work_metadata(recording_data or {})
    
    # Combine into sidecar
    try:
        sidecar = WEMISidecar(
            item=item,
            manifestation=manifestation,
            expression=expression,
            work=work
        )
        logger.info(f"Successfully created sidecar for {flac_path.name}")
        return sidecar
    
    except Exception as e:
        logger.error(f"Error creating sidecar for {flac_path.name}: {e}")
        return None


def write_sidecar_file(sidecar: WEMISidecar, flac_path: Path) -> Path:
    """Write WEMI sidecar to JSON file next to the FLAC.
    
    Args:
        sidecar: WEMISidecar object
        flac_path: Path to original FLAC file
        
    Returns:
        Path to written sidecar file
    """
    sidecar_path = flac_path.with_suffix('.mb.json')
    
    try:
        with open(sidecar_path, 'w') as f:
            # Use .dict() for Pydantic v1, .model_dump() for v2
            data = sidecar.model_dump(exclude_none=True)
            json.dump(data, f, indent=2, default=str)  # default=str for date serialization
        
        logger.info(f"Wrote sidecar to {sidecar_path}")
        return sidecar_path
    
    except Exception as e:
        logger.error(f"Error writing sidecar to {sidecar_path}: {e}")
        raise

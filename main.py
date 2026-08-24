#!/usr/bin/env python3
"""Main entry point for WEMI music tagger.

Scans a music library directory for FLAC files, extracts MusicBrainz metadata,
and creates WEMI sidecar JSON files.

Usage:
    python main.py /path/to/music/library
    python main.py /path/to/music/library --output /path/to/sidecars
"""

import logging
import sys
from pathlib import Path
from argparse import ArgumentParser

from musicbrainz_client import init_musicbrainz
from extractor import extract_to_wemi_sidecar, write_sidecar_file


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def scan_flac_library(library_path: Path) -> list[Path]:
    """Find all FLAC files in a directory tree.
    
    Args:
        library_path: Root directory of music library
        
    Returns:
        List of FLAC file paths
    """
    if not library_path.is_dir():
        logger.error(f"Library path is not a directory: {library_path}")
        return []
    
    flac_files = list(library_path.rglob('*.flac'))
    logger.info(f"Found {len(flac_files)} FLAC files in {library_path}")
    
    return sorted(flac_files)


def process_library(library_path: Path, output_path: Optional[Path] = None) -> int:
    """Process entire music library, extracting metadata and writing sidecars.
    
    Args:
        library_path: Root directory of music library
        output_path: Optional directory to write sidecars (default: same as FLAC)
        
    Returns:
        Exit code (0 for success)
    """
    logger.info(f"Starting WEMI extraction for library: {library_path}")
    
    # Initialize MusicBrainz client
    init_musicbrainz()
    
    # Find all FLAC files
    flac_files = scan_flac_library(library_path)
    
    if not flac_files:
        logger.warning("No FLAC files found. Exiting.")
        return 1
    
    # Process each file
    successful = 0
    failed = 0
    
    for i, flac_path in enumerate(flac_files, 1):
        logger.info(f"Processing {i}/{len(flac_files)}: {flac_path.relative_to(library_path)}")
        
        try:
            # Extract metadata
            sidecar = extract_to_wemi_sidecar(flac_path)
            
            if sidecar:
                # Write sidecar file
                write_sidecar_file(sidecar, flac_path)
                successful += 1
            else:
                failed += 1
        
        except Exception as e:
            logger.error(f"Unexpected error processing {flac_path}: {e}")
            failed += 1
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"WEMI Extraction Complete")
    logger.info(f"Successful: {successful}/{len(flac_files)}")
    logger.info(f"Failed: {failed}/{len(flac_files)}")
    logger.info(f"{'='*60}")
    
    return 0 if failed == 0 else 1


def main():
    """Parse arguments and run the extractor."""
    parser = ArgumentParser(
        description="Extract MusicBrainz metadata into WEMI sidecar files"
    )
    parser.add_argument(
        "library_path",
        type=Path,
        help="Path to music library root directory"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional: directory to write sidecar files (default: same directory as FLAC)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    exit_code = process_library(args.library_path, args.output)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

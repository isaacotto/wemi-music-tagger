"""IFLA LRM (WEMI) schema definitions for music metadata.

Defines Pydantic models for organizing music metadata according to
IFLA Logical Reference Model: Work, Expression, Manifestation, Item.
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Represents a person or organization (composer, performer, label, etc)."""
    id: str = Field(..., description="MusicBrainz artist/label ID")
    name: str = Field(..., description="Name of the person or organization")
    role: Optional[str] = Field(None, description="Role (e.g., 'composer', 'performer', 'label')")
    instrument: Optional[str] = Field(None, description="Instrument played (if performer)")


class ItemMetadata(BaseModel):
    """Item-level: the physical file itself."""
    filename: str = Field(..., description="Original filename")
    filetype: str = Field(..., description="File format (e.g., 'flac', 'mp3')")
    duration_ms: int = Field(..., description="Duration in milliseconds")
    track_number: int = Field(..., description="Track number on the medium")


class ManifestationMetadata(BaseModel):
    """Manifestation-level: the specific release/album as published."""
    title: str = Field(..., description="Album title as transcribed")
    release_id: str = Field(..., description="MusicBrainz release ID")
    label_id: Optional[str] = Field(None, description="MusicBrainz label ID")
    label_name: Optional[str] = Field(None, description="Label name")
    medium_id: Optional[str] = Field(None, description="MusicBrainz medium ID")
    release_date: Optional[date] = Field(None, description="Official release date")
    release_country: Optional[str] = Field(None, description="Country of release (ISO 3166)")


class ExpressionMetadata(BaseModel):
    """Expression-level: how the work was performed/recorded."""
    arranger: Optional[List[Agent]] = Field(None, description="Arrangers")
    key: Optional[str] = Field(None, description="Key of transposition")
    instrumentation: Optional[str] = Field(None, description="Instrumentation description")
    tempo: Optional[str] = Field(None, description="Tempo marking or BPM")
    recording_date: Optional[date] = Field(None, description="Date of recording/performance")
    recording_location: Optional[str] = Field(None, description="Location where recorded")
    recording_event: Optional[str] = Field(None, description="Concert/session name if applicable")


class WorkMetadata(BaseModel):
    """Work-level: the abstract musical composition."""
    composer: Optional[List[Agent]] = Field(None, description="Composers (controlled vocabulary via MB)")
    work_title: str = Field(..., description="Title of the work (controlled)")
    work_type: Optional[str] = Field(None, description="Work type (e.g., 'song', 'symphony', 'concerto')")
    work_key: Optional[str] = Field(None, description="Original key of the work")


class WEMISidecar(BaseModel):
    """Complete WEMI sidecar for a single music file.
    
    Combines all four levels of IFLA LRM to provide rich,
    facetable metadata for music library applications.
    """
    item: ItemMetadata
    manifestation: ManifestationMetadata
    expression: ExpressionMetadata
    work: WorkMetadata
    
    class Config:
        json_schema_extra = {
            "example": {
                "item": {
                    "filename": "01_maiden_voyage.flac",
                    "filetype": "flac",
                    "duration_ms": 360000,
                    "track_number": 1
                },
                "manifestation": {
                    "title": "Maiden Voyage",
                    "release_id": "abc123",
                    "label_name": "Herbie Hancock Institute",
                    "release_date": "1973-10-15",
                    "release_country": "US"
                },
                "expression": {
                    "arranger": [],
                    "key": "C major",
                    "instrumentation": "Piano, electric piano, fender rhodes",
                    "recording_date": "1973-06-21",
                    "recording_location": "CBS Studios, New York"
                },
                "work": {
                    "composer": [{"id": "herbie-id", "name": "Herbie Hancock", "role": "composer"}],
                    "work_title": "Maiden Voyage",
                    "work_type": "song",
                    "work_key": "C major"
                }
            }
        }

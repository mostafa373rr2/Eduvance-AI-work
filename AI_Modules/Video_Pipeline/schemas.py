"""
Eduvance AI - Video Pipeline Data Contracts
WBS 3.4 - Video Agent Schemas

Defines Pydantic v2 validation models strictly adhering to:
- Contract 3 (Video Agent) from WBS 2.1 (Architecture & Contracts)
- Database entity representations (Database/models/all_models.py: VideoAsset)

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from pathlib import Path
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SlideSpec(BaseModel):
    """
    Individual slide specification within an instructional lesson video.
    Directly conforms to WBS 2.1 Contract 3 (LessonVideoAssetOutput.slides[]).
    """
    model_config = ConfigDict(from_attributes=True)

    slide_number: int = Field(
        ge=1,
        description="1-indexed sequence number of the slide",
    )
    header: str = Field(
        min_length=3,
        max_length=200,
        description="Slide title / headline",
    )
    bullet_points: List[str] = Field(
        min_length=2,
        max_length=5,
        description="2 to 5 concise bullet points highlighting key concepts",
    )
    visual_cue: Optional[str] = Field(
        default=None,
        description="Visual composition directive (e.g. 'Architecture Card', 'Comparison Table')",
    )
    narration_script: str = Field(
        min_length=20,
        description="Spoken voiceover script for this slide (~20 to 100 words)",
    )
    source_chunk_id: UUID = Field(
        description="UUID reference to source document chunk providing citation evidence",
    )


class LessonVideoAssetOutput(BaseModel):
    """
    Root contract output produced by the Video Pipeline Agent.
    Strictly conforms to WBS 2.1 Contract 3 schema specification.
    """
    model_config = ConfigDict(from_attributes=True)

    lesson_id: UUID = Field(
        description="UUID of the parent lesson",
    )
    total_estimated_seconds: int = Field(
        ge=10,
        le=420,
        description="Estimated duration in seconds (constrained to maximum 420 seconds / 7 minutes)",
    )
    slides: List[SlideSpec] = Field(
        min_length=3,
        max_length=8,
        description="Curated slides for the lesson video (constrained to 3 to 8 slides)",
    )


class RenderedSlide(BaseModel):
    """Metadata for a rasterized slide image file."""
    slide_number: int
    image_path: str
    width: int = 1920
    height: int = 1080


class SubtitleEntry(BaseModel):
    """Individual subtitle timestamp entry."""
    index: int
    start_seconds: float
    end_seconds: float
    text: str


class VideoPackageResult(BaseModel):
    """Result of assembling the multimedia assets into a lesson video asset."""
    lesson_id: UUID
    slide_deck_json: List[dict]
    script_json: dict
    audio_path: Optional[str] = None
    srt_subtitles_path: Optional[str] = None
    video_path: Optional[str] = None
    duration_seconds: int = 0
    is_compiled_mp4: bool = False

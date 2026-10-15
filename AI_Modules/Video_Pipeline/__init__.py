"""
Eduvance AI - Video Pipeline Agent Module
WBS 3.4 - Automated Instructional Video Generation Pipeline

Exports slide rendering, narration scripting, audio synthesis, caption synchronization,
and video packaging services conforming strictly to WBS 2.1 Contract 3.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from .audio_synthesizer import AudioSynthesizer
from .caption_synchronizer import CaptionSynchronizer
from .persistence import VideoAssetPersistenceService
from .pipeline import VideoGenerationPipeline
from .schemas import (
    LessonVideoAssetOutput,
    RenderedSlide,
    SlideSpec,
    SubtitleEntry,
    VideoPackageResult,
)
from .script_generator import VideoScriptGenerator
from .slide_renderer import SlideRenderer
from .video_assembler import VideoAssembler

__all__ = [
    "VideoGenerationPipeline",
    "VideoScriptGenerator",
    "SlideRenderer",
    "AudioSynthesizer",
    "CaptionSynchronizer",
    "VideoAssembler",
    "VideoAssetPersistenceService",
    "LessonVideoAssetOutput",
    "SlideSpec",
    "RenderedSlide",
    "SubtitleEntry",
    "VideoPackageResult",
]

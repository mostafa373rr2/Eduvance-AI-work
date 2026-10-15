"""
Eduvance AI - Video Pipeline Master Orchestrator (Video Agent)
WBS 3.4 - Automated Lesson Video Generation Pipeline

End-to-end coordinator integrating:
1. Script & storyboard generation (VideoScriptGenerator -> Contract 3)
2. 1080p slide rasterization (SlideRenderer)
3. Neural audio voiceovers (AudioSynthesizer)
4. Subtitle synchronization (CaptionSynchronizer -> .srt / .vtt)
5. Video compilation & manifest packaging (VideoAssembler)
6. Relational database persistence (VideoAssetPersistenceService)

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from AI_Modules.Extraction.schemas import ExtractedChunk, ExtractedConcept
from .audio_synthesizer import AudioSynthesizer
from .caption_synchronizer import CaptionSynchronizer
from .persistence import VideoAssetPersistenceService
from .schemas import LessonVideoAssetOutput, VideoPackageResult
from .script_generator import VideoScriptGenerator
from .slide_renderer import SlideRenderer
from .video_assembler import VideoAssembler


class VideoGenerationPipeline:
    """
    Master orchestrator for the Video Pipeline Agent.
    """

    def __init__(
        self,
        script_generator: Optional[VideoScriptGenerator] = None,
        slide_renderer: Optional[SlideRenderer] = None,
        audio_synthesizer: Optional[AudioSynthesizer] = None,
        caption_synchronizer: Optional[CaptionSynchronizer] = None,
        video_assembler: Optional[VideoAssembler] = None,
        persistence_service: Optional[VideoAssetPersistenceService] = None,
    ):
        self.script_generator = script_generator or VideoScriptGenerator()
        self.slide_renderer = slide_renderer or SlideRenderer()
        self.audio_synthesizer = audio_synthesizer or AudioSynthesizer()
        self.caption_synchronizer = caption_synchronizer or CaptionSynchronizer()
        self.video_assembler = video_assembler or VideoAssembler()
        self.persistence_service = persistence_service or VideoAssetPersistenceService()

    async def process_lesson_video(
        self,
        lesson_id: UUID,
        lesson_title: str,
        learning_objectives: List[str],
        concepts: List[Union[ExtractedConcept, Dict[str, Any]]],
        chunks: List[Union[ExtractedChunk, Dict[str, Any]]],
        output_dir: Union[str, Path],
        session: Optional[Session] = None,
        persist: bool = True,
        num_slides: Optional[int] = None,
    ) -> VideoPackageResult:
        """
        Executes end-to-end video synthesis for a lesson.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        slides_dir = output_dir / "slides"
        audio_dir = output_dir / "audio"
        srt_file = output_dir / "captions.srt"
        vtt_file = output_dir / "captions.vtt"

        # 1. Synthesize slide specifications and narration script (Contract 3)
        script_output: LessonVideoAssetOutput = self.script_generator.generate_lesson_script(
            lesson_id=lesson_id,
            lesson_title=lesson_title,
            learning_objectives=learning_objectives,
            concepts=concepts,
            chunks=chunks,
            num_slides=num_slides,
        )

        # 2. Render 1080p slide images using Pillow
        rendered_slides = self.slide_renderer.render_slide_deck(
            slides=script_output.slides,
            output_dir=slides_dir,
        )

        # 3. Synthesize voiceover audio for each slide
        audio_timings = await self.audio_synthesizer.synthesize_deck_audio(
            slides=script_output.slides,
            output_dir=audio_dir,
        )

        # 4. Generate synchronized subtitles (.srt and .vtt)
        slide_script_timings = [
            (slide.slide_number, slide.narration_script, duration)
            for slide, (_, _, duration) in zip(script_output.slides, audio_timings)
        ]
        self.caption_synchronizer.generate_subtitles(
            slide_timings=slide_script_timings,
            output_srt_path=srt_file,
            output_vtt_path=vtt_file,
        )

        # 5. Assemble video package (MP4 encoding or multimedia bundle)
        package_result: VideoPackageResult = self.video_assembler.assemble_video_package(
            lesson_id=lesson_id,
            slides=rendered_slides,
            audio_timings=audio_timings,
            srt_path=srt_file,
            output_dir=output_dir,
        )

        # 6. Relational database persistence
        if session is not None and persist:
            self.persistence_service.persist_video_asset(
                session=session,
                package=package_result,
                script_output=script_output,
            )

        return package_result

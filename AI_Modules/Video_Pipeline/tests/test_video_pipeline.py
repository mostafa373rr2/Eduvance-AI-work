"""
Eduvance AI - Video Pipeline End-to-End & Persistence Tests
WBS 3.4 - Automated Lesson Video Generation Pipeline

Tests:
- End-to-end integration: script -> 1080p slides -> audio -> captions -> packaging.
- Database persistence into VideoAsset table with status COMPLETED.
- Verification of manifest JSON and multimedia folder structure.
- Deterministic offline audio synthesis.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from pathlib import Path
import pytest
from sqlalchemy.orm import Session

from AI_Modules.Video_Pipeline.audio_synthesizer import AudioSynthesizer
from AI_Modules.Video_Pipeline.pipeline import VideoGenerationPipeline
from AI_Modules.Video_Pipeline.schemas import VideoPackageResult
from AI_Modules.Video_Pipeline.video_assembler import VideoAssembler
from Database.models.all_models import Lesson, VideoAsset


@pytest.mark.anyio
async def test_video_pipeline_end_to_end_persists_to_database(
    temp_output_dir: Path,
    db_session: Session,
    persisted_db_lesson: Lesson,
    mock_video_lesson_data: dict,
):
    """Verifies complete video pipeline runs and persists a VideoAsset record to the database."""
    # Force offline audio mock for fast, 100% deterministic local test execution
    audio_synth = AudioSynthesizer(prefer_offline_mock=True)
    pipeline = VideoGenerationPipeline(audio_synthesizer=audio_synth)

    result = await pipeline.process_lesson_video(
        lesson_id=mock_video_lesson_data["lesson_id"],
        lesson_title=mock_video_lesson_data["lesson_title"],
        learning_objectives=mock_video_lesson_data["learning_objectives"],
        concepts=mock_video_lesson_data["concepts"],
        chunks=mock_video_lesson_data["chunks"],
        output_dir=temp_output_dir,
        session=db_session,
        persist=True,
    )

    assert isinstance(result, VideoPackageResult)
    assert result.lesson_id == mock_video_lesson_data["lesson_id"]
    assert result.duration_seconds > 0

    # 1. Verify filesystem outputs
    slides_dir = temp_output_dir / "slides"
    audio_dir = temp_output_dir / "audio"
    srt_file = temp_output_dir / "captions.srt"
    manifest_file = temp_output_dir / "lesson_video_manifest.json"

    assert slides_dir.exists()
    assert audio_dir.exists()
    assert srt_file.exists()
    assert manifest_file.exists()

    slide_images = list(slides_dir.glob("slide_*.png"))
    audio_files = list(audio_dir.glob("audio_*.mp3"))
    assert len(slide_images) >= 3
    assert len(audio_files) >= 3

    # 2. Verify Database Persistence (VideoAsset)
    str_lesson_id = str(mock_video_lesson_data["lesson_id"])
    db_asset = db_session.query(VideoAsset).filter(VideoAsset.lesson_id == str_lesson_id).first()

    assert db_asset is not None
    assert db_asset.generation_status == "COMPLETED"
    assert db_asset.duration_seconds == result.duration_seconds
    assert db_asset.srt_subtitles_path == str(srt_file)

    # Verify script_json matches Contract 3 structure
    assert "slides" in db_asset.script_json
    assert len(db_asset.script_json["slides"]) == len(slide_images)
    assert "total_estimated_seconds" in db_asset.script_json

    # Verify slide_deck_json records 1080p slide frames
    assert len(db_asset.slide_deck_json) == len(slide_images)
    assert db_asset.slide_deck_json[0]["width"] == 1920
    assert db_asset.slide_deck_json[0]["height"] == 1080


@pytest.mark.anyio
async def test_audio_synthesizer_offline_mock(temp_output_dir: Path):
    """Verifies AudioSynthesizer offline mode writes valid audio stubs."""
    synthesizer = AudioSynthesizer(prefer_offline_mock=True)
    out_file = temp_output_dir / "test_offline.mp3"

    script = "This is a deterministic offline test for audio narration synthesis."
    duration = await synthesizer.synthesize_slide_audio(script, out_file)

    assert out_file.exists()
    assert out_file.stat().st_size > 0
    assert duration > 0.0


def test_video_assembler_without_ffmpeg(temp_output_dir: Path, mock_video_lesson_data: dict):
    """Verifies VideoAssembler gracefully bundles assets when ffmpeg is not present."""
    assembler = VideoAssembler(ffmpeg_binary=None)
    assert not assembler.has_ffmpeg

    from AI_Modules.Video_Pipeline.schemas import RenderedSlide

    fake_slides = [
        RenderedSlide(slide_number=1, image_path=str(temp_output_dir / "s1.png")),
        RenderedSlide(slide_number=2, image_path=str(temp_output_dir / "s2.png")),
    ]
    fake_timings = [
        (1, str(temp_output_dir / "a1.mp3"), 10.0),
        (2, str(temp_output_dir / "a2.mp3"), 12.0),
    ]
    srt_path = temp_output_dir / "test.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:05,000\nSubtitle\n", encoding="utf-8")

    result = assembler.assemble_video_package(
        lesson_id=mock_video_lesson_data["lesson_id"],
        slides=fake_slides,
        audio_timings=fake_timings,
        srt_path=srt_path,
        output_dir=temp_output_dir,
    )

    assert not result.is_compiled_mp4
    assert result.duration_seconds == 22
    assert (temp_output_dir / "lesson_video_manifest.json").exists()

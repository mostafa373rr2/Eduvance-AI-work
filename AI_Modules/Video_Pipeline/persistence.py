"""
Eduvance AI - Video Asset Database Persistence Service
WBS 3.4 - VideoAsset Entity Storage

Persists generated multimedia video assets into the relational database,
linking to Lesson entities and tracking compilation status.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from Database.models.all_models import Lesson, VideoAsset
from .schemas import LessonVideoAssetOutput, VideoPackageResult


class VideoAssetPersistenceService:
    """
    Manages database transactions for VideoAsset records.
    """

    def persist_video_asset(
        self,
        session: Session,
        package: VideoPackageResult,
        script_output: Optional[LessonVideoAssetOutput] = None,
    ) -> VideoAsset:
        """
        Persists or updates a VideoAsset record in the database.
        """
        str_lesson_id = str(package.lesson_id)
        lesson = session.query(Lesson).filter(Lesson.id == str_lesson_id).first()
        if not lesson:
            raise ValueError(f"Lesson with ID '{package.lesson_id}' does not exist in database.")

        # Serialize script JSON from Contract 3 output
        script_payload = (
            script_output.model_dump(mode="json")
            if script_output
            else package.script_json
        )

        # Check if VideoAsset already exists for this lesson
        db_asset = session.query(VideoAsset).filter(VideoAsset.lesson_id == str_lesson_id).first()

        if db_asset is None:
            db_asset = VideoAsset(
                lesson_id=str_lesson_id,
                script_json=script_payload,
                slide_deck_json=package.slide_deck_json,
                audio_path=package.audio_path,
                srt_subtitles_path=package.srt_subtitles_path,
                video_path=package.video_path,
                duration_seconds=package.duration_seconds,
                generation_status="COMPLETED",
                error_message=None,
            )
            session.add(db_asset)
        else:
            db_asset.script_json = script_payload
            db_asset.slide_deck_json = package.slide_deck_json
            db_asset.audio_path = package.audio_path
            db_asset.srt_subtitles_path = package.srt_subtitles_path
            db_asset.video_path = package.video_path
            db_asset.duration_seconds = package.duration_seconds
            db_asset.generation_status = "COMPLETED"
            db_asset.error_message = None

        session.commit()
        session.refresh(db_asset)
        return db_asset

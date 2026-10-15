"""
Eduvance AI - Video Assembly & FFmpeg Orchestration Engine
WBS 3.4 - Video Compilation & Multimedia Packaging

Coordinates slide frames, audio narration, and subtitle tracks. If FFmpeg CLI
is detected on the system, encodes a unified 1080p MP4. If FFmpeg is absent,
packages the slide deck and audio tracks into a synchronized manifest bundle.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import List, Optional, Tuple, Union
from uuid import UUID

from .schemas import RenderedSlide, VideoPackageResult


class VideoAssembler:
    """
    Assembles rasterized slides and audio tracks into an MP4 video or presentation bundle.
    """

    def __init__(self, ffmpeg_binary: Optional[str] = None):
        self.ffmpeg_path = ffmpeg_binary or shutil.which("ffmpeg")

    @property
    def has_ffmpeg(self) -> bool:
        """Returns True if a working FFmpeg binary is available on the system PATH."""
        return self.ffmpeg_path is not None

    def assemble_video_package(
        self,
        lesson_id: UUID,
        slides: List[RenderedSlide],
        audio_timings: List[Tuple[int, str, float]],
        srt_path: Union[str, Path],
        output_dir: Union[str, Path],
    ) -> VideoPackageResult:
        """
        Assembles all generated components into the final video asset.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        srt_path = Path(srt_path)
        total_duration = int(round(sum(t[2] for t in audio_timings)))

        # Slide deck metadata for DB JSON storage
        slide_deck_json = [
            {
                "slide_number": s.slide_number,
                "image_path": str(s.image_path),
                "width": s.width,
                "height": s.height,
            }
            for s in slides
        ]

        master_audio_path = str(audio_timings[0][1]) if audio_timings else None
        video_target_path = output_dir / f"lesson_{lesson_id}.mp4"

        is_compiled = False
        final_video_path: Optional[str] = None

        # 1. If FFmpeg is installed, attempt encoding MP4
        if self.has_ffmpeg:
            is_compiled = self._encode_with_ffmpeg(slides, audio_timings, srt_path, video_target_path)
            if is_compiled:
                final_video_path = str(video_target_path)

        # 2. Build multimedia manifest bundle
        manifest_path = output_dir / "lesson_video_manifest.json"
        manifest_data = {
            "lesson_id": str(lesson_id),
            "duration_seconds": total_duration,
            "is_compiled_mp4": is_compiled,
            "video_path": final_video_path,
            "srt_path": str(srt_path),
            "slides": slide_deck_json,
            "audio_tracks": [
                {"slide_number": t[0], "audio_path": str(t[1]), "duration_seconds": t[2]}
                for t in audio_timings
            ],
        }

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return VideoPackageResult(
            lesson_id=lesson_id,
            slide_deck_json=slide_deck_json,
            script_json=manifest_data,
            audio_path=master_audio_path,
            srt_subtitles_path=str(srt_path),
            video_path=final_video_path,
            duration_seconds=total_duration,
            is_compiled_mp4=is_compiled,
        )

    def _encode_with_ffmpeg(
        self,
        slides: List[RenderedSlide],
        audio_timings: List[Tuple[int, str, float]],
        srt_path: Path,
        output_mp4: Path,
    ) -> bool:
        """Invokes FFmpeg to compile slides and audio into an MP4 container."""
        if not self.ffmpeg_path:
            return False

        try:
            # Build concat demuxer file for slides
            temp_dir = output_mp4.parent / ".ffmpeg_tmp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            concat_file = temp_dir / "slides_concat.txt"

            with open(concat_file, "w", encoding="utf-8") as f:
                for s, (_, _, dur) in zip(slides, audio_timings):
                    # FFmpeg concat format requires forward slashes
                    escaped_img = str(Path(s.image_path).resolve()).replace("\\", "/")
                    f.write(f"file '{escaped_img}'\n")
                    f.write(f"duration {dur}\n")
                # Repeat last image once to avoid premature truncation
                if slides:
                    escaped_last = str(Path(slides[-1].image_path).resolve()).replace("\\", "/")
                    f.write(f"file '{escaped_last}'\n")

            # Run FFmpeg command
            cmd = [
                self.ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                str(output_mp4),
            ]

            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=120,
            )

            # Cleanup temp demuxer
            if concat_file.exists():
                concat_file.unlink()

            return process.returncode == 0 and output_mp4.exists()
        except Exception:
            return False

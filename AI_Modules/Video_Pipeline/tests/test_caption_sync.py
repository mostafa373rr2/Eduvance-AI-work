"""
Eduvance AI - Caption Synchronizer Tests
WBS 3.4 - SRT / WebVTT Timing Alignment

Tests:
- SubRip (.srt) and WebVTT (.vtt) file generation and syntax conformance.
- Timestamp precision formatting (HH:MM:SS,mmm vs HH:MM:SS.mmm).
- Monotonic cumulative offset progression across multi-slide transitions.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from pathlib import Path
import pytest

from AI_Modules.Video_Pipeline.caption_synchronizer import CaptionSynchronizer


def test_format_timestamp():
    """Verifies precise millisecond timestamp formatting."""
    sync = CaptionSynchronizer()

    # Zero seconds
    assert sync.format_timestamp(0.0, separator=",") == "00:00:00,000"
    assert sync.format_timestamp(0.0, separator=".") == "00:00:00.000"

    # 65.25 seconds (1 minute, 5 seconds, 250 ms)
    assert sync.format_timestamp(65.25, separator=",") == "00:01:05,250"

    # 3661.005 seconds (1 hour, 1 minute, 1 second, 5 ms)
    assert sync.format_timestamp(3661.005, separator=",") == "01:01:01,005"


def test_generate_srt_and_vtt_subtitles(temp_output_dir: Path):
    """Verifies complete SRT and WebVTT file generation from slide narration tracks."""
    sync = CaptionSynchronizer(pause_between_slides_sec=0.5)

    slide_timings = [
        (1, "Welcome to this lesson on cloud security architecture. We will explore core defenses.", 5.0),
        (2, "Identity is the primary boundary. Multi-factor authentication stops credential stuffing.", 6.0),
        (3, "To summarize: always enforce least privilege across all service endpoints.", 4.0),
    ]

    srt_path = temp_output_dir / "test_captions.srt"
    vtt_path = temp_output_dir / "test_captions.vtt"

    entries = sync.generate_subtitles(
        slide_timings=slide_timings,
        output_srt_path=srt_path,
        output_vtt_path=vtt_path,
    )

    assert len(entries) >= 3
    assert srt_path.exists()
    assert vtt_path.exists()

    # 1. Verify SRT content
    srt_content = srt_path.read_text(encoding="utf-8")
    assert "1\n00:00:00,000 --> " in srt_content
    assert "Welcome to this lesson" in srt_content

    # 2. Verify WebVTT content
    vtt_content = vtt_path.read_text(encoding="utf-8")
    assert vtt_content.startswith("WEBVTT\n\n")
    assert "00:00:00.000 --> " in vtt_content


def test_cumulative_timing_monotonicity(temp_output_dir: Path):
    """Verifies that all subtitle entries advance monotonically with zero backward jumps."""
    sync = CaptionSynchronizer(pause_between_slides_sec=0.5)

    slide_timings = [
        (1, "Slide one content is engaging and concise.", 3.5),
        (2, "Slide two provides further technical depth and practical examples.", 4.5),
        (3, "Slide three concludes the session with actionable next steps.", 3.0),
    ]

    srt_path = temp_output_dir / "monotonic_test.srt"
    entries = sync.generate_subtitles(slide_timings, srt_path)

    prev_end = 0.0
    for entry in entries:
        assert entry.start_seconds >= prev_end
        assert entry.end_seconds > entry.start_seconds
        prev_end = entry.end_seconds

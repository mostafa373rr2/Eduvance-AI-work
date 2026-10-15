"""
Eduvance AI - Caption & Subtitle Synchronization Engine
WBS 3.4 - SRT / WebVTT Timing Alignment

Generates word- and sentence-accurate SubRip (.srt) and WebVTT (.vtt) caption
streams aligned with narration audio and inter-slide transition buffers.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from pathlib import Path
import re
from typing import List, Optional, Tuple, Union

from .schemas import SubtitleEntry


class CaptionSynchronizer:
    """
    Constructs millisecond-accurate subtitle files from slide narration scripts and durations.
    """

    def __init__(self, pause_between_slides_sec: float = 0.5):
        self.pause_between_slides = pause_between_slides_sec

    def generate_subtitles(
        self,
        slide_timings: List[Tuple[int, str, float]],
        output_srt_path: Union[str, Path],
        output_vtt_path: Optional[Union[str, Path]] = None,
    ) -> List[SubtitleEntry]:
        """
        Generates synchronized subtitle tracks from slide scripts and durations.

        Args:
            slide_timings: List of tuples (slide_number, narration_script, slide_duration_seconds).
            output_srt_path: Target path for the .srt file.
            output_vtt_path: Optional target path for the .vtt file.

        Returns:
            List of generated SubtitleEntry records.
        """
        output_srt_path = Path(output_srt_path)
        output_srt_path.parent.mkdir(parents=True, exist_ok=True)

        entries: List[SubtitleEntry] = []
        global_time = 0.0
        entry_idx = 1

        for slide_no, script, duration in slide_timings:
            # Segment slide narration script into concise subtitle phrases (by sentence or comma)
            phrases = self._segment_into_phrases(script)
            if not phrases:
                phrases = [script]

            total_words = max(1, sum(len(p.split()) for p in phrases))
            slide_active_duration = max(1.0, duration - 0.2)

            for phrase in phrases:
                phrase_words = len(phrase.split())
                # Duration allocated proportionally by word count
                phrase_duration = (phrase_words / total_words) * slide_active_duration
                start_time = global_time
                end_time = global_time + phrase_duration

                entries.append(
                    SubtitleEntry(
                        index=entry_idx,
                        start_seconds=round(start_time, 3),
                        end_seconds=round(end_time, 3),
                        text=phrase,
                    )
                )

                global_time = end_time
                entry_idx += 1

            # Append inter-slide transition pause buffer
            global_time += self.pause_between_slides

        # 1. Write SRT format
        self._write_srt_file(entries, output_srt_path)

        # 2. Write WebVTT format if requested
        if output_vtt_path:
            output_vtt_path = Path(output_vtt_path)
            output_vtt_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_vtt_file(entries, output_vtt_path)

        return entries

    def _segment_into_phrases(self, script: str) -> List[str]:
        """Splits sentences into manageable phrase chunks of ~6 to 12 words."""
        sentences = re.split(r"(?<=[.!?])\s+", script.strip())
        phrases: List[str] = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            words = sentence.split()
            if len(words) <= 12:
                phrases.append(sentence)
            else:
                # Sub-split long sentences
                sub_phrases = re.split(r"(?<=[,;])\s+", sentence)
                for sp in sub_phrases:
                    sp = sp.strip()
                    if sp:
                        phrases.append(sp)

        return phrases

    def _write_srt_file(self, entries: List[SubtitleEntry], target_path: Path):
        """Writes SubRip (.srt) subtitle format."""
        with open(target_path, "w", encoding="utf-8") as f:
            for entry in entries:
                start_ts = self.format_timestamp(entry.start_seconds, separator=",")
                end_ts = self.format_timestamp(entry.end_seconds, separator=",")
                f.write(f"{entry.index}\n")
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(f"{entry.text}\n\n")

    def _write_vtt_file(self, entries: List[SubtitleEntry], target_path: Path):
        """Writes WebVTT (.vtt) subtitle format."""
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for entry in entries:
                start_ts = self.format_timestamp(entry.start_seconds, separator=".")
                end_ts = self.format_timestamp(entry.end_seconds, separator=".")
                f.write(f"{start_ts} --> {end_ts}\n")
                f.write(f"{entry.text}\n\n")

    @staticmethod
    def format_timestamp(seconds: float, separator: str = ",") -> str:
        """Formats fractional seconds into HH:MM:SS,mmm or HH:MM:SS.mmm."""
        total_ms = int(round(seconds * 1000))
        hours = total_ms // 3600000
        total_ms %= 3600000
        minutes = total_ms // 60000
        total_ms %= 60000
        secs = total_ms // 1000
        ms = total_ms % 1000

        return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{ms:03d}"

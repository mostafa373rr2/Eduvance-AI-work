"""
Eduvance AI - Slide Renderer Tests
WBS 3.4 - Pillow Slide Deck Generator

Tests:
- 1080p (1920x1080) slide image rasterization.
- Multi-slide deck batch rendering.
- Visual elements, card layouts, and word wrapping.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from pathlib import Path
from uuid import uuid4
import pytest
from PIL import Image

from AI_Modules.Video_Pipeline.schemas import SlideSpec
from AI_Modules.Video_Pipeline.slide_renderer import SlideRenderer


def test_render_single_slide(temp_output_dir: Path):
    """Verifies rendering a single slide creates a 1920x1080 PNG image."""
    renderer = SlideRenderer()
    slide = SlideSpec(
        slide_number=1,
        header="Introduction to Cloud Security",
        bullet_points=[
            "Shared responsibility model across IaaS, PaaS, and SaaS.",
            "Identity is the primary security boundary in cloud native deployments.",
        ],
        visual_cue="Cloud Responsibility Architecture Matrix",
        narration_script="Welcome to cloud security foundations. Let us examine the shared responsibility model.",
        source_chunk_id=uuid4(),
    )

    out_file = temp_output_dir / "test_slide_01.png"
    result = renderer.render_slide(slide, total_slides=4, output_path=out_file)

    assert Path(result.image_path).exists()
    assert result.width == 1920
    assert result.height == 1080

    # Inspect image with Pillow
    with Image.open(result.image_path) as img:
        assert img.size == (1920, 1080)
        assert img.format == "PNG"


def test_render_slide_deck(temp_output_dir: Path):
    """Verifies batch rendering of a 4-slide presentation deck."""
    renderer = SlideRenderer()
    dummy_chunks = [uuid4() for _ in range(4)]

    slides = [
        SlideSpec(
            slide_number=i,
            header=f"Slide {i}: Key Topics & Analysis",
            bullet_points=[f"Point {i}.1: Core mechanism", f"Point {i}.2: Operational practice"],
            visual_cue=f"Diagram {i}",
            narration_script=f"Narration script for slide number {i} with sufficient text length.",
            source_chunk_id=dummy_chunks[i - 1],
        )
        for i in range(1, 5)
    ]

    rendered_list = renderer.render_slide_deck(slides, output_dir=temp_output_dir)

    assert len(rendered_list) == 4
    for idx, r in enumerate(rendered_list, start=1):
        assert r.slide_number == idx
        p = Path(r.image_path)
        assert p.exists()
        assert p.name == f"slide_{idx:02d}.png"


def test_slide_renderer_text_wrapping():
    """Verifies internal text wrapping breaks long strings without losing words."""
    renderer = SlideRenderer()
    long_text = "This is a remarkably comprehensive explanatory bullet point detailing operational practices for zero trust."
    wrapped = renderer._wrap_text(long_text, max_chars=35)

    assert len(wrapped) > 1
    # Check that all original words are preserved
    reconstructed = " ".join(wrapped)
    assert reconstructed == long_text

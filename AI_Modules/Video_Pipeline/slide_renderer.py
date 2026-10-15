"""
Eduvance AI - 1080p Slide Rasterization Engine
WBS 3.4 - Pillow Slide Deck Generator

Renders high-contrast, professional 1080p (1920x1080) presentation slides
using Pillow (PIL) with modular cards, clean typography, and explicit source citations.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

from .schemas import RenderedSlide, SlideSpec


# Palette constants (Dark Slate & Cyan/Blue Academic Theme)
COLOR_BG = (15, 23, 42)          # #0F172A - Deep Slate
COLOR_CARD = (30, 41, 59)        # #1E293B - Card Surface
COLOR_CARD_BORDER = (51, 65, 85) # #334155 - Subtle Border
COLOR_ACCENT = (37, 99, 235)     # #2563EB - Primary Brand Blue
COLOR_CYAN = (56, 189, 248)      # #38BDF8 - Bright Highlight
COLOR_TEXT_PRIMARY = (248, 250, 252)  # #F8FAFC - High-contrast white
COLOR_TEXT_SECONDARY = (203, 213, 225) # #CBD5E1 - Light Slate
COLOR_TEXT_MUTED = (148, 163, 184)     # #94A3B8 - Metadata Slate
COLOR_CUE_BG = (13, 32, 61)      # Dark Navy Visual Box


class SlideRenderer:
    """
    Renders 1080p slide images for video compilation and presentation preview.
    """

    WIDTH = 1920
    HEIGHT = 1080

    def __init__(self):
        self._init_fonts()

    def _init_fonts(self):
        """Loads scalable TrueType fonts with cross-platform fallback."""
        font_candidates = [
            "arial.ttf",
            "segoeui.ttf",
            "calibri.ttf",
            "DejaVuSans.ttf",
            "Helvetica.ttf",
        ]

        def get_font(size: int):
            for candidate in font_candidates:
                try:
                    return ImageFont.truetype(candidate, size)
                except (IOError, OSError):
                    continue
            return ImageFont.load_default()

        self.font_title = get_font(52)
        self.font_header = get_font(38)
        self.font_body = get_font(30)
        self.font_badge = get_font(22)
        self.font_footer = get_font(20)

    def render_slide(
        self,
        slide: SlideSpec,
        total_slides: int,
        output_path: Union[str, Path],
    ) -> RenderedSlide:
        """
        Renders a single slide to a 1920x1080 PNG image file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 1. Base 1080p Canvas
        image = Image.new("RGB", (self.WIDTH, self.HEIGHT), COLOR_BG)
        draw = ImageDraw.Draw(image)

        # 2. Top Accent Stripe
        draw.rectangle([0, 0, self.WIDTH, 8], fill=COLOR_ACCENT)

        # 3. Slide Number & Topic Badge
        badge_text = f"SLIDE {slide.slide_number} OF {total_slides}  •  EDUVANCE AI"
        draw.rectangle([80, 50, 420, 88], fill=COLOR_CARD, outline=COLOR_CARD_BORDER, width=1)
        draw.text((100, 58), badge_text, font=self.font_badge, fill=COLOR_CYAN)

        # 4. Slide Title / Header
        draw.text((80, 110), slide.header, font=self.font_title, fill=COLOR_TEXT_PRIMARY)

        # 5. Main Content Card (Left / Center)
        card_x0, card_y0 = 80, 200
        card_x1, card_y1 = 1200, 920
        draw.rectangle([card_x0, card_y0, card_x1, card_y1], fill=COLOR_CARD, outline=COLOR_CARD_BORDER, width=2)

        # Card Title
        draw.text((card_x0 + 40, card_y0 + 35), "Key Concepts & Principles", font=self.font_header, fill=COLOR_CYAN)
        draw.line([card_x0 + 40, card_y0 + 90, card_x1 - 40, card_y0 + 90], fill=COLOR_CARD_BORDER, width=1)

        # Bullet Points
        bullet_y = card_y0 + 120
        for bp in slide.bullet_points:
            # Bullet point indicator dot
            draw.ellipse([card_x0 + 45, bullet_y + 10, card_x0 + 57, bullet_y + 22], fill=COLOR_CYAN)

            # Word-wrap bullet text
            wrapped_lines = self._wrap_text(bp, max_chars=54)
            for line in wrapped_lines:
                draw.text((card_x0 + 75, bullet_y), line, font=self.font_body, fill=COLOR_TEXT_SECONDARY)
                bullet_y += 42
            bullet_y += 24

        # 6. Visual Cue / Instructional Directive Box (Right Column)
        cue_x0, cue_y0 = 1240, 200
        cue_x1, cue_y1 = 1840, 920
        draw.rectangle([cue_x0, cue_y0, cue_x1, cue_y1], fill=COLOR_CUE_BG, outline=COLOR_ACCENT, width=2)

        draw.text((cue_x0 + 35, cue_y0 + 35), "Visual Focus", font=self.font_header, fill=COLOR_CYAN)
        draw.line([cue_x0 + 35, cue_y0 + 90, cue_x1 - 35, cue_y0 + 90], fill=COLOR_CARD_BORDER, width=1)

        # Visual directive text
        cue_text = slide.visual_cue or "Conceptual Schematic"
        wrapped_cue = self._wrap_text(cue_text, max_chars=28)
        cue_text_y = cue_y0 + 130
        for line in wrapped_cue:
            draw.text((cue_x0 + 35, cue_text_y), line, font=self.font_body, fill=COLOR_TEXT_PRIMARY)
            cue_text_y += 44

        # Schematic Decorative Box
        draw.rectangle([cue_x0 + 35, cue_text_y + 40, cue_x1 - 35, cue_y1 - 40], fill=COLOR_CARD, outline=COLOR_CARD_BORDER)
        draw.text((cue_x0 + 70, cue_text_y + 120), "[ Dynamic Graphic ]", font=self.font_badge, fill=COLOR_TEXT_MUTED)

        # 7. Provenance & Source Citation Footer
        footer_text = f"Source Provenance: Chunk {slide.source_chunk_id}  |  Graduation Project 2026"
        draw.line([80, 980, 1840, 980], fill=COLOR_CARD_BORDER, width=1)
        draw.text((80, 1000), footer_text, font=self.font_footer, fill=COLOR_TEXT_MUTED)

        # Save image
        image.save(output_path, format="PNG")

        return RenderedSlide(
            slide_number=slide.slide_number,
            image_path=str(output_path),
            width=self.WIDTH,
            height=self.HEIGHT,
        )

    def render_slide_deck(
        self,
        slides: List[SlideSpec],
        output_dir: Union[str, Path],
    ) -> List[RenderedSlide]:
        """
        Renders all slides in a slide deck and returns the list of generated file metadata.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results: List[RenderedSlide] = []
        total = len(slides)

        for s in slides:
            file_name = f"slide_{s.slide_number:02d}.png"
            target_path = output_dir / file_name
            rendered = self.render_slide(s, total, target_path)
            results.append(rendered)

        return results

    def _wrap_text(self, text: str, max_chars: int = 50) -> List[str]:
        """Simple word-wrapping helper."""
        words = text.split()
        lines: List[str] = []
        current_line: List[str] = []
        current_len = 0

        for word in words:
            if current_len + len(word) + (1 if current_line else 0) <= max_chars:
                current_line.append(word)
                current_len += len(word) + (1 if len(current_line) > 1 else 0)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_len = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return lines or [text]

"""
Unit and Integration Tests for PDFValidator & TextExtractor
WBS 3.2 - Step 2: Extraction Service Validation
"""

import io
import pytest
from pypdf import PdfReader, PdfWriter

from AI_Modules.Extraction.pdf_validator import PDFValidator
from AI_Modules.Extraction.text_extractor import TextExtractor


def make_test_pdf(pages_text: list[str]) -> bytes:
    """Helper to synthesize valid PDF bytes with text streams for deterministic unit tests."""
    objs = []
    objs.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    font_id = 3
    objs.append(f"{font_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    page_objs = []
    content_objs = []
    next_id = 4

    page_ids = []
    for text in pages_text:
        p_id = next_id
        c_id = next_id + 1
        page_ids.append(p_id)
        next_id += 2

        safe_text = text.replace("(", "\\(").replace(")", "\\)")
        stream_data = f"BT\n/F1 12 Tf\n72 712 Td\n({safe_text}) Tj\nET"
        content_objs.append((c_id, stream_data))
        page_objs.append((p_id, c_id))

    kids_str = " ".join(f"{pid} 0 R" for pid in page_ids)
    objs.insert(1, f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {len(page_ids)} >>\nendobj\n")

    for p_id, c_id in page_objs:
        objs.append(
            f"{p_id} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {c_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>\nendobj\n"
        )
    for c_id, stream_data in content_objs:
        s_bytes = stream_data.encode("latin1")
        objs.append(f"{c_id} 0 obj\n<< /Length {len(s_bytes)} >>\nstream\n{stream_data}\nendstream\nendobj\n")

    body = "%PDF-1.4\n"
    offsets = [0]
    for obj in objs:
        offsets.append(len(body.encode("latin1")))
        body += obj

    xref_offset = len(body.encode("latin1"))
    body += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n"
    for off in offsets[1:]:
        body += f"{off:010d} 00000 n \n"
    body += f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    return body.encode("latin1")


# Sample paragraph with sufficient character density (> 150 chars)
SAMPLE_TEXT_PAGE_1 = (
    "The NIST Cybersecurity Framework consists of five concurrent and continuous functions: "
    "Identify, Protect, Detect, Respond, and Recover. When considered together, these functions "
    "provide a high-level, strategic view of the lifecycle of an organization's management of risk."
)

SAMPLE_TEXT_PAGE_2 = (
    "Implementation tiers provide context on how an organization views cybersecurity risk and the "
    "processes in place to manage that risk. Tiers describe an increasing degree of rigor and sophistication "
    "in cybersecurity risk management practices, from Partial (Tier 1) to Adaptive (Tier 4)."
)


def test_pdf_validator_valid_pdf():
    pdf_bytes = make_test_pdf([SAMPLE_TEXT_PAGE_1, SAMPLE_TEXT_PAGE_2])
    validator = PDFValidator(max_pages=50, min_avg_chars_per_page=100.0)
    result = validator.validate(pdf_bytes)

    assert result.is_valid is True
    assert result.page_count == 2
    assert result.is_scanned_or_empty is False
    assert result.total_characters > 300
    assert result.average_chars_per_page > 100.0
    assert result.error_message is None


def test_pdf_validator_page_limit_exceeded():
    # Configure validator with a small max_pages threshold
    pdf_bytes = make_test_pdf([SAMPLE_TEXT_PAGE_1, SAMPLE_TEXT_PAGE_2])
    validator = PDFValidator(max_pages=1)
    result = validator.validate(pdf_bytes)

    assert result.is_valid is False
    assert result.page_count == 2
    assert "exceeds maximum course page limit" in result.error_message


def test_pdf_validator_scanned_or_empty_rejected():
    # Only 10 characters: triggers scanned/insufficient text heuristic
    pdf_bytes = make_test_pdf(["Page 1", "Page 2"])
    validator = PDFValidator(min_avg_chars_per_page=100.0, min_total_chars=150)
    result = validator.validate(pdf_bytes)

    assert result.is_valid is False
    assert result.is_scanned_or_empty is True
    assert "insufficient extractable text" in result.error_message


def test_pdf_validator_corrupt_stream():
    validator = PDFValidator()
    result = validator.validate(b"%PDF-1.4\ncorrupted gibberish not a real pdf structure")

    assert result.is_valid is False
    assert "Failed to parse PDF file" in result.error_message


def test_text_extractor_extracts_pages_accurately():
    pdf_bytes = make_test_pdf([SAMPLE_TEXT_PAGE_1, SAMPLE_TEXT_PAGE_2])
    extractor = TextExtractor()
    pages = extractor.extract_pages(pdf_bytes)

    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Identify, Protect, Detect" in pages[0].text
    assert pages[0].char_count == len(pages[0].text)
    assert pages[0].word_count > 20

    assert pages[1].page_number == 2
    assert "Implementation tiers" in pages[1].text
    assert pages[1].word_count > 20


def test_text_extractor_clean_text_normalizations():
    raw = "This is a cyber-\nsecurity guide.\r\n\r\n\r\nIt covers   threat   modeling."
    cleaned = TextExtractor.clean_text(raw)

    # Hyphen rejoining
    assert "cybersecurity guide." in cleaned
    # Multiple newline collapse to 2
    assert "\n\n" in cleaned
    assert "\n\n\n" not in cleaned
    # Multiple spaces collapsed
    assert "threat modeling." in cleaned


def test_text_extractor_raises_on_invalid_pdf():
    extractor = TextExtractor()
    with pytest.raises(ValueError, match="PDF validation failed"):
        extractor.extract_pages(b"not a valid pdf")

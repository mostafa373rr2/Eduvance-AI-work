"""
Unit tests for DocumentChunker
WBS 3.2 - Step 3: Chunking Service Verification
"""

from uuid import uuid4
import pytest

from AI_Modules.Extraction.schemas import ExtractedPage
from AI_Modules.Extraction.chunker import DocumentChunker


def test_chunker_invalid_overlap_raises():
    with pytest.raises(ValueError, match="strictly less than"):
        DocumentChunker(chunk_size_tokens=100, chunk_overlap_tokens=100)


def test_chunker_single_page_basic():
    doc_id = uuid4()
    page = ExtractedPage(
        page_number=1,
        text=(
            "The Cybersecurity Framework organizes cybersecurity activities into five core Functions. "
            "These Functions are Identify, Protect, Detect, Respond, and Recover. "
            "They facilitate risk management communications and strategic planning."
        ),
        char_count=230,
        word_count=32,
    )

    chunker = DocumentChunker(chunk_size_tokens=100, chunk_overlap_tokens=20)
    chunks = chunker.chunk_pages([page], document_id=doc_id)

    assert len(chunks) == 1
    assert chunks[0].document_id == doc_id
    assert chunks[0].chunk_index == 0
    assert chunks[0].page_number == 1
    assert "Identify, Protect, Detect" in chunks[0].text_content
    assert chunks[0].token_count > 20


def test_chunker_multi_page_and_sequential_index():
    doc_id = uuid4()
    pages = [
        ExtractedPage(
            page_number=1,
            text=(
                "Section 1. Introduction to Risk Analysis.\n\n"
                "Risk analysis forms the foundation of modern organizational security. "
                "Organizations must systematically catalogue assets, evaluate threats, and determine vulnerabilities."
            ),
            char_count=220,
            word_count=30,
        ),
        ExtractedPage(
            page_number=2,
            text=(
                "Section 2. Implementation Framework.\n\n"
                "Framework profiles help organizations align cybersecurity activities with business requirements. "
                "Profiles represent outcomes based on business needs and risk tolerance."
            ),
            char_count=220,
            word_count=28,
        ),
    ]

    chunker = DocumentChunker(chunk_size_tokens=40, chunk_overlap_tokens=10)
    chunks = chunker.chunk_pages(pages, document_id=doc_id)

    assert len(chunks) >= 2
    # Ensure sequential indexing
    for idx, c in enumerate(chunks):
        assert c.chunk_index == idx
        assert c.document_id == doc_id

    # Check that page anchors are preserved
    assert chunks[0].page_number == 1
    assert chunks[-1].page_number == 2


def test_chunker_section_header_detection():
    doc_id = uuid4()
    pages = [
        ExtractedPage(
            page_number=1,
            text=(
                "## 1. Governance Principles\n\n"
                "Governance ensures that cybersecurity strategies align with organizational goals. "
                "Executive oversight establishes acceptable risk thresholds and regulatory compliance priorities."
            ),
            char_count=230,
            word_count=28,
        )
    ]

    chunker = DocumentChunker(chunk_size_tokens=100)
    chunks = chunker.chunk_pages(pages, document_id=doc_id)

    assert len(chunks) == 1
    assert chunks[0].section_header == "1. Governance Principles"


def test_chunker_token_estimation():
    text = "The quick brown fox jumps over the lazy dog."
    tokens = DocumentChunker.estimate_tokens(text)
    # 9 words * 1.33 = ~11 tokens
    assert 9 <= tokens <= 14

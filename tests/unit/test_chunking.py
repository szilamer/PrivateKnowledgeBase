from domain.chunking import chunk_text, estimate_token_count


def test_chunk_text_produces_segments() -> None:
    text = "Paragraph one.\n\n" + ("word " * 200)
    segments = chunk_text(text, chunk_size=100, overlap=10)
    assert len(segments) >= 2
    assert all(segment.text for segment in segments)
    assert estimate_token_count("hello world") == 2

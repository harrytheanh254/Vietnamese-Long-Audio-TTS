from split_text import split_text

def test_short_text_is_one_chunk():
    assert split_text("Xin chào") == ["Xin chào"]

def test_chunks_respect_limit_and_keep_order():
    text = ("Đây là một câu chuyện. " * 120).strip()
    chunks = split_text(text, 500)
    assert len(chunks) > 1
    assert all(len(chunk) <= 500 for chunk in chunks)
    assert " ".join(chunks).replace("  ", " ") == text

def test_empty_text_rejected():
    try:
        split_text("   ")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected empty input to fail")

"""Text normalisation (prisma_s.normalize)."""

from prisma_s.normalize import normalize_text


def test_line_endings_to_lf():
    assert normalize_text("a\r\nb\rc") == "a\nb\nc"


def test_trailing_whitespace_stripped_per_line():
    assert normalize_text("a  \nb\t\n c ") == "a\nb\n c"


def test_nfc_normalisation():
    decomposed = "á"          # 'a' + combining acute
    assert normalize_text(decomposed) == "á"  # precomposed 'á'


def test_idempotent():
    s = "Régião  \r\nfarm\n"
    assert normalize_text(normalize_text(s)) == normalize_text(s)


def test_internal_whitespace_is_preserved():
    assert normalize_text("supply   shed") == "supply   shed"

"""Shared fixtures: synthetic PDF / DOCX documents with known contents."""

import pytest


def _make_pdf(path, pages):
    """Write a PDF at *path*; *pages* is a list of strings, one per page."""
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=LETTER)
    for text in pages:
        y = 720
        for line in text.splitlines() or [""]:
            c.drawString(72, y, line)
            y -= 14
        c.showPage()
    c.save()
    return path


@pytest.fixture
def make_pdf(tmp_path):
    counter = {"n": 0}

    def _factory(pages, name=None):
        counter["n"] += 1
        target = tmp_path / (name or f"doc{counter['n']}.pdf")
        return _make_pdf(target, pages)

    return _factory


@pytest.fixture
def make_docx(tmp_path):
    counter = {"n": 0}

    def _factory(text, name=None):
        from docx import Document

        counter["n"] += 1
        target = tmp_path / (name or f"doc{counter['n']}.docx")
        d = Document()
        for para in text.split("\n"):
            d.add_paragraph(para)
        d.save(str(target))
        return target

    return _factory

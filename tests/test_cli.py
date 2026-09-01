"""CLI argument handling (prisma_s.cli)."""

import pytest

import prisma_s.cli as cli


def test_version(capsys):
    import sys

    sys.argv = ["prisma-s", "--version"]
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert e.value.code == 0
    assert "1.5.0" in capsys.readouterr().out


def test_run_requires_a_source(monkeypatch, capsys):
    import sys

    sys.argv = ["prisma-s", "run", "--batch", "b", "--output", "x.xlsx"]
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert e.value.code == 1
    assert "input_path or drive_folder" in capsys.readouterr().err


def test_drive_url_is_reduced_to_id(monkeypatch):
    captured = {}

    def fake_run_analysis(**kwargs):
        captured.update(kwargs)

        class _DF:
            def __len__(self):
                return 0

        return _DF()

    monkeypatch.setattr("prisma_s.runner.run_analysis", fake_run_analysis)
    import sys

    sys.argv = [
        "prisma-s", "run", "--batch", "b", "--output", "x.xlsx",
        "--drive-folder", "https://drive.google.com/drive/folders/1AbcXYZ?usp=sharing",
        "--drive-credentials", "creds.json",
    ]
    cli.main()
    assert captured["drive_folder_id"] == "1AbcXYZ"


def test_cite_lang(capsys):
    import sys

    sys.argv = ["prisma-s", "cite", "--lang", "pt-br"]
    cli.main()
    out = capsys.readouterr().out
    assert "Como citar" in out and "World Resources Institute" in out

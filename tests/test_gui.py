"""Tests for the desktop GUI kwarg assembly (no display required)."""

from __future__ import annotations

import pytest

gui = pytest.importorskip("prisma_s.gui")


@pytest.fixture()
def base_state(tmp_path):
    (tmp_path / "corpus").mkdir()
    return {
        "source_mode": "folder",
        "source_path": str(tmp_path / "corpus"),
        "drive_url": "",
        "drive_credentials": "",
        "output_dir": str(tmp_path),
        "batch_id": "batch_01",
        "dict_mode": "v13",
        "custom_dict_path": "",
        "figures": True,
        "citation": True,
        "ocr": True,
        "ocr_lang": "eng",
    }


def test_defaults_map_to_run_analysis(base_state, tmp_path):
    k = gui.build_run_kwargs(base_state)
    assert k["batch_id"] == "batch_01"
    assert k["output_xlsx"] == str(tmp_path / "batch_01_results.xlsx")
    assert k["keyword_csv"] is None  # bundled v1.3
    assert k["input_path"] == base_state["source_path"]
    assert k["figures"] is True and k["enable_ocr"] is True
    assert k["emit_citation"] is True and k["ocr_lang"] == "eng"


def test_dictionary_radio_maps(base_state):
    assert gui.build_run_kwargs({**base_state, "dict_mode": "v11"})["keyword_csv"] == "bundled:1.1"


def test_custom_dictionary_requires_file(base_state, tmp_path):
    with pytest.raises(ValueError):
        gui.build_run_kwargs({**base_state, "dict_mode": "custom", "custom_dict_path": ""})
    csv = tmp_path / "d.csv"
    csv.write_text("group,term\nA,x\n", encoding="utf-8")
    k = gui.build_run_kwargs({**base_state, "dict_mode": "custom", "custom_dict_path": str(csv)})
    assert k["keyword_csv"] == str(csv)


def test_batch_id_is_sanitised(base_state, tmp_path):
    k = gui.build_run_kwargs({**base_state, "batch_id": 'Pilot 2026/v2*?'})
    assert k["batch_id"] == "Pilot_2026v2"
    assert k["output_xlsx"] == str(tmp_path / "Pilot_2026v2_results.xlsx")


def test_blank_batch_falls_back(base_state):
    assert gui.build_run_kwargs({**base_state, "batch_id": "   "})["batch_id"] == "batch_01"


def test_drive_source_parses_folder_id(base_state, tmp_path):
    creds = tmp_path / "credentials.json"
    creds.write_text("{}", encoding="utf-8")
    k = gui.build_run_kwargs(
        {
            **base_state,
            "source_mode": "drive",
            "drive_url": "https://drive.google.com/drive/folders/1AbcDEF_xyz",
            "drive_credentials": str(creds),
        }
    )
    assert k["drive_folder_id"] == "1AbcDEF_xyz"
    assert k["drive_credentials"] == str(creds)
    assert "input_path" not in k


def test_missing_output_dir_raises(base_state):
    with pytest.raises(ValueError):
        gui.build_run_kwargs({**base_state, "output_dir": ""})


def test_missing_corpus_raises(base_state):
    with pytest.raises(ValueError):
        gui.build_run_kwargs({**base_state, "source_path": "/no/such/path"})


def test_toggles_thread_through(base_state):
    k = gui.build_run_kwargs(
        {**base_state, "figures": False, "citation": False, "ocr": False, "ocr_lang": ""}
    )
    assert k["figures"] is False and k["emit_citation"] is False
    assert k["enable_ocr"] is False and k["ocr_lang"] == "eng"  # blank -> default

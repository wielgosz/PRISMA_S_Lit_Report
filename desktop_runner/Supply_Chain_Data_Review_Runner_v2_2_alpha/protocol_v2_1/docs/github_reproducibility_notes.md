# GitHub reproducibility notes

This package is designed to be committed to GitHub without raw PDFs. Store large source PDFs in an external artifact store or local `data/raw_pdfs/` folder excluded by `.gitignore`.

To reproduce the milestone exactly, use the reference outputs under `outputs/reference_milestone/`. To rerun from source, provide the raw PDFs or extracted text corresponding to `examples/current_milestone/vetted_corpus_metadata_2026-05-13.csv`.

Recommended branch workflow:

1. Commit this package as `protocol-v1.4-milestone`.
2. Add local PDFs under `data/raw_pdfs/` but do not commit them.
3. Run extraction and protocols locally.
4. Commit only config changes, code changes, schemas, and small summary outputs.
5. Use GitHub Releases or external storage for large output workbooks if needed.


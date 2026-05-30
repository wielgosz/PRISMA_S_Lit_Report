# Supply Chain Data Review Protocol v2.2 Desktop Runner

This package is a Tkinter + PyInstaller Windows desktop runner for the
Supply Chain Data Review Protocol. It uses the v2.1 protocol package as the
backend engine and an Excel input workbook as the editable source of truth.

## User workflow

1. Open `templates/Supply_Chain_Data_Review_Input_Template_v2_2.xlsx`.
2. Edit the tabs:
   - `A1_Organizations`
   - `B1_Corpus_Documents`
   - `Dictionary`
   - `Run_Settings`
   - `Exclusions_Duplicates`
   - optionally `New_Documents`
3. Place PDF files and/or ZIP batches in a corpus folder.
4. Launch the desktop app.
5. Select the input workbook, PDF corpus folder, and output folder.
6. Click **Validate only** or **Run protocol**.

The runner creates a date-stamped folder containing the validated input copy,
validation log, protocol outputs, CSVs, SVGs, frozen text files, logs, and a
run manifest.

## Build on Windows

From this folder:

```bat
build_windows.bat
```

The executable folder will be created under:

```text
dist\SupplyChainDataReviewRunner    ```

This alpha build uses PyInstaller `--onedir` because it is more reliable for
pandas, openpyxl, matplotlib, and PDF extraction dependencies than `--onefile`.

## Command-line run

```bash
python -m protocol_engine.run_protocol ^
  --input-workbook templates/Supply_Chain_Data_Review_Input_Template_v2_2.xlsx ^
  --pdf-folder path/to/pdf_folder ^
  --output-folder path/to/outputs
```

## Notes

- The executable dictionary is the `Dictionary` tab.
- Matching rule remains exact case-insensitive regex with alphanumeric boundaries.
- Figure outputs use `reports_referencing`; Figure 1 excludes AOI terms.
- The v2.1 backend is stored in `protocol_v2_1/`.

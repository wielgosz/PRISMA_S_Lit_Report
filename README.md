# PRISMA-S / Supply Chain Data Review Protocol Update

This update package adds the **Supply Chain Data Review Protocol v2.1** and the
**Supply Chain Data Review Desktop Runner v2.2-alpha** for Windows desktop use.


## Contents

```text
protocols/
  supply_chain_data_review_protocol_v2_1/
    README.md
    CHANGELOG.md
    MANIFEST.yml
    config/
    docs/
    scripts/
    schemas/
    outputs/v2_1_reference_outputs/

desktop_runner/
  Supply_Chain_Data_Review_Runner_v2_2_alpha/
    README.md
    app.py
    build_windows.bat
    templates/Supply_Chain_Data_Review_Input_Template_v2_2.xlsx
    protocol_engine/
    protocol_v2_1/
```

## Protocol v2.1 summary

Protocol v2.1 consolidates the May 2026 revisions to the Supply Chain Data
Review workflow:

- v1.3 exact keyword-counting rule retained: exact, case-insensitive regex
  matching with alphanumeric boundaries; variants rolled up to canonical terms.
- Frozen extracted-text workflow retained for reproducible keyword counts.
- v1.4 dataset-reference extraction / canonicalization / crosswalk workflow
  retained.
- v2.1 output revisions added:
  - v1.3-style tabular reference workbook;
  - canonical SVG outputs only;
  - SVG figures use `reports_referencing` rather than raw occurrence totals;
  - Figure 1 excludes AOI terms and is limited to jurisdictional / landscape
    terms;
  - APA references added for the RTRS and ECF corpus additions.

## Desktop Runner v2.2-alpha availability

The desktop runner is available under:

```text
desktop_runner/Supply_Chain_Data_Review_Runner_v2_2_alpha/
```

It is a Tkinter + PyInstaller `onedir` runner that uses the v2.1 protocol
package as its backend engine and an Excel input workbook as the editable source
of truth.

The editable input workbook is:

```text
desktop_runner/Supply_Chain_Data_Review_Runner_v2_2_alpha/templates/Supply_Chain_Data_Review_Input_Template_v2_2.xlsx
```

The input workbook contains:

- `README`
- `A1_Organizations`
- `B1_Corpus_Documents`
- `Dictionary`
- `Run_Settings`
- `Exclusions_Duplicates`
- `New_Documents`
- `Validation_Log`

The runner allows users to select:

1. the Excel input workbook;
2. a folder containing PDFs and/or batch ZIPs;
3. an output folder.

It then validates the workbook and can run the protocol to generate a
date-stamped output folder with Excel, SVG, CSV, QA, frozen-text, log, and
manifest outputs.

## Build the Windows desktop runner

On a Windows machine with Python installed:

```bat
cd desktop_runner\Supply_Chain_Data_Review_Runner_v2_2_alpha
python -m pip install -r requirements.txt
build_windows.bat
```

The PyInstaller `onedir` executable folder will be created under:

```text
dist\SupplyChainDataReviewRunner\
```

## Suggested repository commit message

```text
Add Supply Chain Data Review Protocol v2.1 and Desktop Runner v2.2-alpha

Includes:
- protocol v2.1 engine and reference outputs
- frozen-text keyword workflow with v1.3 matching rule
- v1.4 dataset crosswalk workflow
- v1.3-style tabular reference workbook
- corrected canonical SVG figure contract
- APA updates for RTRS and ECF corpus additions
- Tkinter/PyInstaller Windows desktop runner alpha
- Excel input template as editable source of truth
```

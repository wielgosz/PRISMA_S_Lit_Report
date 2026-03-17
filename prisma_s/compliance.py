"""
PRISMA-S compliance reporting module.

PRISMA-S (Preferred Reporting Items for Systematic Reviews and Meta-Analyses
— Search extension) is a 16-item checklist for transparent reporting of
literature searches in systematic reviews.

Reference
---------
Rethlefsen ML, Kirtley S, Waffenschmidt S, et al.
"PRISMA-S: an extension to the PRISMA Statement for Reporting Literature
Searches in Systematic Reviews."
Systematic Reviews 10, 39 (2021). https://doi.org/10.1186/s13643-020-01542-z

Checklist landing page: https://www.prisma-statement.org/prisma-search

About this module
-----------------
This tool performs full-text keyword searching on a *pre-collected corpus* of
documents (PDFs and DOCX files).  It is therefore a corpus-analysis tool
rather than a primary database-search tool.  Consequently some PRISMA-S items
are directly applicable, some are partially applicable, and some fall outside
scope.

The ``build_compliance_report()`` function returns a DataFrame that is written
as a second sheet ("PRISMA-S Compliance") in every output workbook, making the
methodological status of each item transparent to readers and replicators.

Status values
-------------
APPLIED         — the tool addresses this item and the information is captured
                  in the output.
PARTIAL         — the item is relevant but only partially addressed; the note
                  explains what is missing and how a user could supplement it.
NOT_APPLICABLE  — the item concerns primary database searching and does not
                  apply to a corpus that is already assembled.
NOT_APPLIED     — the item is within scope but was not implemented in this run;
                  the note explains what would be needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

Status = Literal["APPLIED", "PARTIAL", "NOT_APPLICABLE", "NOT_APPLIED"]


@dataclass
class PrismaSItem:
    """One PRISMA-S checklist item.

    Attributes
    ----------
    number : int
        Item number in the published checklist (1–16).
    label : str
        Short label as used in the published checklist.
    description : str
        Plain-language description of what the item requires.
    scope_note : str
        Explanation of how this item relates to corpus-analysis use.
    default_status : Status
        Default compliance status when using this tool.
    runtime_notes : str
        Populated at runtime with specifics from the current run.
    """
    number: int
    label: str
    description: str
    scope_note: str
    default_status: Status
    runtime_notes: str = field(default="", repr=False)


# ---------------------------------------------------------------------------
# The 16 PRISMA-S items with corpus-analysis scope notes
# ---------------------------------------------------------------------------

PRISMA_S_ITEMS: list[PrismaSItem] = [
    PrismaSItem(
        number=1,
        label="Databases",
        description=(
            "Name each individual database searched, stating the full name, "
            "abbreviated name if applicable, and the host platform."
        ),
        scope_note=(
            "In a corpus analysis the 'database' is the folder of collected documents. "
            "The source reference (local path or Google Drive folder ID) is recorded in "
            "every output row and in the run metadata sheet."
        ),
        default_status="PARTIAL",
    ),
    PrismaSItem(
        number=2,
        label="Legacy/supplementary databases",
        description=(
            "Report use of any legacy databases or database aggregators, "
            "or supplementary non-database methods."
        ),
        scope_note=(
            "Not applicable to corpus analysis of a pre-assembled document set. "
            "If grey-literature or supplementary sources were included in the "
            "corpus, document them manually in the batch identifier or a "
            "companion methods note."
        ),
        default_status="NOT_APPLICABLE",
    ),
    PrismaSItem(
        number=3,
        label="Date of search",
        description="Report the date each search was run.",
        scope_note=(
            "The ISO-8601 UTC timestamp of every analysis run is captured in the "
            "'Run UTC' column of the output, satisfying this item."
        ),
        default_status="APPLIED",
    ),
    PrismaSItem(
        number=4,
        label="Dates of coverage",
        description=(
            "Specify the date range that the database covers or was searched, "
            "including any date restrictions applied."
        ),
        scope_note=(
            "Publication years are extracted from document metadata and reported "
            "in the 'Year' column.  The user should document any date restriction "
            "applied to corpus assembly separately (e.g. in the batch label)."
        ),
        default_status="PARTIAL",
    ),
    PrismaSItem(
        number=5,
        label="Full search strategy",
        description=(
            "Present the full, exact search strategy used for at least one database, "
            "including all search terms, operators, and limits."
        ),
        scope_note=(
            "The complete keyword list (all terms, groups, and the regex matching "
            "rules) is recorded in the versioned keyword dictionary CSV and protocol "
            "document that are committed alongside the code. The 'Keyword Dict "
            "Version' and 'Protocol Version' columns in the output point to the "
            "exact files."
        ),
        default_status="APPLIED",
    ),
    PrismaSItem(
        number=6,
        label="Search limits/restrictions",
        description=(
            "Report any search limits or restrictions (language, date, "
            "publication type, etc.)."
        ),
        scope_note=(
            "The current implementation applies no language, date, or type filters "
            "to the full-text search itself.  If the corpus was assembled with "
            "restrictions (e.g. English-only, post-2010), these must be documented "
            "externally by the user."
        ),
        default_status="PARTIAL",
    ),
    PrismaSItem(
        number=7,
        label="Search filters",
        description=(
            "Describe any search filters used (e.g. validated filters for "
            "study design)."
        ),
        scope_note=(
            "No study-design or methodology filters are applied.  All documents "
            "in the source folder are searched without exclusion.  This is "
            "intentional for full-corpus coverage."
        ),
        default_status="NOT_APPLIED",
    ),
    PrismaSItem(
        number=8,
        label="Within-database deduplication",
        description=(
            "Describe the deduplication process used within a single database."
        ),
        scope_note=(
            "Each file in the source folder is processed exactly once.  "
            "Duplicate filenames within the same folder are prevented by the "
            "file system; however the tool does not detect semantically duplicate "
            "documents with different filenames."
        ),
        default_status="PARTIAL",
    ),
    PrismaSItem(
        number=9,
        label="Multi-database deduplication",
        description=(
            "Describe the process used to deduplicate records across databases."
        ),
        scope_note=(
            "Not applicable unless multiple source folders are combined into one "
            "corpus.  If batches from multiple sources are merged, deduplication "
            "must be performed before or after the analysis and documented by "
            "the user."
        ),
        default_status="NOT_APPLICABLE",
    ),
    PrismaSItem(
        number=10,
        label="Search updates",
        description=(
            "Report whether the search was updated after the original search "
            "was conducted."
        ),
        scope_note=(
            "The batch labelling system supports incremental runs.  Each run "
            "records its own timestamp and source reference.  Users should use "
            "distinct batch IDs for update runs and document the relationship "
            "between batches."
        ),
        default_status="PARTIAL",
    ),
    PrismaSItem(
        number=11,
        label="Peer review of search",
        description=(
            "Report whether the search strategy was peer reviewed before execution, "
            "e.g. by a second information specialist."
        ),
        scope_note=(
            "The keyword dictionary and protocol document are version-controlled "
            "and publicly available for peer review.  Formal peer review of the "
            "search strategy by a second researcher is not enforced by the tool "
            "and must be documented externally."
        ),
        default_status="NOT_APPLIED",
    ),
    PrismaSItem(
        number=12,
        label="Translation of search strategies",
        description=(
            "Describe how search strategies were translated across databases "
            "with different syntaxes."
        ),
        scope_note=(
            "Not applicable.  The tool applies a single unified regex-based "
            "matching protocol to all documents regardless of source."
        ),
        default_status="NOT_APPLICABLE",
    ),
    PrismaSItem(
        number=13,
        label="Forward and backward citation searching",
        description=(
            "Report whether forward citation searching (citing articles) or "
            "backward citation searching (reference lists) was performed."
        ),
        scope_note=(
            "Citation searching is outside scope for this tool.  If citation "
            "searching was used to assemble the corpus, document it separately."
        ),
        default_status="NOT_APPLICABLE",
    ),
    PrismaSItem(
        number=14,
        label="Grey literature and other sources",
        description=(
            "Report search methods for grey literature and other non-database "
            "sources (websites, trial registries, etc.)."
        ),
        scope_note=(
            "The tool accepts any PDF or DOCX file, including grey literature. "
            "Whether grey literature was included in the corpus depends on how "
            "the source folder was assembled, and must be documented by the user."
        ),
        default_status="PARTIAL",
    ),
    PrismaSItem(
        number=15,
        label="Multi-lingual searches",
        description=(
            "Report whether searches were conducted in languages other than English."
        ),
        scope_note=(
            "The current keyword dictionary (v1.1) contains English-only terms. "
            "The regex engine is Unicode-safe and can match non-ASCII terms if "
            "a multi-lingual keyword dictionary is supplied.  Document language "
            "scope in the keyword dictionary version notes."
        ),
        default_status="PARTIAL",
    ),
    PrismaSItem(
        number=16,
        label="Search results",
        description=(
            "Report the total number of results retrieved from each database "
            "or source."
        ),
        scope_note=(
            "The run metadata sheet records total documents processed and total "
            "non-zero term matches per document, satisfying this item for "
            "corpus-analysis purposes."
        ),
        default_status="APPLIED",
    ),
]


# ---------------------------------------------------------------------------
# Runtime compliance builder
# ---------------------------------------------------------------------------

def build_compliance_report(
    *,
    source_ref: str,
    batch_id: str,
    keyword_dict_version: str,
    protocol_version: str,
    run_utc: str,
    n_documents: int,
    n_terms: int,
    extra_notes: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Build a PRISMA-S compliance DataFrame for inclusion in the output workbook.

    Each row corresponds to one of the 16 PRISMA-S checklist items.  Runtime
    information (source, keyword version, document count, etc.) is injected
    into the 'Runtime Notes' column.

    Parameters
    ----------
    source_ref:
        The document source used in this run (local path or gdrive:FOLDER_ID).
    batch_id:
        The batch label for this run.
    keyword_dict_version:
        Version string of the keyword dictionary CSV used.
    protocol_version:
        Protocol version applied.
    run_utc:
        ISO-8601 timestamp of the run.
    n_documents:
        Number of documents processed.
    n_terms:
        Number of unique terms searched.
    extra_notes:
        Optional dict mapping PRISMA-S item number → additional note string,
        allowing callers to inject run-specific context (e.g. date restrictions).

    Returns
    -------
    pd.DataFrame
        Columns: Item No., Label, Description, Status, Scope Note, Runtime Notes
    """
    extra_notes = extra_notes or {}

    # Build runtime notes for items where we have concrete run data
    auto_notes: dict[int, str] = {
        1: f"Source: {source_ref}",
        3: f"Run UTC: {run_utc}",
        5: (
            f"Keyword dict v{keyword_dict_version} | "
            f"Protocol v{protocol_version} | "
            f"{n_terms} terms searched."
        ),
        8: f"{n_documents} documents processed; each processed once.",
        16: f"{n_documents} documents in corpus; {n_terms} terms applied.",
    }

    rows = []
    for item in PRISMA_S_ITEMS:
        notes_parts = []
        if item.number in auto_notes:
            notes_parts.append(auto_notes[item.number])
        if item.number in extra_notes:
            notes_parts.append(extra_notes[item.number])
        rows.append({
            "Item No.": item.number,
            "Label": item.label,
            "Description": item.description,
            "Status": item.default_status,
            "Scope Note": item.scope_note,
            "Runtime Notes": "  |  ".join(notes_parts) if notes_parts else "",
        })

    return pd.DataFrame(rows)

# Third-Party Notices

This file inventories third-party software and data used by
`prisma-s-lit-review`. Inclusion here does not replace the original licence
terms. Machine-readable detail is in [`DEPENDENCY_LICENSES.csv`](DEPENDENCY_LICENSES.csv)
and [`DATA_PROVENANCE.csv`](DATA_PROVENANCE.csv).

## Runtime dependencies

Every runtime dependency is permissively licensed (no copyleft, no network
copyleft). PyMuPDF (AGPL-3.0) was removed in v1.6.0.

| Component | Source | Licence | How used |
|---|---|---|---|
| pandas | https://github.com/pandas-dev/pandas | BSD-3-Clause | dataframes, Excel output |
| openpyxl | https://foss.heptapod.net/openpyxl/openpyxl | MIT | `.xlsx` writer |
| pypdf | https://github.com/py-pdf/pypdf | BSD-3-Clause | PDF text-layer extraction |
| python-docx | https://github.com/python-openxml/python-docx | MIT | DOCX text extraction |
| matplotlib | https://github.com/matplotlib/matplotlib | Matplotlib licence (BSD-style, PSF-based) | term-frequency figures (Agg backend) |
| google-api-python-client | https://github.com/googleapis/google-api-python-client | Apache-2.0 | optional Google Drive ingestion |
| google-auth-httplib2 | https://github.com/googleapis/google-auth-library-python-httplib2 | Apache-2.0 | Google Drive OAuth transport |
| google-auth-oauthlib | https://github.com/googleapis/google-auth-library-python-oauthlib | Apache-2.0 | Google Drive OAuth flow |

## Development-only dependencies

| Component | Licence |
|---|---|
| pytest, pytest-cov | MIT |
| reportlab | BSD-3-Clause (test fixtures generate sample PDFs) |
| pyinstaller *(desktop build only)* | GPL-2.0-or-later **with a bundling exception** — the exception permits distributing the frozen application under the application's own licence; PyInstaller itself is not redistributed |

## WRI-derived inputs

The keyword taxonomy and protocol text bundled in `prisma_s/data/` are **adapted
from** a World Resources Institute publication (see `DATA_PROVENANCE.csv` and
`prisma_s/data/DATA_LICENSE.md`):

> Wielgosz, B., dos Santos, A. B., Carter, S., Berger, A., Schneider, M.,
> Despontin, M., Immelman, J., Richter, J., Couto, A., Fitts, L. A., Gao, Y., &
> Dionizio, E. (in press). *Data for deforestation- and conversion-free (DCF)
> supply chain analyses: Applied learnings from soy in Brazil (Guidebook).*
> World Resources Institute.

WRI's standard licences are CC BY 4.0 for data/publications and MIT for code
([Open Data Commitment](https://www.wri.org/data/open-data-commitment)). Its
[Permissions & Licensing](https://www.wri.org/research/permissions-licensing)
policy notes that **co-authored** publications are frequently marked "All Rights
Reserved". **The guidebook's own licence is therefore treated as PENDING** until
its published landing page states one; if it is not CC BY, a WRI permissions
request is required before redistributing the derived files. See
`IP_HARDENING_PLAN.md` (portfolio).

Attribution requirement when the guidebook is CC BY: credit the work as shown on
its wri.org page, link back to that page, and state that modifications were made.

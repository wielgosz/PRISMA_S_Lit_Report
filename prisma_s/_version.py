"""Single source of truth for version strings.

Kept dependency-free so that ``pyproject.toml``'s
``[tool.setuptools.dynamic] version = {attr = "prisma_s._version.__version__"}``
can resolve it by static analysis without importing the package (which would
pull in pandas at build time).
"""

__version__ = "1.6.0"

# Version of the locked keyword-matching protocol spec shipped in
# ``prisma_s/data/PRISMA_keyword_protocol_v*.md``.  Stamped into every output row.
PROTOCOL_VERSION = "1.1"

"""
Google Drive ingestion module.

Downloads PDFs and DOCX files from a specified Drive folder to a
local temporary directory for processing. Authentication uses OAuth 2.0
with a credentials.json obtained from Google Cloud Console.

First-time use opens a browser window for consent; subsequent runs load
the cached token from ``token_path`` (default: ``token.json``).

Public API
----------
parse_folder_id(url_or_id)
    Extract the folder ID from a Drive URL or return the raw ID unchanged.
    Accepts any of these formats:
        https://drive.google.com/drive/folders/FOLDER_ID
        https://drive.google.com/drive/u/0/folders/FOLDER_ID
        FOLDER_ID  (bare ID, returned as-is)

list_folder_files(service, folder_id)
    Return file metadata for all PDFs and DOCX files in the folder.

download_folder(folder_id, credentials_path, token_path)
    Full pipeline: authenticate → list → download → return local paths.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# MIME types we can process and their local file extensions
SUPPORTED_MIME: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


def parse_folder_id(url_or_id: str) -> str:
    """Extract a Google Drive folder ID from a URL or return the bare ID.

    Supported URL formats
    ---------------------
    - https://drive.google.com/drive/folders/FOLDER_ID
    - https://drive.google.com/drive/u/0/folders/FOLDER_ID
    - https://drive.google.com/drive/u/1/folders/FOLDER_ID?...
    - bare folder ID string (returned unchanged)

    Parameters
    ----------
    url_or_id:
        A Drive folder URL pasted from the browser address bar, or a raw
        folder ID string.

    Returns
    -------
    str
        The folder ID component only.

    Examples
    --------
    >>> parse_folder_id("https://drive.google.com/drive/folders/1Abc123XYZ")
    '1Abc123XYZ'
    >>> parse_folder_id("1Abc123XYZ")
    '1Abc123XYZ'
    """
    m = re.search(r"/folders/([a-zA-Z0-9_-]+)", url_or_id)
    return m.group(1) if m else url_or_id.strip()


def _authenticate(credentials_path: str | Path, token_path: str | Path):
    """Return an authorised Google API credentials object."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    token_path = str(token_path)
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as fh:
            fh.write(creds.to_json())

    return creds


def _build_service(credentials_path: str | Path, token_path: str | Path = "token.json"):
    from googleapiclient.discovery import build
    creds = _authenticate(credentials_path, token_path)
    return build("drive", "v3", credentials=creds)


def list_folder_files(service, folder_id: str) -> list[dict]:
    """Return metadata for all supported files in *folder_id* (non-recursive)."""
    mime_filter = " or ".join(f"mimeType='{m}'" for m in SUPPORTED_MIME)
    query = f"'{folder_id}' in parents and ({mime_filter}) and trashed=false"

    files: list[dict] = []
    page_token = None
    while True:
        resp = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def _download_file(service, file_id: str, filename: str, mime_type: str, dest_dir: Path) -> Path:
    from googleapiclient.http import MediaIoBaseDownload

    ext = SUPPORTED_MIME.get(mime_type, "")
    dest = dest_dir / (Path(filename).stem + ext)

    request = service.files().get_media(fileId=file_id)
    with open(dest, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest


def download_folder(
    folder_id: str,
    credentials_path: str | Path,
    token_path: str | Path = "token.json",
) -> tuple[list[Path], Path]:
    """Download all supported files from a Drive folder to a temp directory.

    Parameters
    ----------
    folder_id:
        Google Drive folder ID (the long alphanumeric string in the folder URL).
    credentials_path:
        Path to your ``credentials.json`` from Google Cloud Console.
    token_path:
        Where to cache the OAuth token between runs (created on first auth).

    Returns
    -------
    local_paths : list[Path]
        Local paths of downloaded files.
    tmp_dir : Path
        Temporary directory holding the downloads.
        **Caller is responsible for deleting this directory** when done
        (``runner.run_analysis`` handles this automatically).
    """
    service = _build_service(credentials_path, token_path)
    files = list_folder_files(service, folder_id)

    tmp = Path(tempfile.mkdtemp(prefix="prisma_s_drive_"))
    local_paths: list[Path] = []
    for f in files:
        path = _download_file(service, f["id"], f["name"], f["mimeType"], tmp)
        local_paths.append(path)
        print(f"  Downloaded: {f['name']}")

    return local_paths, tmp

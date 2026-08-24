"""Fetch a Google Doc as raw Docs API JSON.

We deliberately use `documents.get` rather than Drive's HTML export.
The export is `<span class="c12">` soup with no semantics; the API JSON
gives us real named paragraph styles, first-class `footnotes` objects,
and `inlineObjects` for images.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

CLIENT_SECRETS = Path(
    os.environ.get("ETA_CLIENT_SECRETS", Path.home() / ".config/eta-publish/client_secret.json")
)
TOKEN_PATH = Path(
    os.environ.get("ETA_TOKEN", Path.home() / ".config/eta-publish/token.json")
)


def _credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
        creds = flow.run_local_server(port=0)
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())
    return creds


def doc_id_from(ref: str) -> str:
    """Accept either a bare document id or any Google Docs URL."""
    if "docs.google.com" not in ref:
        return ref
    parts = ref.split("/d/", 1)[1]
    return parts.split("/", 1)[0]


def fetch(ref: str) -> dict:
    from googleapiclient.discovery import build

    service = build("docs", "v1", credentials=_credentials())
    return service.documents().get(documentId=doc_id_from(ref)).execute()


def fetch_to(ref: str, dest: Path) -> dict:
    doc = fetch(ref)
    dest.write_text(json.dumps(doc, indent=2))
    return doc

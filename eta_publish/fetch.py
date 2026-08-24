"""Fetch a Google Doc as raw Docs API JSON.

We use the Docs API (`documents.get`) rather than Drive's HTML export.
The export is `<span class="c12">` soup with no semantics; the API JSON
carries real named paragraph styles, first-class `footnotes`, and
`inlineObjects`.

Tabs are the subtle part. ETA reports live in multi-tab documents, and by
default `documents.get` fills `document.body` from the *first tab only* and
leaves `document.tabs` empty. A report drafted in the third tab would
therefore parse silently and produce a plausible, wrong document. So we
always request `includeTabsContent` and select a tab explicitly, honoring
the `?tab=` id in the URL that was handed to us.

Suggestions matter for the same reason. The API's default,
`DEFAULT_FOR_CURRENT_ACCESS`, resolves to `SUGGESTIONS_INLINE` for anyone
with edit access, which mixes suggested text into the content as though it
were part of the document. ETA reports are drafted with suggestions open,
so we ask for `PREVIEW_WITHOUT_SUGGESTIONS`: what the report says with
every open suggestion rejected, which is what the doc reads as today.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .docs_json import JsonObject

SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

# Rejecting is the safe default: it publishes what the document currently
# says, rather than silently adopting whatever anyone has proposed.
SUGGESTIONS = {
    "rejected": "PREVIEW_WITHOUT_SUGGESTIONS",
    "accepted": "PREVIEW_SUGGESTIONS_ACCEPTED",
}

CLIENT_SECRETS = Path(
    os.environ.get("ETA_CLIENT_SECRETS", Path.home() / ".config/eta-publish/client_secret.json")
)
TOKEN_PATH = Path(os.environ.get("ETA_TOKEN", Path.home() / ".config/eta-publish/token.json"))


class TabNotFound(LookupError):
    pass


class FetchFailed(RuntimeError):
    """A Docs API request failed for a reason the user can act on."""


def _explain(error: object) -> str:
    """Turn a Google API error into something with a next step in it.

    `HttpError`'s own string is a wall of JSON with the useful sentence
    buried in it, and the two failures worth naming here both have a
    specific fix rather than a general one.
    """
    from googleapiclient.errors import HttpError

    if not isinstance(error, HttpError):
        return str(error)

    status = error.status_code
    reason = ""
    details = getattr(error, "error_details", None) or []
    for detail in details:
        if isinstance(detail, dict) and detail.get("reason"):
            reason = str(detail["reason"])
            break

    if reason == "SERVICE_DISABLED":
        project = ""
        for detail in details:
            if isinstance(detail, dict):
                project = str(detail.get("metadata", {}).get("consumer", "")).split("/")[-1]
                if project:
                    break
        return (
            "the Google Docs API is not enabled for this OAuth project.\n"
            "Enable it at https://console.cloud.google.com/apis/api/"
            f"docs.googleapis.com/overview?project={project}\n"
            "then wait a minute for it to propagate and try again."
        )
    if status == 403:
        return (
            "access denied by the Docs API. Either the account you authorized "
            "cannot open this document, or the API is not enabled for the "
            f"OAuth project.\n{error.reason}"
        )
    if status == 404:
        return "no such document, or the account you authorized cannot open it."
    if status == 429:
        return "rate limited by the Docs API; wait a minute and try again."
    return f"the Docs API returned {status}: {error.reason}"


def parse_ref(ref: str) -> tuple[str, str | None]:
    """Split a Docs URL into its document id and its `?tab=` id, if any.

    A bare document id is accepted unchanged.
    """
    if "docs.google.com" not in ref:
        return ref, None
    url = urlparse(ref)
    doc_id = url.path.split("/d/", 1)[1].split("/", 1)[0]
    tab_id = parse_qs(url.query).get("tab", [None])[0]
    return doc_id, tab_id


# ---- tabs ----------------------------------------------------------


def iter_tabs(tabs: list[JsonObject], depth: int = 0):
    """Yield `(depth, tab)` for every tab, descending into child tabs."""
    for tab in tabs:
        yield depth, tab
        yield from iter_tabs(tab.get("childTabs", []), depth + 1)


def tab_title(tab: JsonObject) -> str:
    return tab.get("tabProperties", {}).get("title", "(untitled)")


def tab_id(tab: JsonObject) -> str:
    return tab.get("tabProperties", {}).get("tabId", "")


def describe_tabs(document: JsonObject) -> str:
    return "\n".join(
        f"  {'  ' * depth}{tab_id(tab)}  {tab_title(tab)}"
        for depth, tab in iter_tabs(document.get("tabs", []))
    )


def select_tab(document: JsonObject, wanted: str | None) -> JsonObject:
    """Return one tab's content, shaped like a single-tab document.

    The parser only ever sees `body`, `footnotes`, `inlineObjects`, and
    `lists`, so a tab and a document are interchangeable to it.
    """
    tabs = list(iter_tabs(document.get("tabs", [])))
    if not tabs:
        # A document with no tabs at all still populates `body` directly.
        return document

    if wanted is None:
        if len(tabs) > 1:
            raise TabNotFound(
                f"this document has {len(tabs)} tabs; name one with `--tab`, "
                f"or pass the URL including its `?tab=` id:\n{describe_tabs(document)}"
            )
        chosen = tabs[0][1]
    else:
        matches = [tab for _, tab in tabs if tab_id(tab) == wanted]
        if not matches:
            raise TabNotFound(
                f"no tab {wanted!r} in this document; available tabs:\n{describe_tabs(document)}"
            )
        chosen = matches[0]

    content = chosen.get("documentTab", {})
    return {
        "title": document.get("title", ""),
        "tabId": tab_id(chosen),
        "tabTitle": tab_title(chosen),
        "body": content.get("body", {}),
        "footnotes": content.get("footnotes", {}),
        "inlineObjects": content.get("inlineObjects", {}),
        "lists": content.get("lists", {}),
    }


# ---- api -----------------------------------------------------------


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


def fetch_document(doc_id: str, suggestions: str = "rejected") -> JsonObject:
    """The whole document, every tab included, suggestions resolved."""
    from googleapiclient.discovery import build

    service = build("docs", "v1", credentials=_credentials())
    # `build` returns a `Resource` whose methods are generated at runtime from
    # the API's discovery document, so no static type can know about `documents`.
    documents = service.documents()  # pyrefly: ignore[missing-attribute]
    request = documents.get(
        documentId=doc_id,
        includeTabsContent=True,
        suggestionsViewMode=SUGGESTIONS[suggestions],
    )
    try:
        return request.execute()
    except Exception as e:  # noqa: BLE001
        raise FetchFailed(_explain(e)) from e


def fetch(ref: str, tab: str | None = None, suggestions: str = "rejected") -> JsonObject:
    doc_id, url_tab = parse_ref(ref)
    return select_tab(fetch_document(doc_id, suggestions), tab or url_tab)


def fetch_to(
    ref: str, dest: Path, tab: str | None = None, suggestions: str = "rejected"
) -> JsonObject:
    """Fetch and save the selected tab, so later runs need no credentials."""
    document = fetch(ref, tab, suggestions)
    dest.write_text(json.dumps(document, indent=2))
    return document

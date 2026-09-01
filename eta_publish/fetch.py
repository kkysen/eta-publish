"""Fetch a Google Doc as raw Docs API JSON.

The Docs API rather than Drive's HTML export:
the export is `<span class="c12">` soup with no semantics,
where the API JSON carries real named paragraph styles,
first-class `footnotes`, and `inlineObjects`.

Tabs are the subtle part.
ETA reports live in multi-tab documents,
and by default `documents.get` fills `document.body` from the *first tab only*
and leaves `document.tabs` empty,
so a report drafted in the third tab parses silently into a plausible, wrong document.
So we always request `includeTabsContent` and select a tab explicitly,
honoring the `?tab=` id in the URL handed to us.

Suggestions matter for the same reason.
The default, `DEFAULT_FOR_CURRENT_ACCESS`,
resolves to `SUGGESTIONS_INLINE` for anyone with edit access,
mixing suggested text into the content as though it were part of the document.
ETA reports are drafted with suggestions open,
so we ask for `PREVIEW_WITHOUT_SUGGESTIONS`: what the doc reads as today.
"""

import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .docs_json import JsonObject

SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    # Charts are linked as Drive files rather than embedded:
    # Docs cannot place an SVG, so the vector lives in Drive and a raster stands in.
    # Downloading it needs Drive read access, which is broader than we would like,
    # but Drive offers nothing narrower for a file this application did not create.
    "https://www.googleapis.com/auth/drive.readonly",
]

# Rejecting is the safe default: it publishes what the document currently says,
# rather than silently adopting whatever anyone has proposed.
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

    `HttpError`'s own string is a wall of JSON with the useful sentence buried in it,
    and the failures worth naming here have a specific fix.
    """
    from googleapiclient.errors import HttpError

    if not isinstance(error, HttpError):
        return str(error)

    details = [d for d in (getattr(error, "error_details", None) or []) if isinstance(d, dict)]
    reasons = {str(d.get("reason", "")) for d in details}
    messages = [str(d.get("message", "")) for d in details if d.get("message")]

    # An API not switched on for the project:
    # `SERVICE_DISABLED` from Docs, `accessNotConfigured` from Drive.
    # Both put the console URL in the message, so pass Google's own wording along.
    if reasons & {"SERVICE_DISABLED", "accessNotConfigured"}:
        enable = next((m for m in messages if "has not been used in project" in m), "")
        return enable or "an API this needs is not enabled for the OAuth project."

    status = error.status_code
    if status == 403:
        if "insufficient" in " ".join(messages).lower() or "ACCESS_TOKEN_SCOPE" in str(error):
            return (
                "the saved authorization does not cover this. "
                f"Delete {TOKEN_PATH} and run again to grant it."
            )
        return (
            "access denied. Either the account you authorized cannot open this, "
            f"or an API is not enabled for the OAuth project.\n{error.reason}"
        )
    if status == 404:
        return "not found, or the account you authorized cannot open it."
    if status == 429:
        return "rate limited by the API; wait a minute and try again."
    return f"the API returned {status}: {error.reason}"


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

    The parser only sees `body`, `footnotes`, `inlineObjects`, and `lists`,
    so a tab and a document are interchangeable to it.
    """
    tabs = list(iter_tabs(document.get("tabs", [])))
    if not tabs:
        # A document with no tabs at all still populates `body` directly.
        return document

    if wanted is None:
        if len(tabs) > 1:
            raise TabNotFound(
                f"this document has {len(tabs)} tabs; pass the URL including "
                f"the `?tab=` id of the one to publish:\n{describe_tabs(document)}"
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
    """The credentials to call the API with, interactive or not.

    On a person's machine, the installed-app flow: a browser opens once, the token caches.
    Unattended, notably CI, there is no browser to open and no one to click,
    so a service account is used through `google.auth.default`,
    which reads `$GOOGLE_APPLICATION_CREDENTIALS`.

    Application default credentials are checked first,
    because a machine that has them has them deliberately:
    they are set by an environment variable naming a key file, not found by accident.
    """
    ambient = _ambient_credentials()
    if ambient is not None:
        return ambient

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.exists() and _granted_scopes() >= set(SCOPES):
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        from google.auth.exceptions import RefreshError

        try:
            creds.refresh(Request())
        except RefreshError as e:
            # A refresh token that Google has expired or revoked
            # is exactly the case consent has to be given again,
            # so fall through to the flow below rather than failing the build.
            reason = e.args[0] if e.args else e
            print(
                f"the saved sign-in is no longer valid ({reason}); asking for it again",
                file=sys.stderr,
            )
            creds = None
    if not creds or not creds.valid:
        missing = set(SCOPES) - _granted_scopes()
        if TOKEN_PATH.exists() and missing:
            print(
                f"asking for access again, because this now needs {', '.join(sorted(missing))}",
                file=sys.stderr,
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())
    return creds


def _ambient_credentials():
    """Service account credentials, when the environment supplies them.

    `None` when it does not,
    so the interactive flow stays the default for someone running this by hand.

    A service account reaches only what has been shared with it,
    which is why CI can be given one:
    its Drive is empty, so the key grants read access to the report and nothing else.
    """
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return None

    import google.auth
    from google.auth.exceptions import DefaultCredentialsError

    try:
        creds, _ = google.auth.default(scopes=SCOPES)
    except DefaultCredentialsError as e:
        raise FetchFailed(
            "$GOOGLE_APPLICATION_CREDENTIALS is set but the credentials it "
            f"names could not be loaded: {e}"
        ) from e
    return creds


def _granted_scopes() -> set[str]:
    """What the saved token was actually granted.

    From the file rather than from `Credentials`,
    whose `scopes` are whatever was passed to the loader, not what was consented to.
    Adding a scope must trigger a new consent, and the object would always answer yes.
    """
    try:
        return set(json.loads(TOKEN_PATH.read_text()).get("scopes") or ())
    except OSError, ValueError:
        return set()


def fetch_document(doc_id: str, suggestions: str = "rejected") -> JsonObject:
    """The whole document, every tab included, suggestions resolved."""
    from googleapiclient.discovery import build

    service = build("docs", "v1", credentials=_credentials())
    # `build` returns a `Resource` whose methods are generated at runtime
    # from the API's discovery document, so no static type knows about `documents`.
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


def download_drive_file(file_id: str) -> bytes:
    """The raw bytes of a Drive file, for vectors the document links."""
    from googleapiclient.discovery import build

    service = build("drive", "v3", credentials=_credentials())
    files = service.files()  # pyrefly: ignore[missing-attribute]
    try:
        return files.get_media(fileId=file_id).execute()
    except Exception as e:  # noqa: BLE001
        raise FetchFailed(_explain(e)) from e

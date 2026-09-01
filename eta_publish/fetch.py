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
import re
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
    # Not a mode the command line offers: nothing publishes a document
    # with the suggestion marks still in it.
    # It is how they are counted, which is the only way to know there are any.
    "inline": "SUGGESTIONS_INLINE",
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


SUGGESTION_KEYS = (
    "suggestedInsertionIds",
    "suggestedDeletionIds",
    "suggestedTextStyleChanges",
    "suggestedParagraphStyleChanges",
    "suggestedBulletChanges",
    "suggestedPositionedObjectPropertiesChanges",
    "suggestedInlineObjectPropertiesChanges",
)
"""Where a suggestion leaves its id, whatever kind of change it is.

The insertion and deletion keys hold a list of ids;
the rest hold an object keyed by id.
Both are read for their ids and not for what they say,
because the question is how many suggestions are open rather than what they propose.
"""


def open_suggestions(doc_id: str, tab: str | None = None) -> int | None:
    """How many suggestions are still open on `tab`.

    A second request, because the first cannot answer it:
    the build asks for `PREVIEW_WITHOUT_SUGGESTIONS`, which resolves them away
    and leaves nothing behind to count.

    Counted by id rather than by occurrence.
    One suggestion touching a sentence marks every run in it,
    which is 240 insertion marks for a document with far fewer suggestions in it.

    Reading them needs more than reading the document does:
    an account with view access is told it does not have permission,
    which is what CI's service account is.
    That is a question this cannot answer rather than a build that cannot run,
    so it is `None` and the caller keeps whatever the last answer was.
    """
    try:
        document = fetch_document(doc_id, suggestions="inline")
    except FetchFailed:
        return None
    return len(_suggestion_ids(select_tab(document, tab)))


def _suggestion_ids(node: object) -> set[str]:
    """Every suggestion id anywhere under `node`."""
    found: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            if key not in SUGGESTION_KEYS:
                found |= _suggestion_ids(value)
            elif isinstance(value, (list, dict)):
                # A list of ids, or an object keyed by them:
                # iterating either yields the ids, which is all that is wanted.
                found.update(str(i) for i in value)
    elif isinstance(node, list):
        for item in node:
            found |= _suggestion_ids(item)
    return found


EXPORT_ATTEMPTS = 3
"""How many times to ask for a tab's text before giving up on it.

The export answers an ordinary request with a sign-in page often enough
that one failure says nothing about the next.
"""


def open_comments_on_tab(doc_id: str, tab: str | None) -> int | None:
    """How many comment threads are open on `tab`, or `None` if that cannot be read.

    Neither API carries this.
    Drive holds the comments but knows nothing about tabs,
    and its anchors are opaque ids that appear nowhere in the Docs response,
    so there is nothing to join the two on.
    The document's own text export takes a `tab` parameter and lists,
    after the text, the comments left on that tab, which is the answer.

    It is not an API, and it does not always answer:
    often enough it returns a sign-in page instead, with a 200 beside it.
    That page has no comments in it, so a run that took it at its word
    would report a document under review as clean,
    which is worse than reporting nothing. Hence the shape check, the retries,
    and `None` rather than a zero this cannot stand behind.
    """
    from google.auth.transport.requests import AuthorizedSession

    session = AuthorizedSession(_credentials())
    url = f"https://docs.google.com/document/d/{doc_id}/export"
    params = {"format": "txt"}
    if tab:
        params["tab"] = tab

    for _ in range(EXPORT_ATTEMPTS):
        response = session.get(url, params=params, timeout=180)
        text = response.text
        # The export writes a byte order mark and then the document.
        # Anything else is not the document, whatever the status says.
        if response.status_code == 200 and text.startswith("\ufeff"):
            # Each comment on the tab is listed after the text as `[a] what it says`.
            return len(re.findall(r"^\[[a-z]+\]", text, re.MULTILINE))
    return None


def open_comments(doc_id: str) -> int | None:
    """How many comment threads are open on the whole document, every tab of it.

    Drive rather than Docs: the Docs API does not carry comments at all.
    Every page is read, because the count is the point
    and Drive returns them 100 at a time.

    The fallback for when the export will not answer:
    a number that is too large beats no number,
    as long as what it counts is said plainly.
    """
    from googleapiclient.discovery import build

    service = build("drive", "v3", credentials=_credentials())
    comments = service.comments()  # pyrefly: ignore[missing-attribute]
    request = comments.list(fileId=doc_id, fields="comments(resolved),nextPageToken", pageSize=100)
    open_threads = 0
    while request is not None:
        try:
            response = request.execute()
        except Exception:  # noqa: BLE001
            # As with the suggestions: an account that cannot read these
            # is a question left unanswered, not a build that cannot run.
            return None
        open_threads += sum(1 for c in response.get("comments", []) if not c.get("resolved"))
        request = comments.list_next(request, response)
    return open_threads


def fetch(ref: str, tab: str | None = None, suggestions: str = "rejected") -> JsonObject:
    doc_id, url_tab = parse_ref(ref)
    wanted = tab or url_tab
    document = select_tab(fetch_document(doc_id, suggestions), wanted)
    # Recorded into the response rather than warned about here,
    # for the reason `tabTitle` is: a build from a saved response
    # has to write the same page as the build that fetched it,
    # and neither the suggestions nor the comments survive in what is saved.
    # Only what could actually be read.
    # A key left out is one the last answer stands for,
    # which `build_one` carries over from the saved response.
    suggested = open_suggestions(doc_id, wanted)
    if suggested is not None:
        document["openSuggestions"] = suggested
    on_tab = open_comments_on_tab(doc_id, wanted)
    comments = on_tab if on_tab is not None else open_comments(doc_id)
    if comments is not None:
        document["openComments"] = comments
        document["openCommentsAreThisTab"] = on_tab is not None
    return document


def download_drive_file(file_id: str) -> bytes:
    """The raw bytes of a Drive file, for vectors the document links."""
    from googleapiclient.discovery import build

    service = build("drive", "v3", credentials=_credentials())
    files = service.files()  # pyrefly: ignore[missing-attribute]
    try:
        return files.get_media(fileId=file_id).execute()
    except Exception as e:  # noqa: BLE001
        raise FetchFailed(_explain(e)) from e

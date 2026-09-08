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

import hashlib
import json
import os
import re
import sys
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from .docs_json import JsonObject

if TYPE_CHECKING:
    from google.auth.credentials import Credentials

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


def iter_tabs(tabs: list[JsonObject], depth: int = 0) -> Iterator[tuple[int, JsonObject]]:
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


RESPONSE_KEYS = (
    "body",
    "documentId",
    "footnotes",
    "inlineObjects",
    "lists",
    "tabId",
    "tabTitle",
    "title",
    "url",
)
"""Every key `select_tab` writes, which is what a saved response is made of.

Kept here rather than read off one, because the point is to notice
when it changes: `test_a_saved_response_says_what_shape_it_is`
fails the moment `select_tab` writes a key this does not list,
and updating this is what invalidates the responses saved in the old shape.

Not the keys added afterwards. `modifiedTime`, `suggestions`, `openComments`,
and `openSuggestions` are written by `fetch` and some of them only sometimes,
so a `--no-comments` run would otherwise look like a different shape.
"""

RESPONSE_FORMAT = hashlib.sha256(",".join(RESPONSE_KEYS).encode()).hexdigest()[:8]
"""What the shape above comes to, recorded in every response written in it.

A saved response in an older shape is missing whatever was added since,
and reusing it publishes a report built from half a document.
That is not something Drive can be asked about: the document did not change,
the code did. So the response says which shape it is,
and a build reuses only what it would have written itself.
"""


def document_url(doc_id: str, tab: str = "") -> str:
    """The URL of a document, or of one of its tabs, spelled one way.

    Built from the ids rather than kept from whatever was passed in.
    A reference reaching a build can be a bare document id or a local path
    to a saved response, neither of which is a URL,
    and a URL that was one can be spelled several ways:
    `/edit`, `/view`, and whatever else was in the address bar when it was copied.
    None of that belongs in a committed file, and a link written once here
    is one that reads the same beside every report.

    Not what a saved response is matched by, which is the pair of ids:
    this is for whoever opens `doc.json` and wants the document it came from.
    """
    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    return f"{url}?tab={tab}" if tab else url


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
                f"no tab `{wanted}` in this document; available tabs:\n{describe_tabs(document)}"
            )
        chosen = matches[0]

    content = chosen.get("documentTab", {})
    doc_id = str(document.get("documentId", ""))
    return {
        # Which shape this is, so a build that writes a different one
        # fetches rather than reusing a response missing what it now needs.
        "format": RESPONSE_FORMAT,
        # Which document and which tab this was, so a saved response says what
        # it is. Nothing else does: the outputs beside it are named after the
        # report's own `URL:` line, which is a path and not an id, and a
        # `?tab=` id in `reports.toml` has nothing to match against without this.
        "documentId": doc_id,
        "tabId": tab_id(chosen),
        # The same two, as the link that opens them.
        # Derived and not kept, so it says the same thing for every report
        # however the entry that reached this build was spelled.
        "url": document_url(doc_id, tab_id(chosen)),
        "title": document.get("title", ""),
        "tabTitle": tab_title(chosen),
        "body": content.get("body", {}),
        "footnotes": content.get("footnotes", {}),
        "inlineObjects": content.get("inlineObjects", {}),
        "lists": content.get("lists", {}),
    }


# ---- api -----------------------------------------------------------


_SIGNING_IN = Lock()
"""Held while the answer is being worked out, and not while it is being used.

Reports are built in parallel, and the cache alone does not stop two threads
that both miss it from both running the flow: on a machine with no saved token
that is two browser windows asking for the same consent, and the second
overwrites what the first wrote. One at a time through here, and the second
finds it cached.
"""


def _credentials() -> Credentials:
    """The credentials to call the API with, worked out once per process."""
    with _SIGNING_IN:
        return _sign_in()


@cache
def _sign_in() -> Credentials:
    """Whatever this machine has to offer, interactive or not.

    Cached rather than worked out per call.
    A build of two reports asks six times, and each answer read the token
    file, checked its scopes, and refreshed it if it had expired,
    which is half a second of a thirteen second build spent
    re-deciding something that cannot change while a build runs.
    `cache_clear` is what a test uses to be given a different answer.

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


def _ambient_credentials() -> Credentials | None:
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
    except Exception as e:
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


def modified_time(doc_id: str) -> str | None:
    """When Drive last saw this document edited, or `None` if it will not say.

    The cheapest question there is about a document: half a second,
    against two for the document itself and another two for its suggestions.
    Editing a document is what moves this, and proposing, accepting, or
    rejecting a suggestion is editing it, so a document that has not moved
    has the same text and the same suggestions as the last build saw.

    Comments are not editing, and do not move it. They are counted every time.

    `None` rather than a raised error: not knowing whether a document changed
    is a reason to fetch it, which is what this was trying to avoid
    and not something it may decide against.
    """
    from googleapiclient.discovery import build

    try:
        service = build("drive", "v3", credentials=_credentials())
        files = service.files()  # pyrefly: ignore[missing-attribute]
        return files.get(fileId=doc_id, fields="modifiedTime").execute().get("modifiedTime")
    except Exception:
        # Broad on purpose, and building the client is inside it:
        # every way of not getting an answer is the same answer here,
        # which is that this build does not know and will fetch.
        return None


def unchanged(doc_id: str, cached: Path, suggestions: str) -> JsonObject | None:
    """The saved response, if it is of this document as this build wants it.

    Three questions, and a no to any of them is a fetch.
    Whether the document has been edited since, which Drive answers.
    Whether it was saved with the suggestions resolved the way this run
    resolves them, which the response itself says.
    And whether it is the shape a build writes today,
    because a response saved before a key was added is missing that key,
    and no amount of asking Drive would turn that up:
    the document did not change, the code did.
    A response saved with them rejected is a different document
    from the same file with them accepted, and no edit has to happen
    for the two to differ, so `modifiedTime` cannot see the difference.

    `None` whenever neither can be established,
    which is a saved response that is missing, unreadable, or was written
    before a build recorded what it is of.
    Every one of those is a reason to fetch rather than a reason to guess.
    """
    try:
        document = json.loads(cached.read_text())
    except OSError, ValueError:
        return None
    if not isinstance(document, dict):
        return None
    was = document.get("modifiedTime")
    if not was or document.get("suggestions") != suggestions:
        return None
    if document.get("format") != RESPONSE_FORMAT:
        # Written by an older version of this code, in a shape it no longer
        # writes. The document did not change; what a build makes of it did.
        return None
    return document if was == modified_time(doc_id) else None


def fetch(
    ref: str,
    tab: str | None = None,
    suggestions: str = "rejected",
    comments: bool = True,
    cached: Path | None = None,
) -> JsonObject:
    doc_id, url_tab = parse_ref(ref)
    wanted = tab or url_tab
    document = unchanged(doc_id, cached, suggestions) if cached is not None else None
    reused = document is not None
    if document is None:
        document = select_tab(fetch_document(doc_id, suggestions), wanted)
        # Recorded on the way out rather than asked for on the way in,
        # so the next build has something to compare against.
        # After the fetch, so a document edited while it was in flight
        # reads as changed next time rather than as already current.
        # What this response is of, so the next build can tell whether it is
        # the one it wants: which document, when, and read which way.
        document["suggestions"] = suggestions
        current = modified_time(doc_id)
        if current:
            document["modifiedTime"] = current
    # Recorded into the response rather than warned about here,
    # for the reason `tabTitle` is: a build from a saved response
    # has to write the same page as the build that fetched it,
    # and neither the suggestions nor the comments survive in what is saved.
    # Only what could actually be read.
    # A key left out is one the last answer stands for,
    # which `build_one` carries over from the saved response.
    if _ambient_credentials() is not None:
        # A service account is not a person with the document open,
        # and neither question has an answer it can give.
        # Suggestions it is refused outright.
        # Comments it is not refused: the export answers,
        # renders a document with no comments in it because it cannot see any,
        # and returns a confident nought that no retry would catch.
        # So it is not asked, and the last answer stands.
        #
        # Said out loud, because otherwise it is silent.
        # `google.auth.default` finds a key named by the environment,
        # and it finds `gcloud auth application-default login` too,
        # so a machine that acquires one stops counting these
        # and goes on publishing the last numbers as though it had checked.
        print(
            "not asking about suggestions or comments: this is a service account, "
            "which cannot see either; keeping the counts from the last build that could",
            file=sys.stderr,
        )
        return document

    # Not asked again about a document that has not been edited:
    # proposing, accepting, or rejecting a suggestion is editing it,
    # so the count in the response being reused is still the count.
    if not reused:
        suggested = open_suggestions(doc_id, wanted)
        if suggested is not None:
            document["openSuggestions"] = suggested
    # Not asked when the caller said not to, and a key left out is a key
    # `carry_over_review` fills in from the last build that did ask,
    # which is the same shape as being unable to ask.
    if comments:
        open_threads = open_comments_on_tab(doc_id, wanted)
        if open_threads is not None:
            document["openComments"] = open_threads
    return document


def download_drive_file(file_id: str) -> bytes:
    """The raw bytes of a Drive file, for vectors the document links."""
    from googleapiclient.discovery import build

    service = build("drive", "v3", credentials=_credentials())
    files = service.files()  # pyrefly: ignore[missing-attribute]
    try:
        return files.get_media(fileId=file_id).execute()
    except Exception as e:
        raise FetchFailed(_explain(e)) from e

"""What a report's embedded videos and posts look like before anyone plays them.

A page shows a card for each: who posted it, what it says, and a thumbnail.
The platform's own player is loaded only when the reader asks for it,
so reading the report asks nothing of YouTube, X, or Bluesky.

The card is looked up once and recorded in `embeds.json`, which is committed:
an offline build writes the same card, and a post deleted since keeps the one
it had. The thumbnail and a Drive video are files, rebuilt like the images.
"""

import hashlib
import json
from pathlib import Path
from urllib.parse import quote

import requests

from .docs_json import JsonObject
from .naming import IMAGE_DIR, VIDEO_DIR
from .nodes import VIDEO_TYPES, Card, Document, Embed, Platform, Shown

EMBEDS_JSON = "embeds.json"

TIMEOUT = 30

THUMBNAIL_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

PAGES_FILE_LIMIT = 100_000_000
"""The largest file GitHub Pages will publish."""


def read_embed_index(dest: Path, doc: Document) -> None:
    """Tell `doc` what every embed's platform said about it, as last recorded."""
    index = dest / EMBEDS_JSON
    if not index.exists():
        return
    for url, entry in json.loads(index.read_text()).items():
        card = {k: v for k, v in entry.items() if k != "file"}
        doc.cards.setdefault(url, Card(**card))
        if entry.get("file"):
            doc.media_files.setdefault(url, entry["file"])


def write_embed_index(dest: Path, doc: Document) -> None:
    """Record the cards of the embeds the document has, and no others.

    An embed taken out of the document leaves the record with it, the way it
    leaves the page; nothing would ever read its card again.
    """
    index = dest / EMBEDS_JSON
    entries = {}
    for embed in doc.embeds:
        card = doc.cards.get(embed.url)
        if card is None:
            continue
        entry = {k: v for k, v in card.__dict__.items() if v}
        if embed.url in doc.media_files:
            entry["file"] = doc.media_files[embed.url]
        entries[embed.url] = entry
    if not entries:
        index.unlink(missing_ok=True)
        return
    index.write_text(json.dumps(entries, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def look_up(doc: Document, http: requests.Session | None = None) -> None:
    """Ask each platform about the embeds nothing has recorded a card for.

    A failure is recorded rather than raised, as the archive's are:
    X in particular answers when it feels like it, and a report is not held
    back over a thumbnail. The card falls back to the link it was.
    """
    http = http or requests.Session()
    for embed in doc.embeds:
        if embed.url in doc.cards:
            continue
        try:
            card = _describe(embed, http)
        # Broad, because Drive's errors are its client library's own
        # and a malformed answer is a `KeyError` as often as anything.
        except Exception as e:
            card = Card(error=str(e) or type(e).__name__)
        doc.cards[embed.url] = card


def check_embeds(doc: Document) -> None:
    """Say which embeds publish as a plain link, on every build rather than the first.

    The page carries its warnings, so one said only by the build that asked
    would vanish from it on the next.
    """
    for embed in doc.embeds:
        card = doc.cards.get(embed.url)
        if card is None:
            doc.warn("nothing has looked up the embed {}; it shows as a link", Shown(embed.url))
        elif card.error:
            doc.warn(
                "could not look up the embed {} ({}); it shows as a link",
                Shown(embed.url),
                card.error,
            )
        elif embed.platform is Platform.DRIVE and not is_video(card):
            doc.warn(
                "{} is a Drive file of type {}, not a video this can play; it shows as a link",
                Shown(embed.url),
                Shown(card.mime or "unknown"),
            )


def _describe(embed: Embed, http: requests.Session) -> Card:
    match embed.platform:
        case Platform.YOUTUBE:
            # oEmbed rather than the Data API, which wants a key.
            found = _json(
                http,
                "https://www.youtube.com/oembed?format=json&url="
                + quote(f"https://www.youtube.com/watch?v={embed.key}", safe=""),
            )
            return Card(
                author=found["author_name"], text=found["title"], thumbnail=found["thumbnail_url"]
            )
        case Platform.X:
            # What X's own embed reads, and the one way left to read a post
            # without an account: its oEmbed answers with an empty body.
            # The token is checked for being present and nothing else.
            found = _json(
                http, f"https://cdn.syndication.twimg.com/tweet-result?id={embed.key}&token=0"
            )
            media = found.get("mediaDetails") or [{}]
            start, end = found.get("display_text_range") or (0, len(found["text"]))
            text = found["text"][start:end].strip()
            # A long post comes back cut short, with its full text somewhere
            # this cannot read, so the card says it stops rather than ending
            # mid-sentence as if that were all.
            if "note_tweet" in found:
                text += "\u2026"
            return Card(
                author=f"{found['user']['name']} (@{found['user']['screen_name']})",
                text=text,
                thumbnail=media[0].get("media_url_https", ""),
            )
        case Platform.BLUESKY:
            handle, rkey = embed.key.split("/", 1)
            did = handle
            if not did.startswith("did:"):
                did = _json(
                    http,
                    "https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle?handle="
                    + quote(handle),
                )["did"]
            uri = f"at://{did}/app.bsky.feed.post/{rkey}"
            posts = _json(
                http,
                "https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?uris="
                + quote(uri, safe=""),
            )["posts"]
            if not posts:
                raise ValueError("no such post")
            post = posts[0]
            author = post["author"]
            return Card(
                author=f"{author.get('displayName') or author['handle']} (@{author['handle']})",
                text=post["record"].get("text", ""),
                thumbnail=_bluesky_thumbnail(post.get("embed") or {}),
                did=did,
            )
        case Platform.DRIVE:
            from .fetch import drive_file_type

            return Card(mime=drive_file_type(embed.key))


def _bluesky_thumbnail(embed: JsonObject) -> str:
    """The picture a Bluesky post shows first, wherever in the embed it is kept."""
    if embed.get("thumbnail"):
        return embed["thumbnail"]
    for image in embed.get("images") or []:
        return image.get("thumb", "")
    if "media" in embed:
        return _bluesky_thumbnail(embed["media"])
    external = embed.get("external") or {}
    return external.get("thumb", "")


def _json(http: requests.Session, url: str) -> JsonObject:
    response = http.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def is_video(card: Card | None) -> bool:
    """Whether a Drive link's card says it is a video this can play."""
    return card is not None and card.mime in VIDEO_TYPES


def download(doc: Document, dest: Path, http: requests.Session | None = None) -> None:
    """Write each embed's thumbnail, and each Drive video, beside the images.

    Fetched every build, as the images are, because nothing is committed to
    tell a changed file from an unchanged one. A failure warns and the card
    goes without its picture.
    """
    http = http or requests.Session()
    for embed in doc.embeds:
        card = doc.cards.get(embed.url)
        if card is None or card.error:
            continue
        stem = f"embed-{hashlib.sha256(embed.url.encode()).hexdigest()[:8]}"
        try:
            if embed.platform is Platform.DRIVE:
                if is_video(card):
                    doc.media_files[embed.url] = _video(embed, card, stem, dest / VIDEO_DIR, doc)
            elif card.thumbnail:
                doc.media_files[embed.url] = _thumbnail(card, stem, dest / IMAGE_DIR, http)
        except Exception as e:
            doc.warn("could not download what {} shows ({})", Shown(embed.url), str(e))


def _thumbnail(card: Card, stem: str, outdir: Path, http: requests.Session) -> str:
    response = http.get(card.thumbnail, timeout=TIMEOUT)
    response.raise_for_status()
    kind = response.headers.get("content-type", "").split(";")[0].strip()
    extension = THUMBNAIL_TYPES.get(kind)
    if extension is None:
        raise ValueError(f"the thumbnail came back as {kind or 'nothing'}")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{stem}{extension}").write_bytes(response.content)
    return f"{stem}{extension}"


def _video(embed: Embed, card: Card, stem: str, outdir: Path, doc: Document) -> str:
    from .fetch import download_drive_file

    data = download_drive_file(embed.key)
    if len(data) > PAGES_FILE_LIMIT:
        doc.warn(
            f"the video {{}} is {len(data):,} bytes, over the {PAGES_FILE_LIMIT:,} bytes "
            "GitHub Pages will publish; the deploy will fail until it is smaller",
            Shown(embed.url),
        )
    name = f"{stem}{VIDEO_TYPES[card.mime]}"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / name).write_bytes(data)
    return name

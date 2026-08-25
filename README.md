# `eta-publish`

Convert an [ETA](https://www.etany.org/) report Google Doc
into publish-ready HTML, Markdown, and PDF.

Reports are drafted in Google Docs and published on Squarespace.
Today that hand-off is entirely manual, and it is the source of both
the tedium and the mistakes.

## Why this exists

The most recent report,
[*Digging Out of a Very Deep Hole*](https://www.etany.org/reports/digging-out-deep-hole-sas-west),
is built from **162 hand-placed Squarespace blocks**:
86 text blocks, 54 image blocks, and 22 code blocks.
Squarespace itself [recommends no more than 60 blocks per page](https://support.squarespace.com/hc/en-us/articles/206543087-Page-limits),
warning that pages beyond that load and save slowly.

Those 22 code blocks are not charts or embeds.
They are hand-written anchor targets, one per footnote,
that exist only so the `↑` backlinks work:

```html
<a id="fn7-return"></a>
```

Maintaining that by hand across 21 footnotes went about as well as expected.
The published page is missing the backlink for footnote 13 entirely,
and carries two pieces of leftover debris:
a stray `#` inside an `id` (`id="#fn3-return"`),
and a duplicated `fn18-return`.

None of this is anyone's fault. It is what happens when a person is
asked to be a compiler. So we should use a compiler.

## What it does

Reads the Google Doc, builds a document tree, and emits from that tree:

| Output | Purpose |
| --- | --- |
| `report.html` | One fragment to paste into a single Squarespace code block |
| `report.md` | Human-readable, diffable archive committed to git |
| `report.typ` / `report.pdf` | [Typst](https://typst.app/) source, and the compiled PDF |
| `preview.html` | Standalone page for review, including any warnings |
| `images/` | The doc's inline images, for hosting outside Squarespace |

Headings, anchors, the table of contents, footnote numbering,
and the `↑` backlinks are all generated.
They cannot drift out of sync, because nothing maintains them by hand.

## Design decisions worth knowing

### The Google Docs API, not an HTML export

We read the doc with the Docs API (`documents.get`),
not Drive's HTML export.
The export is `<span class="c12">` soup with no semantics.
The API JSON gives us the three things a report actually needs:

- `footnotes` as first-class objects, with `footnoteReference` inline,
  so numbering and backlinks are derived rather than typed
- real named paragraph styles, so headings are headings
- `inlineObjects`, so images carry their alt text

### One tree, three emitters

Every output is emitted from the same document tree.
In particular, the HTML is **not** rendered from the Markdown.
Chaining them would add a lossy hop
(the source/caption/credit triple, superscripts, exact link targets)
and would create two sources of truth
the moment someone hand-edited the `.md`.

### Determinism is a feature, not a nicety

Unchanged input must produce byte-identical output.
The `.md` is committed to git, so every accidental difference
becomes noise in a diff that someone has to read.

This is why image filenames are keyed on the stable Docs object id
rather than on a counter: inserting one image into a 54-image report
must not rename the other 53, or change their published URLs.
The same reasoning applies to heading anchors, which are published URLs
that must not move when an unrelated section is added.

### Semantic line breaks in the Markdown

The `.md` breaks lines at sentence and clause boundaries
rather than wrapping to a fixed width.
Without this, a paragraph is a single line,
and correcting one word shows up as the entire paragraph changing.
With it, the August 21 addendum to the SAS West report
is a three-line diff and nothing else moves.

The sentence splitter is deliberately conservative,
because the text is full of `125 St.`, `Phase 2.`, and `$7.7 billion.`,
and an over-eager splitter would churn the diff on every regeneration.
Its behavior is pinned: changing it reflows every file,
and should be its own commit.

## Squarespace constraints

These are load-bearing. The block counts, the 7.1 version, and the two
documented limits were verified against the live site and Squarespace's
own documentation; the one estimate below is marked as such.

- **There is no content API.** The public Squarespace API covers commerce only.
  Nothing can create or update a page from a script,
  so the final step is necessarily a human paste.
  The goal is to make it *one* paste instead of 162 placements.
- **`etany.org` runs Squarespace 7.1**, so Developer Mode, Git, and SFTP
  are unavailable; those are 7.0-only. A single code block on an otherwise
  empty page is the closest thing to a pure HTML page, and it is close enough.
- **A code block holds 400 KB (~300,000 characters).**
  Two measurements bracket the SAS West report: its source text is 69 KB,
  and the live page's rendered text blocks come to 226 KB including
  Squarespace's own markup, which this emitter does not produce. The
  fragment should land between them, comfortably inside the limit, but it
  has not been generated from the real document yet. `--split` cuts at `h2`
  boundaries for a report that does not fit.
- **There is no file upload API.** Custom Files is a manual GUI
  that accepts images and fonts only. Host report images elsewhere
  and reference absolute URLs; the PDF needs those same local files anyway,
  so one upload serves both outputs.

## Usage

```sh
uv run eta-publish <google-doc-url> --image-base https://assets.etany.org/sas-west
```

Pass the full URL including its `?tab=` id.
ETA reports live in multi-tab documents, and the Docs API defaults to the
first tab, which is usually an earlier draft. A multi-tab document with no
tab specified refuses to guess and lists its tabs.

Outputs land in `out/`. Add `--split` for a report over the code block
limit, and `--no-pdf` to skip compiling the Typst.

### Authentication

The Docs API needs an OAuth client, which is free and takes a few minutes.
It is per-person: the token identifies you, and only grants read access to
documents you can already open.

1. Open the [Google Cloud console](https://console.cloud.google.com/) and
   create a project, or reuse one.
2. Enable the **Google Docs API** for it, under
   *APIs & Services* → *Library*.
3. Under *APIs & Services* → *OAuth consent screen*, configure it as
   **External**, in **Testing**, and add your own Google account under
   *Test users*. Nothing is being published to Google, so it never needs
   verification.
4. Under *APIs & Services* → *Credentials*, create an
   **OAuth client ID** of type **Desktop app**, and download its JSON.
5. Save it as `~/.config/eta-publish/client_secret.json`,
   or point `$ETA_CLIENT_SECRETS` at it.

The first run opens a browser to approve read-only access. The resulting
token is cached at `~/.config/eta-publish/token.json` and refreshes itself,
so this happens once. Both files are secrets; the repository ignores them
by name, but they belong outside it anyway.

### Rate limits

Not a concern at this scale. The Docs API allows
[3,000 read requests per minute per project, and 300 per minute per
user](https://developers.google.com/workspace/docs/api/limits).
One publish is one request, so an afternoon of re-running the build sits
several orders of magnitude under the limit. Exceeding it returns HTTP 429
rather than costing anything.

The saved `out/doc.json` also means the pipeline can be re-run against the
last fetch without touching the network at all, which is what the tests do.

## Development

```sh
uv sync
uv run pre-commit install
uv run pytest
```

`ruff format`, `ruff check`, `ty`, `pyrefly`, and `pytest`
run as pre-commit hooks and again in CI.
Tests run against checked-in Docs API responses,
so neither ever needs Google credentials or the network.

`tests/real/` holds an actual `documents.get` response for the published
SAS West report, together with the output it currently produces. Every bug
that mattered came from that document's shape rather than from a
hand-written fixture, so the snapshots are the regression net for all of
it. When one changes, read the diff before accepting it: it is exactly
what the change does to a real published report. Regenerate with
`uv run pytest --regenerate-snapshots`.

## Document conventions

The converter reads structure, so the doc has to carry it.
Anything it cannot classify is reported as a warning rather than
silently dropped.

None of this is fixed. If a convention is awkward to write,
it is easier to change the converter than to fight it in every report,
so say so.

### Front matter

"Front matter" is the block of `Key: value` lines at the top of a document
that describes it rather than being part of it:
where it publishes, what its summary is, who wrote it.
The name comes from printing, where the front matter is the title page and
copyright notice, as distinct from the body.

ETA reports already have one, under the `Header` heading:

```
Header
Project Manager: Khyber Sen
Phase: published
URL: /reports/digging-out-deep-hole-sas-west
Short: A 125 St subway should be a slam dunk. But at $7.7B ...
SEO Description: A 125 St subway should be a slam dunk ...
```

The converter reads that block into metadata and keeps it out of the body.
`URL:` becomes the published path, `Short:` becomes the standfirst,
`SEO Description:` becomes the page description,
`Public Contributors:` becomes the byline,
named the way the header lists them,
and `Final Due Date:` becomes the dateline.
`Private Contributors:` is never read for the byline,
which is the point of the two fields being separate.
Everything else is carried along and made available to the templates.

Two rules matter, because both are load-bearing:

**The block ends at the first line that is not `Key: value`.** Any heading,
the headline, a paragraph containing an image, or ordinary prose. Keep the
header lines together, with nothing between them.

Lines *before* the `Header` heading are treated as production scaffolding
and dropped, with each one reported so nothing leaves silently. The SAS West
tabs open with `Header` directly, so this is defensive.

**The headline must be styled `Title`.** Otherwise it is
`Digging Out of a Very Deep Hole: Saving Billions on 125th Street`, which
looks exactly like a `Key: value` line and gets filed as metadata. The
converter warns when this happens, and falls back to the document's Drive
filename, which is a working name (`SAS West Feasibility Response`) and not
what should publish. Alternatively, put `Title:` in the header block.

Unrecognized keys are kept rather than treated as body text, so adding a
field to a future report is safe. A parenthetical note in a key is not part
of its name: `SEO Description (300 char limit):` is read as
`seo description`.

### The rest

- **Real heading styles**, not bolded body text.
  Heading text determines the anchor, which is a published URL,
  so renaming a heading moves it unless an override is set.
- **Real footnotes.** Numbering and backlinks are generated from them.
- **Images inserted inline.** The lines around an image are folded into its
  figure: a `Source: <file>` paragraph before it, or an
  `[Image Source](<url>)` paragraph after the caption, plus the caption and
  a `Credit:` line.
  Both spellings of the source are treated as editorial notes: they are kept
  in the Markdown archive as comments and never appear in the published HTML
  or the PDF, matching the live page, where `Source:` and `Image Source`
  each appear zero times and `Credit:` appears 26 times.
  When an image has no alt text in Docs, its caption is used, which is what
  the live page does by hand.
- **Suggestions are rejected.** The doc is fetched as it currently reads,
  with every open suggestion rejected, so nothing publishes because someone
  proposed it and no one noticed. `--suggestions accepted` previews the
  other way.
- **Tabs.** Pass the URL including its `?tab=` id. The SAS West document has
  eight tabs, including `Draft 1 [OBSOLETE]`, `Draft 3 [OBSOLETE]`,
  `Research`, and `Notes/Scratch`. The Docs API returns only the first tab
  unless asked otherwise, so publishing the wrong draft is a real
  possibility rather than a theoretical one. A multi-tab document with no
  tab named refuses to guess and lists what it found.

## Status

The parser and all three emitters work, against a fixture.

**Not yet run against a real report.** That needs OAuth credentials, and it
is the next thing worth doing: every finding so far that mattered came from
the real document's shape rather than from the fixture, and there are
almost certainly more. It will also settle the code block size estimate,
which is currently the one unmeasured number here.

## TODO

### Preserve the anchors of already-published reports

Existing reports have short, hand-chosen anchors.
The live SAS West table of contents links to `#elephants` and
`#unlearned-lessons`, where generated anchors would be
`#the-elephants-in-the-room` and `#the-unlearned-lessons-of-recent-projects`.
Regenerating one of those reports as-is would break every inbound link
to a section, including links from outside `etany.org`
that we cannot see or fix.

`AnchorAllocator` already accepts an `overrides` mapping;
what is missing is somewhere in the doc to write them
and a decision between two approaches:

- **Remap**, pinning each heading to its existing anchor.
  Keeps one anchor per section and keeps the short readable URLs,
  which are nicer than slugified headline text regardless of history.
- **Emit both**, generating the new anchor and keeping the legacy one
  alongside it as an empty target, so old links keep working.
  Safer for links already loose in the world,
  at the cost of two anchors per section.

These are not exclusive: remapping suits reports we are actively
republishing, and duplicate legacy targets suit ones we are not.

Wherever the overrides live, they have to be in the Google Doc,
since that is the source of truth
and the person republishing a report will be working there, not here.

## Possible directions

**Version history.** Because the `.md` is regenerated and committed
on every publish, git accumulates a usable history for free.
Reconstructing the *existing* Google Docs history is a separate problem
and probably not worth it: the Drive Revisions API merges revisions for Docs
and may omit older ones, so a faithful replay is not available.

**A PDF-first review loop.** The Typst template is deliberately plain.
Once a report has actually been through it, the house style is the obvious
next thing to invest in.

**A static site.** `reports.etany.org` built from the same tree in CI
would remove the paste step entirely, along with the block limits,
and would give real per-draft previews.
Once the tree and emitters exist this is nearly free: same HTML,
different wrapper. It is an organizational decision rather than a technical
one, and nothing here forecloses it.

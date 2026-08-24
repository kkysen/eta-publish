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
| `report.typ` | [Typst](https://typst.app/) source, rendered to a PDF |
| `preview.html` | Standalone styled page for review before publishing |
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
  The SAS West report is *estimated* at roughly 220 KB, measured from the
  live page's text blocks plus a per-figure allowance; nothing has been
  generated and pasted yet. If that holds it fits at about half the budget,
  but longer reports will not, so the HTML emitter can split at `h2`
  boundaries when needed.
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

First run opens a browser for OAuth.
Put the OAuth client JSON at `~/.config/eta-publish/client_secret.json`,
or point `$ETA_CLIENT_SECRETS` at it.

## Document conventions

The converter reads structure, so the doc has to carry it.
Anything it cannot classify is reported as a warning rather than silently dropped.

- A leading section headed `Header`, holding `Key: value` lines
  (`URL:`, `Short:`, `SEO Description:`, contributors, dates).
  Unrecognized keys are preserved rather than treated as body text.
- Real Google Docs heading styles, not bolded body text.
  Heading text determines the anchor, which is a published URL,
  so renaming a heading moves it unless an override is set.
- Real Google Docs footnotes.
- Images inserted inline. An optional `Source:` paragraph immediately
  *before* an image, and caption and `Credit:` paragraphs immediately
  *after* it, are folded into that image's figure.

## Status

Early. The document tree and the Docs parser come first;
the three emitters are being filled in behind it.

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

**A static site.** `reports.etany.org` built from the same tree in CI
would remove the paste step entirely, along with the block limits,
and would give real per-draft previews.
Once the tree and emitters exist this is nearly free: same HTML,
different wrapper. It is an organizational decision rather than a technical
one, and nothing here forecloses it.

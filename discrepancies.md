# Discrepancies

Every place the generated output differs from the same report
as it is published today on Squarespace, and whether that difference
is intended or still to do.

A report is compared by normalizing both sides to a tagged stream
(headings, paragraphs, list items, captions, alt text, cells)
and diffing that in both directions,
then checking footnote anchors, figure captions, credits,
and heading levels against `doc.json`.
Wording, credits, and caption text are not listed when they match;
today they do, for every figure and every footnote body.

A live page is not the reference.
It was assembled by hand out of Squarespace blocks,
so a difference can just as easily be a defect on the live side,
and several are.

## All reports

These follow from what the emitters do,
so they apply to whatever report is published next.

### Table of contents lists only top-level sections (todo)

The generated table of contents has one entry per `HEADING_1`.
The live page also lists every subsection under them.
This is the one place where a live page is genuinely richer
than what we emit.

### One `h1`, not a split title (intended)

The live page puts the title in an `h1` and the subtitle in an `h2`,
which makes the subtitle look like the first section.
The generated page keeps the whole title in the `h1`
and the standfirst in a paragraph.

### A byline instead of a contributors section (intended)

The live page ends with a `Contributors` heading, a sentence of
acknowledgement, and a list of names.
The generated page names the same people in a byline under the title,
which is where a reader looks for them.
See the commit `Credit the contributors the header already names`.

### Short dates (intended)

`Aug 19, 2026`, against `August 19, 2026` live.

### Footnote markers are bare superscripts after the punctuation (intended)

Live renders `[3]` and places it before the closing period.
The generated marker is a plain superscript number
and sits where the document puts the reference, after the period.

## SAS West

<https://www.etany.org/reports/digging-out-deep-hole-sas-west>

### The live footnotes are misnumbered from 13 onward (intended)

The live page carries 21 markers and 21 `id="fnN"` anchors
but only 20 rendered footnote bodies.
An extra marker sits on
"...has space for more tracks than it needs",
so every marker after it resolves one footnote too far:
live `[14]`, on the steep-tracks sentence, lands on the soft-costs note,
and live `[21]` lands on nothing at all.
The live page also still carries the debris the `README.md` describes,
an `id="#fn3-return"` and a duplicated `fn18-return`.

Nothing to do. The generated apparatus is 1:1,
20 references, 20 bodies, 20 backlinks,
and this is the discrepancy the project exists to produce.

### The chart captions lost their `SVG` and `PNG` links (todo)

Live ends both chart captions with `[SVG] [PNG]` download links.
The document now holds bare `SVG: TODO` and `SVG:` placeholders
where those links were, which is what the `unfinished text` warning reports.
The links have to go back into the document.
There is nothing to fix in the emitters.

### Appendix A and B are a level too low (todo)

The document styles both as `HEADING_2`
while the report's own sections are `HEADING_1`,
so they emit as `h3` and fall out of the table of contents.
Live shows them as `h2` because someone corrected it by hand.
Restyle them in the document.

### The lead image has no alt text (todo)

It also carries no caption, so nothing describes it.
Add a description in the document.

### An image is styled as a heading (todo)

An empty `HEADING_3` holds an image.
Set that paragraph to normal text in the document.

### Four wordings the live page predates (intended)

The document has been edited since it was published:
`10-story` for `10 story`,
`station box, while` for `station box while`,
`more cheaply` for `cheaper`,
and footnote 9's reference moved to a different sentence.
The generated output is the current one.

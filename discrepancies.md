# Discrepancies

## What is being compared

Three things, not two.
For a report whose header block names `URL: /reports/$report`,
which is the one place its name is written:

1. `https://www.etany.org/reports/$report`,
   the live page, as Squarespace serves it today.
   It is assembled by hand, one block at a time,
   162 of them for SAS West,
   so it is a record of what a person typed, not a reference.
2. `site/reports/$report/doc.json`,
   the `documents.get` response for the tab named in that report's
   `url` in `reports.toml`, committed next to the outputs it produced.
   This is the source: everything published comes from here.
3. `site/reports/$report/index.html`,
   written from that `doc.json` by `uv run eta-publish -o site`,
   or offline by `uv run eta-publish site/reports/$report --no-images`.

Below, `doc.json` and `index.html` are those two files
for the report the section is about, and *live* is that URL.

Naming all three is what makes an entry actionable,
because where a difference sits says who fixes it:

- Emitter. `doc.json` and `index.html` disagree.
  The document is right and the code is wrong. Fix the code.
- Document. `index.html` faithfully carries something
  missing or miswritten in `doc.json`.
  Live may look right, because someone fixed it by hand after publishing.
  Fix the document, and the fix reaches every output at once.
- Hand assembly. `doc.json` and `index.html` agree and live differs.
  Either the live page is defective,
  or the emitter deliberately publishes something else.
  Nothing to fix in this repository.
- Stale live. All three agreed when the report published,
  and `doc.json` has been edited since.

A report is compared by normalizing live and `index.html`
to a tagged stream
(headings, paragraphs, list items, captions, alt text, cells)
and diffing that in both directions,
then settling every hit against `doc.json`:
footnote references and bodies, figure captions, credits, heading styles.
Anything the three agree on is not listed.
Today that includes every figure caption, every image credit,
and the text of every footnote body.

## All reports

These follow from what the emitters do,
so they apply to whatever report is published next.

### The table of contents lists every heading, indented (intended)

Hand assembly.
Live runs six links together on one line separated by pipes,
so the eight subsections `doc.json` carries appear nowhere
and `Ground Conditions` is unreachable from the top of the page.
`index.html` lists all twenty-one headings as a nested list,
one per line, each indented under the section it belongs to.

`Footnotes` and `Contributors` are listed too,
though the emitter writes those two headings rather than the document.
They are sections of the page like any other,
and "at the end" is not an address in a report this long.

### One `h1`, not a split title (intended)

Hand assembly.
`doc.json` holds one `TITLE` paragraph,
`Digging Out of a Very Deep Hole: Saving Billions on 125th Street`,
and `index.html` emits exactly that as a single `h1`.
Live splits it across an `h1` and an `h2`,
which leaves the subtitle looking like the first section heading.

### Everything on the page has an id (intended)

Hand assembly.
Live gives ids to headings and to the footnote anchors someone typed by
hand, and to nothing else,
so there is no way to link to a paragraph, a figure, or a table.
`index.html` gives an id to the title, the standfirst, the table of
contents, the date, every heading, every paragraph, list, figure, and
table, each footnote, and the footnotes and contributors sections
themselves.

The ids of blocks with no name of their own are hashes of what they say,
not of where they sit.
Numbering them would mean inserting a paragraph silently repoints every
link after it at the wrong text;
hashing means editing a paragraph breaks links to that paragraph and
nothing else.

### Section references are links (intended)

Hand assembly.
Google Docs cannot write a link to a heading in the same document,
so the report italicizes the section's name and means a link by it.
Live publishes the italics as italics:
`See SAS Phase 2 Tail Tracks`, `as suggested in Station Depth`,
and the addendum's `Station Depth`,
each of them a name pointing nowhere.
One of the three was linked by hand, to `#phase2-tail-tracks`.

The parser reads the convention,
so all three resolve to the heading they name,
in the HTML, the Markdown, and the PDF alike.
This is a defect the live page and the generated page shared,
which is why comparing the two could not surface it.

### The back matter headings are `h2` (intended)

Hand assembly.
`index.html` credits the same nine people the live page credits,
in the same order, in a `Contributors` section after the footnotes,
under the sentence the live page introduces them with.
The names come from `Public Contributors:` in the header block
and are sorted by surname, which is how etany.org credits contributors
and is not the order that field happens to be typed in.

What differs is the level.
`Footnotes` and `Contributors` are `h2` here and `h3` live,
which makes them sections of the report rather than
subsections of whatever came last.

### Footnote markers are bare superscripts after the punctuation (intended)

Hand assembly.
`index.html` puts each marker exactly where `doc.json` puts the
`footnoteReference`, which for reference 3 is after the period in
`takes seven minutes.`, and renders it as a plain superscript number.
Live renders `[3]` and places it before the period.

## SAS West

- <https://www.etany.org/reports/digging-out-deep-hole-sas-west>
- `site/reports/digging-out-deep-hole-sas-west/doc.json`
- `site/reports/digging-out-deep-hole-sas-west/index.html`

### The live footnotes are misnumbered from 13 onward (intended)

Hand assembly, and the clearest case of it.
`doc.json` holds 20 footnotes and 20 references,
and `index.html` emits 20 references, 20 bodies, and 20 backlinks, 1:1.
Live carries 21 markers and 21 `id="fnN"` anchors against 20 rendered
bodies: an extra marker sits on
`...has space for more tracks than it needs`,
so every marker after it resolves one footnote too far.
Live `[14]`, on the steep-tracks sentence, lands on the soft-costs note,
and live `[21]` lands on nothing at all.
Live also still carries the debris the `README.md` describes,
an `id="#fn3-return"` and a duplicated `fn18-return`.

Nothing to do. This is the discrepancy the project exists to produce.

### The chart captions lost their `SVG` and `PNG` links (todo)

Document.
Live ends both chart captions with `[SVG] [PNG]` download links.
`doc.json` has bare `SVG: TODO` and `SVG:` placeholders where those links
were, so `index.html` has no links to emit and the `unfinished text`
warning fires.
Put the links back in the document.

### Appendix A and B are a level too low (todo)

Document.
`doc.json` styles both as `HEADING_2`,
the same level as `Station Depth` and `Fire Code`,
while the report's own sections are `HEADING_1`.
`index.html` follows that and emits `h3`,
so the table of contents indents both appendices under `Conclusion`,
which is what the document says and not what the report means.
Live shows them as `h2` because someone corrected it by hand.
Restyle them in the document, and they rise in every output at once.

### The share card has no alt text (todo)

Document.
The wide image with the title set into it, which the document puts above
the headline, publishes as `og:image` and nowhere else,
the same image live serves as `saswest.jpg`.
`og:image:alt` is written when the image has alt text, and this one has
none, so a link preview that is read aloud says nothing.
Describe it in the document.

### The images are named by hash (todo)

Emitter.
`index.html` references `images/img-8827f5de.jpg`, from the Docs object id,
because the document gives an image no name at all.
Live serves `saswest.jpg`, named by a person.
A name belongs in the document, next to the image, the way `Credit:` is,
and until it is there a hash is the only thing that is stable across edits.

### An image is styled as a heading (todo)

Document.
`doc.json` has an empty `HEADING_3` paragraph holding an image.
`index.html` treats it as a figure and warns.
Set that paragraph to normal text in the document.

### Four wordings the live page predates (intended)

Stale live.
`doc.json` has been edited since the report published,
and `index.html` carries the current text:
`10-story` for `10 story`,
`station box, while` for `station box while`,
`more cheaply` for `cheaper`,
and footnote 9's reference moved to a different sentence.

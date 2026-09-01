// ETA report house style.
//
// The emitted `.typ` is a document body that imports this,
// so a change to how reports look is a change to one file rather than to every report.

// No image is taller than this.
// The reports are illustrated at whatever size someone dropped the picture in at,
// and a tall one pushed the title page's own picture onto page two.
// 4.5in is what leaves the headline, the standfirst, the hero and its caption
// together on page one, which is the page the cap is for.
#let max_image_height = 4.5in

// An image at the width it is given, unless that makes it too tall,
// in which case the height is what is set and the width follows from it.
// `layout` is what supplies the width to measure against:
// a figure in the body and one in the title block have different widths available,
// and neither is known here.
#let capped_image(path, ..args) = layout(size => {
  let full = image(path, width: size.width, ..args)
  if measure(full).height <= max_image_height {
    full
  } else {
    align(center, image(path, height: max_image_height, ..args))
  }
})

#let report(
  title: "",
  url: none,
  short: none,
  // `Public Contributors:` only.
  // The header block keeps the private list under its own key
  // so that those names do not reach a published page.
  public_contributors: none,
  dateline: none,
  contributors: (),
  contributors_note: none,
  hero: none,
  // The date the report publishes on, as the document shows it.
  final_due_date: none,
  ..rest,
  body,
) = {
  set document(title: title)
  set page(
    paper: "us-letter",
    margin: (x: 1.4in, y: 1.2in),
    // Footnotes land at the bottom of the page they are cited on,
    // which is the whole reason these reports are typeset
    // rather than printed from the web page.
    footer: context {
      set align(center)
      set text(size: 9pt, fill: luma(40%))
      counter(page).display("1")
    },
  )
  set text(font: ("Libertinus Serif", "Linux Libertine", "Georgia"), size: 11pt, lang: "en")
  set par(justify: true, leading: 0.65em, spacing: 1.2em)
  show link: set text(fill: rgb("#1a4d7a"))

  set heading(numbering: none)
  show heading.where(level: 1): it => {
    set text(size: 15pt, weight: "bold")
    block(above: 1.8em, below: 0.8em, it)
  }
  show heading.where(level: 2): it => {
    set text(size: 12.5pt, weight: "bold")
    block(above: 1.4em, below: 0.6em, it)
  }
  show heading.where(level: 3): it => {
    set text(size: 11pt, weight: "bold", style: "italic")
    block(above: 1.2em, below: 0.5em, it)
  }

  set footnote.entry(separator: line(length: 35%, stroke: 0.5pt + luma(60%)))
  show footnote.entry: set text(size: 8.5pt)

  show figure.caption: set text(size: 9pt, fill: luma(35%))
  show figure: set block(above: 1.6em, below: 1.6em)

  // Title block.
  block(width: 100%)[
    #set align(left)
    #text(size: 21pt, weight: "bold")[#title]
    #if short != none [
      #v(0.6em)
      #text(size: 11.5pt, fill: luma(35%), style: "italic")[#short]
    ]
    #if dateline not in (none, "") [
      #v(0.6em)
      #text(size: 10pt, fill: luma(35%))[#dateline]
    ]
    #v(0.4em)
    #line(length: 100%, stroke: 0.8pt)
  ]
  // With the title rather than after the contents:
  // the document puts it under the headline,
  // and it introduces the report
  // rather than the section that happens to follow the outline.
  if hero != none {
    hero
  }

  v(1.2em)

  // The report is too long to find a section by turning pages,
  // the same reason the page has a table of contents.
  // Typst builds it from the headings, so it cannot disagree with them.
  outline(title: [Table of Contents], depth: 3, indent: auto)
  v(1.2em)

  body

  // Credited at the end, not under the title:
  // a report is the work of most of a chapter,
  // and nine names above the first paragraph read as a masthead rather than a credit.
  if contributors.len() > 0 {
    heading(level: 1, [Contributors])
    if contributors_note != none [#contributors_note]
    list(..contributors)
  }
}

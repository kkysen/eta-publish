(() => {
  const GAP = 8;
  // Long enough to cross the gap into the box, short enough that a box left
  // behind is gone before the reader wonders why it is still there.
  const HOLD = 200;
  const closing = new WeakMap();
  // A citation's box is built the first time it is wanted, out of the entry it
  // already points at, rather than emitted beside every link. The report cites
  // 113 sources and a copy of each one's address next to each of its citations
  // is 17 KB of a fragment that has 400 KB to fit in. The section is the form
  // that always works; this is the shortcut for a reader who has a pointer.
  const sourceTip = (cited) => {
    const existing = cited.querySelector(".source-tip");
    if (existing) return existing;
    const ref = cited.querySelector(".source-ref a");
    const entry = ref && document.getElementById(ref.getAttribute("href").slice(1));
    if (!entry) return null;
    const tip = document.createElement("span");
    tip.className = "source-tip";
    tip.setAttribute("aria-hidden", "true");
    // Everything the entry says except the ways back into the text, which from
    // here would lead to the sentence the reader is already reading.
    for (const node of [...entry.cloneNode(true).childNodes]) {
      if (node.classList?.contains("source-back")) continue;
      tip.append(node);
    }
    // Every link in the box is a copy of one the entry has, and the entry is a
    // jump away: the keyboard walks past the copy rather than stopping at it.
    for (const link of tip.querySelectorAll("a")) link.tabIndex = -1;
    cited.append(tip);
    return tip;
  };
  const tipOf = (e) => {
    // Not inside a note's box, which is already a box: a citation in there is
    // a copy of one in the note, and its entry is a jump away from both.
    const cited = e.target.closest?.(".eta-report .cited:not(.footnote-tip *)");
    if (cited) return sourceTip(cited);
    return e.target.closest?.(".eta-report .footnote-ref")?.querySelector(".footnote-tip");
  };
  const place = (event) => {
    // The stylesheet shows this on hover only where the device hovers, and a
    // tap raises hover on a touch screen. Asking the same question here keeps
    // the two from disagreeing.
    if (!matchMedia("(hover: hover)").matches) return;
    const tip = tipOf(event);
    if (!tip) return;
    clearTimeout(closing.get(tip));
    // Already open: the pointer has only moved within the box or back onto
    // the reference, and measuring again would answer the same.
    if (tip.style.position === "fixed") return;
    // Laid out where it can be measured, and not yet shown there: the handler
    // runs before the frame is painted.
    tip.style.cssText =
      "display:block;visibility:hidden;position:fixed;left:0;top:0;transform:none";
    const box = tip.getBoundingClientRect();
    const ref = tip.parentElement.getBoundingClientRect();
    const below = ref.bottom + GAP;
    const above = ref.top - GAP - box.height;
    // Under it unless that runs off the bottom, and over it only where the
    // box fits: with neither edge free, under is the one that can be scrolled to.
    const top = below + box.height <= innerHeight - GAP || above < GAP ? below : above;
    const middle = ref.left + ref.width / 2 - box.width / 2;
    const left = Math.min(Math.max(middle, GAP), innerWidth - box.width - GAP);
    tip.style.cssText = `display:block;position:fixed;left:${left}px;top:${top}px;transform:none`;
  };
  // Handed back to the stylesheet, so that a box measured against one scroll
  // position is not still carrying those numbers at the next one. After a
  // pause, because the pointer leaves the reference on its way into the box.
  const release = (event) => {
    const tip = tipOf(event);
    if (!tip) return;
    clearTimeout(closing.get(tip));
    closing.set(tip, setTimeout(() => { tip.style.cssText = ""; }, HOLD));
  };
  for (const name of ["pointerover", "focusin"]) document.addEventListener(name, place);
  for (const name of ["pointerout", "focusout"]) document.addEventListener(name, release);
})();

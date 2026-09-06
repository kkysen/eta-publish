(() => {
  const GAP = 8;
  // Long enough to cross the gap into the box, short enough that a box left
  // behind is gone before the reader wonders why it is still there.
  const HOLD = 200;
  const closing = new WeakMap();
  const tipOf = (e) =>
    e.target.closest?.(".eta-report .footnote-ref")?.querySelector(".footnote-tip");
  const place = (event) => {
    // The stylesheet shows this on hover only where the device hovers, and a
    // tap raises hover on a touch screen. Asking the same question here keeps
    // the two from disagreeing.
    if (!matchMedia("(hover: hover)").matches) return;
    const tip = tipOf(event);
    if (!tip) return;
    clearTimeout(closing.get(tip));
    // Already open, and the pointer has only moved within it or back onto the
    // reference. Measuring again would answer the same, so this leaves the box
    // exactly where the reader is reading it.
    if (tip.style.position === "fixed") return;
    // Laid out where it can be measured, and not yet shown there. The event
    // handler runs before the frame is painted, so nothing is drawn in this
    // position.
    tip.style.cssText =
      "display:block;visibility:hidden;position:fixed;left:0;top:0;transform:none";
    const box = tip.getBoundingClientRect();
    const ref = tip.parentElement.getBoundingClientRect();
    const below = ref.bottom + GAP;
    const above = ref.top - GAP - box.height;
    // Under it unless that runs off the bottom, and over it only if that is
    // somewhere the box actually fits: when neither edge has room, under is
    // the one the reader can scroll to.
    const top = below + box.height <= innerHeight - GAP || above < GAP ? below : above;
    const middle = ref.left + ref.width / 2 - box.width / 2;
    const left = Math.min(Math.max(middle, GAP), innerWidth - box.width - GAP);
    tip.style.cssText = `display:block;position:fixed;left:${left}px;top:${top}px;transform:none`;
  };
  // Handed back to the stylesheet, so that a box measured against one scroll
  // position is not still carrying those numbers at the next one. After a
  // pause, because the pointer leaves the reference on its way into the box,
  // and a box that closes on the way to it is a box nobody can reach or read.
  const release = (event) => {
    const tip = tipOf(event);
    if (!tip) return;
    clearTimeout(closing.get(tip));
    closing.set(tip, setTimeout(() => { tip.style.cssText = ""; }, HOLD));
  };
  for (const name of ["pointerover", "focusin"]) document.addEventListener(name, place);
  for (const name of ["pointerout", "focusout"]) document.addEventListener(name, release);
})();

# dau-in/dau-in — GitHub profile README

This repo generates the README shown on https://github.com/dau-in (the profile
README special-case: repo name == username). Read this before making changes —
several of the rules below come from real bugs found on the actual GitHub
mobile app, not theory.

## Architecture

- `build_readme.py` is the template: it assembles `README.md` from f-strings,
  reading generated card assets from `assets/`. **Never hand-edit `README.md`
  directly** — run `python build_readme.py` after editing the template instead,
  or your edit gets silently overwritten by the next bot refresh or the next
  person who runs the script.
- `scripts/build_*.py` each generate one card PNG by rendering an HTML/CSS
  string with headless Chrome, then cropping to content (steam, spotify,
  last-commit, wakatime, typing name banner). They need Chrome
  (`CHROME_PATH` env var or a few common install paths) and Pillow.
- `scripts/build_language_colors.py` / `build_language_icons.py` are one-off
  tools, not run by CI — re-run manually and occasionally to refresh
  `scripts/language_colors.json` / `language_icon_slugs.json` from
  GitHub linguist / devicon upstream.
- `.github/workflows/update-widgets.yml` runs all four dynamic cards
  (steam/spotify/last-commit/wakatime), then `build_readme.py`, then commits
  if anything changed. Triggers: `push` to main (instant refresh, and the
  only trigger where the last-commit card can trust `GITHUB_SHA` directly),
  and `workflow_dispatch` fired externally every 30 min by **cron-job.org**
  (GitHub's own `schedule:` trigger was tried first and dropped — confirmed
  unreliable, sat idle 10+ hours at a stretch). The dispatch uses a
  fine-grained PAT scoped to this repo's Actions only, **expires
  2026-09-28 — renew it** or the cron silently stops working.
- `design-assets/` is old profile-design scratch/iteration (mockup HTML/PNGs,
  layout catalogs, glyph tests) kept for reference, not tracked
  (`.gitignore`) and not part of the build.

## Local workflow

The external cron commits every ~30 min, so **always sync before editing**:
```
git stash push -q -m "wip" -- build_readme.py README.md   # if you have local changes already
git pull --rebase -q
git stash pop                                              # if you stashed
python build_readme.py                                     # regenerate, resolves README.md conflicts too
git add build_readme.py README.md
git commit -m "..."
git push   # if rejected, git pull --rebase && git push again
```
`git push` gets rejected fairly often mid-session just from the cron; that's
normal, not a sign anything is wrong.

## Hard constraints (found the hard way — verify on the actual GitHub mobile
app before assuming a fix works, desktop rendering hides all of these)

1. **No Unicode box-drawing characters** (`┌─│└┘├┤` etc., U+2500 block) in any
   ASCII-art content. Confirmed on the GitHub mobile app: that block falls
   back to a different, poorly-hinted font there and renders as a dashed
   line instead of solid, or misaligned, even though it's fine on desktop.
   Use plain ASCII instead: `+`/`-`/`|` for borders, `` |-- `` / `` `-- ``
   for tree connectors. This is real `tree --charset=ascii` output, not an
   invented workaround.
2. **`style="..."` on raw HTML is stripped** by GitHub's markdown sanitizer.
   Confirmed by shipping `<span style="color:...">` and finding it rendered
   as a bare `<span>` with no color in the live DOM. There is no way to get
   real per-character color in a README without it being baked into an
   actual image (PNG/SVG) — a fenced code block's own pixels aren't
   sanitized, but its text has zero styling control (no bold/color at all).
3. **Any unwrappable monospace block** (a fenced code block, `white-space:
   pre`) needs a `<table><td>` ancestor with a **definite width** — GitHub
   sets `overflow-x:auto` on the `<pre>` itself, but without a width-bound
   ancestor the box just expands past the viewport instead of scrolling.
   A bare `<div align="center">` does not count; a `<td>` does.
4. **Every line in that block must be padded to the same total width.**
   Confirmed: a block of *varying*-length lines, once wider than the mobile
   viewport, renders with each line's own scroll position seemingly
   centered independently instead of sharing one left edge — visibly
   staggered/misaligned. A block with a drawn border (`build_terminal_box`)
   is immune to this as a side effect of the border padding every line to
   equal width; anything without a border needs to pad on purpose (see how
   `build_terminal_box` does it, or just `.ljust(width)` every line
   including the header/prompt).
5. **Never nest a `<table>` inside a `<td>`.** Confirmed elsewhere in this
   file's history: it silently drops images on the GitHub mobile app
   specifically (fine on desktop/Chrome mobile). Independent sections that
   need their own width-bound wrapper go in separate top-level tables, not
   nested ones — see how the whoami box, the projects+cards table, and the
   widgets table are three separate `<table>`s in sequence rather than one
   nested structure.
6. The last-commit card's non-push fallback (`scripts/build_last_commit_card.py`)
   reads the repo list sorted by `pushed_at`, **not** the public events feed.
   The events feed was tried first and found to be worse than laggy —
   confirmed a repo that had just gone public never generated a single
   `PushEvent` for it at all, hours and several real commits later. A repo's
   own `pushed_at` is core metadata GitHub updates synchronously on every
   push. `dau-in/dau-in` itself is excluded from that repo list (its own bot
   refresh commits would otherwise always look like "the latest").
   `assets/last_commit_meta.json` is a small sidecar recording the freshness
   anchor behind whatever's currently shown, so a stale non-push run can't
   regress the card backward once a fresher commit has been recorded.

7. **An `<img>` can never claim table-column width.** GitHub injects
   `style="max-width:100%"` into every image it renders, so an image
   contributes *zero* min-content width: its column only gets what's left
   after its siblings are satisfied. Put an image cell next to a cell
   holding a fenced code block wider than the viewport and the image column
   collapses to 27px (td padding alone) and the image renders 0x0 — in the
   DOM, invisible on screen. Measured on the live profile at a 375px
   viewport: the projects row's code column demands 406px inside a 293px
   container. A 1x1 spacer *image* does not fix it (zero min-content for the
   same reason). Only real text claims min-content, so the photo cell holds
   its column open with `<br>` + a run of `&nbsp;` (`PHOTO_COL_SPACER` in
   `build_readme.py`, 18 of them ≈ 69px). The `<br>` is load-bearing —
   without it the run shares the image's line and the column's *max*-content
   grows to image+spacer, widening the desktop layout. The name-banner row
   up top is the same shape but survives untouched because its code block is
   only ~196px wide, so leftovers remain — **leave that one spacer-free**.
   Pinning it was tried and reverted: it pushed that row to 376px, so the
   name itself needed a sideways drag on a phone, and the spacer's own line
   adds ~24px under the image, which read as a gap on desktop because
   nothing else in that row is tall enough to absorb it. Down in the
   projects row the ps box is ~190px tall and absorbs it for free. That is
   also why the spacer is sized to 69px, what the top photo renders at,
   rather than the image's own 160px: the two GIFs then read as the same
   photo size. They can only match at one container width, since the top one
   is elastic and this one is pinned. Side effect: the photo column is
   real width now, so the projects table's scroll extent grew from 434px to
   502px. That's fine for the box itself (a wide terminal box scrolls
   sideways on a phone by design), but it dragged the last-commit and
   wakatime cards along, since a `colspan` cell is as wide as its table —
   they had to be scrolled to be seen whole, unlike every other card. Fixed
   by moving those two into their own table, see below.

8. **The name banner's code block is padded to 9 lines on purpose** (2 blank
   lines above the glyphs, 3 below, in `name_block`). Don't "clean up" those
   blank lines. At its natural 6 lines that box rendered 118px tall next to
   a 180px photo, a 60px gap that read as plainly misaligned. At 9 it comes
   out 187px, the same height as the projects box, so both rows put the
   photo in an identical relationship to the block beside it — measured on
   the live profile, the photo starts 9px below the box's top edge and ends
   2px past its bottom, in both. That 7px of overhang is the closest an
   integer number of lines gets to 180 (8 lines is 170, 10 is 205). Blank
   lines add height without width, so the header table stays as wide as it
   was and that row still fits a phone with nothing to scroll.

## Design decisions already made (don't re-propose these — they were tried
and explicitly rejected in favor of what's live now)

The "projects" section (photo + text next to it, above the last-commit/
wakatime cards) went through a lot of iteration. Rejected, in order:
- Devicon language badges/icons next to each project — two unrelated
  projects can share a language and end up looking identical; rejected as
  visually noisy regardless of styling (plain square icon, colored dot, all
  rejected).
- A fifth rendered PNG "card" matching the steam/spotify/wakatime style —
  rejected: "ya está demasiado lleno de cards", the page already has four.
- A bordered box around the photo, or around the photo+text pair — rejected
  explicitly, twice ("no border la foto, ni el bloque tampoco").
- Stacking the photo above the text (instead of side by side) — rejected as
  reading like two disconnected blocks, not one unit.
- A standalone ASCII terminal continuation (`$ chafa photo.gif` +
  `$ ls ~/projects`, its own table below whoami.cpp) — rejected on
  reorganization grounds: photo+text read better side by side in the
  original table than as a standalone block.
- Within the current side-by-side layout: a `tree ~/projects` rendering
  (two lines per project, zigzag) was tried and replaced with the current
  `ps`-style one-line-per-project table — the tree version's uneven line
  lengths per project read as less "designed" than a clean aligned table.

**Current state**: side-by-side table (photo left, `ps`-style terminal box
right, see `projects_box` / `projects_ps_lines` in `build_readme.py`), no
color, no icons, no border. The last-commit and wakatime cards are a
**separate top-level table** right below it, at a fixed pixel width
(`CARD_WIDTH`), not `colspan` rows of it and not `width="100%"`. They were
colspan rows once, so both halves would read as one block; that made their
width a hostage of the projects box's, and they overflowed a phone screen.
Split out, they shrink to the viewport, and on desktop both tables still
render 587px wide at the same left edge, so the section still reads as one
(only a 16px table margin between them now). A percentage width does *not*
work in the split table: it resolves against a table that is itself sizing
to its contents, collapsing the whole thing to 28px (measured). Re-measure
`CARD_WIDTH` if the projects box ever changes width. `fakalab` is suspended (commented out of the
project lists, not deleted) — `kintsugi` has no public repo yet either.

## Website / portfolio work does NOT belong in this repo or this thread

The personal portfolio site (separate from this GitHub profile) is being
planned and built in a different conversation. If asked to pick up website
work from here, redirect instead of improvising: the shared continuity file
is `X:\Dev\dauin\CONTEXT.md` (reference sites reviewed, design direction,
open items — see its "🔀 División de chats" section for the handoff).

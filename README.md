<div align="center">

![name](assets/typing_dark.png#gh-dark-mode-only)
![name](assets/typing_light.png#gh-light-mode-only)

</div>

<table align="center"><tr>
<td width="197" align="center" valign="middle"><a href="https://x.com/inoitoh"><img width="170" src="assets/section1_photos.gif"/></a></td>
<td align="center" valign="middle">

```
                     
                     
,--. ,---..   .|,   .
|   ||---||   |||\  |
|   ||   ||   ||| \ |
`--' `   '`---'``  `'
                     
                     
```

</td>
</tr></table>

<!-- table+td, not <div align="center"> -- on real mobile (GitHub app and
     Chrome mobile both) this box was rendering broken: overflow-x:auto is
     set on the <pre> same as everywhere else, but nothing above it in a bare
     <div> ancestor chain forces a definite (viewport-bound) width, so the
     unwrappable (white-space:pre) 846px-wide content just expands its own
     box instead of scrolling inside a contained one. A <td> is the one
     wrapper already proven (by the rest of this file) to hold its content
     to a definite width without GitHub stripping/ignoring it. -->
<table align="center"><tr><td align="center">

```
+- [dauin@cachyos ~]$ -----------------------------------------------------------+
| $ cat whoami.cpp                                                               |
|                                                                                |
| namespace dauin {                                                              |
|     constexpr auto role     = "Computer Engineer.";                            |
|     constexpr auto ai       = "\"Why is AI so addictive?\" "                   |
|                               "-- because architecting autonomy is fun.";      |
|     constexpr auto stack    = { "full-stack dev", "IT support", "network" };   |
|     constexpr auto mindset  = "Perpetual student with endless curiosity "      |
|                               "for how things tick.";                          |
|     constexpr auto hardware = "Hardware lover at the core.";                   |
|     constexpr auto vibe     = "Just for fun, I guess...";                      |
|     constexpr auto habitat  = "Living in the terminal (CachyOS enjoyer), "     |
|                               "but Windows is my cozy fallback.";              |
|     constexpr auto loop     = "Clauding my way forward, step by step.";        |
| }                                                                              |
|                                                                                |
| // -- [ Memory Log ] ----------------------------------------------------      |
| // "Everything that lives is designed to end"...                               |
| // meanwhile, I leave proof of my existence on my passport ↓                   |
|                                                                                |
| [dauin@cachyos ~]$ _                                                           |
+--------------------------------------------------------------------------------+
```

</td></tr></table>

<hr>

<!-- photo + projects box only. The last-commit and wakatime cards used to
     be colspan rows of this same table, so both halves would read as one
     block; they were split into the table below once that turned out to
     drag the cards' own width along with this row's (see the note there).
     Matching widths and align="center" on both keep them reading as one
     section anyway. -->
<table align="center">
<tr>
<td width="197" align="center" valign="middle">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br><a href="https://x.com/inoitoh"><img src="assets/section2_photos_v2.gif" width="170"/></a><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>
<td width="360" valign="middle">

```
+- [dauin@cachyos ~]$ ------------------------------+
| $ ps -o pid,stat,command -C projects              |
|                                                   |
| PID  STAT  PROJECT     DETAILS                    |
| 001  RUN   channel-3   NES emulator (WebGL CRT)   |
| 002  DEV   kintsugi    Go TUI / Windows DISM      |
| [dauin@cachyos ~]$ _                              |
+---------------------------------------------------+
```

</td>
</tr>
</table>

<!-- the two cards sit in their OWN table, not as colspan rows of the one
     above. They used to live there so both halves read as one block, but a
     colspan cell is as wide as its table, and that table is as wide as the
     photo column plus the (unwrappable, 406px) projects box -- 587px, which
     on a phone means the cards themselves had to be scrolled sideways to be
     seen whole, unlike every other card on the page. Split out, this table
     has nothing forcing it wide, so it shrinks to the viewport and the cards
     land complete. They still line up with the box above on desktop: 559 +
     28px of td padding is exactly the 587 that table renders at. width= here
     is a pixel count, NOT width="100%" -- a percentage resolves against a
     table that is itself sizing to its contents, which collapses the whole
     thing to 28px (measured). Re-measure CARD_WIDTH if the projects box ever
     changes width. -->
<table align="center">
<tr><td align="center"><a href="https://github.com/dau-in?tab=repositories"><picture><source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/dau-in/dau-in/cards/last_commit_card_light.png"><img src="https://raw.githubusercontent.com/dau-in/dau-in/cards/last_commit_card.png" width="576"/></picture></a></td></tr>
<tr><td align="center"><a href="https://github.com/dau-in?tab=repositories"><picture><source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/dau-in/dau-in/cards/wakatime_card_light.png"><img src="https://raw.githubusercontent.com/dau-in/dau-in/cards/wakatime_card.png" width="576"/></picture></a></td></tr>
</table>

<!-- Every image on this page is wrapped in an <a>, including the two photos
     and this card, because GitHub links any unwrapped image to its own raw
     file -- so a tap that looks like it should go somewhere just opens a
     PNG. The photos go to the artist credited in the footer; that credit
     line stays, since a link is invisible until someone taps it and is no
     substitute for visible attribution. This card points at the repos tab
     rather than wakatime.com/@dauin: that profile is private and 404s
     (checked). Repoint it here if it's ever made public.
     TODO: the typing name banner is the one image still unlinked -- it goes
     to the personal site once that exists (dauin.dev). It can't take a plain
     <a> wrapper, since the light/dark swap needs markdown image syntax;
     use [![name](...#gh-dark-mode-only)](url) instead. Rebuilt alongside the
     other cards by update-widgets.yml (scripts/build_wakatime_card.py). -->
<!-- TODO: add real repo link once Kintsugi has a demoable run -->

<hr>

<p align="center">∴ off the clock: games, music, and a terminal that never quite closes — full taste below ↓</p>

<!-- back to one unified table (colspan for passport/discord) -- three
     separate tables let each widget size independently, but on the native
     GitHub mobile app a <table> gets forced to width:100% regardless of
     what's inside it, which broke align="center" once the image was much
     narrower than that forced width (dead space that should've centered
     just... didn't, in the app specifically -- fine on web and Chrome
     mobile). Small standalone tables made that visible; one wide table
     doesn't leave enough dead space for it to be noticeable.
     Every width here is a pixel count now, and they add up on purpose: the
     passport/discord rows carry CARD_WIDTH, and the steam/spotify <td>s are
     301 and 302, which is not a typo. This row is what sets the table's
     width -- the passport/discord rows can't, because an image contributes
     no min-content width (see CLAUDE.md constraint 7), so their cells never
     claim anything. That leaves the total in 2px steps: 301+301 renders 603
     and 302+302 renders 605, both off the 604 the projects box and the
     cards above land on. One of each hits it exactly, and a pixel of
     difference between two cells holding centred images is invisible. The steam and spotify images went from 220 to
     275 in the same pass. Those two are drawn at 414 CSS px wide and were
     being shown at 220 -- 53% -- which put their 13px body text on screen
     at about 7px, and that is what reads as "blurry": not the source, the
     downscale. 275 is the widest they can be without this table growing
     past the others. -->
<table align="center">
<tr><td colspan="2" align="center"><a href="https://passportdex.com/dauin"><picture><source media="(prefers-color-scheme: light)" srcset="assets/passport_card_light.png"><img src="assets/passport_card.png" width="576"/></picture></a></td></tr>
<tr>
<td width="301" align="center"><a href="https://steamcommunity.com/id/dauin"><picture><source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/dau-in/dau-in/cards/steam_card_light.png"><img src="https://raw.githubusercontent.com/dau-in/dau-in/cards/steam_card.png" width="275"/></picture></a></td>
<td width="302" align="center"><a href="https://open.spotify.com/user/31aluwrafhtrzpee4pqzyodbvusm"><picture><source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/dau-in/dau-in/cards/spotify_card_light.png"><img src="https://raw.githubusercontent.com/dau-in/dau-in/cards/spotify_card.png" width="275"/></picture></a></td>
</tr>
<tr><td colspan="2" align="center"><a href="https://discord.com/users/780932598922084384"><picture><source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/dau-in/dau-in/cards/discord_card_light.png"><img src="https://raw.githubusercontent.com/dau-in/dau-in/cards/discord_card.png" width="576" alt="discord"/></picture></a></td></tr>
</table>

<!-- steam, spotify, last-commit, wakatime and discord cards (each with a
     _light twin) are rebuilt every 30 min and on every push by
     .github/workflows/update-widgets.yml (scripts/build_*_card.py) -- never
     hand-edited. The passport pair is rebuilt by hand. -->

<hr>

<p align="center"><sub>◇ art by <a href="https://x.com/inoitoh">@inoitoh</a> on twt</sub></p>

<!-- TODO: replace static passport card with a live embed once passportdex offers one -->

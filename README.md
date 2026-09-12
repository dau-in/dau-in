<div align="center">

![name](assets/typing_dark.png#gh-dark-mode-only)
![name](assets/typing_light.png#gh-light-mode-only)

</div>

<table align="center"><tr>
<td width="197" align="center" valign="middle"><img width="170" src="assets/section1_photos.gif"/></td>
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
<td width="197" align="center" valign="middle">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br><img src="assets/section2_photos_v2.gif" width="170"/><br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>
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
<tr><td align="center"><a href="https://github.com/dau-in/dau-in/commit/5d62a16de48b1c1ea2ca861dab6a6d2fe26e0b2f"><img src="assets/last_commit_card.png?v=34673161843" width="576"/></a></td></tr>
<tr><td align="center"><img src="assets/wakatime_card.png?v=34673161843" width="576"/></td></tr>
</table>

<!-- wakatime_card.png has no <a> wrapper -- unlike every other linked card
     here, there's nowhere real to send a click: this WakaTime account's
     profile is private (no public username set either), so a link would
     either 404 or point at a page that shows nothing. Rebuilt alongside the
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
     doesn't leave enough dead space for it to be noticeable. width="100%"
     on the passport/discord cells fills whatever the row actually renders
     as; pinning width= on the steam/spotify <td>s (their own natural size,
     +27 for GitHub's fixed td padding/border) keeps that column from being
     inflated by the wider colspan cells. -->
<table align="center">
<tr><td colspan="2" align="center"><a href="https://passportdex.com/dauin"><img src="assets/passport_card.png" width="100%"/></a></td></tr>
<tr>
<td width="247" align="center"><a href="https://steamcommunity.com/id/dauin"><img src="assets/steam_card.png?v=34673161843" width="220"/></a></td>
<td width="247" align="center"><a href="https://open.spotify.com/user/31aluwrafhtrzpee4pqzyodbvusm"><img src="assets/spotify_card.png?v=34673161843" width="220"/></a></td>
</tr>
<tr><td colspan="2" align="center"><a href="https://discord.com/users/780932598922084384"><img src="https://lanyard.cnrad.dev/api/780932598922084384?theme=dark&bg=000000&borderRadius=18px&animated=true&idleMessage=bored%2C+for+now&showDisplayName=true" width="100%" alt="discord"/></a></td></tr>
</table>

<!-- steam_card.png, spotify_card.png, and wakatime_card.png are rebuilt
     every 30 min and on every push by .github/workflows/update-widgets.yml
     (scripts/build_steam_card.py, build_spotify_card.py, build_wakatime_card.py)
     -- never hand-edited. -->

<hr>

<p align="center"><sub>◇ art by <a href="https://x.com/inoitoh">@inoitoh</a> on twt</sub></p>

<!-- TODO: replace static passport card with a live embed once passportdex offers one -->

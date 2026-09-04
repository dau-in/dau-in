<div align="center">

![name](assets/typing_dark.png#gh-dark-mode-only)
![name](assets/typing_light.png#gh-light-mode-only)

</div>

<table align="center"><tr>
<td><img width="180" src="assets/section1_photos.gif"/></td>
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

<!-- Continues the same terminal session as whoami.cpp above, not a new
     widget: chafa is a real Linux/CachyOS CLI image viewer, so the photo
     sits under a command that actually applies to an image instead of
     `ls` pretending to have produced it. Own <table><td> wrapper for the
     same overflow-x reason as whoami_box (unwrappable monospace content
     needs a definite-width ancestor to scroll inside on mobile) -- kept as
     its own table rather than merged into the cards table below, since
     nesting a table inside a table cell is the exact pattern that silently
     drops images on the GitHub mobile app (confirmed elsewhere in this
     file). Plain text/ASCII on purpose, not a rendered PNG like the other
     cards -- edit PROJECTS above directly, no script/secrets involved. -->
<table align="center"><tr><td align="center">

```
$ chafa section2.gif
```

<img src="assets/section2_photos_v2.gif" width="128"/>

```
$ ls ~/projects
channel-3  [live] NES emulator, browser-based — WebGL CRT, netplay
kintsugi   [wip]  Go TUI — Windows LTSB/LTSC ISOs, DISM internals
fakalab    [wip]  CS 1.6 knife skins, browser-based — palette rewrite, live 3D preview

[dauin@cachyos ~]$ _
```

</td></tr></table>

<hr>

<!-- Own table, not merged with the block above -- same reasoning: no
     nested tables. width="100%" on each image fills whatever the row
     actually renders as (same trick used for passport/discord under the
     widgets section) so back-to-back tables still read as one section
     instead of two unrelated floating boxes. Rebuilt every 30 min
     (cron-job.org pinging workflow_dispatch -- see
     .github/workflows/update-widgets.yml) and instantly on every push to
     this repo, by scripts/build_last_commit_card.py -- never hand-edited. -->
<table align="center">
<tr><td align="center"><a href="https://github.com/dau-in/dau-in/commit/26248143409580683cf2e05cd361c24e1ee31b84"><img src="assets/last_commit_card.png?v=33867074976" width="100%"/></a></td></tr>
<tr><td align="center"><img src="assets/wakatime_card.png?v=33867074976" width="100%"/></td></tr>
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
<td width="247" align="center"><a href="https://steamcommunity.com/id/dauin"><img src="assets/steam_card.png?v=33867074976" width="220"/></a></td>
<td width="247" align="center"><a href="https://open.spotify.com/user/31aluwrafhtrzpee4pqzyodbvusm"><img src="assets/spotify_card.png?v=33867074976" width="220"/></a></td>
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

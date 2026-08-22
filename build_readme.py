# -*- coding: utf-8 -*-
import pyfiglet, sys, os
sys.path.insert(0, os.path.join('..', 'dauin', 'design-assets'))
from unicode_styles import convert

def box(title, lines):
    width = max([len(l) for l in lines] + [len(title) + 4]) + 2
    top = '┌─ ' + title + ' ' + '─' * (width - len(title) - 4) + '┐'
    bot = '└' + '─' * (width - 2) + '┘'
    body = []
    for l in lines:
        pad = width - 2 - len(l)
        body.append('│ ' + l + ' ' * max(pad - 1, 0) + '│')
    return '\n'.join([top] + body + [bot])

def section_title(word):
    return convert(word, 'sans_bold')

name_banner = pyfiglet.figlet_format('DAUIN', font='thin').rstrip('\n')

typing_url = ('https://readme-typing-svg.demolab.com?font=Cutive+Mono&pause=1200'
              '&color=8B949E&center=true&vCenter=true&width=500'
              '&lines=still+typing+this+myself%2C+mostly;'
              'still+figuring+it+out;'
              'still+here%2C+still+terminal-pilled')

whoami_lines = [
 '▸ Computer Engineer',
 '→ Into agentic programming — building with AI, not just using it',
 '▪ Full-stack + IT support + networking, all in one',
 '▴ Eternal student — always hungry for more to learn',
 '≡ Hardware enthusiast at heart',
 '► Available for freelance & remote work',
 '○ I live in the terminal — and in the windows too (CachyOS main, though)',
 '» Clauding my way forward, step by step.',
 '● "Everything that lives is designed to end"... meanwhile, I leave proof',
 '   of my existence on my passport ↓',
]
whoami_box = box('whoami.txt', whoami_lines)

projects_lines = [
 'channel-3/   NES emulator, browser-based — WebGL CRT, netplay.  [soon]',
 'kintsugi/    Go TUI, Windows LTS ISOs — DISM internals.         [wip]',
]
projects_box = box('projects.log', projects_lines)

contact_lines = ['Best way to reach me →']
contact_box = box('contact.txt', contact_lines)

badge_style = 'style=flat-square&labelColor=0d1117&color=21262d'

readme = f'''<p align="center">

```
{name_banner}
```

<img src="{typing_url}" width="420" alt="typing"/>

</p>

<h2 align="center">{section_title('INTRO')}</h2>

<table align="center"><tr><td>
<img src="assets/section1_photos.gif" width="360"/>
</td></tr></table>

```
{whoami_box}
```

<!-- passportdex OG image blocked by Cloudflare when fetched by GitHub's camo proxy (server-side,
     no browser) -- confirmed broken, reverted to plain link. Darwin can grab a manual screenshot
     of https://passportdex.com/dauin/og himself (his browser has access) and hand it over to
     use as a static assets/passport_snapshot.png if he wants the visual card back. -->
<table align="center"><tr><td align="center">
<a href="https://passportdex.com/dauin"><b>→ full passport here</b></a>
</td></tr></table>

<h2 align="center">{section_title('PROJECTS')}</h2>

```
{projects_box}
```

<!-- TODO: swap in real repo link + final name once Channel 3 is published -->
<!-- TODO: add real repo link once Kintsugi has a demoable run -->

<h2 align="center">{section_title('CONTACT')}</h2>

<table align="center"><tr><td>
<img src="assets/section2_photos.gif" width="360"/>
</td></tr></table>

```
{contact_box}
```

<table align="center"><tr><td align="center">
<a href="https://github.com/dau-in"><b>→ github.com/dau-in</b></a>
</td></tr></table>

<p align="center">
<a href="https://discord.com/users/780932598922084384"><img src="https://img.shields.io/badge/Discord-.dauin-161b22?{badge_style}"/></a>
<a href="https://open.spotify.com/user/31aluwrafhtrzpee4pqzyodbvusm"><img src="https://img.shields.io/badge/Spotify-open-161b22?{badge_style}"/></a>
<a href="https://steamcommunity.com/id/dauin"><img src="https://img.shields.io/badge/Steam-dauin-161b22?{badge_style}"/></a>
</p>

<p align="center"><sub><img src="https://img.shields.io/badge/art%20by-%40inoitoh-161b22?{badge_style}"/></sub></p>

<!-- TODO: replace Discord badge with lanyard-profile-readme widget once account is monitored -->
<!-- TODO: Spotify/Steam -> real stats + last played/listened, once decided -->
<!-- TODO: stats section (WakaTime / github-readme-stats), once decided -->
'''

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)
print('written, whoami box width:', len(whoami_box.split(chr(10))[0]))

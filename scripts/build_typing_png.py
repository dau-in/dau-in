"""
Builds assets/typing_dark.png and assets/typing_light.png: an animated APNG
"decrypt" effect for the top of the README -- each character position starts
as a random katakana/symbol and resolves (staggered by position, easing from
fast flicker into a settle) into ダーウィン, Darwin's actual name, holds,
then re-scrambles in the exact reverse of that same eased sequence before
looping. Replaces an earlier typed-and-erased version; this reads better for
a name than a typewriter cadence does.

Two variants because a single color can't read well against both GitHub
themes: near-white text for dark mode (relies on plain antialiasing, no
shadow needed -- it's already high contrast against a dark page) and
near-black text for light mode (same reasoning, inverted). build_readme.py
wires them up via GitHub's #gh-dark-mode-only / #gh-light-mode-only URL
fragments so the right one shows automatically.

Both fonts are self-hosted (scripts/fonts/, SIL OFL -- see the *-OFL.txt
files next to each) and baked into the rendered pixels at build time:
Departure Mono for the Latin/symbol scramble characters (not on Google
Fonts, so it always had to be vendored), and now Noto Sans JP too (only the
katakana-covering subset, ~44KB) for the glyphs Departure Mono doesn't have.
Noto Sans JP *is* on Google Fonts, so pulling it via @import at build time
was the original approach -- but that meant every one of the ~27 headless
Chrome launches this script does had to fetch it fresh over the network
(Chrome doesn't share a font cache across separate --headless invocations),
which was the dominant cost per frame, not the frame count. Vendoring it
cut render time from minutes to seconds.

Frame renders are cached to fonts/../_render_cache next to this script,
keyed by a hash of everything that affects a frame's pixels (variant, text,
canvas size). Re-running after an interrupted build (e.g. power loss
mid-render) only re-renders whatever wasn't finished, instead of starting
over -- each frame costs real wall-clock time (a fresh Chrome launch), and
losing that repeatedly to something outside this script's control is exactly
what vendoring the font also isn't enough to prevent on its own.

Static content, no API/secrets involved -- re-run manually whenever the
name, scramble pool, or timing changes, same as build_passport_own.py.

Uses true alpha transparency (APNG, not GIF) so anti-aliased text edges stay
smooth against whatever page background sits behind them -- GIF's 1-bit
alpha would leave a hard fringe. Chrome needs
--default-background-color=00000000 to screenshot with alpha.
"""
import base64
import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
DEPARTURE_FONT_PATH = HERE / 'fonts' / 'DepartureMono-Regular.woff2'
NOTO_FONT_PATH = HERE / 'fonts' / 'NotoSansJP-Katakana.woff2'
ASSETS = HERE.parent / 'assets'
CACHE_DIR = HERE / '_render_cache'

NAME = 'ダーウィン'

# Katakana + a few symbols/digits to scramble through before each position
# locks onto its real character -- katakana so the noise still looks like it
# belongs to the same alphabet as the answer, symbols/digits for a bit of
# "encrypted data" texture instead of reading as just shuffled letters.
SCRAMBLE_POOL = list(
    'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン'
    '0123456789#$%&'
)

# Total decrypt-phase steps and the step at which each character position
# locks in, spread out so positions resolve left-to-right rather than all at
# once. The re-encrypt phase is this same sequence played backwards.
STEPS = 14
LOCK_STEP = [round(i * (STEPS - 4) / (len(NAME) - 1)) + 3 for i in range(len(NAME))]

# How many times each position's scramble character is redrawn before it
# locks, spaced with ease-in timing (t**3) so redraws land dense early (fast
# flicker) and sparse late (the char "holds" briefly right before settling).
REDRAWS_PER_POSITION = 6

# Fixed seed: re-running this script should reproduce the same scramble
# sequence rather than a new random one each time, and both theme variants
# should show the identical sequence as each other.
RANDOM_SEED = 7

CANVAS_W, CANVAS_H = 150, 38

VARIANTS = {
    'typing_dark.png': {'color': '#f0f0f0', 'shadow': '0 1px 1px rgba(0,0,0,0.45)'},
    'typing_light.png': {'color': '#1a1a1a', 'shadow': 'none'},
}


def find_chrome():
    import os
    import shutil
    for candidate in (
        os.environ.get('CHROME_PATH'),
        shutil.which('chrome'),
        shutil.which('chromium'),
        shutil.which('google-chrome'),
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    ):
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit('No Chrome/Chromium binary found -- set CHROME_PATH')


def build_css(departure_b64, noto_b64, color, shadow):
    return f'''
@font-face {{ font-family:"Departure Mono"; src:url(data:font/woff2;base64,{departure_b64}) format("woff2"); }}
@font-face {{ font-family:"Noto Sans JP Katakana"; src:url(data:font/woff2;base64,{noto_b64}) format("woff2"); font-weight:700; }}
html, body {{ background:transparent; margin:0; padding:0; -webkit-font-smoothing:antialiased; overflow:hidden; }}
.row {{
  font-family:"Departure Mono", "Noto Sans JP Katakana", monospace; font-size:22px; font-weight:700; color:{color}; white-space:nowrap;
  text-shadow: {shadow};
  padding:11px 6px;
  text-align:center;
}}
'''


def decrypt_sequence():
    """Per-step text for the decrypt phase: STEPS strings, each len(NAME) chars."""
    import random
    rng = random.Random(RANDOM_SEED)

    def redraw_steps(lock_step):
        steps = set()
        for k in range(REDRAWS_PER_POSITION):
            t = k / (REDRAWS_PER_POSITION - 1) if REDRAWS_PER_POSITION > 1 else 0
            eased = t ** 3
            steps.add(min(round(eased * (lock_step - 1)), lock_step - 1))
        return steps

    grid = []
    for pos, ch in enumerate(NAME):
        lock_step = LOCK_STEP[pos]
        redraws = redraw_steps(lock_step)
        seq = []
        current = None
        for step in range(STEPS):
            if step >= lock_step:
                current = ch
            elif step in redraws or current is None:
                current = rng.choice(SCRAMBLE_POOL)
            seq.append(current)
        grid.append(seq)

    return [''.join(grid[pos][step] for pos in range(len(NAME))) for step in range(STEPS)]


def cache_key(variant_name, text):
    raw = f'{variant_name}|{CANVAS_W}x{CANVAS_H}|{text}'
    return hashlib.sha1(raw.encode('utf-8')).hexdigest()[:16]


def render_frame(css, text, variant_name, html_path, chrome):
    """Renders (or reuses a cached render of) one frame; returns a PIL Image."""
    from PIL import Image

    cached = CACHE_DIR / f'{cache_key(variant_name, text)}.png'
    if cached.exists():
        return Image.open(cached).convert('RGBA')

    html_path.write_text(
        f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head>'
        f'<body><div class="row">{text}</div></body></html>',
        encoding='utf-8',
    )
    subprocess.run([
        chrome, '--headless', '--disable-gpu', '--no-sandbox',
        '--default-background-color=00000000',
        '--force-device-scale-factor=2', f'--window-size={CANVAS_W},{CANVAS_H}',
        '--virtual-time-budget=500', f'--screenshot={cached}', f'file:///{html_path.as_posix()}',
    ], check=True, capture_output=True)
    return Image.open(cached).convert('RGBA')


def build_variant(variant_name, css, out_path, chrome, tmp, decrypt_texts):
    from PIL import Image

    html_path = tmp / 'frame.html'
    frames = []
    durations = []

    for text in decrypt_texts:
        frames.append(render_frame(css, text, variant_name, html_path, chrome))
        durations.append(70)
    durations[-1] = 2200  # hold on the fully-resolved name before re-scrambling

    for text in reversed(decrypt_texts[:-1]):
        frames.append(render_frame(css, text, variant_name, html_path, chrome))
        durations.append(70)
    durations[-1] = 400  # brief beat on the fully-scrambled state before looping

    # Plain markdown ![]() image syntax is what actually gets GitHub's
    # #gh-dark-mode-only / #gh-light-mode-only theme-swap treatment -- a raw
    # HTML <img src="...#gh-dark-mode-only"> does NOT (confirmed by fetching
    # the rendered page: no picture wrap, no hiding class, both shown at
    # once). Markdown image syntax has no width= to scale a 2x render back
    # down, so instead we render at 2x for antialiasing quality and then
    # downscale the frames here -- the file's own pixel width ends up being
    # the actual display width, no HTML-side scaling needed.
    frames = [f.resize((f.width // 2, f.height // 2), Image.LANCZOS) for f in frames]

    # disposal=0 (APNG_DISPOSE_OP_NONE): each of our frames is a complete,
    # independent screenshot, not a hand-computed delta -- Pillow's own APNG
    # writer diffs consecutive frames into a minimal patch + bbox for us.
    # disposal=2 (clear-to-background between frames) breaks that: it wipes
    # the canvas the next frame's small patch was assuming was still there,
    # so playback showed almost nothing but the cursor.
    frames[0].save(
        out_path, save_all=True, append_images=frames[1:],
        duration=durations, loop=0, disposal=0,
    )
    print('written', out_path, 'frames:', len(frames))


def main():
    import tempfile

    chrome = find_chrome()
    departure_b64 = base64.b64encode(DEPARTURE_FONT_PATH.read_bytes()).decode()
    noto_b64 = base64.b64encode(NOTO_FONT_PATH.read_bytes()).decode()
    decrypt_texts = decrypt_sequence()
    CACHE_DIR.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for filename, style in VARIANTS.items():
            css = build_css(departure_b64, noto_b64, style['color'], style['shadow'])
            build_variant(filename, css, ASSETS / filename, chrome, tmp, decrypt_texts)

    # cache is intentionally left on disk (gitignored) for a fast re-run if
    # timing/color get tweaked again -- delete scripts/_render_cache by hand
    # if the scramble pool or name itself changes and you want a clean slate


if __name__ == '__main__':
    main()

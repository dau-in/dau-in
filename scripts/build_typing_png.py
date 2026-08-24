"""
Builds assets/typing_dark.png and assets/typing_light.png: an animated APNG
typing effect for the top of the README, replacing the old
readme-typing-svg.demolab.com widget so the font can be Departure Mono (a
pixel monospace font, not on Google Fonts -- that external service only
accepts Google Fonts family names, so it had to go).

Two variants because a single color can't read well against both GitHub
themes: near-white text for dark mode (relies on plain antialiasing, no
shadow needed -- it's already high contrast against a dark page) and
near-black text for light mode (same reasoning, inverted). build_readme.py
wires them up via GitHub's #gh-dark-mode-only / #gh-light-mode-only URL
fragments so the right one shows automatically. An earlier version used a
single light-gray-with-drop-shadow image for both themes; the shadow's blur
read as muddy rather than crisp, hence the split.

Font is self-hosted (scripts/fonts/DepartureMono-Regular.woff2, SIL OFL --
see DepartureMono-OFL.txt) and baked into the rendered pixels at build time;
nothing downloads it at README view time.

Static content, no API/secrets involved -- re-run manually whenever the
lines or styling change, same as build_passport_own.py.

Uses true alpha transparency (APNG, not GIF) so anti-aliased text edges stay
smooth against whatever page background sits behind them -- GIF's 1-bit
alpha would leave a hard fringe. Chrome needs
--default-background-color=00000000 to screenshot with alpha.
"""
import base64
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
FONT_PATH = HERE / 'fonts' / 'DepartureMono-Regular.woff2'
ASSETS = HERE.parent / 'assets'

LINES = [
    'still typing this myself, mostly',
    'still figuring it out',
    'still here, still terminal-pilled',
]

CANVAS_W, CANVAS_H = 430, 38

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


def build_css(font_b64, color, shadow):
    return f'''
@font-face {{ font-family:"Departure Mono"; src:url(data:font/woff2;base64,{font_b64}) format("woff2"); }}
html, body {{ background:transparent; margin:0; padding:0; -webkit-font-smoothing:antialiased; overflow:hidden; }}
.row {{
  font-family:"Departure Mono", monospace; font-size:16px; color:{color}; white-space:nowrap;
  text-shadow: {shadow};
  padding:11px 6px;
}}
'''


def render_frame(css, text, html_path, out_path, chrome):
    html_path.write_text(
        f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head>'
        f'<body><div class="row">{text}_</div></body></html>',
        encoding='utf-8',
    )
    subprocess.run([
        chrome, '--headless', '--disable-gpu', '--no-sandbox',
        '--default-background-color=00000000',
        '--force-device-scale-factor=2', f'--window-size={CANVAS_W},{CANVAS_H}',
        '--virtual-time-budget=600', f'--screenshot={out_path}', f'file:///{html_path.as_posix()}',
    ], check=True, capture_output=True)


def build_variant(css, out_path, chrome, tmp):
    html_path = tmp / 'frame.html'
    frames = []
    durations = []

    for line in LINES:
        from PIL import Image
        line_frames = []
        for i in range(len(line) + 1):
            out = tmp / f'f{i}.png'
            render_frame(css, line[:i], html_path, out, chrome)
            line_frames.append(Image.open(out).convert('RGBA'))
            out.unlink()

        for img in line_frames:
            frames.append(img)
            durations.append(55)
        durations[-1] = 1100  # hold on the completed line

        for img in reversed(line_frames[:-1]):
            frames.append(img)
            durations.append(30)
        durations[-1] = 150  # brief pause on empty before the next line

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
    font_b64 = base64.b64encode(FONT_PATH.read_bytes()).decode()

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for filename, style in VARIANTS.items():
            css = build_css(font_b64, style['color'], style['shadow'])
            build_variant(css, ASSETS / filename, chrome, tmp)


if __name__ == '__main__':
    main()

"""
Builds assets/typing.png: an animated APNG typing effect for the top of the
README, replacing the old readme-typing-svg.demolab.com widget so the font
can be Departure Mono (a pixel monospace font, not on Google Fonts -- that
external service only accepts Google Fonts family names, so it had to go).

Font is self-hosted (scripts/fonts/DepartureMono-Regular.woff2, SIL OFL --
see DepartureMono-OFL.txt) and baked into the rendered pixels at build time;
nothing downloads it at README view time.

Static content, no API/secrets involved -- re-run manually whenever the
lines or styling change, same as build_passport_own.py.

Uses true alpha transparency (APNG, not GIF) so the text-shadow's blur stays
smooth -- GIF's 1-bit alpha would leave a hard fringe around a soft shadow.
Chrome needs --default-background-color=00000000 to screenshot with alpha.
"""
import base64
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
FONT_PATH = HERE / 'fonts' / 'DepartureMono-Regular.woff2'
OUT_PATH = HERE.parent / 'assets' / 'typing.png'

LINES = [
    'still typing this myself, mostly',
    'still figuring it out',
    'still here, still terminal-pilled',
]

CANVAS_W, CANVAS_H = 430, 38


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


def build_css(font_b64):
    return f'''
@font-face {{ font-family:"Departure Mono"; src:url(data:font/woff2;base64,{font_b64}) format("woff2"); }}
html, body {{ background:transparent; margin:0; padding:0; -webkit-font-smoothing:antialiased; overflow:hidden; }}
.row {{
  font-family:"Departure Mono", monospace; font-size:16px; color:#d8d8d8; white-space:nowrap;
  text-shadow: 0 1px 0 rgba(0,0,0,0.9), 0 0 4px rgba(0,0,0,0.85), 0 0 10px rgba(0,0,0,0.55);
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


def main():
    import tempfile
    from PIL import Image

    chrome = find_chrome()
    font_b64 = base64.b64encode(FONT_PATH.read_bytes()).decode()
    css = build_css(font_b64)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        html_path = tmp / 'frame.html'

        frames = []
        durations = []

        for line in LINES:
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

        frames[0].save(
            OUT_PATH, save_all=True, append_images=frames[1:],
            duration=durations, loop=0, disposal=2,
        )
        print('written', OUT_PATH, 'frames:', len(frames))


if __name__ == '__main__':
    main()

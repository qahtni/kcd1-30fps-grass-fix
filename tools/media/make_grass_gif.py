#!/usr/bin/env python3
"""Side-by-side grass comparison: left half 'Without mod', right half 'With mod', in the shadows mod's label style.

usage: make_grass_gif.py WITHOUT.mkv WITH.mkv OUT_DIR FONTLIB.gfx [name=grass_compare] [scale=1.0] [colors=256] [dither=bayer:bayer_scale=4] [crop=W:H:X:Y] (crop is applied to both inputs before scale)

Both inputs are same-size clips with the same number of frames (one captured frame each). Writes
  OUT_DIR/NAME.gif   every captured frame shown for 0.02 s (50 a second: the fastest a GIF plays reliably)
  OUT_DIR/NAME.mp4   the same frames at the true 60 a second
Labels use the game's menu font (WHS Champ Fleury Pro) drawn by gfx_font_text.py (next to this script).
"""
import os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

a_path, b_path, out, fontlib = sys.argv[1:5]
opts = dict(a.split('=', 1) for a in sys.argv[5:])
name, scale = opts.get('name', 'grass_compare'), float(opts.get('scale', '1.0'))
colors, dither = opts.get('colors', '256'), opts.get('dither', 'bayer:bayer_scale=4')
GFX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gfx_font_text.py')
CREAM = (242, 232, 208)
os.makedirs(out, exist_ok=True)
tmp = tempfile.mkdtemp(dir=out)
w, h = (int(x) for x in subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
        'stream=width,height', '-of', 'csv=p=0', a_path], capture_output=True, text=True, check=True).stdout.strip().split(','))
crop = opts.get('crop')
if crop: w, h = (int(x) for x in crop.split(':')[:2])
w, h = int(w * scale) // 2 * 2, int(h * scale) // 2 * 2
k = max(h / 1080 * 1.2, 0.42)        # label size: a little larger than on the shadows mod's 1080p stills; readable on small GIFs


def label(text):
    p = f'{tmp}/{text}.png'
    subprocess.run([sys.executable, '-I', GFX, fontlib, 'WHS Champ Fleury Pro', text, str(round(64 * k)), p],
                   check=True, stdout=subprocess.DEVNULL)
    a = Image.open(p).getchannel('A')
    a = a.crop(a.getbbox())
    pad_x, pad_y = round(26 * k), round(16 * k)
    box = Image.new('RGBA', (a.width + 2 * pad_x, a.height + 2 * pad_y), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, box.width - 1, box.height - 1), radius=round(12 * k), fill=(12, 10, 8, 150))
    shadow = Image.new('RGBA', a.size, (0, 0, 0, 255)); shadow.putalpha(a.filter(ImageFilter.GaussianBlur(2 * k)))
    txt = Image.new('RGBA', a.size, CREAM + (255,)); txt.putalpha(a)
    box.alpha_composite(shadow, (pad_x + 1, pad_y + 1)); box.alpha_composite(txt, (pad_x, pad_y))
    return box


ov = Image.new('RGBA', (2 * w, h), (0, 0, 0, 0))
m = round(32 * k)
la, lb = label('Without mod'), label('With mod')
ov.alpha_composite(la, (m, m)); ov.alpha_composite(lb, (2 * w - m - lb.width, m))
d = ImageDraw.Draw(ov)
d.rectangle((w - 3, 0, w + 2, h), fill=(12, 10, 8, 255)); d.rectangle((w - 1, 0, w, h), fill=CREAM + (255,))
ov.save(f'{tmp}/overlay.png')
cf = f'crop={crop},' if crop else ''
base = (f'[0:v]setpts=N/(60*TB),{cf}scale={w}:{h}:flags=lanczos[a];[1:v]setpts=N/(60*TB),{cf}scale={w}:{h}:flags=lanczos[b];[a][b]hstack[s];'
        f'[s][2:v]overlay=0:0:format=auto,format=rgb24')
ins = ['-i', a_path, '-i', b_path, '-i', f'{tmp}/overlay.png']
gif, mp4 = f'{out}/{name}.gif', f'{out}/{name}.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex',
                base + f',setpts=N/(50*TB),split[x][y];[x]palettegen=max_colors={colors}:stats_mode=full[p];'
                       f'[y][p]paletteuse=dither={dither}:diff_mode=rectangle', '-r', '50', '-loop', '0', gif], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', base + ',setpts=N/(60*TB),format=yuv420p',
                '-r', '60', '-c:v', 'libx264', '-crf', '15', '-preset', 'slow', '-movflags', '+faststart', mp4], check=True)
for f in os.listdir(tmp): os.remove(f'{tmp}/{f}')
os.rmdir(tmp)
for p in (gif, mp4):
    n = subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries',
                        'stream=nb_read_packets,width,height,avg_frame_rate', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout.strip()
    print(p, os.path.getsize(p) // 1024, 'KB', n)

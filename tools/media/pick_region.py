#!/usr/bin/env python3
"""Pick the crop and the time windows for the grass comparison GIF.

usage: pick_region.py ON.gray ON.pts OFF.gray OFF.pts OFF_VALID_SECONDS CROP_W CROP_H [FRAMES=180]
The .gray files are 480x270 8-bit proxies (1/8 of the 4K capture), .pts the frame times in seconds.
Prints the crop (native 4K pixels) where the stock grass steps the most, and for each clip the start time of the
FRAMES-long window with the most movement inside that crop that has no capture gap in it.
"""
import sys, numpy as np
on_g, on_p, off_g, off_p = sys.argv[1:5]
valid, cw, ch = float(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7])
nf = int(sys.argv[8]) if len(sys.argv) > 8 else 180
W, H, B, S = 480, 270, 5, 8          # proxy size, block size in proxy pixels, proxy scale

def blocks(path, pts_path, tmax=1e9):
    pts = np.array([float(x) for x in open(pts_path)])
    m = np.memmap(path, dtype=np.uint8, mode='r').reshape(-1, H, W)
    n = min(len(m), len(pts), int(np.searchsorted(pts, tmax)))
    d = np.zeros((n, H // B, W // B), np.float32)
    prev = m[0].astype(np.int16)
    for i in range(1, n):
        cur = m[i].astype(np.int16)
        d[i] = np.abs(cur - prev).reshape(H // B, B, W // B, B).mean((1, 3))
        prev = cur
    return pts[:n], d

p_on, d_on = blocks(on_g, on_p)
p_off, d_off = blocks(off_g, off_p, valid)
g = d_off.reshape(len(d_off), -1).mean(1)
thr = np.sort(g[1:])[int(len(g) * 0.52)]            # stock: about 52 % of frames show no grass step
lo = g[1:] <= thr
step = np.r_[False, ~lo]
print('fix off: frames %d, movement on quiet frames %.3f, on step frames %.3f, step share %.2f' %
      (len(g), g[1:][lo].mean(), g[1:][~lo].mean(), step.mean()))
M = d_off[step].mean(0) - d_off[1:][lo].mean(0)     # stepped part of the movement per block
bw, bh = cw // (B * S), ch // (B * S)
I = np.pad(M, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
score = I[bh:, bw:] - I[:-bh, bw:] - I[bh:, :-bw] + I[:-bh, :-bw]
by, bx = np.unravel_index(score.argmax(), score.shape)
x, y = bx * B * S, by * B * S
print('crop (native): %dx%d at x=%d y=%d  (stepped movement %.2f, frame average %.2f)' % (cw, ch, x, y, score.max() / (bw * bh), M.mean()))

def best(pts, d, name):
    e = d[:, by:by + bh, bx:bx + bw].mean((1, 2))
    c = np.r_[0, e.cumsum()]
    gap = np.r_[0, (np.diff(pts) > 0.021).cumsum()]
    best_i, best_v = None, -1
    for i in range(30, len(e) - nf - 30):
        if gap[i + nf] != gap[i - 1]: continue
        v = c[i + nf] - c[i]
        if v > best_v: best_i, best_v = i, v
    print('%s: best window starts at frame %d, t=%.3f s (movement %.2f; clip average %.2f)' % (name, best_i, pts[best_i], best_v / nf, e.mean()))
best(p_on, d_on, 'fix on'); best(p_off, d_off, 'fix off')
np.save('/mnt/cache/kcd1-grass-proxy/M.npy', M)

# check_bind.py WHGame.dll sig.h: offline re-run of kcd_water.c bind() (scan1 uniqueness in .text, decode rows, helper bodies).
import sys, re, struct, pefile
dll, sigh = sys.argv[1], sys.argv[2]
src = open(sigh).read()
sigs = {}
for m in re.finditer(r'static const short (\w+)\[(\d+)\] = \{(.*?)\};', src, re.S):
    vals = [(-1 if t.strip() == 'X' else int(t, 16)) for t in m.group(3).replace('\n', '').split(',') if t.strip()]
    assert len(vals) == int(m.group(2)), m.group(1)
    sigs[m.group(1)] = vals
decs = {}
for m in re.finditer(r'static const struct dec (\w+)\[\] = \{(.*?)\n\};', src, re.S):
    rows = re.findall(r'\{ "(\w+)", (0x[0-9a-f]+), (DK_\w+), (\d+), (\d+), (0x[0-9a-f]+)ull \}', m.group(2))
    decs[m.group(1)] = {r[0]: (int(r[1], 16), r[2], int(r[3]), int(r[4]), int(r[5], 16)) for r in rows}
pe = pefile.PE(dll, fast_load=True); img = pe.get_memory_mapped_image(); base = pe.OPTIONAL_HEADER.ImageBase
text = [s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text'][0]
t0, tl = text.VirtualAddress, text.Misc_VirtualSize
code = [s.Name.rstrip(b'\0') for s in pe.sections if s.Characteristics & 0x20000000]
print('executable sections:', code, '.text', hex(t0), hex(tl))
def rx(p): return re.compile(b''.join(b'.' if b < 0 else re.escape(bytes([b])) for b in p), re.S)
def scan1(name):
    hits = [m.start() + t0 for m in rx(sigs[name]).finditer(img, t0, t0 + tl)]
    # overlapping matches: finditer is non-overlapping; re-check by stepping
    allh = []; pos = t0
    r = rx(sigs[name])
    while True:
        m = r.search(img, pos, t0 + tl)
        if not m: break
        allh.append(m.start()); pos = m.start() + 1
    print(f'{name}: {len(allh)} matches', [hex(h) for h in allh][:4])
    return allh[0] if len(allh) == 1 else None
def match_at(rva, name):
    p = sigs[name]
    if not (t0 <= rva and rva + len(p) <= t0 + tl): print(name, 'outside .text'); return False
    ok = all(b < 0 or img[rva + j] == b for j, b in enumerate(p))
    print(f'{name} at {rva:#x}: {"ok" if ok else "DIFFERS"}'); return ok
def dec(tab, at, name):
    off, kind, a, b, want = decs[tab][name]; va = at + off
    if kind == 'DK_RIP': v = va + b + struct.unpack_from('<i', img, va + a)[0]
    elif kind == 'DK_CALL': v = va + 5 + struct.unpack_from('<i', img, va + 1)[0]
    elif kind == 'DK_D32': v = struct.unpack_from('<I', img, va + a)[0]
    elif kind == 'DK_D8': v = img[va + a]
    else: v = va
    flag = '' if v == want else '   <-- differs from 1.9.8 row'
    print(f'  {tab}.{name} = {v:#x}{flag}')
    return v
r = scan1('SIG_RENDER'); cs = scan1('SIG_CREATE_SITE')
assert r is not None and cs is not None
# whole Render body by hash, as body_ok() in kcd_water.c does it
blen = int(re.search(r'#define SIG_RENDER_LEN (\d+)', src).group(1)); bhash = int(re.search(r'#define SIG_RENDER_HASH (0x[0-9a-f]+)ull', src).group(1), 16)
bm = re.search(r'static const unsigned char SIG_RENDER_MASK\[(\d+)\] = \{[^\n]*\n(.*?)\};', src, re.S)
bmask = [int(t, 16) for t in bm.group(2).replace('\n', '').split(',') if t.strip()]; assert len(bmask) == int(bm.group(1)) == (blen + 7) // 8
h = 0xcbf29ce484222325
for j in range(blen): h = ((h ^ (0 if (bmask[j >> 3] >> (j & 7)) & 1 else img[r + j])) * 0x100000001b3) & 0xffffffffffffffff
print(f'SIG_RENDER body {blen} bytes: hash {h:#018x}', 'ok' if h == bhash else 'DIFFERS'); assert h == bhash
E = {k: dec('DEC_RENDER', r, k) for k in decs['DEC_RENDER']}
assert dec('DEC_CREATE_SITE', cs, 'DDN_PTR') == E['DDN_PTR']
nm = dec('DEC_CREATE_SITE', cs, 'NAME_PTR'); assert img[nm:nm + 19] == b'$WaterRipplesDDN_0\0'
crt = dec('DEC_CREATE_SITE', cs, 'FN_CREATERT')
ok = True
for fn, sg in [('FN_PUSH', 'SIG_FN_PUSH'), ('FN_POP', 'SIG_FN_POP'), ('FN_SHBEGIN', 'SIG_FN_SHBEGIN'), ('FN_SHEND', 'SIG_FN_SHEND'),
               ('FN_SETPSF', 'SIG_FN_SETPSF'), ('FN_SETTEX', 'SIG_FN_SETTEX'), ('FN_DRAWTRI', 'SIG_FN_DRAWTRI'), ('FN_GENMIPS', 'SIG_FN_GENMIPS')]:
    ok &= match_at(E[fn], sg)
ok &= match_at(crt, 'SIG_FN_CREATERT')
sb = E['FN_SHBEGIN']; assert dec('DEC_SHBEGIN', sb, 'CURPFX_PTR') == E['CURPFX_PTR']
st = dec('DEC_SHBEGIN', sb, 'FN_SETTECH'); ok &= match_at(st, 'SIG_FN_SETTECH')
for k in decs['DEC_SETTECH']: dec('DEC_SETTECH', st, k)
assert dec('DEC_SETPSF', E['FN_SETPSF'], 'RD_PTR') == E['RD_PTR']
pl = dec('DEC_SETPSF', E['FN_SETPSF'], 'FN_PLOOKUP'); ok &= match_at(pl, 'SIG_FN_PLOOKUP')
for k in decs['DEC_SETPSF']: dec('DEC_SETPSF', E['FN_SETPSF'], k)
for k in decs['DEC_PLOOKUP']: dec('DEC_PLOOKUP', pl, k)
for k in decs['DEC_GENMIPS']: dec('DEC_GENMIPS', E['FN_GENMIPS'], k)
step = struct.unpack_from('<d', img, E['STEP_PTR'])[0]; print('step', step); assert step == 0.025
print('A1 bytes', img[E['A1_SITE']:E['A1_SITE'] + 2].hex())
print('entry', img[r:r + 7].hex())
# CopyScreenToTexture: utils vtable is in .rdata, slot filled by relocation (static), check it statically too
print('render entry rva', hex(r), 'all helpers ok' if ok else 'HELPER MISMATCH')

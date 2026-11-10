#!/usr/bin/env python3
"""Generate sig.h for KCDWater from the stock Steam 1.9.8 WHGame.dll.

usage: gen_sig.py WHGame.dll sig.h

Every signature is the exact byte image of a code range of the stock DLL with the parts that move between builds
(RIP-relative disp32, rel32 of call/jmp/jcc) replaced by wildcards (-1). Each decode offset used by the plugin is
asserted here against the stock bytes (opcode bytes and the 1.9.8 value it yields), so a wrong offset fails the build,
not the game.
"""
import sys, hashlib, struct, zlib
import pefile, capstone

STOCK_SHA = 'cf9f6dc384edcf35c20647a912745ddb8adb5ba65953e329c24e89dd9c4381aa'
path, out = sys.argv[1], sys.argv[2]
raw = open(path, 'rb').read()
if hashlib.sha256(raw).hexdigest() != STOCK_SHA:
    sys.exit('not the stock Steam 1.9.8 WHGame.dll (sha256 differs)')
pe = pefile.PE(data=raw, fast_load=True)
BASE = pe.OPTIONAL_HEADER.ImageBase
data = pe.__data__
def v2o(v):
    for s in pe.sections:
        a = BASE + s.VirtualAddress
        if a <= v < a + s.SizeOfRawData:
            return s.PointerToRawData + v - a
    raise ValueError(hex(v))
def rd(v, n): o = v2o(v); return bytes(data[o:o + n])
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); md.detail = True

def masked(va, n):
    code = rd(va, n); m = list(code); end = None
    for i in md.disasm(code, va):
        o = i.address - va
        if i.disp_offset and 'rip' in i.op_str:
            for k in range(4): m[o + i.disp_offset + k] = -1
        if i.mnemonic in ('call', 'jmp') and i.size == 5 and code[o] in (0xe8, 0xe9):
            for k in range(1, 5): m[o + k] = -1
        if i.mnemonic.startswith('j') and i.size == 6 and code[o] == 0x0f:
            for k in range(2, 6): m[o + k] = -1
        end = i.address + i.size
    if end != va + n:
        sys.exit(f'range {va:#x}+{n:#x} does not end on an instruction boundary (last end {end:#x})')
    return m

def u32(v): return struct.unpack('<I', rd(v, 4))[0]
def i32(v): return struct.unpack('<i', rd(v, 4))[0]
def rip(insn_va, disp_off, insn_len): return insn_va + insn_len + i32(insn_va + disp_off)
def expect(va, hexbytes, what):
    want = bytes.fromhex(hexbytes)
    if rd(va, len(want)) != want:
        sys.exit(f'{what}: bytes at {va:#x} are {rd(va, len(want)).hex()} not {hexbytes}')

# ---------------------------------------------------------------- CWaterRipples::Render (vtable slot 6)
RENDER = 0x182086cfc; RENDER_LEN = 0x6f7
# (name, offset of the instruction, expected leading bytes, kind, extra) ; kinds:
#   rip: (disp offset in insn, insn length) -> absolute target   | call: rel32 target   | d32 / d8: displacement value
R = [
    ('RECUR_PTR',  0x020, '488b0d',     'rip', 3, 7,  0x1829d1780),
    ('VT_RECUR',   0x044, 'ff90',       'd32', 2, 0,  0x3a0),
    ('OFF_RECUR_B',0x04d, '4438a0',     'd32', 3, 0,  0x248),
    ('OFF_RECUR_I',0x066, '4439a0',     'd32', 3, 0,  0x24c),
    ('DDN_PTR',    0x073, '4c3925',     'rip', 3, 7,  0x18378f790),
    ('BBS_PTR',    0x080, '488b05',     'rip', 3, 7,  0x18358fd48),
    ('OFF_DEVTEX', 0x090, '4c3960',     'd8',  3, 0,  0x30),
    ('RD_PTR',     0x09a, '488b0d',     'rip', 3, 7,  0x183786ba0),
    ('OFF_TID',    0x0af, '8b99',       'd32', 2, 0,  0x4bec),
    ('VT_GETVP',   0x14d, 'ff90',       'd32', 2, 0,  0x158),
    ('STRIDE_TI',  0x15d, '4869eb',     'd32', 3, 0,  0x338),
    ('OFF_TIME',   0x167, 'f20f10b429', 'd32', 5, 0,  0x4bf8),
    ('VT_GPU',     0x170, 'ff90',       'd32', 2, 0,  0x8c8),
    ('OFF_LAST',   0x186, 'f20f5c4e',   'd8',  4, 0,  0x38),
    ('A1_SITE',    0x18e, '7533',       'at',  0, 0,  0x182086e8a),
    ('STEP_PTR',   0x190, 'f20f1005',   'rip', 4, 8,  0x1827d8fd0),
    ('OFF_SNAP',   0x273, '448866',     'd8',  3, 0,  0x48),
    ('S0_PTR',     0x3c9, '488b05',     'rip', 3, 7,  0x183786c78),
    ('R_OBJ',      0x3d0, '488d2d',     'rip', 3, 7,  0x1834c6980),
    ('S1_PTR',     0x3d7, '480b05',     'rip', 3, 7,  0x183786c80),
    ('OFF_FLAGS',  0x3e1, '4c8bbb',     'd32', 3, 0,  0x5a40),
    ('FN_PUSH',    0x410, 'e8',         'call',1, 5,  0x1802dce08),
    ('VT_SETVP',   0x44c, 'ff97',       'd32', 2, 0,  0xbb8),
    ('OFF_CRC',    0x49d, '488d56',     'd8',  3, 0,  0x18),
    ('SHPE_PTR',   0x4b5, '488b0d',     'rip', 3, 7,  0x183786b58),
    ('FN_SHBEGIN', 0x4bc, 'e8',         'call',1, 5,  0x1803c00dc),
    ('VT_STATE',   0x4db, 'ff90',       'd32', 2, 0,  0xc98),
    ('FN_SETPSF',  0x4ef, 'e8',         'call',1, 5,  0x1802dba00),
    ('FN_SETTEX',  0x508, 'e8',         'call',1, 5,  0x1802da9f4),
    ('FN_DRAWTRI', 0x533, 'e8',         'call',1, 5,  0x1803c0980),
    ('FN_SHEND',   0x538, 'e8',         'call',1, 5,  0x1802ebe20),
    ('CURPFX_PTR', 0x54e, '4c8925',     'rip', 3, 7,  0x182feb988),
    ('UTILS_OBJ',  0x555, '488d0d',     'rip', 3, 7,  0x1834b95b0),
    ('VT_COPY',    0x55c, 'ff50',       'd8',  2, 0,  0x10),
    ('OFF_RESOLVED',0x643,'8048',       'd8',  2, 0,  0x59),
    ('FN_POP',     0x647, 'e8',         'call',1, 5,  0x1802dd244),
    ('FN_GENMIPS', 0x653, 'e8',         'call',1, 5,  0x1802a0dd4),
]
def decode(base, items, what):
    res = {}
    for name, off, lead, kind, a, b, want in items:
        va = base + off
        expect(va, lead, f'{what}.{name}')
        if kind == 'rip': v = rip(va, a, b)
        elif kind == 'call': v = va + 5 + i32(va + 1)
        elif kind == 'd32': v = u32(va + a)
        elif kind == 'd8': v = rd(va + a, 1)[0]
        elif kind == 'at': v = va
        if v != want: sys.exit(f'{what}.{name}: decodes to {v:#x}, expected {want:#x}')
        res[name] = (off, kind, a, b, v)
    return res
rdec = decode(RENDER, R, 'Render')
expect(RENDER, '488bc448895808', 'Render entry (7 bytes moved into the trampoline)')
expect(RENDER + 0x18e, '7533f20f1005', 'A1 jne + gate load')
step = struct.unpack('<d', rd(0x1827d8fd0, 8))[0]
if step != 0.025: sys.exit('step constant is not 0.025')

# ---------------------------------------------------------------- creation of $WaterRipplesDDN_0 (finds the RT helper)
CSITE = 0x180d6f1a5; CSITE_LEN = 0x30
C = [
    ('DDN_PTR',  0x05, '488d15', 'rip', 3, 7, 0x18378f790),
    ('NAME_PTR', 0x14, '488d0d', 'rip', 3, 7, 0x1827a2d70),
    ('FN_CREATERT', 0x2b, 'e8',  'call',1, 5, 0x181f41334),
]
cdec = decode(CSITE, C, 'create site')
if rd(0x1827a2d70, 19) != b'$WaterRipplesDDN_0\x00': sys.exit('DDN name string')

# ---------------------------------------------------------------- helper bodies (checked at their decoded address)
FUNCS = [  # name, va, length
    ('PUSH',    0x1802dce08, 0x57),
    ('POP',     0x1802dd244, 0x21),
    ('SHBEGIN', 0x1803c00dc, 0x2e),
    ('SETTECH', 0x1803c010c, 0x5c),
    ('SHEND',   0x1802ebe20, 0x2d),
    ('SETPSF',  0x1802dba00, 0x9a),
    ('PLOOKUP', 0x1802dba9c, 0x65),
    ('SETTEX',  0x1802da9f4, 0x56),
    ('DRAWTRI', 0x1803c0980, 0x25),
    ('GENMIPS', 0x1802a0dd4, 0xb2),
    ('CREATERT',0x181f41334, 0x11e),
    ('COPYSCR', 0x180694eb0, 0x50),
]
# values read out of helper bodies (offset inside that body)
H = {
    'SHBEGIN': [('CURPFX_PTR', 0x09, '48890d', 'rip', 3, 7, 0x182feb988), ('FN_SETTECH', 0x10, 'e8', 'call', 1, 5, 0x1803c010c)],
    'SETTECH': [('OFF_NTECH', 0x00, '448b49', 'd8', 3, 0, 0x58), ('OFF_TECHS', 0x0f, '4c8b51', 'd8', 3, 0, 0x50), ('OFF_TECHCRC', 0x1c, '8b42', 'd8', 2, 0, 0x08)],
    'SETPSF':  [('RD_PTR', 0x0f, '488b05', 'rip', 3, 7, 0x183786ba0), ('OFF_RP_SHADER', 0x1c, '4883b8', 'd32', 3, 0, 0x4880),
                ('OFF_RP_TECH', 0x26, '4883b8', 'd32', 3, 0, 0x48c0), ('OFF_RP_PASS', 0x30, '488b98', 'd32', 3, 0, 0x48c8),
                ('OFF_PASS_PS', 0x3c, '488b5b', 'd8', 3, 0, 0x10), ('FN_PLOOKUP', 0x48, 'e8', 'call', 1, 5, 0x1802dba9c)],
    'PLOOKUP': [('OFF_HW_INST', 0x00, '488b89', 'd32', 3, 0, 0xa8), ('OFF_PBEG', 0x12, '4c8b89', 'd32', 3, 0, 0x98),
                ('OFF_PEND', 0x23, '488b89', 'd32', 3, 0, 0xa0), ('PSTRIDE', 0x59, '4883c0', 'd8', 3, 0, 0x18)],
    'GENMIPS': [('ASYNC_PTR', 0x75, '8b05', 'rip', 2, 6, 0x1834ef998), ('CTX_PTR', 0x83, '488b0d', 'rip', 3, 7, 0x1834f0290)],
}
hdec = {}
for name, va, n in FUNCS:
    masked(va, n)
    if name in H: hdec[name] = decode(va, H[name], name)
expect(0x1802dbab5, '48b8abaaaaaaaaaaaa2a', 'PLOOKUP divide by 0x18')

# CCryNameTSCRC: 0x180656d78 -> 0x1802d3114 (init ~0, final NOT) -> 0x1802d3144 (lower-case A-Z, table at 0x182632dd0)
def zlib_table():
    t = []
    for n in range(256):
        c = n
        for _ in range(8): c = (c >> 1) ^ 0xEDB88320 if c & 1 else c >> 1
        t.append(c)
    return t
if list(struct.unpack('<256I', rd(0x182632dd0, 1024))) != zlib_table(): sys.exit('CRC table is not the zlib table')
expect(0x1802d3118, '834c2420ff', 'CRC init ~0')
expect(0x1802d313a, 'f7d0', 'CRC final NOT')
expect(0x1802d3159, '418d40bf3c19', 'CRC lower-case test (c - 0x41 <= 0x19)')

# ---------------------------------------------------------------- write sig.h
def arr(name, m):
    s = ','.join('X' if b < 0 else f'0x{b:02x}' for b in m)
    lines = []
    while s:
        cut = s[:118]
        if len(s) > 118: cut = cut[:cut.rfind(',') + 1]
        lines.append('    ' + cut); s = s[len(cut):]
    return f'static const short {name}[{len(m)}] = {{\n' + '\n'.join(lines) + '\n};\n'
o = ['/* generated by gen_sig.py from the stock Steam 1.9.8 WHGame.dll (sha256 %s). Do not edit. */\n' % STOCK_SHA,
     '#define X (-1)\n']
# CWaterRipples::Render: only a short prefix is stored as bytes (it finds the function); the rest of the body is
# checked by a hash, with the address fields left out of it (SIG_RENDER_MASK: bit i set = byte i is not hashed).
RENDER_PFX = 64
rm = masked(RENDER, RENDER_LEN)
import re as _re
_tx = [s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text'][0]
_txd = bytes(data[_tx.PointerToRawData:_tx.PointerToRawData + _tx.SizeOfRawData])
_rx = _re.compile(b''.join(b'.' if b < 0 else _re.escape(bytes([b])) for b in rm[:RENDER_PFX]), _re.S)
_n, _pos = 0, 0
while True:
    _m = _rx.search(_txd, _pos)
    if not _m: break
    _n += 1; _pos = _m.start() + 1
if _n != 1: sys.exit(f'the {RENDER_PFX}-byte prefix of Render matches {_n} times in .text (need 1)')
def fnv64(m):
    h = 0xcbf29ce484222325
    for b in m: h = ((h ^ (0 if b < 0 else b)) * 0x100000001b3) & 0xffffffffffffffff
    return h
def maskbits(m):
    out = bytearray((len(m) + 7) // 8)
    for i, b in enumerate(m):
        if b < 0: out[i >> 3] |= 1 << (i & 7)
    return out
o.append(f'/* CWaterRipples::Render, Steam 1.9.8 RVA {RENDER - BASE:#x}: first {RENDER_PFX} bytes; the whole body ({RENDER_LEN} bytes) by hash */\n')
o.append(arr('SIG_RENDER', rm[:RENDER_PFX]))
o.append(f'#define SIG_RENDER_LEN {RENDER_LEN}\n')
o.append(f'#define SIG_RENDER_HASH 0x{fnv64(rm):016x}ull   /* FNV-1a 64 of the body, bytes under the mask counted as 0 */\n')
_mb = ','.join(f'0x{b:02x}' for b in maskbits(rm)); _ml = []
while _mb:
    _c = _mb[:115]
    if len(_mb) > 115: _c = _c[:_c.rfind(',') + 1]
    _ml.append('    ' + _c); _mb = _mb[len(_c):]
o.append(f'static const unsigned char SIG_RENDER_MASK[{(RENDER_LEN + 7) // 8}] = {{   /* bit i set = byte i is an address field */\n' + '\n'.join(_ml) + '\n};\n')
o.append(f'/* call of the render-target helper that creates $WaterRipplesDDN_0, Steam 1.9.8 RVA {CSITE - BASE:#x} */\n')
o.append(arr('SIG_CREATE_SITE', masked(CSITE, CSITE_LEN)))
for name, va, n in FUNCS:
    o.append(f'/* helper {name}, Steam 1.9.8 RVA {va - BASE:#x}, first {n:#x} bytes */\n')
    o.append(arr('SIG_FN_' + name, masked(va, n)))
o.append('#undef X\n\n/* decode table: offset of the instruction inside its signature, then where the value sits */\n')
o.append('enum dkind { DK_RIP, DK_CALL, DK_D32, DK_D8, DK_AT };\n')
o.append('struct dec { const char *name; int off; int kind; int a; int b; unsigned long long rva198; };\n')
kmap = {'rip': 'DK_RIP', 'call': 'DK_CALL', 'd32': 'DK_D32', 'd8': 'DK_D8', 'at': 'DK_AT'}
def table(tname, dd):
    rows = []
    for k, (off, kind, a, b, v) in dd.items():
        val = v - BASE if kind in ('rip', 'call', 'at') else v
        rows.append(f'    {{ "{k}", {off:#x}, {kmap[kind]}, {a}, {b}, {val:#x}ull }},')
    return f'static const struct dec {tname}[] = {{\n' + '\n'.join(rows) + '\n};\n'
o.append(table('DEC_RENDER', rdec))
o.append(table('DEC_CREATE_SITE', cdec))
for k, dd in hdec.items(): o.append(table('DEC_' + k, dd))
o.append('\n/* CRC32 of the lower-cased name (CCryNameTSCRC; the engine routine is zlib CRC32, checked in gen_sig.py) */\n')
for nm in ('WaterRipplesGen', 'WaterRipplesHit', 'BlurInterpolation'):
    o.append(f'#define CRC_{nm.upper()} 0x{zlib.crc32(nm.lower().encode()):08x}u   /* "{nm}" */\n')
o.append(f'#define RVA198_RENDER {RENDER - BASE:#x}u\n')
open(out, 'w').write(''.join(o))
print('sig.h written:', out)

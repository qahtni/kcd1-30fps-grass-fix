/* KCD Grass Animation Fix - ASI plugin for Kingdom Come: Deliverance (KCD1).
 *
 * The game simulates grass in fixed 35 ms steps and holds the pose in between, so grass moves at
 * about 28.6 updates per second at any frame rate. This plugin adds a small piece of code after the
 * simulation that shifts each grass point back along its speed by the time still missing to the next
 * step. The drawn pose then moves every frame; the simulation itself is unchanged.
 *
 * Rules this file follows:
 *  - no game file is changed, only WHGame.dll's code in memory, once, when the DLL is loaded;
 *  - the place is found by its bytes, not by a fixed address; anything unexpected = do nothing;
 *  - no C runtime, only kernel32 (and one optional ntdll call), so no extra DLLs are needed;
 *  - one small log file next to the plugin says what happened.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include "sig.h"

#define FIX_TITLE "KCD Grass Animation Fix 1.0.0"

/* ---- tiny runtime (built without the C runtime) ---- */
void *memcpy(void *d, const void *s, size_t n) { BYTE *a = d; const BYTE *b = s; while (n--) *a++ = *b++; return d; }
void *memset(void *d, int c, size_t n) { BYTE *a = d; while (n--) *a++ = (BYTE)c; return d; }
static int same(const BYTE *a, const BYTE *b, SIZE_T n) { while (n--) if (*a++ != *b++) return 0; return 1; }

/* ---- log ---- */
static WCHAR g_log_path[MAX_PATH + 8];
static int g_log_open;
static char g_line[400];
static DWORD g_len;

static void log_s(const char *s) { while (*s && g_len < sizeof g_line - 2) g_line[g_len++] = *s++; }
static void log_x(ULONG_PTR v)
{
    char t[16]; int i = 0;
    do { t[i++] = "0123456789abcdef"[v & 15]; v >>= 4; } while (v);
    log_s("0x");
    while (i && g_len < sizeof g_line - 2) g_line[g_len++] = t[--i];
}
static void log_u(DWORD v)
{
    char t[10]; int i = 0;
    do { t[i++] = (char)('0' + v % 10); v /= 10; } while (v);
    while (i && g_len < sizeof g_line - 2) g_line[g_len++] = t[--i];
}
static void log_end(void)
{
    HANDLE h; DWORD w;
    g_line[g_len++] = '\r'; g_line[g_len++] = '\n';
    if (g_log_path[0]) {
        h = CreateFileW(g_log_path, GENERIC_WRITE, FILE_SHARE_READ, NULL,
                        g_log_open ? OPEN_ALWAYS : CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
        if (h != INVALID_HANDLE_VALUE) {
            g_log_open = 1;
            SetFilePointer(h, 0, NULL, FILE_END);
            WriteFile(h, g_line, g_len, &w, NULL);
            CloseHandle(h);
        }
    }
    g_len = 0;
}
static void log_init(HINSTANCE self)
{
    DWORD n = GetModuleFileNameW(self, g_log_path, MAX_PATH), i;
    if (!n || n >= MAX_PATH) { g_log_path[0] = 0; return; }
    for (i = n; i > 0 && g_log_path[i - 1] != L'\\' && g_log_path[i - 1] != L'/'; i--)
        if (g_log_path[i - 1] == L'.') { n = i - 1; break; }
    g_log_path[n] = L'.'; g_log_path[n + 1] = L'l'; g_log_path[n + 2] = L'o'; g_log_path[n + 3] = L'g'; g_log_path[n + 4] = 0;
}

/* ---- memory helpers ---- */
static int readable(const BYTE *p, SIZE_T n)
{
    MEMORY_BASIC_INFORMATION mbi; const BYTE *end = p + n;
    while (p < end) {
        if (!VirtualQuery(p, &mbi, sizeof mbi)) return 0;
        if (mbi.State != MEM_COMMIT || (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD))) return 0;
        p = (const BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    return 1;
}

/* one free page within reach of a 32-bit jump from 'target' */
static BYTE *alloc_near(const BYTE *target)
{
    SYSTEM_INFO si; MEMORY_BASIC_INFORMATION mbi;
    ULONG_PTR gran, lo, hi, t = (ULONG_PTR)target, p; BYTE *r; int guard;
    GetSystemInfo(&si);
    gran = si.dwAllocationGranularity;
    lo = t > 0x7ff00000u ? t - 0x7ff00000u : 0;
    hi = t + 0x7ff00000u;
    if (lo < (ULONG_PTR)si.lpMinimumApplicationAddress) lo = (ULONG_PTR)si.lpMinimumApplicationAddress;
    if (hi > (ULONG_PTR)si.lpMaximumApplicationAddress || hi < t) hi = (ULONG_PTR)si.lpMaximumApplicationAddress;
    for (p = t & ~(gran - 1), guard = 0; p > lo && guard < 200000; guard++) {          /* below */
        if (!VirtualQuery((void *)p, &mbi, sizeof mbi)) break;
        if (mbi.State == MEM_FREE) {
            r = VirtualAlloc((void *)p, 0x1000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
            if (r) return r;
            p -= gran;
        } else {
            ULONG_PTR ab = (ULONG_PTR)mbi.AllocationBase;
            p = (ab && ab < p ? ab : p) - gran;
            p &= ~(gran - 1);
        }
    }
    for (p = (t + gran) & ~(gran - 1), guard = 0; p < hi && guard < 200000; guard++) {  /* above */
        if (!VirtualQuery((void *)p, &mbi, sizeof mbi)) break;
        if (mbi.State == MEM_FREE) {
            r = VirtualAlloc((void *)p, 0x1000, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
            if (r) return r;
            p += gran;
        } else {
            p = ((ULONG_PTR)mbi.BaseAddress + mbi.RegionSize + gran - 1) & ~(gran - 1);
        }
    }
    return NULL;
}

static void put32(BYTE *p, INT64 v) { p[0] = (BYTE)v; p[1] = (BYTE)(v >> 8); p[2] = (BYTE)(v >> 16); p[3] = (BYTE)(v >> 24); }

/* ---- the patch ---- */
static BYTE *g_patched_base;

static void patch_whgame(BYTE *base)
{
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)base;
    IMAGE_NT_HEADERS64 *nt;
    IMAGE_SECTION_HEADER *sec;
    BYTE *hit = NULL, *hook, *code, jmp[HOOK_LEN];
    DWORD i, old, tmp; int hits = 0; INT64 rel;

    if (!base || base == g_patched_base) return;
    log_s("WHGame.dll at "); log_x((ULONG_PTR)base); log_end();
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) { log_s("not a PE image: nothing changed"); log_end(); return; }
    nt = (IMAGE_NT_HEADERS64 *)(base + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE || nt->OptionalHeader.Magic != IMAGE_NT_OPTIONAL_HDR64_MAGIC) {
        log_s("not a 64-bit PE image: nothing changed"); log_end(); return;
    }
    sec = IMAGE_FIRST_SECTION(nt);
    for (i = 0; i < nt->FileHeader.NumberOfSections; i++, sec++) {
        BYTE *s = base + sec->VirtualAddress, *p, *end; SIZE_T n = sec->Misc.VirtualSize;
        if (!(sec->Characteristics & IMAGE_SCN_MEM_EXECUTE)) continue;
        if (n < SIG_PRE_LEN + HOOK_LEN + SIG_POST_LEN || !readable(s, n)) continue;
        end = s + n - (SIG_PRE_LEN + HOOK_LEN + SIG_POST_LEN);
        for (p = s; p <= end; p++) {
            SIZE_T k;
            if (p[0] != SIG_PRE[0] || p[1] != SIG_PRE[1] || p[2] != SIG_PRE[2] || p[3] != SIG_PRE[3]) continue;
            for (k = 4; k < SIG_PRE_LEN; k++) if (SIG_PRE_MASK[k] && p[k] != SIG_PRE[k]) break;
            if (k == SIG_PRE_LEN) { if (!hits) hit = p; hits++; }
        }
    }
    if (hits != 1) {
        log_s("grass code found "); log_u((DWORD)hits);
        log_s(" times (need exactly 1): unsupported game version, nothing changed"); log_end(); return;
    }
    hook = hit + SIG_PRE_LEN;
    if (!same(hook + HOOK_LEN, SIG_POST, SIG_POST_LEN)) {
        log_s("code after the grass loop differs: unsupported game version, nothing changed"); log_end(); return;
    }
    if (!same(hook, HOOK_ORIG, HOOK_LEN)) {
        if (hook[0] == 0xE9 && hook[5] == 0x0F && hook[6] == 0x1F && hook[7] == 0x44 && hook[8] == 0 && hook[9] == 0)
            log_s("WHGame.dll already carries the grass fix (patched file): nothing to do");
        else
            log_s("grass loop already changed by something else: nothing changed");
        log_end(); return;
    }
    code = alloc_near(hook);
    if (!code) { log_s("no free memory near WHGame.dll: nothing changed"); log_end(); return; }
    memcpy(code, CAVE, CAVE_LEN);
    rel = (INT64)(ULONG_PTR)(hook + HOOK_LEN) - (INT64)(ULONG_PTR)(code + CAVE_TAIL_OFF + 5);
    if (rel > 0x7fffffffLL || rel < -0x7fffffffLL - 1) { VirtualFree(code, 0, MEM_RELEASE); log_s("new code out of jump range: nothing changed"); log_end(); return; }
    put32(code + CAVE_TAIL_OFF + 1, rel);
    if (!VirtualProtect(code, 0x1000, PAGE_EXECUTE_READ, &old)) { VirtualFree(code, 0, MEM_RELEASE); log_s("cannot make the new code executable: nothing changed"); log_end(); return; }
    FlushInstructionCache(GetCurrentProcess(), code, CAVE_LEN);

    rel = (INT64)(ULONG_PTR)code - (INT64)(ULONG_PTR)(hook + 5);
    jmp[0] = 0xE9; put32(jmp + 1, rel);
    jmp[5] = 0x0F; jmp[6] = 0x1F; jmp[7] = 0x44; jmp[8] = 0x00; jmp[9] = 0x00;       /* 5-byte nop */
    if (!VirtualProtect(hook, HOOK_LEN, PAGE_EXECUTE_READWRITE, &old)) {
        VirtualFree(code, 0, MEM_RELEASE); log_s("cannot write to WHGame.dll's code: nothing changed"); log_end(); return;
    }
    memcpy(hook, jmp, HOOK_LEN);
    VirtualProtect(hook, HOOK_LEN, old, &tmp);
    FlushInstructionCache(GetCurrentProcess(), hook, HOOK_LEN);
    g_patched_base = base;
    log_s("grass fix applied: hook at WHGame.dll+"); log_x((ULONG_PTR)(hook - base));
    log_s(", new code at "); log_x((ULONG_PTR)code); log_end();
}

/* ---- wait for WHGame.dll when the plugin is loaded before it ---- */
typedef struct { USHORT Length, MaximumLength; PWSTR Buffer; } USTR;
typedef struct { ULONG Flags; const USTR *FullDllName; const USTR *BaseDllName; PVOID DllBase; ULONG SizeOfImage; } DLL_NOTE;
typedef VOID (CALLBACK *DLL_NOTE_FN)(ULONG reason, const DLL_NOTE *data, PVOID ctx);
typedef LONG (NTAPI *REGISTER_FN)(ULONG flags, DLL_NOTE_FN fn, PVOID ctx, PVOID *cookie);

static int is_whgame(const USTR *n)
{
    static const WCHAR want[] = L"whgame.dll"; USHORT i, len;
    if (!n || !n->Buffer) return 0;
    len = n->Length / sizeof(WCHAR);
    if (len != 10) return 0;
    for (i = 0; i < len; i++) {
        WCHAR c = n->Buffer[i];
        if (c >= L'A' && c <= L'Z') c = (WCHAR)(c + 32);
        if (c != want[i]) return 0;
    }
    return 1;
}

static VOID CALLBACK on_dll(ULONG reason, const DLL_NOTE *d, PVOID ctx)
{
    (void)ctx;
    if (!d || !is_whgame(d->BaseDllName)) return;
    if (reason == 1) patch_whgame((BYTE *)d->DllBase);                 /* loaded */
    else if (reason == 2 && (BYTE *)d->DllBase == g_patched_base) g_patched_base = NULL;   /* unloaded */
}

BOOL WINAPI DllMain(HINSTANCE self, DWORD reason, LPVOID reserved)
{
    (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        HMODULE pin, wh, ntdll; REGISTER_FN reg; PVOID cookie = NULL;
        DisableThreadLibraryCalls(self);
        GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_PIN | GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS, (LPCWSTR)(void *)on_dll, &pin);
        log_init(self);
        log_s(FIX_TITLE); log_end();
        ntdll = GetModuleHandleW(L"ntdll.dll");
        reg = ntdll ? (REGISTER_FN)(void *)GetProcAddress(ntdll, "LdrRegisterDllNotification") : NULL;
        if (!reg || reg(0, on_dll, NULL, &cookie) != 0) reg = NULL;
        wh = GetModuleHandleW(L"WHGame.dll");
        if (wh) patch_whgame((BYTE *)wh);
        else if (reg) { log_s("WHGame.dll not loaded yet: waiting for it"); log_end(); }
        else { log_s("WHGame.dll not loaded and no load notification available: nothing changed"); log_end(); }
    }
    return TRUE;
}

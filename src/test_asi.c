/* Wine/Windows test for KCDGrassFix.asi against a real WHGame.dll image (mapped, never executed).
 * usage: test_asi.exe wh-first|asi-first WHGAME_DLL ASI patched|untouched */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sig.h"

static BYTE *text_of(BYTE *base, SIZE_T *size, DWORD *raw)
{
    IMAGE_NT_HEADERS64 *nt = (IMAGE_NT_HEADERS64 *)(base + ((IMAGE_DOS_HEADER *)base)->e_lfanew);
    IMAGE_SECTION_HEADER *s = IMAGE_FIRST_SECTION(nt);
    for (int i = 0; i < nt->FileHeader.NumberOfSections; i++, s++)
        if (s->Characteristics & IMAGE_SCN_MEM_EXECUTE) { *size = s->Misc.VirtualSize; *raw = s->PointerToRawData; return base + s->VirtualAddress; }
    return NULL;
}

int main(int argc, char **argv)
{
    if (argc < 5) { puts("usage: test_asi wh-first|asi-first WHGAME ASI patched|untouched"); return 2; }
    int wh_first = !strcmp(argv[1], "wh-first"), want_patch = !strcmp(argv[4], "patched"), fail = 0;
    BYTE *base, *text, *ref; SIZE_T tsize = 0; DWORD raw = 0; MEMORY_BASIC_INFORMATION mbi;
    HMODULE asi = NULL;

    if (!wh_first) { asi = LoadLibraryA(argv[3]); if (!asi) { printf("FAIL: asi load error %lu\n", GetLastError()); return 1; } }
    base = (BYTE *)LoadLibraryExA(argv[2], NULL, argc > 5 && !strcmp(argv[5], "normal") ? 0 : DONT_RESOLVE_DLL_REFERENCES);
    if (!base) { printf("FAIL: cannot map WHGame.dll, error %lu\n", GetLastError()); return 1; }
    text = text_of(base, &tsize, &raw);
    ref = malloc(tsize);
    if (wh_first) {
        memcpy(ref, text, tsize);                       /* exact picture before the plugin */
        asi = LoadLibraryA(argv[3]);
        if (!asi) { printf("FAIL: asi load error %lu\n", GetLastError()); return 1; }
    } else {                                            /* plugin already ran during the load: compare with the file */
        FILE *f = fopen(argv[2], "rb"); fseek(f, raw, SEEK_SET);
        if (fread(ref, 1, tsize, f) != tsize) { puts("FAIL: short read"); return 1; }
        fclose(f);
    }
    BYTE *hook = base + STOCK_HOOK_RVA;
    for (SIZE_T i = 0; i + SIG_PRE_LEN + HOOK_LEN <= tsize; i++) {      /* stand-in DLLs: find the grass code by its bytes */
        SIZE_T k = 0;
        if (ref[i] != SIG_PRE[0] || ref[i + 3] != SIG_PRE[3]) continue;
        while (k < SIG_PRE_LEN && (!SIG_PRE_MASK[k] || ref[i + k] == SIG_PRE[k])) k++;
        if (k == SIG_PRE_LEN) { hook = text + i + SIG_PRE_LEN; break; }
    }
    SIZE_T in = 0, outside = 0;
    for (SIZE_T i = 0; i < tsize; i++)
        if (text[i] != ref[i]) { if (text + i >= hook && text + i < hook + HOOK_LEN) in++; else outside++; }
    printf("order=%s base=%p text=%p size=0x%llx hook=+0x%llx: bytes changed inside hook=%llu, elsewhere=%llu\n", argv[1], base, text, (unsigned long long)tsize, (unsigned long long)(hook - base), (unsigned long long)in, (unsigned long long)outside);
    if (outside) { puts("FAIL: bytes changed outside the hook"); fail = 1; }
    if (!want_patch) {
        if (in) { puts("FAIL: hook changed but should be untouched"); fail = 1; }
    } else {
        INT32 rel; memcpy(&rel, hook + 1, 4);
        BYTE *code = hook + 5 + rel;
        if (hook[0] != 0xE9 || memcmp(hook + 5, "\x0f\x1f\x44\x00\x00", 5)) { puts("FAIL: hook is not jmp+nop"); fail = 1; }
        else {
            INT32 back; memcpy(&back, code + CAVE_TAIL_OFF + 1, 4);
            printf("hook -> %p (distance %lld MB)\n", code, (long long)((code - hook) / (1024 * 1024)));
            if (memcmp(code, CAVE, CAVE_TAIL_OFF)) { puts("FAIL: new code differs from the proven bytes"); fail = 1; }
            if (code[CAVE_TAIL_OFF] != 0xE9 || code + CAVE_TAIL_OFF + 5 + back != hook + HOOK_LEN) { puts("FAIL: return jump wrong"); fail = 1; }
            if (memcmp(code + CAVE_TAIL_OFF + 5, CAVE + CAVE_TAIL_OFF + 5, CAVE_LEN - CAVE_TAIL_OFF - 5)) { puts("FAIL: constants differ"); fail = 1; }
            VirtualQuery(code, &mbi, sizeof mbi);
            printf("new code page: state=0x%lx protect=0x%lx\n", mbi.State, mbi.Protect);
            if (mbi.State != MEM_COMMIT || mbi.Protect != PAGE_EXECUTE_READ) { puts("FAIL: new code page not read+execute"); fail = 1; }
        }
        VirtualQuery(hook, &mbi, sizeof mbi);
        printf("hook page protect=0x%lx\n", mbi.Protect);
        if (mbi.Protect & (PAGE_EXECUTE_READWRITE | PAGE_READWRITE)) { puts("FAIL: hook page left writable"); fail = 1; }
    }
    puts(fail ? "RESULT: FAIL" : "RESULT: PASS");
    return fail;
}

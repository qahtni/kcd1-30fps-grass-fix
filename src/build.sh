#!/bin/bash
# Build KCDGrassFix.asi (x64, no C runtime) and the Wine test harness into src/out/.
# Needs mingw-w64 (x86_64-w64-mingw32-gcc, -windres, -objdump).
# usage: ./build.sh                     build from the committed sig.h
#        ./build.sh /path/to/WHGame.dll first regenerate sig.h from your own stock WHGame.dll
#                                       (Steam 1.9.8, build 22623230; also needs gcc, objcopy, python3)
set -eu
cd "$(dirname "$0")"
mkdir -p out
if [ $# -ge 1 ]; then
  gcc -c cave.S -o out/cave.o                              # the 124 bytes of new code (host gcc, ELF object)
  objcopy -O binary -j .text out/cave.o out/cave.bin
  python3 -I gen_sig.py "$1" out/cave.bin 6d sig.h          # 0x6d = offset of the return jump in cave.bin
fi
x86_64-w64-mingw32-windres version.rc -O coff -o out/version.res
x86_64-w64-mingw32-gcc -Os -s -Wall -Wextra -ffreestanding -fno-builtin -fno-stack-protector \
  -fno-asynchronous-unwind-tables -fno-tree-loop-distribute-patterns -fno-ident -mno-stack-arg-probe \
  -shared -nostdlib -nostartfiles -Wl,-e,DllMain -Wl,--dynamicbase,--nxcompat,--high-entropy-va \
  -Wl,--no-insert-timestamp -o out/KCDGrassFix.asi kcd_grass_fix.c out/version.res -lkernel32
x86_64-w64-mingw32-gcc -O1 -Wall -static -o out/test_asi.exe test_asi.c
ls -l out/KCDGrassFix.asi out/test_asi.exe; sha256sum out/KCDGrassFix.asi
x86_64-w64-mingw32-objdump -p out/KCDGrassFix.asi | grep -E "DLL Name|^\s+[0-9a-f]+\s+[0-9]+\s+\w+$" | head -40

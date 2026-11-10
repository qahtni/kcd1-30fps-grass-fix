# How it works

Game: Kingdom Come: Deliverance 1.9.8 (Steam, build 22623230), CryEngine.

## The cause: a fixed 35 ms grass step on the CPU

- Most short grass in KCD is drawn as CryEngine "merged meshes". Their motion (wind, bending when something walks through) is simulated on the CPU in `Bin/Win64/WHGame.dll`, not in a shader. KCD's own help text for `e_VegetationBending` says so: "does not affect merged grass".
- The public CryEngine 3.8 source (the Lumberyard fork) has the same simulator with `#define MMRM_FIXED_STEP (0.035f)` and the loop `while (dtcur > MMRM_FIXED_STEP) { simulate one step }`. Time left over is carried to the next frame. Nothing blends between steps: every frame, the mesh is rebuilt from the last simulated pose.
- `WHGame.dll` contains the same loop. The numbers 0.035, 0.036 (the step plus 1 ms) and 28.571 (1 / 0.035) each occur once in the DLL, and the grass function uses all three as the source does. The code after the loop matches the source: store the pose, store the left-over time, build the mesh.
- 35 ms is 28.6 steps a second, at any frame rate. At 60 fps grass moves on about every second frame, at 120 fps on every fourth. That is the "30 fps grass" look.

Why not a shader mod or a setting:

- The vegetation shaders do use a clock that advances every frame, but merged grass does not take its motion from them: the CPU hands over final blade positions. The shader never sees the in-between state, so a shader mod cannot fix this.
- No setting controls the 35 ms step; it is a compile-time constant. `e_MergedMeshesUseSpines 0` (what Physics quality "Low" sets) switches the grass simulation off: no stepping, but also no grass motion or bending.

## The model: Crysis 3 Remastered

Digital Foundry noted that Crysis 3 Remastered runs grass animation at full frame rate, where the original looked 30 fps. The remaster's exe still has the same 35 ms simulation. What it adds after the loop: on frames without a simulation step, every blade point is moved along its stored speed, and the true simulation state is kept aside, so the simulation itself is unchanged. Its vegetation bending shader is identical to KCD's; the fix is not in its shaders.

This mod uses the same idea, written from scratch. One difference: the remaster pushes points forward along their speed; this mod places each point between the last two simulated states. It shows the simulation up to 35 ms late but never overshoots.

## The fix: 124 bytes of new code

The hook sits in the grass simulator's per-point store loop, after the simulated point and its speed have been saved back and before the point is converted for the mesh build. 10 bytes there are replaced by a jump to new code ([src/cave.S](src/cave.S)) that does:

```
pose += speed * -(35 ms - left-over time) / 1000      (for x, y, z)
```

then runs the two instructions the jump replaced and jumps back. The left-over time is already stored by the game in the spine's root point. The result is the pose between the previous and the latest simulation step, so the drawn grass changes every frame. Only the pose used for drawing moves; the saved simulation state is untouched. The new code uses only registers that are free at that point (`rax`, `xmm4`, `xmm5`).

## The plugin: KCDGrassFix.asi

- **Loading.** [Ultimate ASI Loader](https://github.com/ThirteenAG/Ultimate-ASI-Loader), saved as `version.dll` in `Bin/Win64`, loads the plugin. `WHGame.dll` imports `version.dll`, and the game's own DLLs live in `Bin/Win64Shared`, so no game file is replaced.
- **Finding the code by its bytes, not by an address.** A 201-byte pattern of the grass loop (4 wildcard bytes for one address) must occur exactly once in `WHGame.dll`'s code, the 10 bytes at the hook must be the original ones, and the 34 bytes after them must match too. Anything else, for example another game version or another mod that changed this loop, and the plugin changes nothing and writes why to `KCDGrassFix.log`. The pattern is generated from the stock DLL by [src/gen_sig.py](src/gen_sig.py) into [src/sig.h](src/sig.h).
- **When.** The plugin patches while `WHGame.dll` is being loaded, before any game code runs. If the plugin is loaded first, it waits for Windows' "DLL loaded" notification (`LdrRegisterDllNotification`) instead of polling.
- **Memory.** The new code goes into its own page within jump range of the DLL; that page is made read+execute after writing, and the DLL's code page gets its old protection back.
- **Small and plain.** No C runtime and no extra DLLs: the plugin imports only `KERNEL32.dll` and is 8.7 KB. No file on disk changes, so Steam's "verify files" does not undo it, and removing the two files makes the game stock again.

### Linux and Steam Deck

Wine and Proton prefer their own built-in `version.dll`, and the loader is then never loaded. `WINEDLLOVERRIDES="version=n,b"` (native first, then built-in) fixes that, either as a Steam launch option or as the same entry in the game prefix's `user.reg` under `[Software\\Wine\\DllOverrides]`. Without it, a test `version.dll` was ignored on Wine 10.0; with it, it was used. The Linux installer sets both; either alone is enough.

## Measured effect

Measured in the running game at 120 fps, following single grass points for 95 frames, with wind at 4x the default (`wh_env_WindFactor 2`):

| | frames on which the point moved | size of each move |
|---|---|---|
| without the fix | 22-23 of 95 (every 4th frame = 28.6 a second) | median 0.55-5.65 mm, largest 14.6 mm |
| with the fix | 95 of 95 | median 0.13-1.49 mm, largest 3.5 mm |

The total path is the same; the fix splits each jump into one small move per frame. For calm grass a few metres away that jump is about a pixel. Short, fast-shaking tufts close to the camera show it clearly. At 30 fps or below there is nothing to blend.

## Water ripples: the same problem, a different fix

The ripples on water come from a small simulation that runs on the graphics card (`CWaterRipples::Render`). The game runs one step of it when at least 25 ms have passed since the last one, and checks that once per frame: 30 steps a second at 60 fps, 40 at most. The water shaders read the same ripple texture until the next step, so the rings move in steps whatever the frame rate is.

`KCDWater.asi` hooks that one function and leaves the simulation alone:

- right before a step it puts the true ripple state back into the game's texture, so the simulation reads exactly what it would read without the mod;
- after a step it keeps the new state and the one before it;
- on every frame it writes a blend of the two into the texture the water shaders read: `previous + (current - previous) x (time since the step / 25 ms)`, then rebuilds the texture's mip levels.

The blend is drawn with a shader technique the game already ships (`BlurInterpolation`, a plain mix of two textures), through the game's own render functions. No shader and no game file is changed. When the simulation re-centres itself around the camera (about every 5 m of travel) the previous state no longer lines up, and that one step is shown without a blend.

Every assumption the plugin makes is checked while the game runs (texture formats and sizes, the shader pass, the thread, one GPU). If a check fails, that call falls back to the game's own behaviour; if one of its own textures is lost, the water fix switches itself off for the session and says so in `KCDWater.log`.

Settings and test commands: one command per line in `Bin\Win64\KCDWater.ini` (read at start) or `KCDWater.cmd` (read while the game runs, then deleted). `mode 0` = the game's own ripples, `mode 1` = smooth (the default), `stats` = counters in the log. `step N` makes the simulation step only every N ms and `gun N` adds N ripple hits a second around the camera: both are test tools that make the difference easy to film, not settings to play with.

The source is in [src/water/](src/water/): `kcd_water.c`, the generated `sig.h` (byte patterns and decode tables for Steam 1.9.8), `gen_sig.py` (makes `sig.h` from your own stock `WHGame.dll`) and `check_bind.py` (replays the plugin's search against a DLL file).

## Testing

- [src/test_asi.c](src/test_asi.c) maps a real `WHGame.dll` under Wine or Windows, loads the plugin and checks that exactly the 10 hook bytes changed, that the new code equals the built bytes and that both pages have the right protection. Cases checked during development, all as expected: stock DLL (fix applied), plugin loaded before the DLL (waits, then applies), one byte of the loop altered (found 0 times, nothing changed), the loop present twice (found 2 times, nothing changed), the code after the hook altered (nothing changed).
- The new machine code was also run natively against reference arithmetic: 200,000 random cases matched bit for bit.
- Real game: the fix loaded ("grass fix applied") on Windows 11, Steam Deck (SteamOS 3.9.5) and Bazzite.
- [release/test_linux_install.sh](release/test_linux_install.sh): 42 tests of the Linux installer and uninstaller against fake Steam setups (Steam running or closed, several libraries, launch options already set, a foreign `version.dll`, a damaged download, Native DLSS Support and the CPU Performance Patch installed next to it, an update from 1.0.0).

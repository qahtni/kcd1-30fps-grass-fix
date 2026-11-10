# 30 FPS Grass & Water Fix - High Framerate Water and Grass

Two small plugins for **Kingdom Come: Deliverance** (the first game) that make grass and water ripples move at your real frame rate instead of looking like 30 fps. Windows, Steam Deck and Linux.

## What it does

The game moves grass in fixed steps of 35 ms, about 28 times a second, and holds each pose until the next step. So grass looks like 30 fps even when the game runs at 60, 120 or more. This mod blends smoothly between those steps every frame, the same method Crysis 3 Remastered uses on the same engine, so grass moves at your real frame rate. The grass simulation itself is unchanged: same wind, same bending, same speed.

The difference is easiest to see on short, shaking tufts of grass close to the camera in windy weather. At 30 fps or below nothing changes.

**Water (new in 1.1.0).** The ripples on water are simulated in fixed steps of 25 ms, at most one step per frame, and the same ripple picture is shown until the next step: 30 steps a second at 60 fps, 40 at most. The mod shows a smooth blend between the last two steps on every frame, so the rings around you move at your real frame rate. The ripple simulation itself is unchanged: same shape, same speed.

How it works in detail: [HOW-IT-WORKS.md](HOW-IT-WORKS.md).

## Download

`30FPSGrassWaterFix-1.1.0.7z` from the [Releases page](https://github.com/qahtni/kcd1-30fps-grass-fix/releases/latest) or [Nexus Mods](https://www.nexusmods.com/kingdomcomedeliverance/mods/2457). It contains:

- `install/KCDGrassFix.asi`: the grass fix. When the game starts it finds the grass code in `WHGame.dll` and adds the blend, in memory only. No game file is changed.
- `install/KCDWater.asi`: the water ripple fix, a second plugin that works the same way.
- `install/version.dll`: [Ultimate ASI Loader](https://github.com/ThirteenAG/Ultimate-ASI-Loader) 10.0.2 by ThirteenAG (MIT license, included). It loads `.asi` plugins.
- Installers and uninstallers for Windows and Steam Deck / Linux. They are plain text: open them in a text editor to see exactly what they do.

## Requirements

- Kingdom Come: Deliverance, Steam version 1.9.8. On any other version the plugin finds nothing it knows, changes nothing and says so in its log.
- Windows: nothing else.
- Steam Deck / Linux: Proton must load `version.dll` from the game folder: `WINEDLLOVERRIDES="version=n,b"`. The installer sets this for you.

## Install

### Windows
1. Extract the archive anywhere, for example to Downloads.
2. Double-click **Install-Windows.bat** in the extracted folder.

It finds the game in your Steam libraries and copies `KCDGrassFix.asi`, `KCDWater.asi` and `version.dll` to `Bin\Win64`. If it can't find the game, drag the game folder onto `Install-Windows.bat`. Windows needs no launch options.

### Steam Deck / Linux
1. Switch to Desktop Mode and extract the archive anywhere, for example to Downloads.
2. Exit Steam: right-click the Steam icon in the taskbar > Exit Steam.
3. Right-click an empty spot in the extracted folder > Open Terminal Here, type `bash Install-Linux-SteamDeck.sh` and press Enter.

It finds the game in every Steam library (SD card included, also Flatpak Steam) and in `~/Games` (Heroic, Lutris), copies the three files to `Bin/Win64` and tells Proton to load `version.dll` from the game folder (otherwise Proton uses its own built-in `version.dll` and the fix does not load). It does that in two places, and either one is enough:

- the game's Steam launch options get `WINEDLLOVERRIDES="version=n,b"` in front of what is already there. Steam must be closed for this, because it rewrites its settings when it exits. If Steam is still running, the installer asks you to close it, or you can skip that step;
- the game's Proton prefix gets the same setting (works without closing Steam, once the game has been started at least once).

If neither was possible, the installer says so and shows the exact launch options to type in (right-click the game > Properties > General > Launch Options). For a game somewhere else, pass its folder: `bash Install-Linux-SteamDeck.sh "/path/to/KingdomComeDeliverance"`.

### By hand (no script)
In the game folder (Steam: right-click the game > Manage > Browse local files):
1. Copy `install\KCDGrassFix.asi`, `install\KCDWater.asi` and `install\version.dll` into `Bin\Win64` (the folder with `KingdomCome.exe`). With [Native DLSS Support](https://github.com/qahtni/kcd1-dlss) installed, leave `KCDGrassFix.asi` out: that mod already contains the grass fix.
2. Steam Deck / Linux only: set the game's launch options to `WINEDLLOVERRIDES="version=n,b" %command%`. Keep anything that was there already after `%command%`, for example `WINEDLLOVERRIDES="version=n,b" %command% -devmode`.

### Check that it works
After starting the game, `Bin\Win64\KCDGrassFix.log` says `grass fix applied` and `Bin\Win64\KCDWater.log` says `mode 1 (smooth ripples)`.

To turn only the water part off, create `Bin\Win64\KCDWater.ini` with the single line `mode 0`.

## Uninstall

- With the script: in the game folder, double-click `30FPSGrassWaterFix-Uninstall.bat` (Windows), or run `bash 30FPSGrassWaterFix-Uninstall.sh` with Steam closed (Steam Deck / Linux). The uninstallers in the extracted archive do the same.
- By hand: delete `KCDGrassFix.asi`, `KCDWater.asi`, their `.log` files and `version.dll` from `Bin\Win64` (keep `version.dll` if you use other `.asi` mods). On Linux also remove `WINEDLLOVERRIDES="version=n,b"` from the launch options.

## Compatibility and limits

- Made for the Steam version 1.9.8. Grass: tested on Windows 11 and on Linux with Proton (Steam Deck, Bazzite). Water: tested on Linux with Proton (Bazzite).
- Not tested: GOG and Epic copies (the plugin refuses code it does not recognise and logs it), Flatpak Steam and Heroic on real machines (covered by the installer's unit tests only).
- Works next to other mods; pak mods and the Mods folder are not involved. If you already use another ASI loader as `version.dll`, the installer leaves it alone and the fix loads through it.
- Works together with the author's other mods, installed in any order: [Native DLSS Support](https://github.com/qahtni/kcd1-dlss) already contains the grass fix, so with it present the installers store `KCDGrassFix.asi` as `KCDGrassFix.asi.off` (not loaded) and add only the water plugin; the CPU Performance Patch (`KCDPerf.asi`) and [Far Contact Shadows](https://github.com/qahtni/kcd1-far-contact-shadows) have no overlap. The plugin mods share one `version.dll`; each uninstaller removes it only when no other `.asi` plugin is left.
- If the water plugin meets anything unexpected while the game runs, it switches itself off for that session and says so in `KCDWater.log`.
- Only merged-mesh grass uses this code. Trees and bushes are animated elsewhere and are not changed.

## Building from source

Needs mingw-w64 (the 1.0.0 release was built with x86_64-w64-mingw32-gcc 13 and GNU ld 2.45.90; with those, `src/build.sh` gives a byte-identical `KCDGrassFix.asi`).

```sh
src/build.sh                                   # -> src/out/KCDGrassFix.asi, src/out/KCDWater.asi and src/out/test_asi.exe
src/build.sh /path/to/WHGame.dll               # same, but first regenerate src/sig.h from your stock Steam 1.9.8 WHGame.dll
wine src/out/test_asi.exe wh-first /path/to/WHGame.dll src/out/KCDGrassFix.asi patched   # self-test, prints RESULT: PASS
release/build_release.sh /path/to/dinput8.dll /path/to/UAL-LICENSE   # -> dist/30FPSGrassWaterFix-1.1.0.7z
bash release/test_linux_install.sh dist/single/30FPSGrassWaterFix    # 42 installer tests against fake Steam setups
```

`build_release.sh` takes `dinput8.dll` from `Ultimate-ASI-Loader-NoPDB_x64.zip` of [Ultimate ASI Loader v10.0.2](https://github.com/ThirteenAG/Ultimate-ASI-Loader/releases/tag/v10.0.2) and that project's license file; neither is stored in this repository.

`tools/media/` holds the scripts that made the Nexus header, thumbnail and comparison GIF (not stored here). They draw text in the game's menu font, read from your own copy of the game: extract `Libs/UI/gfxfontlib_glyphs.gfx` from `Data/GameData.pak` (a plain zip archive). The font is not included here.

## Credits

- By mrtaxerman.
- [Ultimate ASI Loader](https://github.com/ThirteenAG/Ultimate-ASI-Loader) by ThirteenAG (MIT license), see [THIRD_PARTY.md](THIRD_PARTY.md).
- The idea of blending between grass simulation steps comes from Crysis 3 Remastered. The code here was written from scratch.

## License

The code in this repository is released into the public domain under [The Unlicense](LICENSE): do whatever you want with it. Game files are not included and not covered; `src/sig.h` and `src/water/sig.h` hold byte patterns of the game's `WHGame.dll`, used only to find the grass and water code.

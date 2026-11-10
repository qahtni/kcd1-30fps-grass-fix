30 FPS GRASS & WATER FIX 1.1.0
High Framerate Water and Grass
Kingdom Come: Deliverance (Steam, 1.9.8)
Author: mrtaxerman

GRASS
The game moves grass in fixed steps of 35 ms, about 28 times a second, and
holds each pose until the next step. So grass looks like 30 fps even when
the game runs at 60, 120 or more. This mod blends smoothly between those
steps every frame (the same method Crysis 3 Remastered uses on the same
engine), so grass moves at your real frame rate. The grass simulation
itself is unchanged: same wind, same bending, same speed.

WATER (new in 1.1.0)
The ripples on water are simulated in fixed steps of 25 ms, at most one
step per frame, and the same ripple picture is shown until the next step:
30 steps a second at 60 fps, 40 at most. This mod shows a smooth blend
between the last two steps on every frame, so ripples move at your real
frame rate. The ripple simulation itself is unchanged: same shape, same
speed.

FILES IN THIS ARCHIVE
- install\KCDGrassFix.asi: the grass fix, a small plugin. When the game
  starts it finds the grass code in WHGame.dll and adds the blend, in
  memory only.
- install\KCDWater.asi: the water ripple fix, a second small plugin that
  works the same way.
  No game file is changed by either of them.
- install\version.dll: Ultimate ASI Loader 10.0.2 by ThirteenAG (MIT
  license, install\Ultimate-ASI-Loader-LICENSE.txt). It loads .asi plugins.
- Install-Windows.bat, Uninstall-Windows.bat
- Install-Linux-SteamDeck.sh, Uninstall-Linux-SteamDeck.sh
  Plain text: open them in a text editor to see exactly what they do.

UPDATING FROM 30 FPS GRASS FIX 1.0.0
Just run the installer of this version. The grass plugin is the same file
as in 1.0.0; the water plugin is added and the old uninstaller is replaced.

INSTALL (WINDOWS)
1. Extract the archive anywhere, for example to Downloads.
2. Double-click Install-Windows.bat in the extracted folder.
It finds the game in your Steam libraries and copies KCDGrassFix.asi,
KCDWater.asi and version.dll to Bin\Win64. If it can't find the game, drag
the game folder onto Install-Windows.bat. Windows needs no launch options.

INSTALL ON STEAM DECK / LINUX
1. Switch to Desktop Mode and extract the archive anywhere, for example to
   Downloads.
2. Exit Steam: right-click the Steam icon in the taskbar > Exit Steam.
3. Right-click an empty spot in the extracted folder > Open Terminal Here,
   type
     bash Install-Linux-SteamDeck.sh
   and press Enter.
It finds the game in every Steam library (SD card included, also Flatpak
Steam) and in ~/Games (Heroic, Lutris), copies the three files to Bin/Win64
and tells Proton to load version.dll from the game folder. Proton prefers
its own built-in version.dll otherwise, and the fix would not load. It does
that in two places:
- the game's launch options in Steam get WINEDLLOVERRIDES="version=n,b" in
  front of what is already there. Steam must be closed for this, because
  Steam rewrites its settings when it exits. If Steam is still running, the
  installer asks you to close it, or you can skip that step;
- the game's Proton prefix gets the same setting (works without closing
  Steam, but only after the game has been started once).
If neither was possible, the installer says so and shows the exact launch
options to type in: right-click the game > Properties > General > Launch
Options. For a game somewhere else, add its folder:
  bash Install-Linux-SteamDeck.sh "/path/to/KingdomComeDeliverance"

INSTALL BY HAND (NO SCRIPT)
To open the game folder: in Steam, right-click Kingdom Come: Deliverance >
Manage > Browse local files.
1. Copy install\KCDGrassFix.asi, install\KCDWater.asi and
   install\version.dll into Bin\Win64 (the folder with KingdomCome.exe).
   If you use the mod "Native DLSS Support" (KCDDLSS.asi), leave
   KCDGrassFix.asi out: that mod already contains the grass fix.
2. Steam Deck / Linux only: set the game's launch options to
     WINEDLLOVERRIDES="version=n,b" %command%
   If there was something in the box already, keep it after %command%,
   for example: WINEDLLOVERRIDES="version=n,b" %command% -devmode

CHECK THAT IT WORKS
After starting the game, Bin\Win64\KCDGrassFix.log says
"grass fix applied" and Bin\Win64\KCDWater.log says
"mode 1 (smooth ripples)". The grass difference is easiest to see on short,
shaking tufts of grass close to the camera in windy weather; the water
difference on the rings around you while you walk through shallow water.
At 30 fps or below nothing changes.

TURNING THE WATER PART OFF
Create a text file Bin\Win64\KCDWater.ini with the single line
  mode 0
and the game keeps its own ripple animation. Delete the file to turn the
fix on again.

OTHER MODS BY THE SAME AUTHOR
All of them can be installed together, in any order.
- Native DLSS Support: it already contains the grass fix. The installers
  handle that: with the DLSS mod present, KCDGrassFix.asi is stored as
  KCDGrassFix.asi.off (not loaded) and only the water plugin is added. If
  you remove the DLSS mod later, its uninstaller turns the grass plugin
  back on.
- CPU Performance Patch (KCDPerf.asi) and Far Contact Shadows: no overlap.
The plugin mods share one version.dll. Each uninstaller removes it only
when no other .asi plugin is left in Bin\Win64.

UNINSTALL
- With the script: in the game folder, double-click
  30FPSGrassWaterFix-Uninstall.bat (Windows), or run
    bash 30FPSGrassWaterFix-Uninstall.sh
  (Steam Deck / Linux, with Steam closed). Uninstall-Windows.bat /
  Uninstall-Linux-SteamDeck.sh in the extracted archive do the same.
- By hand: delete KCDGrassFix.asi, KCDWater.asi, their .log files and
  version.dll from Bin\Win64 (keep version.dll if you use other .asi
  mods). On Linux also remove WINEDLLOVERRIDES="version=n,b" from the
  launch options.

GOOD TO KNOW
- Made for the Steam version 1.9.8. On any other version the plugins find
  nothing they know, change nothing and say so in their .log files.
- Works next to other mods; pak mods and the Mods folder are not involved.
  If you already use another ASI loader as version.dll, the installer leaves
  it alone and the fix loads through it.
- Grass: tested on Windows 11 and on Linux with Proton (Steam Deck,
  Bazzite). Water: tested on Linux with Proton (Bazzite).
- If the water plugin meets anything unexpected while the game runs, it
  switches itself off for that session and says so in KCDWater.log; the
  game then shows its own ripples.

CHANGES
1.1.0
- New: water ripple fix (KCDWater.asi). The mod is now called
  30 FPS Grass & Water Fix.
- The installers work together with Native DLSS Support and the other
  plugin mods (shared version.dll, grass fix not loaded twice).
- The grass plugin is unchanged.
1.0.0
- First release.

30 FPS GRASS FIX 1.0.0
High Framerate Grass
Kingdom Come: Deliverance (Steam, 1.9.8)
Author: mrtaxerman

The game moves grass in fixed steps of 35 ms, about 28 times a second, and
holds each pose until the next step. So grass looks like 30 fps even when
the game runs at 60, 120 or more. This mod blends smoothly between those
steps every frame (the same method Crysis 3 Remastered uses on the same
engine), so grass moves at your real frame rate. The grass simulation
itself is unchanged: same wind, same bending, same speed.

FILES IN THIS ARCHIVE
- install\KCDGrassFix.asi: the fix, a small plugin. When the game starts it
  finds the grass code in WHGame.dll and adds the blend, in memory only. No
  game file is changed.
- install\version.dll: Ultimate ASI Loader 10.0.2 by ThirteenAG (MIT
  license, install\Ultimate-ASI-Loader-LICENSE.txt). It loads .asi plugins.
- Install-Windows.bat, Uninstall-Windows.bat
- Install-Linux-SteamDeck.sh, Uninstall-Linux-SteamDeck.sh
  Plain text: open them in a text editor to see exactly what they do.

INSTALL (WINDOWS)
1. Extract the archive anywhere, for example to Downloads.
2. Double-click Install-Windows.bat in the extracted folder.
It finds the game in your Steam libraries and copies KCDGrassFix.asi and
version.dll to Bin\Win64. If it can't find the game, drag the game folder
onto Install-Windows.bat. Windows needs no launch options.

INSTALL ON STEAM DECK / LINUX
1. Switch to Desktop Mode and extract the archive anywhere, for example to
   Downloads.
2. Exit Steam: right-click the Steam icon in the taskbar > Exit Steam.
3. Right-click an empty spot in the extracted folder > Open Terminal Here,
   type
     bash Install-Linux-SteamDeck.sh
   and press Enter.
It finds the game in every Steam library (SD card included, also Flatpak
Steam) and in ~/Games (Heroic, Lutris), copies the two files to Bin/Win64
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
1. Copy install\KCDGrassFix.asi and install\version.dll into Bin\Win64 (the
   folder with KingdomCome.exe).
2. Steam Deck / Linux only: set the game's launch options to
     WINEDLLOVERRIDES="version=n,b" %command%
   If there was something in the box already, keep it after %command%,
   for example: WINEDLLOVERRIDES="version=n,b" %command% -devmode

CHECK THAT IT WORKS
After starting the game, Bin\Win64\KCDGrassFix.log says
"grass fix applied". The difference is easiest to see on short, shaking
tufts of grass close to the camera in windy weather. At 30 fps or below
nothing changes.

UNINSTALL
- With the script: in the game folder, double-click
  30FPSGrassFix-Uninstall.bat (Windows), or run
    bash 30FPSGrassFix-Uninstall.sh
  (Steam Deck / Linux, with Steam closed). Uninstall-Windows.bat /
  Uninstall-Linux-SteamDeck.sh in the extracted archive do the same.
- By hand: delete KCDGrassFix.asi, KCDGrassFix.log and version.dll from
  Bin\Win64 (keep version.dll if you use other .asi mods). On Linux also
  remove WINEDLLOVERRIDES="version=n,b" from the launch options.

GOOD TO KNOW
- Made for the Steam version 1.9.8. On any other version the plugin finds
  nothing it knows, changes nothing and says so in KCDGrassFix.log.
- Works next to other mods; pak mods and the Mods folder are not involved.
  If you already use another ASI loader as version.dll, the installer leaves
  it alone and the fix loads through it.
- Tested on Windows 11 and on Linux with Proton (Steam Deck, Bazzite).
- The comparison GIF plays at 50 fps (the GIF limit), slightly slower than
  the 60 fps it was recorded at. The video plays at the real 60 fps.
- The comparison media were recorded with a stronger wind
  (wh_env_WindFactor 2, the default is 0.5) so the movement is easy to see.

CHANGES
1.0.0
- First release.

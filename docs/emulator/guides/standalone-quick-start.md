# S760Studio Quick Start

1. Verify the download checksum. In File Explorer, right-click the ZIP,
   choose Properties, check Unblock and Apply, then extract into a new folder.
   Keep the whole application folder together.
2. Install the prerequisites listed in `SYSTEM-PREREQUISITES.json`: the Windows
   x64 VC++ runtime, .NET Framework and WebView2. Install your audio/MIDI drivers
   separately. Python and Node are not required.
3. Put your own raw 32KB IC15 boot ROM in `roms/BOOT/`, and your raw 1.44MB OS
   disk in `roms/System/`. OS `.IMG` and Roland `.OUT` are supported without
   conversion. Put sample floppies in `roms/FDD/`. All folders ship empty.
4. Run `S760Studio.exe`. Wait for Perform Play. If configuration is needed, use
   the gear button to select firmware paths, output audio and MIDI input.
5. Select a sample image using Gotek Up/Down and Select, then use the original
   firmware Disk → Load to load its volume/performance. Return to Perform Play
   and play from MIDI or the optional on-screen keyboard.
6. Save firmware edits to your private disk, export the disk, and Save session
   when you want a restorable checkpoint.
7. Use **Quit application** or the window **X**. Save recovery and quit, or
   explicitly confirm discarding unsaved changes. A failed recovery save leaves
   the app open with a message.

Private profiles, recovery and staged firmware default to
`%LOCALAPPDATA%\S760Studio\default`; documentation does not hold runtime data.
The application never downloads firmware or sample libraries for you.

See the [full user guide](user-guide.md), [controls](controls.md) and
[troubleshooting](troubleshooting.md). These files work offline.

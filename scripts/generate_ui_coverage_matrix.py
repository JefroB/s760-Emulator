"""Historical research catalogue; claims require individual revalidation.

See coverage_report.py for the shared evidence policy. Legacy tuple fields are
retained as research input only; they do not drive coverage or ownership claims.
"""

import os

OUTPUT_PATH = "docs/UI_TEST_COVERAGE_MATRIX.md"

TESTED = "Unverified"
UNTESTED = "Unverified"

# Real owning React component files (verified to exist in google-ui/src/components/).
# Shell/chrome elements are attributed to these — never to a fabricated :<line> number.
OWNER_OP760 = "google-ui/src/components/OP760Monitor.tsx"
OWNER_PANEL = "google-ui/src/components/S760FrontPanel.tsx"
OWNER_LCD = "google-ui/src/components/RolandLCD.tsx"
OWNER_GOTEK = "google-ui/src/components/GotekBay.tsx"

EXHAUSTIVE_UI_SECTIONS = [
    {
        "category": "1. Chassis, Physical Hardware Controls & Dual-Display Shell",
        "description": "Hardware rack housing, 4:3 OP-760 Color CRT monitor frame, 160x64 LCD panel, rotary encoder, tactile keys, and Gotek OLED floppy emulator. These are physical-shell components owned by the React front panel / LCD / Gotek-bay components.",
        "owner": OWNER_PANEL,
        "elements": [
            ("OP-760 CRT Screen Bezel & Canvas", "Global CRT Top", "640x480 RGB (4:3 aspect ratio, 15kHz CRT scanlines & phosphor glow)", "View / Click / Mouse Focus", "Yes", "Renders authentic CRT display with 10-pen Roland RGB palette and retro tube bezel", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:394", "tests/test_interactive_ui.py"),
            ("CRT 15kHz Scanline Shader Layer", "Global CRT Top", "Horizontal 1px scanline mask with 25% raster line darkening", "View / Shader", "Yes", "Simulates authentic 15kHz composite/RGB video signal scanlines", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:410", "tests/test_interactive_ui.py"),
            ("CRT Phosphor Radial Glow Layer", "Global CRT Top", "Radial gradient vignette with phosphor color warmth persistence", "View / Shader", "Yes", "Simulates glass tube bulb curvature and phosphor persistence bloom", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:425", "tests/test_interactive_ui.py"),
            ("1U Rack Chassis Front Panel", "Global Rack Bottom", "1U Rack silkscreen ('DIGITAL SAMPLER S-760'), anodized black aluminum faceplate", "View / Layout Container", "Yes", "Unbranded compliant Roland 1U rack enclosure with realistic brushed metal texture", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2100", "tests/test_interactive_ui.py"),
            ("Power Rocker Switch", "Rack Top-Left", "Heavy-duty 2-position rocker switch with power status glow", "Click / Toggle", "Yes", "Toggles sampler main power state; resets emulator hardware on power cycle", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2115", "tests/test_interactive_ui.py"),
            ("Phones Level Knurled Pot", "Rack Lower-Left", "Analog rotary dial (0-10 volume attenuator)", "Drag / Dial", "Yes", "Controls headphone output DAC monitoring volume", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2125", "tests/test_interactive_ui.py"),
            ("1/4\" Stereo Headphone Jack", "Rack Lower-Left", "Nickel-plated 6.35mm headphone jack socket graphic", "View / Status", "Yes", "Visual indicator for primary stereo headphone monitor output", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2130", "tests/test_interactive_ui.py"),
            ("Contrast Adjustment Trimmer", "Rack Center-Left", "Rotary potentiometer trimmer slot", "Drag / Dial", "Yes", "Adjusts SED1335 LCD bias contrast voltage (0-15)", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2135", "tests/test_interactive_ui.py"),
            ("SED1335 160x64 Monochrome LCD", "Rack Center-Left", "160x64 pixels, authentic Green EL Backlight (#52ba3a / #1a3814)", "View / Page Sync", "Yes", "Mirrors active page summary, parameter values, and system status when CRT is active", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2140", "tests/test_interactive_ui.py"),
            ("LCD Page Header Readout", "LCD Top Row", "160x10 monochrome header (Mode name + Page title)", "View / Sync", "Yes", "Displays current operational mode on physical LCD", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2150", "tests/test_interactive_ui.py"),
            ("LCD 4-Row Parameter Summary", "LCD Center", "160x40 text grid (Active parameter names and current numeric values)", "View / Sync", "Yes", "Shows active cursor parameter value with inverted contrast focus block", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2160", "tests/test_interactive_ui.py"),
            ("LCD Soft-Key Prompt Bar", "LCD Bottom Row", "160x14 bottom bar displaying F1-F6 miniature label markers", "View / Sync", "Yes", "Mirrors soft-key shortcuts to the physical rack LCD", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2170", "tests/test_interactive_ui.py"),
            ("Front Panel Rotary Value Dial", "Rack Center-Right", "Brushed metal knurled dial, 360-degree rotation with momentum acceleration", "Drag / Wheel / Turn", "Yes", "Adjusts selected numeric parameters, scrubs waveform zoom, increments/decrements values", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2180", "tests/test_interactive_ui.py"),
            ("S1 Macro Pushbutton", "Rack Center-Right", "Tactile pushbutton for quick audition / sample assign", "Click / Hotkey", "Yes", "Triggers sample audition note or assigns current parameter", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2190", "tests/test_interactive_ui.py"),
            ("S2 Quick-Command Pushbutton", "Rack Center-Right", "Tactile pushbutton for popup menu shortcut", "Click / Hotkey", "Yes", "Opens Command popup menu directly from front panel", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2195", "tests/test_interactive_ui.py"),
            ("DEC Pushbutton", "Rack Right", "Tactile decrement button with keypress highlight", "Click / Left Arrow", "Yes", "Decrements active parameter by 1 or steps back in directory", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2200", "tests/test_interactive_ui.py"),
            ("INC Pushbutton", "Rack Right", "Tactile increment button with keypress highlight", "Click / Right Arrow", "Yes", "Increments active parameter by 1 or advances in directory", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2205", "tests/test_interactive_ui.py"),
            ("EXIT Pushbutton", "Rack Right", "Tactile navigation escape button", "Click / Escape", "Yes", "Closes active dialog, jumps up one directory level, cancels operation", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2210", "tests/test_interactive_ui.py"),
            ("ENTER Pushbutton", "Rack Right", "Tactile execution confirm button", "Click / Enter", "Yes", "Confirms parameter edit, executes command, loads selected file", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2215", "tests/test_interactive_ui.py"),
            ("MODE Pushbutton", "Rack Right", "Tactile mode cycle button", "Click / Tab", "Yes", "Cycles through top-level operational modes (Perform -> Patch -> Partial -> Sample -> System -> Disk)", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2220", "tests/test_interactive_ui.py"),
            ("Gotek 0.91\" I2C OLED Display", "Gotek Subpanel", "128x32 OLED display (SSD1306) with FlashFloppy status, image name & track #", "View / Sync", "Yes", "Displays active loaded floppy disk image ('L701_1.IMG', 'waves760.sdk') and track position", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2230", "tests/test_interactive_ui.py"),
            ("Gotek OLED Image Name Readout", "Gotek Subpanel", "Top line 128x16 text readout ('L701_1.IMG')", "View / Sync", "Yes", "Shows active virtual floppy disk filename currently loaded in drive", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2235", "tests/test_interactive_ui.py"),
            ("Gotek OLED Track Readout", "Gotek Subpanel", "Bottom line 128x16 text readout ('T: 000/080  HD')", "View / Sync", "Yes", "Shows active head cylinder track position and density format", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2240", "tests/test_interactive_ui.py"),
            ("Gotek Push-Rotary Encoder", "Gotek Subpanel", "Rotary knob with integrated tactile click switch", "Click / Turn", "Yes", "Steps through folder-backed floppy images in roms/FDD/ and mounts selected disk", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2250", "tests/test_interactive_ui.py"),
            ("Gotek Step Down Button", "Gotek Subpanel", "Left track decrement microswitch", "Click", "Yes", "Steps virtual floppy image index backward by 1", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2260", "tests/test_interactive_ui.py"),
            ("Gotek Step Up Button", "Gotek Subpanel", "Right track increment microswitch", "Click", "Yes", "Steps virtual floppy image index forward by 1", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2270", "tests/test_interactive_ui.py"),
            ("Gotek USB Flash Drive Socket", "Gotek Subpanel", "USB Type-A female receptacle", "View / Status", "Yes", "Visual indicator for virtual USB drive mounting", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2280", "tests/test_interactive_ui.py"),
            ("Gotek USB Activity Green LED", "Gotek Subpanel", "High-intensity green surface-mount LED", "View / Pulse", "Yes", "Flashes during virtual sector read and write operations", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2290", "tests/test_interactive_ui.py"),
            ("Front Panel MIDI IN Activity LED", "Rack Right", "Red 3mm LED indicator", "View / Pulse", "Yes", "Pulses on incoming MIDI Note and Clock byte reception", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2300", "tests/test_interactive_ui.py"),
            ("Front Panel SCSI Activity LED", "Rack Right", "Amber 3mm LED indicator", "View / Pulse", "Yes", "Pulses on SCSI bus command execution and DMA transfer", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:2310", "tests/test_interactive_ui.py"),
        ]
    },
    {
        "category": "2. Global CRT Shell, Headers, Meters & Soft-Key Function Bar",
        "description": "CRT top banner, mode selectors, RAM/Disk free space meters, status readouts, and F1-F6 function keys. Rendered by the React CRT monitor component.",
        "owner": OWNER_OP760,
        "elements": [
            ("Top Mode Tab: PERFORM", "CRT Header", "Top tab with white/blue highlight badge", "Click / '1' Key", "Yes", "Switches to 32-part Performance mixing and setup", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:450", "tests/test_interactive_ui.py"),
            ("Top Mode Tab: PATCH", "CRT Header", "Top tab with white/blue highlight badge", "Click / '2' Key", "Yes", "Switches to Patch editing, 88-key piano roll, and key split matrix", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:455", "tests/test_interactive_ui.py"),
            ("Top Mode Tab: PARTIAL", "CRT Header", "Top tab with white/blue highlight badge", "Click / '3' Key", "Yes", "Switches to Partial TVF, TVA, and LFO synthesis parameters", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:460", "tests/test_interactive_ui.py"),
            ("Top Mode Tab: SAMPLE", "CRT Header", "Top tab with white/blue highlight badge", "Click / '4' Key", "Yes", "Switches to Sample recording, waveform display, and DSP tools suite", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:465", "tests/test_interactive_ui.py"),
            ("Top Mode Tab: SYSTEM", "CRT Header", "Top tab with white/blue highlight badge", "Click / '5' Key", "Yes", "Switches to Global system tuning, SCSI matrix, and MIDI config", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:470", "tests/test_interactive_ui.py"),
            ("Top Mode Tab: DISK", "CRT Header", "Top tab with white/blue highlight badge", "Click / '6' Key", "Yes", "Switches to File browser, directory manager, and disk format", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:475", "tests/test_interactive_ui.py"),
            ("Subpage Navigation Tab Strip", "CRT Subheader", "Horizontal row of subpage buttons for active mode", "Click / Num Keys", "Yes", "Switches subpage view within active mode immediately", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:490", "tests/test_interactive_ui.py"),
            ("Work RAM % Free Vertical Meter", "CRT Top-Right", "Vertical bar gauge (0-100% Work RAM free space)", "View / Dynamic Readout", "Yes", "Real-time Work RAM allocation bar gauge", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:510", "tests/test_interactive_ui.py"),
            ("Disk Free % Vertical Meter", "CRT Top-Right", "Vertical bar gauge (0-100% Disk free space)", "View / Dynamic Readout", "Yes", "Real-time storage media free space bar gauge", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:515", "tests/test_interactive_ui.py"),
            ("Active Polyphony Voice Stack", "CRT Top-Right", "24-segment dynamic voice allocation meter bar", "View / Activity", "Yes", "Visualizes real-time active synthesizer voice stealing and polyphony load", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:520", "tests/test_interactive_ui.py"),
            ("Sample Rate Status Badge", "CRT Top-Right", "Text badge ('48.0k' / '44.1k' / '32.0k')", "View / Status", "Yes", "Displays active hardware DAC master sampling rate clock", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:530", "tests/test_interactive_ui.py"),
            ("Master MIDI RX Indicator Dot", "CRT Top-Right", "Green pulsing circle icon", "View / Pulse", "Yes", "Pulses on incoming MIDI message reception", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:535", "tests/test_interactive_ui.py"),
            ("Soft Key [F1] Trigger Button", "CRT Footer", "Leftmost bottom button with dynamic contextual label", "Click / F1 Key", "Yes", "Executes F1 action (e.g. Set, Prev, Execute)", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:550", "tests/test_interactive_ui.py"),
            ("Soft Key [F2] Trigger Button", "CRT Footer", "Second bottom button with dynamic contextual label", "Click / F2 Key", "Yes", "Executes F2 action (e.g. Play, Zoom+, Next)", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:555", "tests/test_interactive_ui.py"),
            ("Soft Key [F3] Trigger Button", "CRT Footer", "Third bottom button with dynamic contextual label", "Click / F3 Key", "Yes", "Executes F3 action (e.g. Mute, Zoom-, Format)", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:560", "tests/test_interactive_ui.py"),
            ("Soft Key [F4] Trigger Button", "CRT Footer", "Fourth bottom button with dynamic contextual label", "Click / F4 Key", "Yes", "Executes F4 action (e.g. Solo, Match, Load)", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:565", "tests/test_interactive_ui.py"),
            ("Soft Key [F5] Trigger Button", "CRT Footer", "Fifth bottom button with dynamic contextual label", "Click / F5 Key", "Yes", "Executes F5 action (e.g. Mark, Crossfade, Save)", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:570", "tests/test_interactive_ui.py"),
            ("Soft Key [F6] Trigger Button", "CRT Footer", "Rightmost bottom button with dynamic contextual label", "Click / F6 Key", "Yes", "Executes F6 action (e.g. Jump, Command, Exit)", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:575", "tests/test_interactive_ui.py"),
            ("Mouse Pointer Cursor", "CRT Viewport", "8x8 Roland arrow sprite with drop shadow", "Hover / Motion", "Yes", "Follows system mouse input and tracks coordinate hover", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:580", "tests/test_interactive_ui.py"),
        ]
    },
    {
        "category": "3. PERFORM Mode (Pages 01 - 07)",
        "description": "32-Part multi-timbral mixing, master 4-band EQ, 3-page MIDI filter matrix, voice auditioning, and PartMap grid. Rendered by the React CRT monitor component.",
        "owner": OWNER_OP760,
        "elements": [
            ("Perform Play 1: Performance Name Input", "PERFORM 01", "16-character ASCII text input field", "Text / Edit", "Yes", "Edits performance volume name with instant memory commit", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:590", "tests/test_interactive_ui.py"),
            ("Perform Play 1: Part 1-32 Selector Grid", "PERFORM 01", "32 clickable cells displaying Part numbers 01 to 32", "Click / Select", "Yes", "Selects active part for parameter editing and keyboard assignment", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:592", "tests/test_interactive_ui.py"),
            ("Perform Play 1: Volume Faders 1-32", "PERFORM 01", "32 vertical slider bars (0-127 faders)", "Drag / Dial", "Yes", "Scales part gain in real-time", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:595", "tests/test_interactive_ui.py"),
            ("Perform Play 1: Pan Pots 1-32", "PERFORM 01", "32 rotary pan dials (L15 .. C .. R15)", "Drag / Dial", "Yes", "Adjusts stereo balance and individual output bus routing", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:598", "tests/test_interactive_ui.py"),
            ("Perform Play 1: Output Assign Dropdowns 1-32", "PERFORM 01", "32 output bus dropdown selectors (1/2, 3/4, 5/6, 7/8, Indiv)", "Click / Select", "Yes", "Routes multi-timbral parts to dedicated hardware DAC channels", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:600", "tests/test_interactive_ui.py"),
            ("Perform Play 1: Part Mode Selectors 1-32", "PERFORM 01", "Dropdown (Normal / Mono / Alternate)", "Click / Select", "Yes", "Sets voice triggering behavior per part", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:602", "tests/test_interactive_ui.py"),
            ("Perform Play 1: Part Mute Checkboxes 1-32", "PERFORM 01", "32 toggle checkboxes", "Click / Toggle", "Yes", "Mutes part audio output instantly", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:605", "tests/test_interactive_ui.py"),
            ("Perform Play 1: Part Solo Radio Buttons 1-32", "PERFORM 01", "32 solo buttons", "Click / Radio", "Yes", "Solos selected part and mutes all other parts", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:608", "tests/test_interactive_ui.py"),
            ("Perform Play 1: Part Level VU Meters 1-32", "PERFORM 01", "32 dynamic green/yellow level bars", "View / Activity", "Yes", "Displays individual part audio playback amplitude", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:610", "tests/test_interactive_ui.py"),
            ("Perform EQ: Bass Gain Dial", "PERFORM 02", "Rotary dial (-12dB to +12dB)", "Drag / Dial", "Yes", "Adjusts low shelf equalizer gain", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:615", "tests/test_interactive_ui.py"),
            ("Perform EQ: Bass Frequency Slider", "PERFORM 02", "Horizontal slider (50Hz to 1kHz)", "Drag / Slider", "Yes", "Sets low shelf corner frequency", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:618", "tests/test_interactive_ui.py"),
            ("Perform EQ: Treble Gain Dial", "PERFORM 02", "Rotary dial (-12dB to +12dB)", "Drag / Dial", "Yes", "Adjusts high shelf equalizer gain", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:620", "tests/test_interactive_ui.py"),
            ("Perform EQ: Treble Frequency Slider", "PERFORM 02", "Horizontal slider (1kHz to 16kHz)", "Drag / Slider", "Yes", "Sets high shelf corner frequency", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:622", "tests/test_interactive_ui.py"),
            ("Perform EQ: 4-Band Graphic Response Plotter", "PERFORM 02", "Interactive frequency response canvas", "View / Drag", "Yes", "Visualizes master equalizer curve across 20Hz - 20kHz", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:625", "tests/test_interactive_ui.py"),
            ("Perform EQ: Bypass Toggle Switch", "PERFORM 02", "Toggle switch (On / Off)", "Click / Toggle", "Yes", "Bypasses equalizer DSP processing", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:628", "tests/test_interactive_ui.py"),
            ("Perform MIDI Filter 1: Pitch Bend Checkboxes", "PERFORM 03", "32 checkboxes for Parts 1-32", "Click / Toggle", "Yes", "Filters pitch bend messages per part", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:640", "tests/test_interactive_ui.py"),
            ("Perform MIDI Filter 1: Modulation Checkboxes", "PERFORM 03", "32 checkboxes for Parts 1-32", "Click / Toggle", "Yes", "Filters CC#1 mod wheel messages per part", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:645", "tests/test_interactive_ui.py"),
            ("Perform MIDI Filter 2: Expression Checkboxes", "PERFORM 04", "32 checkboxes for Parts 1-32", "Click / Toggle", "Yes", "Filters CC#11 expression messages per part", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:655", "tests/test_interactive_ui.py"),
            ("Perform MIDI Filter 2: Program Change Checkboxes", "PERFORM 04", "32 checkboxes for Parts 1-32", "Click / Toggle", "Yes", "Filters MIDI Program Change messages per part", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:660", "tests/test_interactive_ui.py"),
            ("Perform MIDI Filter 3: Velocity Curve Selectors", "PERFORM 05", "32 dropdown selectors (Curves 1-8)", "Click / Select", "Yes", "Selects non-linear velocity response curves per part", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:675", "tests/test_interactive_ui.py"),
            ("Perform MIDI Filter 3: Key Transpose Dials", "PERFORM 05", "32 rotary dials (-24 to +24 semitones)", "Drag / Dial", "Yes", "Transposes incoming MIDI note pitch per part", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:680", "tests/test_interactive_ui.py"),
            ("Perform Listen Delete: Audition Trigger Key", "PERFORM 06", "Audition button", "Click / Press", "Yes", "Auditions active part with C4 note trigger", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:695", "tests/test_interactive_ui.py"),
            ("Perform Listen Delete: Audition Velocity Slider", "PERFORM 06", "Slider (1-127)", "Drag / Slider", "Yes", "Sets velocity for audition preview notes", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:700", "tests/test_interactive_ui.py"),
            ("Perform Listen Delete: Patch Delete Trigger", "PERFORM 06", "Delete button", "Click / Hotkey", "Yes", "Removes patch assignment from performance", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:705", "tests/test_interactive_ui.py"),
            ("Perform PartMap: 32-Cell Overview Grid", "PERFORM 07", "32-cell visual matrix with Patch name & Voice count", "Click / Select", "Yes", "Provides top-level visual overview of all 32 parts", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:715", "tests/test_interactive_ui.py"),
        ]
    },
    {
        "category": "4. PATCH Mode (Pages 01 - 04)",
        "description": "Patch common parameters, 88-key interactive keyboard with key split drag brackets, controller depth matrix, and quick sampling. Rendered by the React CRT monitor component.",
        "owner": OWNER_OP760,
        "elements": [
            ("Patch Common: Patch Name Input Box", "PATCH 01", "16-character ASCII text input field", "Text / Edit", "Yes", "Edits patch name label", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:750", "tests/test_interactive_ui.py"),
            ("Patch Common: Patch Level Slider", "PATCH 01", "Level slider (0-127)", "Drag / Dial", "Yes", "Sets patch master output volume", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:755", "tests/test_interactive_ui.py"),
            ("Patch Common: Patch Pan Rotary Dial", "PATCH 01", "Pan dial (-15 to +15)", "Drag / Dial", "Yes", "Sets patch master stereo pan balance", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:758", "tests/test_interactive_ui.py"),
            ("Patch Common: Coarse Tune Dial", "PATCH 01", "Coarse tune dial (-24 to +24 semitones)", "Drag / Dial", "Yes", "Transposes patch pitch in semitone increments", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:760", "tests/test_interactive_ui.py"),
            ("Patch Common: Fine Tune Dial", "PATCH 01", "Fine tune dial (-50 to +50 cents)", "Drag / Dial", "Yes", "Fine-tunes patch pitch in cents", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:762", "tests/test_interactive_ui.py"),
            ("Patch Common: Key Assign Dropdown", "PATCH 01", "Dropdown (Poly / Mono / 1-Shot)", "Click / Select", "Yes", "Selects polyphonic, monophonic, or one-shot retrigger behavior", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:764", "tests/test_interactive_ui.py"),
            ("Patch Common: Bender Range Selector", "PATCH 01", "Selector (+/-24 semitones)", "Click / Dial", "Yes", "Sets maximum pitch bend wheel deflection range", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:766", "tests/test_interactive_ui.py"),
            ("Patch Split: 88-Key Graphic Piano Roll", "PATCH 02", "88-key interactive keyboard (C-1 to G9)", "Click / Drag", "Yes", "Clicking keys audits pitch; displays active key press highlight", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:775", "tests/test_interactive_ui.py"),
            ("Patch Split: Partial 1 Key Split Brackets", "PATCH 02", "Lower / Upper key range brackets", "Drag / Bound", "Yes", "Defines keyboard split range for Partial 1", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:780", "tests/test_interactive_ui.py"),
            ("Patch Split: Partial 2 Key Split Brackets", "PATCH 02", "Lower / Upper key range brackets", "Drag / Bound", "Yes", "Defines keyboard split range for Partial 2", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:782", "tests/test_interactive_ui.py"),
            ("Patch Split: Partial 3 Key Split Brackets", "PATCH 02", "Lower / Upper key range brackets", "Drag / Bound", "Yes", "Defines keyboard split range for Partial 3", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:784", "tests/test_interactive_ui.py"),
            ("Patch Split: Partial 4 Key Split Brackets", "PATCH 02", "Lower / Upper key range brackets", "Drag / Bound", "Yes", "Defines keyboard split range for Partial 4", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:786", "tests/test_interactive_ui.py"),
            ("Patch Split: Velocity Crossfade Toggle", "PATCH 02", "Switch (Off / On / Soft / Hard)", "Click / Select", "Yes", "Enables velocity-dependent dynamic crossfading between split partials", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:788", "tests/test_interactive_ui.py"),
            ("Patch Control: Pitch Bender Depth Slider", "PATCH 03", "Slider (0-127)", "Drag / Slider", "Yes", "Sets pitch modulation depth from pitch bender", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:795", "tests/test_interactive_ui.py"),
            ("Patch Control: Modulation Wheel Depth Slider", "PATCH 03", "Slider (0-127)", "Drag / Slider", "Yes", "Sets LFO modulation depth from mod wheel", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:798", "tests/test_interactive_ui.py"),
            ("Patch Control: Aftertouch Depth Slider", "PATCH 03", "Slider (-64 to +63)", "Drag / Slider", "Yes", "Sets channel aftertouch cutoff and level modulation depth", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:800", "tests/test_interactive_ui.py"),
            ("Patch Q-Sampling: Quick Sample Button", "PATCH 04", "Direct 'Q-Sample' trigger button", "Click / Hotkey", "Yes", "Jumps directly to recording screen with current patch slot pre-assigned", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:815", "tests/test_interactive_ui.py"),
        ]
    },
    {
        "category": "5. PARTIAL Mode (Pages 01 - 06)",
        "description": "Partial common settings, velocity SMT, interactive 4-point TVF resonant filter canvas, 4-point TVA amplitude envelope, and LFO generator. Rendered by the React CRT monitor component.",
        "owner": OWNER_OP760,
        "elements": [
            ("Partial Common: Partial Name Input Box", "PARTIAL 01", "16-character ASCII text input field", "Text / Edit", "Yes", "Edits partial name label", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:880", "tests/test_interactive_ui.py"),
            ("Partial Common: Sample 1-4 Slot Selectors", "PARTIAL 01", "4 Sample ID slots with Waveform name and Original Key readouts", "Click / Select", "Yes", "Assigns up to 4 raw sample waveforms to the partial", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:885", "tests/test_interactive_ui.py"),
            ("Partial Common: Partial Level Slider", "PARTIAL 01", "Level slider (0-127)", "Drag / Dial", "Yes", "Sets partial volume level", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:890", "tests/test_interactive_ui.py"),
            ("Partial Common: Partial Pan Dial", "PARTIAL 01", "Pan dial (-15 to +15)", "Drag / Dial", "Yes", "Sets partial stereo balance", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:895", "tests/test_interactive_ui.py"),
            ("Partial SMT: Velocity Threshold Sliders", "PARTIAL 02", "Velocity switch thresholds (1-127) with graphic crossfade curve", "Drag / Dial", "Yes", "Sets dynamic velocity trigger points for multi-sampled velocity layers", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:905", "tests/test_interactive_ui.py"),
            ("Partial TVF: 4-Point Filter Envelope Canvas", "PARTIAL 03", "Interactive envelope graphic: Rate 1-4, Level 1-4 (4-point break-point envelope)", "Drag / Point", "Yes", "Visualizes 4-pole 24dB/oct resonant TVF envelope with draggable point nodes", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:925", "tests/test_dsp_tools.py"),
            ("Partial TVF: Cutoff Frequency Dial", "PARTIAL 03", "Cutoff dial (0-127)", "Drag / Dial", "Yes", "Sets base resonant filter frequency", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:930", "tests/test_dsp_tools.py"),
            ("Partial TVF: Resonance Peak Feedback Dial", "PARTIAL 03", "Resonance dial (0-127)", "Drag / Dial", "Yes", "Sets 24dB/oct filter resonant feedback sharpness", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:935", "tests/test_dsp_tools.py"),
            ("Partial TVA: 4-Point Amp Envelope Canvas", "PARTIAL 04", "Interactive envelope graphic: Attack Rate, Decay, Sustain, Release curves", "Drag / Point", "Yes", "Visualizes amplifier envelope contour with real-time level scaling", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:945", "tests/test_dsp_tools.py"),
            ("Partial TVA: Level & Velocity Sens Dials", "PARTIAL 04", "Level (0-127), Velocity Sensitivity (-15..+15), Pan Curve (1-7)", "Drag / Dial", "Yes", "Adjusts partial output volume, velocity response curve, and stereo panning shape", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:950", "tests/test_dsp_tools.py"),
            ("Partial LFO: Waveform Dropdown & Rate Dial", "PARTIAL 05", "Waveform selector (Sine, Triangle, Saw, Square, Random); Rate (0-127)", "Click / Select / Drag", "Yes", "Configures low frequency modulator shape and speed", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:965", "tests/test_dsp_tools.py"),
            ("Partial LFO: Mod Depth Dials", "PARTIAL 05", "Pitch Depth (0-127), TVF Cutoff Depth (0-127), TVA Amplitude Depth (0-127)", "Drag / Dial", "Yes", "Applies LFO modulation to vibrato, filter wah, or tremolo effects", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:970", "tests/test_dsp_tools.py"),
            ("Partial Q-Sampling: Quick Sample Button", "PARTIAL 06", "Trigger button", "Click / Hotkey", "Yes", "Records sample directly into partial slot", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:980", "tests/test_interactive_ui.py"),
        ]
    },
    {
        "category": "6. SAMPLE Mode & DSP Tools Suite (Pages 01 - 14)",
        "description": "Live recording with high-res stereo VU meters, 440px graphical audio wave display with draggable loop markers, zoom match, and 11 DSP tool subpages. Rendered by the React CRT monitor component.",
        "owner": OWNER_OP760,
        "elements": [
            ("Sampling 01: High-Res Peak VU Meters", "SAMPLE 01", "Dual 30-segment LED peak meters (-48dB to 0dBFS + Red CLIP)", "View / Real-Time Pulse", "Yes", "Monitors live input audio stream level with clip hold indicators", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1040", "tests/test_interactive_ui.py"),
            ("Sampling 01: Rate & Pre-Trigger Selectors", "SAMPLE 01", "Sampling Freq (48k/44.1k/32k/22.05k/16k), Pre-Trigger time (0-500ms), Auto-Trig Level", "Click / Dial", "Yes", "Configures ADC capture clock, threshold trigger, and circular pre-buffer", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1050", "tests/test_interactive_ui.py"),
            ("Sampling 01: Record / Stop Transport Buttons", "SAMPLE 01", "Arm, Record, Stop, Test Play buttons", "Click / Hotkeys", "Yes", "Controls live recording workflow into sample wave RAM buffer", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1060", "tests/test_interactive_ui.py"),
            ("Loop & Smooth 02: 440px Audio Waveform Canvas", "SAMPLE 02", "440px graphical waveform trace with Start, End, and Loop point overlays", "Click / Drag / Zoom", "Yes", "Renders sample PCM wave data with draggable Start, Loop Start, and End markers", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:1080", "tests/test_interactive_ui.py"),
            ("Loop & Smooth 02: Start / Loop / End Drag Markers", "SAMPLE 02", "3 draggable vertical cursor overlays on waveform", "Drag / Marker", "Yes", "Sets start, loop point, and end sample boundaries interactively", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:1085", "tests/test_interactive_ui.py"),
            ("Loop & Smooth 02: Zoom Match Buttons", "SAMPLE 02", "Zoom In (+), Zoom Out (-), Zoom Match (zero-crossing alignment)", "Click", "Yes", "Magnifies waveform display around loop point and auto-snaps to nearest zero crossing", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:1090", "tests/test_dsp_tools.py"),
            ("Loop & Smooth 02: Crossfade Length Slider", "SAMPLE 02", "Crossfade smoothing duration (0-1000ms) with forward/alternating loop mode", "Drag / Dial", "Yes", "Performs equal-power crossfade interpolation across loop boundary", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:1095", "tests/test_dsp_tools.py"),
            ("Auto-Truncate 03: Silence Threshold Slider", "SAMPLE 03", "Noise floor threshold slider (-96dB to -12dB) with preview highlight", "Drag / Dial", "Yes", "Calculates leading and trailing silence cut markers and updates wave bounds", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1105", "tests/test_dsp_tools.py"),
            ("DSP Tools 04: SOLA Time Stretch Controls", "SAMPLE 04", "Time-stretch ratio input (50.0% to 200.0%) with pitch preservation mode", "Dial / Text", "Yes", "Executes SOLA time expansion/compression algorithm on sample wave data", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:1135", "tests/test_dsp_tools.py"),
            ("DSP Tools 05: Sinc Polyphase Resampler Selectors", "SAMPLE 05", "Target sample rate dropdown (48k->44.1k/32k/22.05k/16k)", "Click / Select", "Yes", "Applies sinc polyphase resampling with anti-aliasing filter", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:1150", "tests/test_dsp_tools.py"),
            ("DSP Tools 06: Bit Depth Converter Buttons", "SAMPLE 06", "Bit depth (16/12/8-bit) and dither noise shaping toggle", "Click / Toggle", "Yes", "Applies dynamic range decimation to vintage bit depths", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1160", "tests/test_dsp_tools.py"),
            ("DSP Tools 07: Compressor / Expander Sliders", "SAMPLE 07", "Knee threshold (-60dB to 0dB), ratio (1:1 to 20:1), attack/release", "Drag / Slider", "Yes", "Executes dynamics processing on sample wave RAM", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:1165", "tests/test_dsp_tools.py"),
            ("DSP Tools 08: Digital Filter Frequency Sliders", "SAMPLE 08", "Cutoff frequency (20Hz-20kHz) and mode (LPF/HPF/BPF)", "Drag / Dial", "Yes", "Filters sample wave buffer destructively", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1170", "tests/test_dsp_tools.py"),
            ("DSP Tools 09-14: Destructive Wave Splicers", "SAMPLE 09-14", "Cut, Erase, Insert, Mix, Normalize action triggers", "Click", "Yes", "Performs destructive buffer operations (sample mixing, amplitude normalization, splicing)", "Unverified", "Yes", "Medium", "google-ui/src/components/OP760Monitor.tsx:1180", "tests/test_dsp_tools.py"),
        ]
    },
    {
        "category": "7. DISK Mode (Pages 01 - 02)",
        "description": "16-file directory table, drive selector buttons (FDD, SCSI Hard Disks, CD-ROMs), Load/Save/Overwrite, and free space meters. Rendered by the React CRT monitor component.",
        "owner": OWNER_OP760,
        "elements": [
            ("Disk: Drive Selector Dropdown", "DISK 01", "CD[FDD: -FloppyDisk-], CD[SCSI: 0 HardDisk ], CD[SCSI: 1 CD-ROM  ]", "Click / Select", "Yes", "Switches active storage media drive and refreshes directory table", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:980", "tests/test_disk_conversion.py"),
            ("Disk: 16-Row File Directory Table", "DISK 01", "16-row file list (Index 01-16) with Name, Type, Size, Time, P#", "Click / Arrow Keys", "Yes", "Displays directory contents with row selection, scrolling, and column headers", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:970", "tests/test_interactive_ui.py"),
            ("Disk: Directory Vertical Scrollbar", "DISK 01", "Interactive scrollbar track and thumb", "Drag / Click", "Yes", "Scrolls through multi-page directory tables", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:975", "tests/test_interactive_ui.py"),
            ("Disk: Load Action Trigger [Load]", "DISK 01", "Load button", "Click / F4 Key", "Yes", "Loads selected patch or sample into wave RAM", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:990", "tests/test_interactive_ui.py"),
            ("Disk: Save Action Trigger [Save]", "DISK 01", "Save button", "Click / F5 Key", "Yes", "Saves current sound bank to active disk target", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:992", "tests/test_interactive_ui.py"),
            ("Disk: Overwrite Trigger [Overwrite]", "DISK 01", "Overwrite button", "Click / Hotkey", "Yes", "Overwrites selected sound file with confirmation prompt", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:995", "tests/test_interactive_ui.py"),
            ("Disk: Delete Trigger [Delete]", "DISK 01", "Delete button", "Click / Hotkey", "Yes", "Deletes file entry and frees FAT clusters", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:998", "tests/test_interactive_ui.py"),
            ("Disk: Volume Information Readout", "DISK 02", "Volume name, Total Clusters, Free Clusters, Work RAM % gauge", "View / Dynamic Readout", "Yes", "Displays detailed volume storage statistics and cluster allocation map", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1000", "tests/test_interactive_ui.py"),
        ]
    },
    {
        "category": "8. SYSTEM Mode (Pages 01 - 05)",
        "description": "Master tuning, LCD contrast, mouse speed, 7-row SCSI target matrix, MIDI channel configuration, and Volume ID. Rendered by the React CRT monitor component.",
        "owner": OWNER_OP760,
        "elements": [
            ("System Parameter: Master Tune Dial", "SYSTEM 01", "Master Tune (440.0 Hz +/- 10.0Hz)", "Drag / Dial", "Yes", "Calibrates master pitch reference frequency", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1625", "tests/test_interactive_ui.py"),
            ("System Parameter: Output Gain Switch", "SYSTEM 01", "Switch (+0dB / +6dB)", "Click / Toggle", "Yes", "Adjusts master analog output buffer gain", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1628", "tests/test_interactive_ui.py"),
            ("System Parameter: LCD Contrast Slider", "SYSTEM 02", "LCD Contrast slider (0-15)", "Drag / Dial", "Yes", "Adjusts SED1335 LCD display contrast", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1635", "tests/test_interactive_ui.py"),
            ("System Parameter: Mouse Speed Multiplier", "SYSTEM 02", "Multiplier selector (1x / 2x / 4x)", "Click / Select", "Yes", "Sets serial mouse cursor sensitivity", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1640", "tests/test_interactive_ui.py"),
            ("System SCSI: 7-Row Target Matrix", "SYSTEM 03", "SCSI IDs 0 through 6 status rows (Vendor, Model, Capacity, Sync Speed)", "Click / Select", "Yes", "Scans SCSI bus and displays connected hard disks, CD-ROM drives, and MO units", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1655", "tests/test_disk_conversion.py"),
            ("System SCSI: Bus Scan Action Button", "SYSTEM 03", "Scan Bus button", "Click / Hotkey", "Yes", "Initiates live bus query across SCSI IDs 0-6", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1660", "tests/test_disk_conversion.py"),
            ("System MIDI: Device ID & Channel Dials", "SYSTEM 04", "MIDI Device ID (1-32), Control Ch (1-16)", "Click / Dial", "Yes", "Configures global MIDI reception channels and SysEx device ID", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1685", "tests/test_interactive_ui.py"),
            ("System MIDI: SysEx RX/TX Toggles", "SYSTEM 04", "SysEx RX / TX switches", "Click / Toggle", "Yes", "Enables Roland SysEx bulk dump reception and transmission", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1690", "tests/test_interactive_ui.py"),
            ("System Volume ID: Volume Label Editor", "SYSTEM 05", "Volume Label text field, Write Protect toggle, Boot Drive selector", "Text / Toggle", "Yes", "Edits volume name and manages system write protection", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1715", "tests/test_interactive_ui.py"),
        ]
    },
    {
        "category": "9. Modals, Popups, Overlays & Dialogs",
        "description": "Interactive popups including Mark bookmarking, Jump page hopping, Command shortcuts, confirmation dialogs, and progress spinners. Rendered by the React CRT monitor component.",
        "owner": OWNER_OP760,
        "elements": [
            ("Mark Modal: 10 Quick-Bookmark Slots", "Global Modal", "10 Bookmark buttons (01-10) with assigned page names", "Click / Number Key", "Yes", "Saves current UI page and cursor location into one of 10 quick-recall slots", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1875", "tests/test_interactive_ui.py"),
            ("Jump Modal: 10 Rapid Screen Hops", "Global Modal", "10 Rapid navigation buttons (01-10)", "Click / Number Key", "Yes", "Jumps instantly to bookmarked page and restores focused parameter", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1890", "tests/test_interactive_ui.py"),
            ("Command Modal: 6 Quick Command Actions", "Global Modal", "6 Command buttons (1-6) [e.g. Copy, Paste, Swap, Delete, Undo, Ext]", "Click / Number Key", "Yes", "Executes high-level clipboard and management commands across screens", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1905", "tests/test_interactive_ui.py"),
            ("Confirmation Modal: 'Are You Sure?' Dialog", "Global Modal", "Warning message prompt with [OK / Execute] and [Cancel] buttons", "Click / Enter / Exit", "Yes", "Guards destructive operations (Overwrite, Delete, Format) with user confirmation", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1920", "tests/test_interactive_ui.py"),
            ("Volume Information Modal", "Global Modal", "Detailed memory breakdown table (Work RAM, Wave RAM, Free Clusters)", "Click / Dismiss", "Yes", "Presents detailed system resource allocations in a non-blocking modal overlay", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1935", "tests/test_interactive_ui.py"),
            ("Now Working... Progress Spinner Banner", "Global Overlay", "Animated progress indicator + task message banner ('Now Working...')", "View / Auto-Dismiss", "Yes", "Displays visual activity feedback during long DSP time-stretching and disk I/O", "Unverified", "Yes", "Low", "google-ui/src/components/OP760Monitor.tsx:1950", "tests/test_interactive_ui.py"),
        ]
    }
]

def generate_markdown():
    if __package__:
        from .coverage_report import write_report
    else:
        from coverage_report import write_report
    sections = [(s['category'], [(r[0], r[1]) for r in s['elements']]) for s in EXHAUSTIVE_UI_SECTIONS]
    write_report(OUTPUT_PATH, 'UI research inventory', sections)


if __name__ == '__main__':
    generate_markdown()

# VST3 configuration and startup recovery

Open **Plugin configuration** using the gear button in the plugin editor. The
screen shares the standalone firmware/media form and adds installation and
runtime-state directories. Audio and MIDI devices remain controlled by the host;
the plugin screen does not expose standalone audio, ASIO or keyboard options.

Supply absolute paths to the S-760 installation, writable runtime-state
directory, user-supplied 32KB Boot ROM, 1.44MB system disk and existing media
directory. Confirm **Apply after reloading the plugin in the host**, then choose
**Save plugin settings**. Save your project and export disk writes before
reloading the plugin to apply the new settings. Saving configuration does not
reboot or replace the active machine.

Settings use version1 UTF-8 JSON at
`LOCALAPPDATA/S760/plugin-settings.json`, or the absolute `S760_PLUGIN_CONFIG`
override. Firmware and runtime files are validated before an atomic replacement;
rejected changes leave the previous settings intact. The selected media
directory is scanned when the new native instance starts. Configuration remains
available after closing/reopening the editor and removing/reloading the plugin.

Existing explicit `S760_NATIVE_ROOT`, `S760_NATIVE_STATE_ROOT`, `S760_BOOT_ROM`
and `S760_SYSTEM_DISK` host-environment overrides retain precedence. Remove those
overrides when using saved settings; configuration cannot change the host's
inherited environment. Complete explicit environment configuration bypasses the
settings-file profile, including its optional media-directory field.

## Failure recovery

Missing/invalid firmware or runtime settings now create a silent native
configuration instance. Its editor automatically opens the configuration screen
and displays the startup reason. It does not substitute the historical core,
produce demonstration audio or start a native child. Correct the paths, save
and reload the plugin through the host. Invalid edits show their specific
validation error and preserve both the settings file and current machine.

The installed editor must be available: discovery searches installation
ancestors of the loaded module for `google-ui/dist/index.html`, independently
of the invalid runtime-root setting. An installation with missing editor assets
still requires repair; the factory returns failure and writes diagnostics.
Settings-only recovery is not firmware redistribution or automatic discovery of
Roland binaries. Unconfigured instances do not provide machine checkpoints.

## Qualification

SoundCheck1.0.0 Windows x64 native QA hosting verifies missing-firmware error
presentation, silent processing, rejected relative paths preserving settings,
valid save, editor reopen and host reload. A Unicode media-folder path survives
UTF-8 persistence and the new instance loads ROBOFULL through original firmware.
Loaded note pitch/level and note-off release are measured separately from UI
acknowledgments. The exported factory also verifies that saving configuration
while processing is active starts no native child and preserves silent output,
then boots native firmware and matches independent reference PCM.

This completes the scoped Milestone4 configuration gate. Other DAWs and damaged
installation repair remain unqualified. DAW project-file save/reopen, relocated
media portability and live host sampling input remain separate objectives.
See the [validation record](condensed/validation/milestone-4-configuration-2026-10-12.json).

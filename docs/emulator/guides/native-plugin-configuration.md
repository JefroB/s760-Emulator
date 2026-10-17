# Native VST3 configuration

The Windows plugin accepts persistent runtime paths, independent of the host's
working directory. Supply your own Roland boot ROM and system disk; the settings
contain paths only. This is the development configuration workflow. In-plugin
graphical setup and recovery remain Milestone 4 work.

From the S-760 installation, build the native runtime, concrete WebView2 plugin
and `google-ui/dist`, then run:

```powershell
python scripts/configure_vst3.py --root D:/S-760 --state-root D:/S760-sessions --boot-rom D:/MyFirmware/s760.bin --system-disk D:/MyFirmware/S760224.IMG
```

The tool validates absolute paths, the native executable/Lua and built editor,
the 32KB boot ROM and 1.44MB system disk, then atomically saves
`%LOCALAPPDATA%/S760/plugin-settings.json`. Invalid changes preserve existing
settings; firmware/runtime files cannot be overwritten by the settings writer.
Validation checks file shape/readability, not authenticity or OS compatibility.
OS 2.24 is the qualified profile.

Reload the plugin after changing settings. Each new instance allocates a separate
directory beneath `stateRoot`. Active instances and their saved sessions are not
changed. Media browsing remains available through the Gotek Select dialog.

For a custom settings location, pass `--config <absolute-file>` and set
`S760_PLUGIN_CONFIG` to that filename in the host environment. JSON format:

```json
{
  "version": 1,
  "root": "D:/S-760",
  "stateRoot": "D:/S760-sessions",
  "bootRom": "D:/MyFirmware/s760.bin",
  "systemDisk": "D:/MyFirmware/S760224.IMG"
}
```

The existing `S760_NATIVE_ROOT`, `S760_NATIVE_STATE_ROOT`, `S760_BOOT_ROM` and
`S760_SYSTEM_DISK` environment variables override individual file values. A
complete environment configuration bypasses the file. Clear stale overrides when
switching to saved settings. The editor URL follows the configured root;
`S760_UI_URL` remains an explicit development override.

## Startup failure and recovery

The factory rejects invalid configuration without substituting a demo engine.
It writes the reason, settings location and repair instruction to the host's
stderr and, best-effort, `<settings-file>.last-error.txt`. The latter records the
**last failure**, which can predate a subsequent successful launch. Hosts may hide
stderr; inspect this file or run:

```powershell
python scripts/configure_vst3.py --diagnose
python scripts/configure_vst3.py --check
```

Correct the reported path/size or malformed JSON using the setup command, then
reload/rescan in the host. A host that blacklists failed plugins may require its
own rescan action. Failed instance creation cannot display an in-plugin dialog;
graphical recovery is not claimed by this workflow.

SoundCheck/SDK configuration and audio evidence is recorded in
[Milestone 2 progress](../../testing/milestone-2-progress.md). These checks do not qualify a
clean-machine installer, all DAWs, arbitrary workloads, or hardware parity.

# SoundCheck S-760 project workflow

The supported Milestone4 DAW matrix is SoundCheck1.0.0 Windows x64 with the
private Steinberg SDK adapter and the project-document runner. The user accepted
SoundCheck as the DAW for this gate. This is a reproducible command-driven host
workflow; stock SoundCheck GUI project integration and other DAW containers are
not qualified.

`scripts/soundcheck_project.py` writes/reads version1 JSON project documents.
Each references a sibling component-state file and stores the host sample rate,
negotiated maximum block size, relative firmware/runtime/media configuration and
SHA-256 identities. The selected module is supplied explicitly by the caller;
the document does not execute a module selected from untrusted text. State and
firmware bytes are not embedded in the JSON document or redistributed.

Opening validates document version, size, sibling state reference and all saved
content identities before launching the host. It returns settings to write to a
project-local file selected with `S760_PLUGIN_CONFIG`, and allocates a fresh
runtime directory. It does not overwrite global plugin configuration. Moving a
project and its referenced files together preserves relative configuration;
relocating external firmware separately requires explicit configuration updates
with identical content. The plugin checkpoint's own native identity checks still
apply after document validation.

The native adapter quiesces processing before `IComponent::getState`/`setState`
and resumes explicitly. Cold reopen loads the selected module, negotiates the
saved profile and restores the saved component state. Project creation is
exclusive: the helper refuses to overwrite an existing document. It is a
qualification workflow, not an autosave/transactional multi-track project editor.

| Case | Qualified outcome |
| --- | --- |
| Cold process,44.1kHz,maximum512 |221184 exact `(L+R)/2` float frames; silent release tail |
| Old runtime/library paths absent | Captured sample and media labels restore; relocated matching firmware selected |
| Project configuration versus invalid global default | Project settings win; global file remains byte-identical |
| Callback64/127/256/511/512, including splits at note boundaries | Same221184 frames exactly |
| Corrupt component state | Rejected; subsequent replay of valid state remains exact |
| Different module bytes | Document rejects before host launch; cross-build migration unsupported |
| Saved44.1kHz state in48kHz host | Native state rejects explicitly |
| Saved maximum512 in negotiated maximum1024 | Native state rejects; returning to512 restores valid exact replay |

The last two rows qualify rejection, not rate conversion or maximum-block
migration. Reopen at the saved profile. Individual callback sizes can vary within
the negotiated maximum. Earlier native three-rate state tests remain separate
evidence; this SoundCheck project matrix is44.1kHz/maximum512 only. Capture is the
host's full-rate L/R average, not independent stereo-channel fidelity. External
SCSI prerequisites, same-build rules and the native archive size bound remain.

Build a private copy of the SoundCheck backend with the cumulative
[QA adapter patch](condensed/validation/soundcheck-project-document-qa-2026-10-14.patch).
Use the SDK/dependency configuration documented in the existing state runbook.
The verifier requires original local firmware/ROBOFULL, Python numpy/websockets/
playwright, a WebView-enabled module, free loopback ports4000/9231 and a new
private state directory. It starts hidden task-owned hosts, then removes them.

```powershell
python scripts/verify_soundcheck_project.py --host <private-SoundCheckServer.exe> --module <WebView-Roland_S760.vst3> --state-dir <new-private-directory>
```

The verifier drives original firmware controls, writes a project document and
state, exits the host, relocates the fixture inputs and opens through the saved
document in a new process. Proprietary state/captures remain private. Results,
source/binary identities and limitations are in the
[validation record](condensed/validation/milestone-4-soundcheck-project-2026-10-14.json).

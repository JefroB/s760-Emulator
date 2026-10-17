# Milestone6 packaged setup and relocation

Qualified2026-10-15 on the Windows development workstation. The package now
includes a [self-contained setup and troubleshooting guide](../emulator/guides/standalone-package-readme.md)
as its root README. It covers installed runtime prerequisites, user-supplied
firmware, first launch, loading, recording limits, media export, session recovery
and actionable errors without requiring source-checkout documents.

BUG-074 reproduced14 absent README destinations in the preceding development
package. The new audit rejects missing README files, broken local inline links
and checkout/absolute/escaping paths. It preserves upstream license texts;
external website availability and Markdown fragment validity are not tested.
The audit's own JSON destination is generated after validation.

## Executed acceptance

| Check | Result and scope |
| --- | --- |
| Failing regression | Old audit accepted README → absent firmware-setup.md; new test failed before implementation |
| Package/inventory regressions |25 passed, including missing-link, missing-README, escaping-path, valid-link and fenced-example cases |
| Full backend regressions |404 passed, zero failures/skips; private harness and snapshot directories |
| Fresh frozen package | Build and development audit pass; no proprietary media embedded; license/notices retained |
| Relocated browser setup | A copied `S760 Studio` package launched from an unrelated working directory with spaces in firmware/media/profile paths |
| Removed development environment | Child PATH contains Windows System32 only; PYTHON*, NODE_* and S760_* variables removed |
| Startup repair | No firmware defaults supplied; Configuration remains available,256-byte boot ROM rejects without saving settings, valid32KB boot ROM starts OS2.24 |
| Persistent profile | A second frozen process launches with only the same state-directory argument; firmware/media paths and muted output persist, OS reaches Perform Play |
| Actual desktop host | Copied package's WebView2 window reports OS ready,640×480 and228564 nonzero CRT pixels with the same stripped environment |
| TypeScript | `npm run lint` passes |

The final Visual C++ prerequisite wording was copied into both built and relocated
README files and both package audits regenerated. Runtime binaries were unchanged
by that documentation correction. No simulator or mocked transport supplied these
browser/desktop results.

## Reproduce

Build with `scripts/build_standalone.ps1` in a provisioned Windows development
environment. If Python dependencies are in a private directory, expose that
directory through PYTHONPATH for the build only. Then, from `google-ui`:

```powershell
$env:S760_SETUP_PACKAGE = 'D:/path/to/build/dist/S760Studio'
$env:S760_SETUP_WORK = 'D:/path/to/fresh-private-work'
node node_modules/@playwright/test/cli.js test packaged-setup.spec.ts --config=playwright.packaged.config.ts --output=../docs/ic20-hle-findings/chatGPT-work/package-setup-results
```

The test stages private copies of local IC15v1.11, OS2.24 and ROBOFULL inputs;
those inputs remain excluded from distributions. Playwright Chromium and local
loopback access are QA prerequisites. The application child itself receives no
development-tool environment. The dedicated config runs no Vite server.

For bounded desktop verification, run the relocated `S760Studio.exe` with
`--verify-desktop --no-sound --fast`, a fresh `--state-dir`, and explicit local
`--boot-rom`, `--system-disk` and `--media-dir`. Paths containing spaces must be
quoted in PowerShell or supplied as separate arguments through a process API.

[Exact commands, source/package hashes and results](../condensed/validation/milestone-6-package-setup-2026-10-15.json).

## Remaining release gates

This machine already has Visual C++ and WebView2 runtimes. Stripping environment
variables and moving files does not establish installation on a clean machine or
qualify an installer. Checks are silent/unthrottled and do not repeat normal-speed
audio-device sampling or the complete editing workflow in WebView. The new package
is development-only: changed-artifact distribution/source/dependency review,
VST3 packaging, final revision freeze and final shipped-artifact acceptance remain
open. Existing dated editing/audio evidence retains its original artifact identity.

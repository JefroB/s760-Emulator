param(
    [string]$OutputDirectory = "$PSScriptRoot/../docs/ic20-hle-findings/chatGPT-work/standalone-package",
    [switch]$Release
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot/..").Path
$output = [IO.Path]::GetFullPath($OutputDirectory)
if ($Release) {
    & python "$repo/scripts/s760_package_audit.py" --repo $repo --package "$output/dist/S760Studio" --require-release
    if ($LASTEXITCODE -ne 0) { throw 'Package does not match the reviewed distribution. See docs/testing/distribution-qualification.md.' }
    Write-Output "Verified reviewed standalone distribution: $output/dist/S760Studio"
    return
}
# No firmware, sample media, captures or private notes enter the package.
Push-Location "$repo/google-ui"
try {
    & cmake --build "$repo/build" --config Release --target s760_asio
    if ($LASTEXITCODE -ne 0) { throw 'Native ASIO bridge build failed' }
    $asioPortAudio = & python "$repo/scripts/s760_asio.py"
    if ($LASTEXITCODE -ne 0) { throw 'ASIO-enabled PortAudio runtime is missing' }
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw 'React build failed' }
} finally { Pop-Location }
Push-Location $repo
try {
    & python -m PyInstaller --noconfirm --onedir --windowed --name S760Studio `
        --add-binary "$repo/build/Release/s760_asio.dll;audio" --add-binary "$asioPortAudio;audio" `
        --paths "$repo/scripts" --collect-all webview --exclude-module webview.__pyinstaller --exclude-module PyInstaller --copy-metadata pywebview `
        --copy-metadata websockets --copy-metadata pythonnet `
        --distpath "$output/dist" --workpath "$output/build" --specpath $output `
        "$repo/scripts/s760_standalone.py"
    if ($LASTEXITCODE -ne 0) { throw 'Standalone executable build failed' }
    $package = "$output/dist/S760Studio"
    New-Item -ItemType Directory -Path "$package/audio" -Force | Out-Null
    Copy-Item -LiteralPath "$repo/mame-source/3rdparty/portaudio/LICENSE.txt" -Destination "$package/audio/PORTAUDIO-LICENSE.txt"
    foreach ($folder in @('scripts','google-ui','mame-source','roms/FDD')) {
        New-Item -ItemType Directory -Path "$package/$folder" -Force | Out-Null
    }
    Copy-Item -LiteralPath "$repo/scripts/s760_runtime.lua" -Destination "$package/scripts/"
    Copy-Item -LiteralPath "$repo/google-ui/dist" -Destination "$package/google-ui/" -Recurse -Force
    Copy-Item -LiteralPath "$repo/mame-source/mames760.exe" -Destination "$package/mame-source/"
    Copy-Item -LiteralPath "$repo/mame-source/plugins" -Destination "$package/mame-source/" -Recurse -Force
    Copy-Item -LiteralPath "$repo/mame-source/COPYING" -Destination "$package/MAME-COPYING.txt"
    if (Test-Path -LiteralPath "$repo/LICENSE") {
        Copy-Item -LiteralPath "$repo/LICENSE" -Destination "$package/LICENSE.txt"
    }
    Copy-Item -LiteralPath "$repo/docs/emulator/guides/standalone-package-readme.md" -Destination "$package/README.md"
    & python "$repo/scripts/s760_distribution_inventory.py" --package $package --build "$output/build/S760Studio" --external-windows-runtime
    if ($LASTEXITCODE -ne 0) { throw 'Bundled input inventory failed' }
    & python "$repo/scripts/s760_package_audit.py" --repo $repo --package $package --prepare
    if ($LASTEXITCODE -ne 0) { throw 'Development package audit failed; do not use this artifact' }
    Write-Output "Development-only standalone package: $package (public distribution is not qualified)"
} finally { Pop-Location }

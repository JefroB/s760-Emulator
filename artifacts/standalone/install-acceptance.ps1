param(
    [string]$Archive,
    [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference = 'Stop'
if (-not $Archive) { $Archive = Join-Path $PSScriptRoot 's760-standalone-acceptance-2026-10-17.zip' }
$archivePath = (Resolve-Path -LiteralPath $Archive).Path
$expected = 'b1dd036c9331058fb2db0dde75d038e985fc75d5919c19040766460f5cdb08f9'
if ((Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Acceptance ZIP checksum mismatch. Nothing has been unblocked or extracted. Download the exact qualification archive again.'
}
$destinationPath = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $destinationPath) { throw 'Choose a new destination folder; existing installations and evidence are preserved.' }
# Explicitly trusting this hash-verified archive removes only its download mark.
# No machine-wide policy, .NET configuration or existing installation is changed.
Unblock-File -LiteralPath $archivePath
Expand-Archive -LiteralPath $archivePath -DestinationPath $destinationPath
$manifestPaths = @(Get-ChildItem -LiteralPath $destinationPath -Filter PACKAGE-MANIFEST.json -Recurse -File)
if ($manifestPaths.Count -ne 1) { throw 'Expected exactly one package manifest in the extracted acceptance kit.' }
$kitRoot = Split-Path -Parent $manifestPaths[0].FullName
$packageRoot = Join-Path $kitRoot 'S760Studio'
$packagePrefix = [IO.Path]::GetFullPath($packageRoot).TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
$manifest = Get-Content -LiteralPath $manifestPaths[0].FullName -Raw | ConvertFrom-Json
foreach ($entry in $manifest.files.PSObject.Properties) {
    $file = [IO.Path]::GetFullPath((Join-Path $packageRoot $entry.Name))
    if (-not $file.StartsWith($packagePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest path escapes package.' }
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Package file missing: $($entry.Name)" }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value.sha256) { throw "Package file mismatch: $($entry.Name)" }
}
if (@(Get-ChildItem -LiteralPath $packageRoot -Recurse -File).Count -ne @($manifest.files.PSObject.Properties).Count) { throw 'Unexpected package files after extraction.' }
# Handle Windows extraction implementations that propagate attachment metadata.
# The ZIP hash and all package hashes have already been verified.
Get-ChildItem -LiteralPath $destinationPath -Recurse -File | Unblock-File
Write-Output "Verified and extracted acceptance kit: $kitRoot"
Write-Output "Run: $(Join-Path $packageRoot 'S760Studio.exe')"
Write-Output 'Clean-machine acceptance still requires two complete workflows and evidence review.'

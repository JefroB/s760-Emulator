param(
    [Parameter(Mandatory=$true)][string]$PortAudioSource,
    [Parameter(Mandatory=$true)][string]$AsioSdk,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $PortAudioSource).Path
$sdk = (Resolve-Path -LiteralPath $AsioSdk).Path
$output = [IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $output) { throw 'Use a fresh output directory without cached objects.' }
if (-not ((Get-Content -LiteralPath "$sdk/LICENSE.txt" -Raw) -match 'General Public License.*Version 3')) {
    throw 'Supply the ASIO SDK 2.3.4 source with its GPLv3 license option.'
}
& cmake -S $source -B "$output/build" -A x64 '-DCMAKE_POLICY_VERSION_MINIMUM=3.5' `
    -DPA_USE_ASIO=ON "-DASIOSDK_ROOT_DIR=$sdk" -DPA_BUILD_SHARED=ON -DPA_BUILD_STATIC=OFF `
    -DPA_BUILD_TESTS=OFF -DPA_BUILD_EXAMPLES=OFF
if ($LASTEXITCODE -ne 0) { throw 'PortAudio/ASIO configuration failed.' }
& cmake --build "$output/build" --config Release --parallel 2
if ($LASTEXITCODE -ne 0) { throw 'PortAudio/ASIO build failed.' }
Copy-Item -LiteralPath "$output/build/Release/portaudio_x64.dll" -Destination "$output/libportaudio64bit-asio.dll"
$inputs = @{}
foreach ($entry in @(@('portaudio', $source), @('ASIOSDK', $sdk))) {
    foreach ($file in Get-ChildItem -LiteralPath $entry[1] -File -Recurse) {
        $relative = $file.FullName.Substring($entry[1].Length + 1).Replace('\','/')
        $inputs["$($entry[0])/$relative"] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
@{
    schema = 1
    license = 'PortAudio MIT; ASIO SDK common code GPL-3.0; retain embedded BSD helper notices'
    binary_sha256 = (Get-FileHash -LiteralPath "$output/libportaudio64bit-asio.dll" -Algorithm SHA256).Hash.ToLowerInvariant()
    source_sha256 = $inputs
    release_qualified = $false
} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$output/ASIO-BUILD.json" -Encoding UTF8
Write-Output "Built $output/libportaudio64bit-asio.dll; distribute corresponding source and notices with the combined application."

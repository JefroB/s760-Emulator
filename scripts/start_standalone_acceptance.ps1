param(
    [string]$PackageDirectory,
    [string]$Manifest,
    [Parameter(Mandatory=$true)][string]$BootRom,
    [Parameter(Mandatory=$true)][string]$SystemDisk,
    [Parameter(Mandatory=$true)][string]$MediaDirectory,
    [string]$ReportDirectory = "$env:LOCALAPPDATA/S760Studio/Acceptance-$(Get-Date -Format yyyyMMdd-HHmmss)",
    [switch]$VerifyOnly
)
$ErrorActionPreference = 'Stop'
$acceptanceRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $PackageDirectory) { $PackageDirectory=Join-Path $acceptanceRoot 'S760Studio' }
if (-not $Manifest) { $Manifest=Join-Path $acceptanceRoot 'PACKAGE-MANIFEST.json' }
$package = (Resolve-Path -LiteralPath $PackageDirectory).Path
$manifestPath = (Resolve-Path -LiteralPath $Manifest).Path
$inventory = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$rootPrefix = $package.TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
foreach ($entry in $inventory.files.PSObject.Properties) {
    $candidate = [IO.Path]::GetFullPath((Join-Path $package $entry.Name))
    if (-not $candidate.StartsWith($rootPrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest path escapes package directory' }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw "Package file missing: $($entry.Name)" }
    if ((Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value.sha256) { throw "Package hash mismatch: $($entry.Name)" }
}
if (@(Get-ChildItem -LiteralPath $package -Recurse -File).Count -ne @($inventory.files.PSObject.Properties).Count) { throw 'Package contains unexpected files' }
$boot = (Resolve-Path -LiteralPath $BootRom).Path
$system = (Resolve-Path -LiteralPath $SystemDisk).Path
$media = (Resolve-Path -LiteralPath $MediaDirectory).Path
if (-not (Test-Path -LiteralPath $media -PathType Container)) { throw 'Media directory must be a folder' }
$bootHash = (Get-FileHash -LiteralPath $boot -Algorithm SHA256).Hash.ToLowerInvariant()
$systemHash = (Get-FileHash -LiteralPath $system -Algorithm SHA256).Hash.ToLowerInvariant()
if ($bootHash -ne 'ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6') { throw 'Acceptance requires the documented IC15 v1.11 ROM' }
if ($systemHash -ne '3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd') { throw 'Acceptance requires the documented OS 2.24 image' }
$report = [IO.Path]::GetFullPath($ReportDirectory)
if (Test-Path -LiteralPath $report) { throw 'Use a fresh report directory; existing evidence is preserved' }
New-Item -ItemType Directory -Path $report | Out-Null
$tools = @('python','node','git','cmake','cl') | ForEach-Object {
    $command = Get-Command $_ -ErrorAction SilentlyContinue
    if ($command) { @{name=$_;path=$command.Source} }
}
$webviewRoots = @("${env:ProgramFiles(x86)}/Microsoft/EdgeWebView/Application", "$env:LOCALAPPDATA/Microsoft/EdgeWebView/Application")
$webview = @($webviewRoots | Where-Object {Test-Path -LiteralPath $_} | ForEach-Object {
    Get-ChildItem -LiteralPath $_ -Directory | ForEach-Object {
        $exe = Join-Path $_.FullName 'msedgewebview2.exe'
        if (Test-Path -LiteralPath $exe) { @{path=$exe;version=(Get-Item -LiteralPath $exe).VersionInfo.FileVersion} }
    }
})
$vc = Join-Path $env:WINDIR 'System32/vcruntime140.dll'
try { $osDetails=Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture,InstallDate }
catch { $osDetails=@{version=[Environment]::OSVersion.VersionString;metadata_error=$_.Exception.Message} }
$environment = @{
    schema=1;date=(Get-Date).ToUniversalTime().ToString('o');status='NOT_RUN';clean_machine_claimed=$false
    package_manifest_sha256=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    package_files_verified=@($inventory.files.PSObject.Properties).Count
    os=$osDetails
    development_tools_on_path=@($tools);webview_runtimes=$webview
    vc_runtime= $(if (Test-Path -LiteralPath $vc) {(Get-Item -LiteralPath $vc).VersionInfo.FileVersion} else {'not detected'})
    firmware_sha256=@{boot=$bootHash;system=$systemHash};profile=(Join-Path $report 'profile')
    verify_only=[bool]$VerifyOnly
}
$environment | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $report 'environment.json') -Encoding UTF8
$steps = 'launch','load','play','edit','sample','firmware_save','export','session_restore','cold_reopen'
$results = @{schema=1;steps=@{}}
foreach ($step in $steps) { $results.steps[$step]=@{status='not_run';evidence='';notes=''} }
$results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $report 'results.json') -Encoding UTF8
if (-not $VerifyOnly) {
    $savedEnvironment = @{}
    foreach ($entry in Get-ChildItem Env:) {
        if ($entry.Name -match '^(PYTHON|NODE_|S760_)' -or $entry.Name -eq 'PATH') {
            $savedEnvironment[$entry.Name]=$entry.Value
        }
    }
    try {
        foreach ($name in $savedEnvironment.Keys) { [Environment]::SetEnvironmentVariable($name,$null,'Process') }
        $env:PATH="$env:WINDIR/System32;$env:WINDIR"
        $arguments = '--state-dir "{0}" --boot-rom "{1}" --system-disk "{2}" --media-dir "{3}"' -f $environment.profile,$boot,$system,$media
        $app=Start-Process -FilePath (Join-Path $package 'S760Studio.exe') -ArgumentList $arguments -WorkingDirectory $report -WindowStyle Hidden -PassThru
        @{pid=$app.Id;arguments=$arguments} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $report 'launch.json') -Encoding UTF8
    } finally {
        foreach ($name in $savedEnvironment.Keys) { [Environment]::SetEnvironmentVariable($name,$savedEnvironment[$name],'Process') }
    }
}
Write-Output "Verified package; acceptance evidence directory: $report"
Write-Output 'Complete the checklist and results.json. This script does not declare workflow or clean-machine acceptance.'

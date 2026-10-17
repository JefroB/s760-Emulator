param([Parameter(Mandatory=$true)][string]$ReportDirectory,[switch]$CleanMachineConfirmed)
$ErrorActionPreference='Stop'
$report=(Resolve-Path -LiteralPath $ReportDirectory).Path
$environment=Get-Content -LiteralPath (Join-Path $report 'environment.json') -Raw | ConvertFrom-Json
$results=Get-Content -LiteralPath (Join-Path $report 'results.json') -Raw | ConvertFrom-Json
$steps='launch','load','play','edit','sample','firmware_save','export','session_restore','cold_reopen'
$pending=@()
foreach ($step in $steps) {
    $entry=$results.steps.$step
    if (-not $entry -or $entry.status -ne 'passed' -or [string]::IsNullOrWhiteSpace($entry.evidence)) { $pending+=$step;continue }
    $evidence=[IO.Path]::GetFullPath((Join-Path $report $entry.evidence))
    $prefix=$report.TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar
    if (-not $evidence.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $evidence -PathType Leaf)) { $pending+=$step }
}
$files=@(Get-ChildItem -LiteralPath $report -Recurse -File | Where-Object {$_.Extension -in @('.png','.wav','.img','.s760state')} | ForEach-Object {
    @{path=$_.FullName.Substring($report.Length+1);bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
})
$summary=@{
    schema=1;date=(Get-Date).ToUniversalTime().ToString('o')
    status=$(if ($environment.verify_only) {'NOT_RUN'} elseif ($pending.Count -gt 0) {'INCOMPLETE'} else {'MANUAL_WORKFLOW_REPORTED_PASS'})
    clean_machine_claimed=[bool]$CleanMachineConfirmed
    package_manifest_sha256=$environment.package_manifest_sha256
    pending_steps=$pending;results=$results;artifact_hashes=$files
    limitation='Manual observations require review with environment.json and evidence. This report does not automatically qualify a release or update the roadmap.'
}
$summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $report 'acceptance-summary.json') -Encoding UTF8
Write-Output "Report written: $(Join-Path $report 'acceptance-summary.json'); status: $($summary.status)"

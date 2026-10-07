<#
  s760.ps1 - Roland S-760 disk image analysis toolkit.
  See SKILL.md for full documentation. Run with a subcommand:
    powershell -ExecutionPolicy Bypass -File .\s760.ps1 <command> [options]
#>

param(
    [Parameter(Position = 0)]
    [string]$Command = "help",

    [string]$Image = ".\S760224.IMG",
    [string]$Offset = "0",
    [string]$Length = "256",
    [int]$Block = 4096,
    [int]$Min = 5,
    [int]$Max = 0,
    [string]$Pattern = "",
    [switch]$Ascii,
    [string]$Arch = "68k",
    [switch]$Swap,
    [string]$Out = "",
    [string]$In = "",
    [string]$Bytes = ""
)

$EXPECTED_SIZE = 0x168000  # 1,474,560 bytes - fixed 1.44MB floppy image

function Parse-Num([string]$s) {
    if ([string]::IsNullOrWhiteSpace($s)) { return 0 }
    $s = $s.Trim()
    if ($s.StartsWith("0x") -or $s.StartsWith("0X")) {
        return [Convert]::ToInt64($s.Substring(2), 16)
    }
    return [Convert]::ToInt64($s, 10)
}

function Get-ImageBytes([string]$path) {
    if (-not (Test-Path $path)) { throw "Image not found: $path" }
    return [System.IO.File]::ReadAllBytes((Resolve-Path $path))
}

function Assert-NotOriginal([string]$path) {
    $orig = (Resolve-Path $Image -ErrorAction SilentlyContinue)
    if ($orig) {
        $full = [System.IO.Path]::GetFullPath($path)
        if ($full -eq $orig.Path) {
            throw "Refusing to write to the original image ($path). Use a copy."
        }
    }
    # Also guard the canonical name regardless of -Image override.
    if ([System.IO.Path]::GetFileName($path) -eq "S760224.IMG") {
        throw "Refusing to write to a file named S760224.IMG. Use a different output name."
    }
}

function Hex-Dump([byte[]]$bytes, [int64]$off, [int64]$count) {
    $end = [Math]::Min($off + $count, $bytes.Length)
    for ($i = $off; $i -lt $end; $i += 16) {
        $line = "{0:X8}  " -f $i
        $ascii = ""
        for ($j = 0; $j -lt 16; $j++) {
            $idx = $i + $j
            if ($idx -lt $end) {
                $b = $bytes[$idx]
                $line += "{0:X2} " -f $b
                if ($b -ge 32 -and $b -lt 127) { $ascii += [char]$b } else { $ascii += "." }
            } else {
                $line += "   "
            }
        }
        Write-Output ($line + " |" + $ascii + "|")
    }
}

function Cmd-Info {
    $b = Get-ImageBytes $Image
    Write-Output ("Image      : {0}" -f (Resolve-Path $Image))
    Write-Output ("Size bytes : {0} (0x{1:X})" -f $b.Length, $b.Length)
    if ($b.Length -eq $EXPECTED_SIZE) {
        Write-Output "Geometry   : 1.44MB floppy OK (2880 x 512)"
    } else {
        Write-Output ("Geometry   : WARNING expected {0} bytes" -f $EXPECTED_SIZE)
    }
    function AsciiAt([int]$start, [int]$len) {
        $sb = New-Object System.Text.StringBuilder
        for ($i = 0; $i -lt $len; $i++) {
            $c = $b[$start + $i]
            if ($c -ge 32 -and $c -lt 127) { [void]$sb.Append([char]$c) } else { [void]$sb.Append(' ') }
        }
        return $sb.ToString().Trim()
    }
    Write-Output ("Model tag  : '{0}'" -f (AsciiAt 0x04 11))
    Write-Output ("Title      : '{0}'" -f (AsciiAt 0x20 31))
    Write-Output ("Copyright  : '{0}'" -f (AsciiAt 0x40 31))
}

function Cmd-Dump {
    $b = Get-ImageBytes $Image
    Hex-Dump $b (Parse-Num $Offset) (Parse-Num $Length)
}

function Cmd-Map {
    $b = Get-ImageBytes $Image
    $len = $b.Length
    for ($off = 0; $off -lt $len; $off += $Block) {
        $ff = 0; $zero = 0; $f0 = 0; $other = 0
        $end = [Math]::Min($off + $Block, $len)
        for ($i = $off; $i -lt $end; $i++) {
            $v = $b[$i]
            if ($v -eq 0xFF) { $ff++ }
            elseif ($v -eq 0x00) { $zero++ }
            elseif ($v -eq 0x0F) { $f0++ }
            else { $other++ }
        }
        $size = $end - $off
        $tag = "DATA/CODE"
        if ($ff -gt $size * 0.9) { $tag = "0xFF-fill" }
        elseif ($zero -gt $size * 0.9) { $tag = "0x00-fill" }
        elseif ($f0 -gt $size * 0.9) { $tag = "0x0F-fill" }
        Write-Output ("{0:X8}  ff={1,5} 00={2,5} 0f={3,5} oth={4,5}  {5}" -f $off, $ff, $zero, $f0, $other, $tag)
    }
}

function Cmd-Strings {
    $b = Get-ImageBytes $Image
    $start = Parse-Num $Offset
    $span = Parse-Num $Length
    if ($span -le 0) { $end = $b.Length } else { $end = [Math]::Min($start + $span, $b.Length) }
    $cur = New-Object System.Text.StringBuilder
    $runStart = 0
    for ($i = $start; $i -lt $end; $i++) {
        $v = $b[$i]
        if ($v -ge 32 -and $v -lt 127) {
            if ($cur.Length -eq 0) { $runStart = $i }
            [void]$cur.Append([char]$v)
        } else {
            if ($cur.Length -ge $Min -and ($Max -le 0 -or $cur.Length -le $Max)) {
                Write-Output ("{0:X8}: {1}" -f $runStart, $cur.ToString())
            }
            [void]$cur.Clear()
        }
    }
    if ($cur.Length -ge $Min) { Write-Output ("{0:X8}: {1}" -f $runStart, $cur.ToString()) }
}

function Cmd-Entropy {
    $b = Get-ImageBytes $Image
    $len = $b.Length
    for ($off = 0; $off -lt $len; $off += $Block) {
        $end = [Math]::Min($off + $Block, $len)
        $counts = New-Object 'int[]' 256
        for ($i = $off; $i -lt $end; $i++) { $counts[$b[$i]]++ }
        $n = $end - $off
        $H = 0.0
        foreach ($c in $counts) {
            if ($c -gt 0) {
                $p = $c / $n
                $H -= $p * [Math]::Log($p, 2)
            }
        }
        $bar = "#" * [int]([Math]::Round($H))
        Write-Output ("{0:X8}  H={1,5:N2}  {2}" -f $off, $H, $bar)
    }
}

function Cmd-Find {
    $b = Get-ImageBytes $Image
    if ([string]::IsNullOrEmpty($Pattern)) { throw "Provide -Pattern" }
    if ($Ascii) {
        $needle = [System.Text.Encoding]::ASCII.GetBytes($Pattern)
    } else {
        $hex = ($Pattern -replace '\s', '')
        if ($hex.Length % 2 -ne 0) { throw "Hex pattern must have even length" }
        $needle = New-Object 'byte[]' ($hex.Length / 2)
        for ($i = 0; $i -lt $needle.Length; $i++) {
            $needle[$i] = [Convert]::ToByte($hex.Substring($i * 2, 2), 16)
        }
    }
    $hits = 0
    $limit = $b.Length - $needle.Length
    for ($i = 0; $i -le $limit; $i++) {
        $match = $true
        for ($j = 0; $j -lt $needle.Length; $j++) {
            if ($b[$i + $j] -ne $needle[$j]) { $match = $false; break }
        }
        if ($match) {
            Write-Output ("{0:X8}" -f $i)
            $hits++
        }
    }
    Write-Output ("--- {0} match(es)" -f $hits)
}

function Cmd-Opcodes {
    $b = Get-ImageBytes $Image
    $start = Parse-Num $Offset
    $span = Parse-Num $Length
    $end = [Math]::Min($start + $span, $b.Length)

    # Optionally byte-swap each 16-bit word before scanning (tests the
    # "code stored word-swapped" hypothesis). Operates on a working copy.
    if ($Swap) {
        $b = $b.Clone()
        for ($i = $start; $i -lt $end - 1; $i += 2) {
            $t = $b[$i]; $b[$i] = $b[$i + 1]; $b[$i + 1] = $t
        }
        Write-Output "(word-swapped scan)"
    }

    if ($Arch -eq "mcs96" -or $Arch -eq "8xc196" -or $Arch -eq "196") {
        # Intel MCS-96 (80C196): little-endian, variable-length, register-memory.
        # Common opcodes (from the MCS-96 opcode map):
        #   F0 RET, FC/FD PUSHF/POPF-ish, C9 PUSH #imm, EF/E7 SCALL/LJMP,
        #   D0-DF conditional jumps (JC/JNC/JE/JNE/... short rel8),
        #   27 SJMP, E3 BR indirect, A0-A3 LD variants, C0-C3 ST variants.
        $tbl = [ordered]@{
            "F0 RET"      = 0;
            "EF SCALL"    = 0;  # 3-byte rel11 call
            "E7 LJMP"     = 0;  # 3-byte rel16 jump
            "27 SJMP"     = 0;  # 2-byte rel8 jump
            "A0..A3 LD"   = 0;
            "C0..C3 ST"   = 0;
            "D0..DF Jcc"  = 0;  # conditional short jumps
            "FE PREFIX"   = 0;  # signed mul/div prefix
            "FC..FF misc" = 0;
        }
        $total = 0
        for ($i = $start; $i -lt $end; $i++) {
            $v = $b[$i]; $total++
            if ($v -eq 0xF0) { $tbl["F0 RET"]++ }
            elseif ($v -eq 0xEF) { $tbl["EF SCALL"]++ }
            elseif ($v -eq 0xE7) { $tbl["E7 LJMP"]++ }
            elseif ($v -eq 0x27) { $tbl["27 SJMP"]++ }
            elseif ($v -ge 0xA0 -and $v -le 0xA3) { $tbl["A0..A3 LD"]++ }
            elseif ($v -ge 0xC0 -and $v -le 0xC3) { $tbl["C0..C3 ST"]++ }
            elseif ($v -ge 0xD0 -and $v -le 0xDF) { $tbl["D0..DF Jcc"]++ }
            elseif ($v -eq 0xFE) { $tbl["FE PREFIX"]++ }
            elseif ($v -ge 0xFC -and $v -le 0xFF) { $tbl["FC..FF misc"]++ }
        }
        Write-Output ("MCS-96 opcode scan of 0x{0:X}..0x{1:X} ({2} bytes):" -f $start, $end, $total)
        foreach ($k in $tbl.Keys) { Write-Output ("  {0,-14} {1}" -f $k, $tbl[$k]) }
        $ret = $tbl["F0 RET"]
        $retDensity = if ($total -gt 0) { $ret / [double]$total } else { 0 }
        Write-Output ("  --- F0(RET) density: {0:P3}  (subroutine-dense code ~0.3-1.5%)" -f $retDensity)
        Write-Output ("  NOTE: MCS-96 is a byte stream; densities are indicative, not exact.")
        return
    }

    if ($Arch -eq "x86") {
        # x86 is a byte stream, not word-aligned. Count common 1-byte opcodes.
        $tbl = @{
            "C3 RET"    = 0;
            "CB RETF"   = 0;
            "E8 CALLrel"= 0;
            "E9 JMPrel" = 0;
            "EB JMPshort"=0;
            "55 PUSHbp" = 0;
            "CD INT"    = 0;
            "90 NOP"    = 0;
            "C9 LEAVE"  = 0;
        }
        $total = 0
        for ($i = $start; $i -lt $end; $i++) {
            $v = $b[$i]; $total++
            switch ($v) {
                0xC3 { $tbl["C3 RET"]++ }
                0xCB { $tbl["CB RETF"]++ }
                0xE8 { $tbl["E8 CALLrel"]++ }
                0xE9 { $tbl["E9 JMPrel"]++ }
                0xEB { $tbl["EB JMPshort"]++ }
                0x55 { $tbl["55 PUSHbp"]++ }
                0xCD { $tbl["CD INT"]++ }
                0x90 { $tbl["90 NOP"]++ }
                0xC9 { $tbl["C9 LEAVE"]++ }
            }
        }
        Write-Output ("x86 opcode scan of 0x{0:X}..0x{1:X} ({2} bytes):" -f $start, $end, $total)
        foreach ($k in $tbl.Keys | Sort-Object) { Write-Output ("  {0,-14} {1}" -f $k, $tbl[$k]) }
        Write-Output ("  NOTE: x86 is a byte stream; use with -Pattern for context.")
        return
    }

    # Signature tables: name -> scoring. 68k is big-endian, 16-bit words.
    # We count aligned 16-bit words matching common instruction encodings.
    if ($Arch -eq "68k") {
        $word2 = @{
            "4E75 RTS"  = 0;
            "4E71 NOP"  = 0;
            "4E56 LINK" = 0;
            "4E5E UNLK" = 0;
            "4EB9 JSR"  = 0;
            "4EF9 JMP"  = 0;
            "48E7 MOVEMpush" = 0;
            "4CDF MOVEMpop"  = 0;
            "6000 BRA.w" = 0;
            "4E73 RTE"  = 0;
        }
        $total = 0
        for ($i = $start; $i -lt $end - 1; $i += 2) {
            $w = ($b[$i] -shl 8) -bor $b[$i + 1]
            $total++
            switch ($w) {
                0x4E75 { $word2["4E75 RTS"]++ }
                0x4E71 { $word2["4E71 NOP"]++ }
                0x4E56 { $word2["4E56 LINK"]++ }
                0x4E5E { $word2["4E5E UNLK"]++ }
                0x4EB9 { $word2["4EB9 JSR"]++ }
                0x4EF9 { $word2["4EF9 JMP"]++ }
                0x48E7 { $word2["48E7 MOVEMpush"]++ }
                0x4CDF { $word2["4CDF MOVEMpop"]++ }
                0x6000 { $word2["6000 BRA.w"]++ }
                0x4E73 { $word2["4E73 RTE"]++ }
            }
        }
        $sum = 0
        Write-Output ("68k opcode scan of 0x{0:X}..0x{1:X} ({2} words):" -f $start, $end, $total)
        foreach ($k in $word2.Keys | Sort-Object) {
            Write-Output ("  {0,-16} {1}" -f $k, $word2[$k])
            $sum += $word2[$k]
        }
        $density = if ($total -gt 0) { $sum / [double]$total } else { 0 }
        Write-Output ("  --- signature words: {0}  density: {1:P3}" -f $sum, $density)
        Write-Output ("  Heuristic: >~0.5% RTS/JSR/LINK density is consistent with real 68k code.")
    } else {
        throw "Unknown -Arch '$Arch'. Supported: 68k, x86 (extend the table for more)."
    }
}

function Cmd-Extract {
    $b = Get-ImageBytes $Image
    if ([string]::IsNullOrEmpty($Out)) { throw "Provide -Out <path>" }
    Assert-NotOriginal $Out
    $start = Parse-Num $Offset
    $span = Parse-Num $Length
    $end = [Math]::Min($start + $span, $b.Length)
    $slice = New-Object 'byte[]' ($end - $start)
    [Array]::Copy($b, $start, $slice, 0, $slice.Length)
    $dir = Split-Path $Out -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllBytes($Out, $slice)
    Write-Output ("Extracted 0x{0:X} bytes from 0x{1:X} -> {2}" -f $slice.Length, $start, $Out)
}

function Cmd-CopyWork {
    $b = Get-ImageBytes $Image
    if ([string]::IsNullOrEmpty($Out)) { $Out = "temp\work\S760224.work.img" }
    Assert-NotOriginal $Out
    $dir = Split-Path $Out -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllBytes($Out, $b)
    Write-Output ("Working copy created: {0} ({1} bytes)" -f $Out, $b.Length)
}

function Cmd-Patch {
    if ([string]::IsNullOrEmpty($In)) { throw "Provide -In <path>" }
    if ([string]::IsNullOrEmpty($Out)) { throw "Provide -Out <path>" }
    if ([string]::IsNullOrEmpty($Bytes)) { throw "Provide -Bytes <hex>" }
    Assert-NotOriginal $Out
    $b = Get-ImageBytes $In
    $at = Parse-Num $Offset
    $hex = ($Bytes -replace '\s', '')
    if ($hex.Length % 2 -ne 0) { throw "Hex bytes must have even length" }
    $patch = New-Object 'byte[]' ($hex.Length / 2)
    for ($i = 0; $i -lt $patch.Length; $i++) {
        $patch[$i] = [Convert]::ToByte($hex.Substring($i * 2, 2), 16)
    }
    if ($at + $patch.Length -gt $b.Length) { throw "Patch would exceed image bounds" }
    $oldStr = ""
    $newStr = ""
    for ($i = 0; $i -lt $patch.Length; $i++) {
        $oldStr += "{0:X2} " -f $b[$at + $i]
        $newStr += "{0:X2} " -f $patch[$i]
        $b[$at + $i] = $patch[$i]
    }
    $dir = Split-Path $Out -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllBytes($Out, $b)
    Write-Output ("Patched 0x{0:X}: [{1}] -> [{2}]" -f $at, $oldStr.Trim(), $newStr.Trim())
    Write-Output ("Wrote {0} ({1} bytes)" -f $Out, $b.Length)
}

function Cmd-Repack {
    if ([string]::IsNullOrEmpty($In)) { throw "Provide -In <path>" }
    if ([string]::IsNullOrEmpty($Out)) { throw "Provide -Out <path>" }
    Assert-NotOriginal $Out
    $b = Get-ImageBytes $In
    if ($b.Length -ne $EXPECTED_SIZE) {
        throw ("Refusing to repack: size is {0}, expected {1} (0x{2:X})" -f $b.Length, $EXPECTED_SIZE, $EXPECTED_SIZE)
    }
    # TODO: recompute loader checksum(s) here once the format is known.
    $dir = Split-Path $Out -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [System.IO.File]::WriteAllBytes($Out, $b)
    Write-Output ("Repacked -> {0} ({1} bytes, size OK)" -f $Out, $b.Length)
    Write-Output ("NOTE: checksum recomputation not yet implemented (see TODO).")
}

function Cmd-Histogram {
    $b = Get-ImageBytes $Image
    $start = Parse-Num $Offset
    $span = Parse-Num $Length
    if ($span -le 0) { $end = $b.Length } else { $end = [Math]::Min($start + $span, $b.Length) }
    $counts = New-Object 'int[]' 256
    for ($i = $start; $i -lt $end; $i++) { $counts[$b[$i]]++ }
    $n = $end - $start
    Write-Output ("Byte histogram of 0x{0:X}..0x{1:X} ({2} bytes). Top 24 by frequency:" -f $start, $end, $n)
    $ranked = 0..255 | Sort-Object { -$counts[$_] }
    foreach ($v in $ranked[0..23]) {
        $pct = 100.0 * $counts[$v] / $n
        $bar = "#" * [int]([Math]::Round($pct))
        $ch = if ($v -ge 32 -and $v -lt 127) { [char]$v } else { '.' }
        Write-Output ("  {0:X2} '{1}'  {2,8}  {3,6:N2}%  {4}" -f $v, $ch, $counts[$v], $pct, $bar)
    }
}

function Cmd-Help {
    Write-Output "s760.ps1 commands: info | dump | map | strings | entropy | find | opcodes | extract | copywork | patch | repack"
    Write-Output "See SKILL.md for options and examples."
}

switch ($Command.ToLower()) {
    "info"     { Cmd-Info }
    "dump"     { Cmd-Dump }
    "map"      { Cmd-Map }
    "strings"  { Cmd-Strings }
    "entropy"  { Cmd-Entropy }
    "find"     { Cmd-Find }
    "opcodes"  { Cmd-Opcodes }
    "histogram" { Cmd-Histogram }
    "hist"     { Cmd-Histogram }
    "extract"  { Cmd-Extract }
    "copywork" { Cmd-CopyWork }
    "patch"    { Cmd-Patch }
    "repack"   { Cmd-Repack }
    default    { Cmd-Help }
}

$c_files = Get-ChildItem -Path "d:\S-760\mame-source\3rdparty\genie\src\host" -Recurse -Filter "*.c" | Where-Object { $_.Name -ne "lua.c" -and $_.Name -ne "luac.c" } | Select-Object -ExpandProperty FullName
$inc = "d:\S-760\mame-source\3rdparty\genie\src\host\lua-5.3.0\src"

$cmd = "`"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat`" && cl /Fe:d:\S-760\mame-source\genie.exe /I `"$inc`" /D `"PLATFORM_WINDOWS`" /D `"LUA_COMPAT_MODULE`" /D `"NDEBUG`" " + ($c_files -join " ") + " Ole32.lib User32.lib Advapi32.lib"
cmd /c $cmd

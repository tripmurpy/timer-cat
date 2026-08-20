$ErrorActionPreference = 'Stop'
$installDir = Join-Path $env:LOCALAPPDATA 'CuteTimer'
$scriptPath = Join-Path $PSScriptRoot 'app.py'
$commandPath = Join-Path $installDir 'timer.cmd'
$pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source

New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Set-Content -LiteralPath $commandPath -Encoding ASCII -Value "@start `"`" `"$pythonw`" `"$scriptPath`" %*"

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$parts = @($userPath -split ';' | Where-Object { $_ })
if ($installDir -notin $parts) {
    [Environment]::SetEnvironmentVariable('Path', (($parts + $installDir) -join ';'), 'User')
}
$env:Path = "$installDir;$env:Path"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Cute Timer.lnk'))
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = "`"$scriptPath`""
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Save()

Write-Host 'Terpasang. Buka lewat shortcut Cute Timer di Desktop atau ketik: timer'

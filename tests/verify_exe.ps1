$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $repo 'dist\AnythingToPDF.exe'

if (-not (Test-Path -LiteralPath $exe)) {
    throw "EXE not found: $exe"
}

$process = Start-Process -FilePath $exe -ArgumentList '--self-test' -PassThru -Wait
if ($process.ExitCode -ne 0) {
    throw "EXE self-test failed with exit code $($process.ExitCode)"
}

Write-Output "EXE self-test passed: $exe"
